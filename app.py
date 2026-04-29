# app.py  (project root)
import sys
import os
import json
import time
import tempfile
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from pipeline import recommend, recommend_codes_only
from retriever import _load_resources

# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app):
    print("🚀 Warming up retrieval resources...")
    _load_resources()
    print("✓ Ready")
    yield

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="BIS Copilot API",
    description="AI-powered BIS standard recommendation engine for Indian MSEs",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Schema ────────────────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    query:          str
    top_n:          Optional[int]  = 5
    with_rationale: Optional[bool] = True

class StandardResult(BaseModel):
    is_code:      str
    title:        str
    scope:        str
    section_name: str
    subcategory:  str
    year:         Optional[int]
    rrf_score:    float
    rationale:    Optional[str] = None

class RecommendResponse(BaseModel):
    query:           str
    standards:       list[StandardResult]
    latency_seconds: float
    message:         Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": time.time()}


@app.post("/recommend", response_model=RecommendResponse)
def recommend_standards(req: RecommendRequest):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    if len(req.query) > 2000:
        raise HTTPException(status_code=400, detail="Query too long (max 2000 chars)")

    top_n = max(1, min(req.top_n or 5, 10))

    try:
        result = recommend(
            query=req.query.strip(),
            top_n=top_n,
            with_rationale=req.with_rationale,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return RecommendResponse(
        query=result["query"],
        standards=[StandardResult(**s) for s in result["standards"]],
        latency_seconds=result["latency_seconds"],
        message=result.get("message"),
    )


@app.get("/recommend")
def recommend_get(query: str, top_n: int = 5, with_rationale: bool = True):
    return recommend_standards(RecommendRequest(
        query=query,
        top_n=top_n,
        with_rationale=with_rationale,
    ))


@app.post("/export")
def export_report(req: RecommendRequest):
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    try:
        from exporter import generate_pdf

        result = recommend(
            query=req.query.strip(),
            top_n=req.top_n or 5,
            with_rationale=req.with_rationale,
        )

        if not result["standards"]:
            raise HTTPException(status_code=404, detail="No standards found")

        tmp  = tempfile.NamedTemporaryFile(
            suffix=".pdf", delete=False, prefix="BIS_Report_"
        )
        path = generate_pdf(
            query=result["query"],
            standards=result["standards"],
            output_path=tmp.name,
        )

        return FileResponse(
            path=path,
            media_type="application/pdf",
            filename="BIS_Compliance_Report.pdf",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/standard/{is_code:path}")
def get_standard(is_code: str):
    lookup_path = os.path.join(
        os.path.dirname(__file__), "index", "lookup.json"
    )
    try:
        with open(lookup_path, encoding="utf-8") as f:
            lookup = json.load(f)
    except Exception:
        raise HTTPException(status_code=500, detail="Lookup index not found")

    standard = lookup.get(is_code)
    if not standard:
        is_code_lower = is_code.lower().replace(" ", "")
        for code, std in lookup.items():
            if code.lower().replace(" ", "") == is_code_lower:
                standard = std
                break

    if not standard:
        raise HTTPException(
            status_code=404,
            detail=f"Standard '{is_code}' not found"
        )

    return standard


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)