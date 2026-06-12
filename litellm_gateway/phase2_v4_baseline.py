"""
Phase 2 — A.1 v4 Baseline vs original baseline comparison.

Is the v4 fuzzer (validity-first) producing materially different baseline
results from the original 10k sample? If TRUE rates are similar, our
original conclusions are robust; if v4 is harder, we need to re-evaluate.
"""
import json
import sys
import re
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

V4_FILE = "eval_10k_v4_l1l3.json"
ORIG_FILE = "eval_10k_l1l3.json"
BASE3 = {"Presidio PII", "Bedrock Guardrail", "Lakera"}


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


def stats_by(cases, key_fn, layers):
    buckets = defaultdict(list)
    for c in cases: buckets[key_fn(c)].append(c)
    out = {}
    for k, cs in sorted(buckets.items(), key=lambda kv: str(kv[0])):
        n = len(cs)
        classes = defaultdict(int)
        for c in cs: classes[classify(c, layers)] += 1
        out[str(k)] = {
            "n": n,
            "true_rate": round(100 * classes["TRUE"] / n, 2),
            "real_bypass_rate": round(100 * (classes["FALSE"] + classes["BYPASS"]) / n, 2),
        }
    return out


def overall(cases, layers):
    n = len(cases)
    classes = defaultdict(int)
    for c in cases: classes[classify(c, layers)] += 1
    return {
        "n": n,
        "TRUE": classes["TRUE"],
        "FALSE": classes["FALSE"],
        "BYPASS": classes["BYPASS"],
        "true_rate": round(100 * classes["TRUE"] / n, 2),
        "real_bypass_rate": round(100 * (classes["FALSE"] + classes["BYPASS"]) / n, 2),
    }


v4 = json.load(open(V4_FILE, "r", encoding="utf-8"))["results"]
orig = json.load(open(ORIG_FILE, "r", encoding="utf-8"))["results"]

summary = {
    "v4_overall": overall(v4, BASE3),
    "orig_overall": overall(orig, BASE3),
    "v4_by_lang": stats_by(v4, lambda c: c.get("lang"), BASE3),
    "orig_by_lang": stats_by(orig, lambda c: c.get("lang"), BASE3),
    "v4_by_validity": stats_by(v4, lambda c: c.get("validity_group"), BASE3),
    "orig_by_validity": stats_by(orig, lambda c: c.get("validity_group"), BASE3),
    "v4_by_lang_x_validity": stats_by(v4, lambda c: f"{c.get('lang')}_{c.get('validity_group')}", BASE3),
    "orig_by_lang_x_validity": stats_by(orig, lambda c: f"{c.get('lang')}_{c.get('validity_group')}", BASE3),
}

print("=" * 90)
print("  Phase 2 — A.1 v4 Fuzzer Baseline vs Original (L1~L3 TRUE detection)")
print("=" * 90)

a, b = summary["orig_overall"], summary["v4_overall"]
print(f"\nOverall ({a['n']} vs {b['n']} cases):")
print(f"  Original (legacy fuzzer): TRUE {a['true_rate']}%   bypass {a['real_bypass_rate']}%")
print(f"  v4 (validity-first):      TRUE {b['true_rate']}%   bypass {b['real_bypass_rate']}%")
print(f"  Δ (v4 - orig):            TRUE {b['true_rate']-a['true_rate']:+.2f}%p   bypass {b['real_bypass_rate']-a['real_bypass_rate']:+.2f}%p")

print(f"\nBy Lang × Validity (side-by-side):")
print(f"  {'bucket':18s} {'orig_n':>7s} {'orig_T':>8s} {'v4_n':>7s} {'v4_T':>8s} {'Δ TRUE':>10s}")
print("-" * 70)
all_buckets = sorted(set(summary["orig_by_lang_x_validity"].keys()) | set(summary["v4_by_lang_x_validity"].keys()))
for b in all_buckets:
    o = summary["orig_by_lang_x_validity"].get(b, {})
    v = summary["v4_by_lang_x_validity"].get(b, {})
    o_true = o.get("true_rate", 0); v_true = v.get("true_rate", 0)
    delta = v_true - o_true
    print(f"  {b:18s} {o.get('n','-'):>7} {o_true:>7.2f}% {v.get('n','-'):>7} {v_true:>7.2f}% {delta:>+9.2f}%p")

json.dump(summary, open("phase2_v4_baseline.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\nSaved: phase2_v4_baseline.json")
