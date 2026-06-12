"""
Phase 1 — B.5 Latency Precision Analysis

Compute p50/p95/p99 per layer + end-to-end for each 4-way config.
"""
import json
import numpy as np
from collections import defaultdict

FILES = {
    "A_Baseline":   ("eval_10k_l1l3.json",      {"Presidio PII", "Bedrock Guardrail", "Lakera"}),
    "B_Baseline_L4":("eval_10k_l1l4_full.json", {"Presidio PII", "Bedrock Guardrail", "Lakera", "gpt4o-pii-judge"}),
    "C_With_L0":    ("eval_10k_l0_l1l3.json",   {"Presidio PII", "Bedrock Guardrail", "Lakera", "korean-layer0"}),
    "D_Full":       ("eval_10k_l0_l1l4_full.json", {"Presidio PII", "Bedrock Guardrail", "Lakera", "korean-layer0", "gpt4o-pii-judge"}),
}

def percentile(vals, p):
    if not vals: return 0
    return float(np.percentile(vals, p))

def summarize(values):
    if not values: return {"n": 0}
    arr = np.array(values)
    return {
        "n": len(arr),
        "min": int(arr.min()),
        "p50": int(np.percentile(arr, 50)),
        "p95": int(np.percentile(arr, 95)),
        "p99": int(np.percentile(arr, 99)),
        "max": int(arr.max()),
        "mean": round(float(arr.mean()), 1),
        "std": round(float(arr.std()), 1),
    }

result = {}
for name, (path, layers) in FILES.items():
    cases = json.load(open(path, "r", encoding="utf-8"))["results"]
    per_layer = defaultdict(list)
    e2e = []

    for c in cases:
        total = 0
        counted_layers = set()
        for lr in c.get("layer_results", []):
            if lr["layer"] not in layers: continue
            if lr.get("latency_ms") is None: continue
            per_layer[lr["layer"]].append(lr["latency_ms"])
            total += lr["latency_ms"]
            counted_layers.add(lr["layer"])
        if counted_layers == layers:  # all layers present
            e2e.append(total)

    result[name] = {
        "end_to_end": summarize(e2e),
        "per_layer": {l: summarize(vals) for l, vals in sorted(per_layer.items())},
    }

json.dump(result, open("phase1_latency_precise.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# Print table
import sys
sys.stdout.reconfigure(encoding="utf-8")
print("=" * 100)
print("  B.5 — Latency Precision (10k, ms)")
print("=" * 100)
print(f"\n{'Config':20s} {'p50':>8s} {'p95':>8s} {'p99':>8s} {'mean':>8s} {'max':>8s}")
print("-" * 70)
for name, data in result.items():
    e = data["end_to_end"]
    print(f"  {name:18s} {e['p50']:>7d}  {e['p95']:>7d}  {e['p99']:>7d}  {e['mean']:>7.0f}  {e['max']:>7d}")

for name, data in result.items():
    print(f"\n--- {name} per-layer ---")
    print(f"  {'layer':22s} {'p50':>7s} {'p95':>7s} {'p99':>7s} {'mean':>7s}")
    for layer, stats in data["per_layer"].items():
        print(f"  {layer:22s} {stats['p50']:>6d}  {stats['p95']:>6d}  {stats['p99']:>6d}  {stats['mean']:>6.0f}")

print(f"\nSaved: phase1_latency_precise.json")
