# eval_local.py  (project root — for local testing only)
import json
import argparse
import sys

def normalize_std(std_string):
    return str(std_string).replace(" ", "").lower()

def evaluate_results(results_file, test_set_file):
    with open(results_file) as f:
        results = json.load(f)
    with open(test_set_file) as f:
        test_set = json.load(f)

    # Build expected map from test set
    expected_map = {item["id"]: item["expected_standards"] for item in test_set}

    total_queries = len(results)
    hits_at_3     = 0
    mrr_sum       = 0.0
    total_latency = 0.0

    for item in results:
        expected  = set(normalize_std(s) for s in expected_map.get(item["id"], []))
        retrieved = [normalize_std(s) for s in item.get("retrieved_standards", [])]
        latency   = item.get("latency_seconds", 0.0)

        total_latency += latency

        # Hit Rate @3
        if any(s in expected for s in retrieved[:3]):
            hits_at_3 += 1

        # MRR @5
        for rank, s in enumerate(retrieved[:5], start=1):
            if s in expected:
                mrr_sum += 1.0 / rank
                break

    print("=" * 40)
    print("   BIS HACKATHON EVALUATION RESULTS")
    print("=" * 40)
    print(f"Total Queries           : {total_queries}")
    print(f"Hit Rate @3             : {hits_at_3/total_queries*100:.2f}%\t(Target: >80%)")
    print(f"MRR @5                  : {mrr_sum/total_queries:.4f}\t(Target: >0.7)")
    print(f"Avg Latency             : {total_latency/total_queries:.2f} sec\t(Target: <5 seconds)")
    print("=" * 40)

    # Per-query breakdown
    print("\nPer-query breakdown:")
    for item in results:
        expected  = set(normalize_std(s) for s in expected_map.get(item["id"], []))
        retrieved = [normalize_std(s) for s in item.get("retrieved_standards", [])]
        hit       = any(s in expected for s in retrieved[:3])
        rank_str  = "not found"
        for rank, s in enumerate(retrieved[:5], start=1):
            if s in expected:
                rank_str = f"rank {rank}"
                break
        status = "✓" if hit else "✗"
        exp    = list(expected_map.get(item["id"], []))
        print(f"  {status} {item['id']} [{rank_str:8s}] expected={exp[0] if exp else '?'} got={item['retrieved_standards'][0]}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--results",  required=True)
    parser.add_argument("--test-set", default="data/public_test_set.json")
    args = parser.parse_args()
    evaluate_results(args.results, args.test_set)