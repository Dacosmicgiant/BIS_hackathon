# src/pipeline.py
import os
import re
import json
import time
from typing import List, Dict
from dotenv import load_dotenv
from google import genai

# ── Setup ─────────────────────────────────────────────────────────────────────

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GEMINI_MODEL  = "gemini-2.0-flash-lite"
MAX_RATIONALE = 80
TOP_N         = 5

# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean_scope_for_display(scope: str, max_chars: int = 180) -> str:
    """Truncate scope at first full sentence for clean fallback display."""
    match = re.search(r"\.(\s|$)", scope)
    if match and match.start() > 30:
        return scope[:match.start() + 1].strip()
    return scope[:max_chars].strip()


# ── Gemini client — lazy init ─────────────────────────────────────────────────

_client = None

def _get_client():
    global _client
    if _client is not None:
        return _client
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in .env")
    _client = genai.Client(api_key=api_key)
    return _client


# ── Query validator ───────────────────────────────────────────────────────────

def _is_valid_product_query(query: str) -> bool:
    """
    Check if query is product/compliance related.
    Falls back to True (permissive) if Gemini is unavailable.
    """
    prompt = f"""Is the following query asking about a product, manufacturing process,
building material, or BIS/regulatory compliance requirement?

Query: "{query}"

Reply with only: YES or NO"""

    try:
        client   = _get_client()
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text.strip().upper().startswith("YES")
    except Exception:
        return True  # permissive fallback


# ── Rationale generation ──────────────────────────────────────────────────────

def _generate_rationale(
    query:     str,
    standards: List[Dict],
) -> List[Dict]:
    """
    Call Gemini Flash Lite to generate rationale per standard.
    Retries up to 3 times on rate limit with exponential backoff.
    Falls back to clean scope text if all retries fail.
    """
    standards_block = "\n".join([
        f"{i+1}. {s['is_code']} — {s['title']}\n   Scope: {s['scope'][:300]}"
        for i, s in enumerate(standards)
    ])

    prompt = f"""You are a BIS (Bureau of Indian Standards) compliance expert helping Indian MSEs.

A business has described their product or compliance need as:
"{query}"

The following BIS standards have been identified as potentially applicable:
{standards_block}

For each standard, write a single concise sentence (max {MAX_RATIONALE} words) explaining
specifically WHY it applies to this product/need. Be direct and practical.
Use plain English that a small business owner can understand.

Respond ONLY with a valid JSON array in this exact format:
[
  {{"is_code": "IS XXX : YYYY", "rationale": "..."}},
  ...
]"""

    MAX_RETRIES  = 3
    RETRY_DELAYS = [5, 15, 30]

    for attempt in range(MAX_RETRIES):
        try:
            client   = _get_client()
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            text = (
                response.text.strip()
                .removeprefix("```json")
                .removeprefix("```")
                .removesuffix("```")
                .strip()
            )

            rationales    = json.loads(text)
            rationale_map = {r["is_code"]: r["rationale"] for r in rationales}

            for s in standards:
                s["rationale"] = rationale_map.get(
                    s["is_code"],
                    _clean_scope_for_display(s["scope"])
                )
            return standards

        except Exception as e:
            is_rate_limit = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
            if is_rate_limit and attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                print(f"  ⚠ Rate limited — retrying in {delay}s "
                      f"(attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
                continue
            else:
                print(f"  ⚠ Gemini failed: {e} — using scope fallback")
                break

    # Fallback
    for s in standards:
        s["rationale"] = _clean_scope_for_display(s["scope"])

    return standards


# ── Main pipeline ─────────────────────────────────────────────────────────────

def recommend(
    query:          str,
    top_n:          int  = TOP_N,
    with_rationale: bool = True,
) -> Dict:
    start = time.time()

    # Guard — reject non-product queries
    if not _is_valid_product_query(query):
        return {
            "query":           query,
            "standards":       [],
            "latency_seconds": round(time.time() - start, 4),
            "message":         "Please describe a product or manufacturing process to get BIS standard recommendations.",
        }

    from retriever import retrieve
    results = retrieve(query, top_n=top_n)

    if with_rationale and results:
        results = _generate_rationale(query, results)

    return {
        "query":           query,
        "standards":       results,
        "latency_seconds": round(time.time() - start, 4),
        "message":         None,
    }


def recommend_codes_only(query: str, top_n: int = TOP_N) -> List[str]:
    """
    Fast path for inference.py.
    Pure retrieval — zero Gemini calls, no validator, no rationale.
    """
    from retriever import retrieve
    results = retrieve(query, top_n=top_n)
    return [r["is_code"] for r in results]


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    query = (
        sys.argv[1] if len(sys.argv) > 1
        else "We manufacture hollow concrete blocks for load bearing walls"
    )

    print(f"\n🔍 Query: {query}\n")
    result = recommend(query, with_rationale=True)
    print(f"⏱  Latency: {result['latency_seconds']}s\n")

    if result["message"]:
        print(f"⚠  {result['message']}")
    else:
        print("📋 Recommended Standards:")
        print("─" * 60)
        for i, s in enumerate(result["standards"], 1):
            print(f"\n{i}. {s['is_code']}")
            print(f"   {s['title']}")
            print(f"   Section  : {s['section_name']}")
            print(f"   Rationale: {s.get('rationale', _clean_scope_for_display(s['scope']))}")
    print()