# inference.py  (project root — judge entry point)
import json
import argparse
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from retriever import _load_resources
from pipeline import recommend_codes_only


def main():
    parser = argparse.ArgumentParser(
        description="BIS Copilot — Inference Entry Point"
    )
    parser.add_argument("--input",  required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"✗ Input file not found: {args.input}")
        sys.exit(1)

    # Pre-warm — load model and index BEFORE timing queries
    print("🔄 Pre-loading retrieval resources...")
    _load_resources()
    print("✓ Ready\n")

    with open(args.input, encoding="utf-8") as f:
        queries = json.load(f)

    print(f"📥 Loaded {len(queries)} queries")

    results     = []
    total_start = time.time()

    for i, item in enumerate(queries):
        query_id = item.get("id", f"Q-{i+1}")
        query    = item["query"]

        start     = time.time()
        standards = recommend_codes_only(query, top_n=5)
        latency   = round(time.time() - start, 4)

        result = {
            "id":                  query_id,
            "retrieved_standards": standards,
            "latency_seconds":     latency,
        }

        # Pass through expected_standards if present in input
        # — required for eval_script.py to calculate metrics
        if "expected_standards" in item:
            result["expected_standards"] = item["expected_standards"]

        results.append(result)

        print(f"  [{i+1:3d}/{len(queries)}] {query_id} → "
              f"{standards[0] if standards else 'none'} ({latency:.3f}s)")

    total_time  = round(time.time() - total_start, 2)
    avg_latency = sum(r["latency_seconds"] for r in results) / len(results)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Results saved to {args.output}")
    print(f"⏱  Total time : {total_time}s")
    print(f"⏱  Avg latency: {avg_latency:.3f}s")
    print(f"📊 Run eval   : python3 eval_script.py --results {args.output}")


if __name__ == "__main__":
    main()