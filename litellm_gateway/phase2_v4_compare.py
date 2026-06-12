"""
Phase 2 — v4 vs v1 A/C comparison (L1~L3 and L0+L1~L3).

If our Layer 0 effect holds on v4's stricter payloads, the thesis is fully
robust. This script runs TRUE detection on both configs side-by-side.
"""
import json
import sys
import re
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

V1_A = "eval_10k_l1l3.json"
V4_A = "eval_10k_v4_l1l3.json"
V1_C = "eval_10k_l0_l1l3.json"
V4_C = "eval_10k_v4_l0_l1l3.json"

BASE3 = {"Presidio PII", "Bedrock Guardrail", "Lakera"}
L0_BASE3 = BASE3 | {"korean-layer0"}


def is_pii(p, t):
    if not p or not t: return False
    if p in t: return True
    pd = re.sub(r"\D","",p); td = re.sub(r"\D","",t)
    return len(pd)>=6 and pd in td


def classify(case, layers):
    pii = case.get("pii_value", "") or case.get("original", "") or ""
    mut = case.get("mutated", "")
    any_t = any_f = False
    for lr in case.get("layer_results", []):
        if lr["layer"] not in layers: continue
        if lr.get("error") or lr.get("action") == "ERROR": continue
        out = lr.get("output", "")
        if out == mut or out == "": continue
        if out == "[BLOCKED]": any_t = True; continue
        if is_pii(pii, out): any_f = True
        else: any_t = True
    return "TRUE" if any_t else ("FALSE" if any_f else "BYPASS")


def slice_true(cases, key_fn, layers):
    buckets = defaultdict(list)
    for c in cases: buckets[key_fn(c)].append(c)
    out = {}
    for k, cs in sorted(buckets.items(), key=lambda kv: str(kv[0])):
        n = len(cs)
        trues = sum(1 for c in cs if classify(c, layers) == "TRUE")
        out[str(k)] = {"n": n, "true_rate": round(100 * trues / n, 2)}
    return out


def overall_true(cases, layers):
    n = len(cases)
    trues = sum(1 for c in cases if classify(c, layers) == "TRUE")
    return round(100 * trues / n, 2), n


v1a = json.load(open(V1_A, "r", encoding="utf-8"))["results"]
v4a = json.load(open(V4_A, "r", encoding="utf-8"))["results"]
v1c = json.load(open(V1_C, "r", encoding="utf-8"))["results"]
v4c = json.load(open(V4_C, "r", encoding="utf-8"))["results"]

v1a_true, v1a_n = overall_true(v1a, BASE3)
v4a_true, v4a_n = overall_true(v4a, BASE3)
v1c_true, v1c_n = overall_true(v1c, L0_BASE3)
v4c_true, v4c_n = overall_true(v4c, L0_BASE3)

print("=" * 90)
print("  Phase 2 — v4 vs v1 robustness (A Baseline + C With L0)")
print("=" * 90)

print(f"\n{'Config':8s} {'n':>8s} {'v1 TRUE':>10s} {'v4 TRUE':>10s} {'Δ':>8s}")
print("-" * 55)
print(f"  {'A (L1~L3)':8s} {v1a_n:>8d} {v1a_true:>9.2f}% {v4a_true:>9.2f}% {v4a_true-v1a_true:>+7.2f}%p")
print(f"  {'C (L0~L3)':8s} {v1c_n:>8d} {v1c_true:>9.2f}% {v4c_true:>9.2f}% {v4c_true-v1c_true:>+7.2f}%p")

v1_effect = v1c_true - v1a_true
v4_effect = v4c_true - v4a_true
print(f"\n[Layer 0 effect (C − A)]")
print(f"  v1 (legacy):        {v1_effect:+.2f}%p")
print(f"  v4 (validity-first): {v4_effect:+.2f}%p")
print(f"  Δ of effect:        {v4_effect - v1_effect:+.2f}%p")

# KR_semantic focus
for cfg, name in [(v1a, "v1_A"), (v4a, "v4_A"), (v1c, "v1_C"), (v4c, "v4_C")]:
    layers = L0_BASE3 if "C" in name else BASE3
    sem = [c for c in cfg if c.get("lang") == "KR" and c.get("validity_group") == "semantic"]
    if sem:
        t = sum(1 for c in sem if classify(c, layers) == "TRUE")
        print(f"  {name} KR_semantic: {t}/{len(sem)} = {100*t/len(sem):.2f}%")

summary = {
    "v1_A": v1a_true, "v4_A": v4a_true,
    "v1_C": v1c_true, "v4_C": v4c_true,
    "v1_layer0_effect": round(v1_effect, 2),
    "v4_layer0_effect": round(v4_effect, 2),
    "effect_delta": round(v4_effect - v1_effect, 2),
    "robustness_conclusion": "Layer 0 effect is consistent across fuzzer versions" if abs(v4_effect - v1_effect) < 3 else "Effect differs materially",
    "v1_slices_A": slice_true(v1a, lambda c: f"{c.get('lang')}_{c.get('validity_group')}", BASE3),
    "v4_slices_A": slice_true(v4a, lambda c: f"{c.get('lang')}_{c.get('validity_group')}", BASE3),
    "v1_slices_C": slice_true(v1c, lambda c: f"{c.get('lang')}_{c.get('validity_group')}", L0_BASE3),
    "v4_slices_C": slice_true(v4c, lambda c: f"{c.get('lang')}_{c.get('validity_group')}", L0_BASE3),
}

json.dump(summary, open("phase2_v4_compare.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\nSaved: phase2_v4_compare.json")
