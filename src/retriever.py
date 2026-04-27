# src/retriever.py
import os
import re
import json
import pickle
import time
from typing import List, Dict

import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

# ── Path setup ────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_DIR = os.path.join(BASE_DIR, "..", "index")

EMBEDDING_MODEL  = "BAAI/bge-small-en-v1.5"
COLLECTION_NAME  = "bis_standards"
RRF_K            = 60      # RRF constant — higher = smoother rank fusion
TOP_N_RETRIEVE   = 20      # candidates before reranking
TOP_N_RETURN     = 5       # final results returned

# ── Singleton loader — load once, reuse across queries ────────────────────────

_model      = None
_collection = None
_bm25_data  = None
_lookup     = None


def _load_resources(index_dir: str = None):
    global _model, _collection, _bm25_data, _lookup

    if _model is not None:
        return  # already loaded

    if index_dir is None:
        index_dir = INDEX_DIR

    print("🔄 Loading retrieval resources...")

    # Embedding model
    _model = SentenceTransformer(EMBEDDING_MODEL)

    # ChromaDB
    chroma_path = os.path.join(index_dir, "chroma")
    client      = chromadb.PersistentClient(path=chroma_path)
    _collection = client.get_collection(COLLECTION_NAME)

    # BM25
    bm25_path  = os.path.join(index_dir, "bm25.pkl")
    with open(bm25_path, "rb") as f:
        _bm25_data = pickle.load(f)

    # Lookup
    lookup_path = os.path.join(index_dir, "lookup.json")
    with open(lookup_path, encoding="utf-8") as f:
        _lookup = json.load(f)

    print("✓ Resources loaded\n")


# ── Tokenizer (same as indexer) ───────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    return re.sub(r"[^\w\s]", " ", text.lower()).split()


# ── RRF fusion ────────────────────────────────────────────────────────────────

def _rrf_fusion(
    dense_codes:  List[str],
    sparse_codes: List[str],
    k: int = RRF_K,
) -> List[str]:
    """
    Reciprocal Rank Fusion.
    Returns IS codes sorted by fused score descending.
    """
    scores = {}

    for rank, code in enumerate(dense_codes, start=1):
        scores[code] = scores.get(code, 0.0) + 1.0 / (k + rank)

    for rank, code in enumerate(sparse_codes, start=1):
        scores[code] = scores.get(code, 0.0) + 1.0 / (k + rank)

    return sorted(scores, key=lambda c: scores[c], reverse=True)


# ── Core retrieval ────────────────────────────────────────────────────────────

def retrieve(
    query:      str,
    top_n:      int = TOP_N_RETURN,
    index_dir:  str = None,
) -> List[Dict]:
    """
    Hybrid retrieval pipeline:
    1. Dense search  (BGE embeddings + ChromaDB cosine)
    2. Sparse search (BM25)
    3. RRF fusion
    4. Return top_n standard objects with scores

    Returns list of dicts:
    {
        "is_code":    "IS 383 : 1970",
        "title":      "...",
        "scope":      "...",
        "section_name": "...",
        "rrf_score":  0.032,
    }
    """
    _load_resources(index_dir)

    # ── 1. Dense retrieval ────────────────────────────────────────────────────
    q_embedding = _model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    dense_results = _collection.query(
        query_embeddings=[q_embedding],
        n_results=TOP_N_RETRIEVE,
    )
    dense_codes = [m["is_code"] for m in dense_results["metadatas"][0]]

    # ── 2. Sparse retrieval (BM25) ────────────────────────────────────────────
    tokens     = _tokenize(query)
    bm25       = _bm25_data["bm25"]
    is_codes   = _bm25_data["is_codes"]
    scores     = bm25.get_scores(tokens)
    top_idx    = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:TOP_N_RETRIEVE]
    sparse_codes = [is_codes[i] for i in top_idx]

    # ── 3. RRF fusion ─────────────────────────────────────────────────────────
    fused = _rrf_fusion(dense_codes, sparse_codes)

    # ── 4. Build result objects ───────────────────────────────────────────────
    results = []
    rrf_scores = {}

    # Recompute scores for annotation
    for rank, code in enumerate(dense_codes, start=1):
        rrf_scores[code] = rrf_scores.get(code, 0.0) + 1.0 / (RRF_K + rank)
    for rank, code in enumerate(sparse_codes, start=1):
        rrf_scores[code] = rrf_scores.get(code, 0.0) + 1.0 / (RRF_K + rank)

    for code in fused[:top_n]:
        standard = _lookup.get(code)
        if not standard:
            continue
        results.append({
            "is_code":      standard["is_code"],
            "title":        standard["title"],
            "scope":        standard["scope"],
            "section_name": standard["section_name"],
            "subcategory":  standard["subcategory"],
            "year":         standard.get("year"),
            "rrf_score":    round(rrf_scores.get(code, 0.0), 6),
        })

    return results


def retrieve_codes_only(query: str, top_n: int = TOP_N_RETURN) -> List[str]:
    """
    Lightweight version for inference.py — returns just IS code strings.
    """
    results = retrieve(query, top_n=top_n)
    return [r["is_code"] for r in results]


# ── Smoke test ────────────────────────────────────────────────────────────────

def _smoke_test():
    """Run all 10 public test queries and report Hit Rate @3 and MRR @5."""

    TEST_CASES = [
        ("We are a small enterprise manufacturing 33 Grade Ordinary Portland Cement. Which BIS standard covers the chemical and physical requirements for our product?",
         "IS 269 : 1989"),
        ("I need to comply with the regulations for coarse and fine aggregates derived from natural sources intended for use in structural concrete.",
         "IS 383 : 1970"),
        ("What is the official specification for manufacturing precast concrete pipes, both with and without reinforcement, for water mains?",
         "IS 458 : 2003"),
        ("Our company is shifting to manufacturing hollow and solid lightweight concrete masonry blocks. What standard outlines the dimensions and physical requirements?",
         "IS 2185 (Part 2) : 1983"),
        ("Looking for the standard detailing corrugated and semi-corrugated asbestos cement sheets used for roofing and cladding.",
         "IS 459 : 1992"),
        ("What is the Indian Standard covering the manufacture, chemical, and physical requirements for Portland slag cement?",
         "IS 455 : 1989"),
        ("We are setting up a plant to produce Portland pozzolana cement that is calcined clay based. What is the applicable standard?",
         "IS 1489 (Part 2) : 1991"),
        ("Which standard applies to masonry cement used for general purposes where mortars for masonry are required, but not intended for structural concrete?",
         "IS 3466 : 1988"),
        ("Looking for the standard that details the composition, manufacture, and testing of supersulphated cement, particularly for marine works or aggressive water conditions.",
         "IS 6909 : 1990"),
        ("Our company manufactures White Portland cement for architectural and decorative purposes. Which standard governs its physical and chemical requirements?",
         "IS 8042 : 1989"),
    ]

    print("── Public test set evaluation ──────────────────────")
    hits_at_3  = 0
    mrr_sum    = 0.0

    for query, expected in TEST_CASES:
        start   = time.time()
        results = retrieve(query, top_n=5)
        latency = time.time() - start
        codes   = [r["is_code"] for r in results]

        hit = expected in codes[:3]
        if hit:
            hits_at_3 += 1

        mrr = 0.0
        for rank, code in enumerate(codes[:5], start=1):
            if code == expected:
                mrr = 1.0 / rank
                break
        mrr_sum += mrr

        status = "✓" if hit else "✗"
        rank_str = f"rank {codes.index(expected) + 1}" if expected in codes else "not found"
        print(f"  {status} [{rank_str:10s}] ({latency:.2f}s) {expected}")

    n = len(TEST_CASES)
    print(f"\n  Hit Rate @3 : {hits_at_3}/{n} = {hits_at_3/n*100:.1f}%  (target >80%)")
    print(f"  MRR @5      : {mrr_sum/n:.4f}              (target >0.7)")
    print("────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    _load_resources()
    _smoke_test()