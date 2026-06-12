"""Phase 2 — v4 4-way comparison (A/B/C/D) using validity-first fuzzer payloads."""
import json
import sys
import re
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

L0 = "korean-layer0"
L4 = "gpt4o-pii-judge"
L3_SET = {"Presidio PII", "Bedrock Guardrail", "Lakera"}
BASE3 = L3_SET
BASE3_L4 = BASE3 | {L4}
L0_BASE3 = BASE3 | {L0}
ALL5 = L0_BASE3 | {L4}

FILES = {
    "A_Baseline":      ("eval_10k_v4_l1l3.json",        BASE3,      "L1+L2+L3"),
    "B_Baseline_L4":   ("eval_10k_v4_l1l4_full.json",   BASE3_L4,   "L1+L2+L3+L4"),
    "C_With_L0":       ("eval_10k_v4_l0_l1l3.json",     L0_BASE3,   "L0+L1+L2+L3"),
    "D_Full":          ("eval_10k_v4_l0_l1l4_full.json",ALL5,       "L0+L1+L2+L3+L4"),
}


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


def stats(cases, layers):
    n = len(cases)
    counts = defaultdict(int)
    for c in cases: counts[classify(c, layers)] += 1
    rb = counts["FALSE"] + counts["BYPASS"]
    return {
        "n": n,
        "TRUE": counts["TRUE"],
        "true_rate": round(100 * counts["TRUE"] / n, 2),
        "real_bypass_rate": round(100 * rb / n, 2),
    }


def slice_by(cases, key_fn, layers):
    b = defaultdict(list)
    for c in cases: b[key_fn(c)].append(c)
    return {str(k): stats(v, layers) for k, v in sorted(b.items(), key=lambda kv: str(kv[0]))}


def hardest(cases, layers, limit=15):
    b = defaultdict(list)
    for c in cases: b[c.get("pii_type")].append(c)
    rows = []
    for t, cs in b.items():
        s = stats(cs, layers)
        if s["n"] >= 30: rows.append((t, s))
    rows.sort(key=lambda x: x[1]["real_bypass_rate"], reverse=True)
    return [{"pii_type": t, **s} for t, s in rows[:limit]]


summary = {"run": "v4_4way", "configs": {}}

for key, (path, layers, desc) in FILES.items():
    cases = json.load(open(path, "r", encoding="utf-8"))["results"]
    summary["configs"][key] = {
        "description": desc,
        "overall": stats(cases, layers),
        "by_lang": slice_by(cases, lambda c: c.get("lang"), layers),
        "by_lang_x_validity": slice_by(cases, lambda c: f"{c.get('lang')}_{c.get('validity_group')}", layers),
        "hardest_top15": hardest(cases, layers, 15),
    }

print("=" * 100)
print("  Phase 2 — v4 4-way Final (validity-first fuzzer)")
print("=" * 100)

print(f"\n{'Config':20s} {'구성':30s} {'TRUE':>10s} {'bypass':>10s}")
print("-" * 75)
for key, d in summary["configs"].items():
    o = d["overall"]
    print(f"  {key:18s} {d['description']:30s} {o['true_rate']:>9.2f}% {o['real_bypass_rate']:>9.2f}%")

a = summary["configs"]["A_Baseline"]["overall"]
b = summary["configs"]["B_Baseline_L4"]["overall"]
c = summary["configs"]["C_With_L0"]["overall"]
d = summary["configs"]["D_Full"]["overall"]

print(f"\nKey deltas:")
print(f"  A → C (Layer 0 effect):  {c['true_rate'] - a['true_rate']:+.2f}%p")
print(f"  A → B (LLM judge):       {b['true_rate'] - a['true_rate']:+.2f}%p")
print(f"  B vs C (head-to-head):   {c['true_rate'] - b['true_rate']:+.2f}%p")
print(f"  A → D (both):            {d['true_rate'] - a['true_rate']:+.2f}%p")

print(f"\n--- KR_semantic (v4 — validity-first) ---")
for key in ["A_Baseline", "B_Baseline_L4", "C_With_L0", "D_Full"]:
    ks = summary["configs"][key]["by_lang_x_validity"].get("KR_semantic", {})
    print(f"  {key:20s} TRUE {ks.get('true_rate',0):>6.2f}%   bypass {ks.get('real_bypass_rate',0):>6.2f}%   n={ks.get('n','-')}")

json.dump(summary, open("phase2_v4_final_4way.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\nSaved: phase2_v4_final_4way.json")
