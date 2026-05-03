# src/auth.py
import os
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# ── Config ──────────────────────────────────────────────────────────────────
# Load from .env
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-for-dev")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()

# Mock DB (In a real app, use SQLite/Postgres)
users_db = {}

# ── Pydantic Models ─────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    password: str

class HistoryItem(BaseModel):
    query: str

class SavedStandard(BaseModel):
    is_code: str
    title: str
    scope: str
    section_name: str
    subcategory: Optional[str] = ""
    year: Optional[int] = None
    rrf_score: float
    rationale: Optional[str] = None

# ── Helper Functions ─────────────────────────────────────────────────────────
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ── Dependency to Protect Routes ─────────────────────────────────────────────
# This MUST be defined before the routes that use it
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    if username not in users_db:
        raise credentials_exception
        
    return username

# ── Auth Routes ──────────────────────────────────────────────────────────────

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    users_db[user.username] = {
        "username": user.username,
        "hashed_password": get_password_hash(user.password),
        "history": [],
        "saved": []
    }
    return {"message": "User created successfully"}

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = users_db.get(form_data.username)
    if not user_dict or not verify_password(form_data.password, user_dict["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user_dict["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

# ── User Data Endpoints ───────────────────────────────────────────────────────

@router.post("/user/delete") 
async def delete_account(username: str = Depends(get_current_user)):
    if username in users_db:
        del users_db[username]
        return {"message": "Account deleted successfully"}
    raise HTTPException(status_code=404, detail="User not found")

@router.get("/user/data")
async def get_user_data(username: str = Depends(get_current_user)):
    user = users_db.get(username, {})
    return {
        "history": user.get("history", []),
        "saved": user.get("saved", [])
    }

@router.post("/user/history")
async def add_history(item: HistoryItem, username: str = Depends(get_current_user)):
    user = users_db[username]
    if item.query in user["history"]:
        user["history"].remove(item.query) 
    user["history"].insert(0, item.query)
    return {"history": user["history"]}

@router.post("/user/saved")
async def toggle_saved(standard: SavedStandard, username: str = Depends(get_current_user)):
    user = users_db[username]
    saved_list = user.get("saved", [])
    
    existing = [s for s in saved_list if s["is_code"] == standard.is_code]
    
    if existing:
        user["saved"] = [s for s in saved_list if s["is_code"] != standard.is_code]
    else:
        user["saved"].append(standard.dict())
        
    return {"saved": user["saved"]}