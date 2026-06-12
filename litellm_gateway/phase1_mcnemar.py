"""
Phase 1 — A.4 McNemar's Test for paired 4-way configs.

Tests whether detection differences between any two configs are
statistically significant (matched-pairs test on the same 10k cases).
"""
import json
import sys
import re
from collections import defaultdict
from math import log

sys.stdout.reconfigure(encoding="utf-8")

FILES = {
    "A_Baseline":    ("eval_10k_l1l3.json",        {"Presidio PII", "Bedrock Guardrail", "Lakera"}),
    "B_Baseline_L4": ("eval_10k_l1l4_full.json",   {"Presidio PII", "Bedrock Guardrail", "Lakera", "gpt4o-pii-judge"}),
    "C_With_L0":     ("eval_10k_l0_l1l3.json",     {"Presidio PII", "Bedrock Guardrail", "Lakera", "korean-layer0"}),
    "D_Full":        ("eval_10k_l0_l1l4_full.json",{"Presidio PII", "Bedrock Guardrail", "Lakera", "korean-layer0", "gpt4o-pii-judge"}),
}


def is_pii_in_text(pii, text):
    if not pii or not text: return False
    if pii in text: return True
    pd = re.sub(r"\D", "", pii); td = re.sub(r"\D", "", text)
    return len(pd) >= 6 and pd in td


def is_true(case, layers):
    pii = case.get("pii_value", "") or case.get("original", "") or ""
    mut = case.get("mutated", "")
    any_t = any_f = False
    for lr in case.get("layer_results", []):
        if lr["layer"] not in layers: continue
        if lr.get("error") or lr.get("action") == "ERROR": continue
        out = lr.get("output", "")
        if out == mut or out == "": continue
        if out == "[BLOCKED]": any_t = True; continue
        if is_pii_in_text(pii, out): any_f = True
        else: any_t = True
    return any_t  # TRUE only; FALSE/BYPASS = not TRUE


# Load all 4 configs keyed by case id
def load_labels(path, layers):
    cases = json.load(open(path, "r", encoding="utf-8"))["results"]
    return {c["id"]: is_true(c, layers) for c in cases if c.get("id")}


configs = {k: load_labels(p, l) for k, (p, l) in FILES.items()}
common_ids = set.intersection(*(set(m.keys()) for m in configs.values()))
print(f"common case IDs across 4 configs: {len(common_ids)}")


def mcnemar(c1, c2):
    """c1, c2: dict id -> bool (TRUE detected)."""
    b = c = 0  # b: c1 TRUE, c2 FALSE; c: c1 FALSE, c2 TRUE
    for i in common_ids:
        v1, v2 = c1[i], c2[i]
        if v1 and not v2: b += 1
        elif v2 and not v1: c += 1
    # Exact McNemar (binomial) for small b+c, chi-sq approx otherwise
    n = b + c
    if n == 0:
        return {"b": b, "c": c, "n": n, "stat": 0, "p_value": 1.0, "test": "none"}
    # Chi-squared approximation with continuity correction (Edwards)
    chi2 = ((abs(b - c) - 1) ** 2) / n if n > 0 else 0
    # p-value via chi-sq distribution (df=1)
    # Using simple approximation: p ≈ exp(-chi2/2) for df=1 (tail)
    # More accurate: 1 - CDF(chi-sq df=1)
    import math
    # survival function of chi-sq df=1 at value x = erfc(sqrt(x/2))
    p_value = math.erfc(math.sqrt(chi2 / 2)) if chi2 > 0 else 1.0
    return {"b": b, "c": c, "n": n, "chi2_edwards": round(chi2, 3),
            "p_value": float(f"{p_value:.2e}"),
            "test": "chi-sq approx (df=1, continuity corrected)"}


pairs = [
    ("A_Baseline", "B_Baseline_L4"),  # LLM judge effect
    ("A_Baseline", "C_With_L0"),      # Layer 0 effect
    ("B_Baseline_L4", "C_With_L0"),   # L0 vs LLM judge (head-to-head)
    ("C_With_L0", "D_Full"),          # L0 + L4 extra
    ("A_Baseline", "D_Full"),         # both defenses vs none
]

print(f"\n{'Comparison':35s} {'b (c1>c2)':>10s} {'c (c2>c1)':>10s} {'chi2':>8s} {'p':>14s}")
print("-" * 85)
results = {}
for a, b in pairs:
    r = mcnemar(configs[a], configs[b])
    r["comparison"] = f"{a} vs {b}"
    results[f"{a}_vs_{b}"] = r
    sig = "***" if r["p_value"] < 0.001 else ("**" if r["p_value"] < 0.01 else ("*" if r["p_value"] < 0.05 else ""))
    print(f"  {a} vs {b:15s} {r['b']:>10d} {r['c']:>10d} {r.get('chi2_edwards',0):>7}  {r['p_value']:>12.2e} {sig}")

print("\nInterpretation:")
print("  b = config1 catches, config2 misses (c1 has advantage here)")
print("  c = config2 catches, config1 misses (c2 has advantage here)")
print("  p < 0.001 (***) : highly significant difference between configs")

json.dump(results, open("phase1_mcnemar.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\nSaved: phase1_mcnemar.json")
