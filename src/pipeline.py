# src/pipeline.py
import os
import re
import json
import time
from typing import List, Dict
from dotenv import load_dotenv
from mistralai import Mistral

# ── Setup ─────────────────────────────────────────────────────────────────────

load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MISTRAL_MODEL = "mistral-small-latest"
MAX_RATIONALE = 80
TOP_N         = 5

# ── Helpers ───────────────────────────────────────────────────────────────────

def _clean_scope_for_display(scope: str, max_chars: int = 180) -> str:
    match = re.search(r"\.(\s|$)", scope)
    if match and match.start() > 30:
        return scope[:match.start() + 1].strip()
    return scope[:max_chars].strip()


def _is_meaningful_query(query: str) -> bool:
    """
    Local guard — zero API calls.
    Rejects greetings and nonsense without touching Mistral.
    """
    q = query.strip().lower()

    if len(q) < 8:
        return False

    GREETINGS = {
        "hello", "hi", "hey", "howdy", "hiya", "sup",
        "good morning", "good evening", "good afternoon",
        "how are you", "what's up", "whats up",
        "thanks", "thank you", "ok", "okay", "test",
    }
    if q in GREETINGS:
        return False

    # Must have at least 2 words longer than 4 chars
    words = re.findall(r"[a-z]{4,}", q)
    if len(words) < 2:
        return False

    return True


# ── Mistral client — lazy init ────────────────────────────────────────────────

_client = None

def _get_client():
    global _client
    if _client is not None:
        return _client
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not set in .env")
    _client = Mistral(api_key=api_key)
    return _client


# ── Rationale generation ──────────────────────────────────────────────────────

def _generate_rationale(
    query:     str,
    standards: List[Dict],
) -> List[Dict]:
    """
    Single Mistral call — generates rationale for all standards at once.
    Falls back to clean scope text on any failure.
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
            response = client.chat.complete(
                model=MISTRAL_MODEL,
                messages=[{"role": "user", "content": prompt}],
            )
            text = (
                response.choices[0].message.content.strip()
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
            is_rate_limit = (
                "429"               in str(e) or
                "rate"              in str(e).lower() or
                "too many requests" in str(e).lower()
            )
            if is_rate_limit and attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[attempt]
                print(f"  ⚠ Rate limited — retrying in {delay}s "
                      f"(attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(delay)
                continue
            else:
                print(f"  ⚠ Mistral failed: {e} — using scope fallback")
                break

    for s in standards:
        s["rationale"] = _clean_scope_for_display(s["scope"])
    return standards


# ── Main pipeline ─────────────────────────────────────────────────────────────

def recommend(
    query:          str,
    top_n:          int  = TOP_N,
    with_rationale: bool = True,
) -> Dict:
    """
    Full pipeline — max 1 LLM call (rationale only).
    Query validation is local, zero API calls.
    """
    start = time.time()

    if not _is_meaningful_query(query):
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
    """Fast path for inference.py — zero LLM calls."""
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