"""Stratified sample 10,000 payloads from payloads_full.json,
preserving lang × validity_group × mutation_level proportions.
"""
import json
import random
from collections import defaultdict, Counter

random.seed(20260419)

with open("payloads_full.json", "r", encoding="utf-8") as f:
    src = json.load(f)
all_payloads = src["payloads"]

TARGET = 10000
N = len(all_payloads)
print(f"source: {N} payloads, target: {TARGET}")

# Stratify by lang + validity_group (3 levels coarse enough)
buckets = defaultdict(list)
for p in all_payloads:
    key = (p.get("lang", "?"), p.get("validity_group", "?"))
    buckets[key].append(p)

print("source distribution:")
for k, v in sorted(buckets.items()):
    print(f"  {k}: {len(v)}")

# Allocate proportionally
allocated = {}
remaining = TARGET
keys = list(buckets.keys())
for i, k in enumerate(keys):
    if i == len(keys) - 1:
        allocated[k] = remaining
    else:
        n = round(TARGET * len(buckets[k]) / N)
        allocated[k] = min(n, len(buckets[k]))
        remaining -= allocated[k]

print("\nallocated:")
for k, n in sorted(allocated.items()):
    print(f"  {k}: {n}")

sampled = []
for k, n in allocated.items():
    random.shuffle(buckets[k])
    sampled.extend(buckets[k][:n])

random.shuffle(sampled)
print(f"\nfinal: {len(sampled)}")

# Verify distribution
print("\nresulting distribution:")
print("  lang:", dict(Counter(p["lang"] for p in sampled)))
print("  validity_group:", dict(Counter(p["validity_group"] for p in sampled)))
print("  mutation_level:", dict(Counter(p["mutation_level"] for p in sampled)))

with open("payloads_10k.json", "w", encoding="utf-8") as f:
    json.dump({"metadata": {"source": "payloads_full.json", "stratified": "lang x validity_group", "seed": 20260419, "count": len(sampled)}, "payloads": sampled}, f, ensure_ascii=False)
print(f"\nsaved: payloads_10k.json")
