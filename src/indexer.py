# src/indexer.py
import json
import os
import sys
import pickle
from pathlib import Path
from tqdm import tqdm

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

# ── Path setup ────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
INDEX_DIR = os.path.join(BASE_DIR, "..", "index")

# ── Config ────────────────────────────────────────────────────────────────────

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
COLLECTION_NAME = "bis_standards"

# ── Helpers ───────────────────────────────────────────────────────────────────

def build_document(standard: dict) -> str:
    """
    Build the text we embed for each standard.
    Combines the most semantically rich fields.
    IS code is included so exact-code queries work via dense search too.
    """
    parts = [
        standard["is_code"],
        standard["title"],
        standard["scope"],
        standard["section_name"],
        standard["subcategory"],
        " ".join(standard.get("keywords", [])),
    ]
    return " | ".join(p for p in parts if p)


def build_bm25_tokens(standard: dict) -> list:
    """
    Tokenize for BM25 — combines title, scope, keywords, IS code.
    Lowercased, split on whitespace and punctuation.
    """
    import re
    text = " ".join([
        standard["is_code"],
        standard["title"],
        standard["scope"],
        " ".join(standard.get("keywords", [])),
    ])
    tokens = re.sub(r"[^\w\s]", " ", text.lower()).split()
    return tokens


# ── Main indexer ──────────────────────────────────────────────────────────────

def build_index(
    standards_path: str = None,
    index_dir: str = None,
):
    if standards_path is None:
        standards_path = os.path.join(DATA_DIR, "standards.json")
    if index_dir is None:
        index_dir = INDEX_DIR

    # Load standards
    print(f"📂 Loading standards from {standards_path}...")
    with open(standards_path, encoding="utf-8") as f:
        standards = json.load(f)
    print(f"✓ Loaded {len(standards)} standards")

    Path(index_dir).mkdir(parents=True, exist_ok=True)

    # ── 1. Dense index (ChromaDB + BGE embeddings) ────────────────────────────

    print(f"\n🔢 Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("✓ Model loaded")

    chroma_path = os.path.join(index_dir, "chroma")
    client = chromadb.PersistentClient(path=chroma_path)

    # Delete existing collection if rebuilding
    try:
        client.delete_collection(COLLECTION_NAME)
        print("🗑  Deleted existing ChromaDB collection")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    print(f"\n📐 Embedding {len(standards)} standards...")

    # Batch embed for speed
    BATCH_SIZE = 64
    all_ids       = []
    all_documents = []
    all_metadatas = []

    for s in standards:
        all_ids.append(s["is_code"])
        all_documents.append(build_document(s))
        all_metadatas.append({
            "is_code":        s["is_code"],
            "title":          s["title"][:500],
            "section_number": s["section_number"],
            "section_name":   s["section_name"],
            "subcategory":    s["subcategory"],
            "year":           s.get("year") or 0,
            "scope":          s["scope"][:500],
        })

    embeddings = []
    for i in tqdm(range(0, len(all_documents), BATCH_SIZE),
                  desc="Embedding batches", unit="batch", ncols=80):
        batch = all_documents[i:i + BATCH_SIZE]
        batch_embeddings = model.encode(
            batch,
            normalize_embeddings=True,  # required for cosine similarity
            show_progress_bar=False,
        )
        embeddings.extend(batch_embeddings.tolist())

    print("💾 Adding to ChromaDB...")
    for i in tqdm(range(0, len(all_ids), BATCH_SIZE),
                  desc="Inserting", unit="batch", ncols=80):
        collection.add(
            ids=all_ids[i:i + BATCH_SIZE],
            documents=all_documents[i:i + BATCH_SIZE],
            embeddings=embeddings[i:i + BATCH_SIZE],
            metadatas=all_metadatas[i:i + BATCH_SIZE],
        )

    print(f"✓ ChromaDB index built: {collection.count()} documents")

    # ── 2. Sparse index (BM25) ────────────────────────────────────────────────

    print(f"\n📚 Building BM25 index...")
    tokenized_corpus = []
    for s in tqdm(standards, desc="Tokenizing", unit="std", ncols=80):
        tokenized_corpus.append(build_bm25_tokens(s))

    bm25 = BM25Okapi(tokenized_corpus)

    # Save BM25 + corpus metadata for retrieval
    bm25_data = {
        "bm25":       bm25,
        "is_codes":   [s["is_code"] for s in standards],
        "corpus":     tokenized_corpus,
    }
    bm25_path = os.path.join(index_dir, "bm25.pkl")
    with open(bm25_path, "wb") as f:
        pickle.dump(bm25_data, f)

    print(f"✓ BM25 index saved to {bm25_path}")

    # ── 3. Standards lookup map ───────────────────────────────────────────────
    # Fast O(1) lookup by IS code for retrieval step

    print(f"\n🗺  Building standards lookup map...")
    lookup = {s["is_code"]: s for s in standards}
    lookup_path = os.path.join(index_dir, "lookup.json")
    with open(lookup_path, "w", encoding="utf-8") as f:
        json.dump(lookup, f, ensure_ascii=False)
    print(f"✓ Lookup map saved: {len(lookup)} entries")

    print(f"\n{'='*50}")
    print(f"  Index build complete")
    print(f"  ChromaDB : {chroma_path}")
    print(f"  BM25     : {bm25_path}")
    print(f"  Lookup   : {lookup_path}")
    print(f"{'='*50}\n")

    return collection, bm25_data, lookup


# ── Smoke test ────────────────────────────────────────────────────────────────

def smoke_test(index_dir: str = None):
    """Quick sanity check — run 3 queries against the built index."""
    if index_dir is None:
        index_dir = INDEX_DIR

    import re
    import pickle
    from sentence_transformers import SentenceTransformer

    print("\n── Smoke test ──────────────────────────────────────")

    # Load ChromaDB
    chroma_path = os.path.join(index_dir, "chroma")
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection(COLLECTION_NAME)

    # Load BM25
    bm25_path = os.path.join(index_dir, "bm25.pkl")
    with open(bm25_path, "rb") as f:
        bm25_data = pickle.load(f)
    bm25     = bm25_data["bm25"]
    is_codes = bm25_data["is_codes"]

    # Load model
    model = SentenceTransformer(EMBEDDING_MODEL)

    TEST_QUERIES = [
        ("33 Grade Ordinary Portland Cement chemical requirements",
         "IS 269 : 1989"),
        ("coarse and fine aggregates natural sources structural concrete",
         "IS 383 : 1970"),
        ("Portland pozzolana cement calcined clay based",
         "IS 1489 (Part 2) : 1991"),
    ]

    for query, expected in TEST_QUERIES:
        print(f"\n  Query    : {query[:60]}")
        print(f"  Expected : {expected}")

        # Dense retrieval
        q_emb = model.encode(query, normalize_embeddings=True).tolist()
        dense_results = collection.query(
            query_embeddings=[q_emb],
            n_results=5,
        )
        dense_codes = [m["is_code"] for m in dense_results["metadatas"][0]]

        # Sparse retrieval
        tokens = re.sub(r"[^\w\s]", " ", query.lower()).split()
        scores = bm25.get_scores(tokens)
        top5_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:5]
        sparse_codes = [is_codes[i] for i in top5_idx]

        print(f"  Dense top-5  : {dense_codes}")
        print(f"  Sparse top-5 : {sparse_codes}")

        dense_hit  = expected in dense_codes
        sparse_hit = expected in sparse_codes
        print(f"  Dense hit  : {'✓' if dense_hit else '✗'}")
        print(f"  Sparse hit : {'✓' if sparse_hit else '✗'}")

    print("\n────────────────────────────────────────────────────\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":

    standards_path = (
        sys.argv[1] if len(sys.argv) > 1
        else os.path.join(DATA_DIR, "standards.json")
    )
    index_dir = (
        sys.argv[2] if len(sys.argv) > 2
        else INDEX_DIR
    )

    if not os.path.exists(standards_path):
        print(f"✗ standards.json not found: {standards_path}")
        print(f"  Run parser.py first.")
        sys.exit(1)

    print(f"📂 Standards : {standards_path}")
    print(f"📂 Index dir : {index_dir}\n")

    build_index(standards_path, index_dir)
    smoke_test(index_dir)