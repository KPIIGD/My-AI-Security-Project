"""
Run E — FINAL 4-way comparison on full 10k with all layers evaluated.

A. Baseline      = L1+L2+L3           (prod stack)
B. Baseline+L4   = L1+L2+L3+L4        (+ GPT-4o-mini judge, full 10k)
C. With L0       = L0+L1+L2+L3        (Korean normalizer, no LLM)
D. Full 5-layer  = L0+L1+L2+L3+L4     (everything)
"""
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

FILE_BASELINE = "eval_10k_l1l3.json"          # A, also source for L4 cascade
FILE_BASELINE_L4 = "eval_10k_l1l4_full.json"  # B (10k all with L4)
FILE_L0 = "eval_10k_l0_l1l3.json"             # C
FILE_FULL = "eval_10k_l0_l1l4_full.json"      # D
OUTPUT = "run_e_final_summary.json"


def is_pii_in_text(pii_value, text):
    if not pii_value or not text:
        return False
    if pii_value in text:
        return True
    pd = re.sub(r"\D", "", pii_value); td = re.sub(r"\D", "", text)
    return len(pd) >= 6 and pd in td


def classify(case, layers_set):
    pii = case.get("pii_value", "") or case.get("original", "") or ""
    mut = case.get("mutated", "")
    any_true = any_false = False
    for lr in case.get("layer_results", []):
        if lr["layer"] not in layers_set:
            continue
        if lr.get("error") or lr.get("action") == "ERROR":
            continue
        out = lr.get("output", "")
        if out == mut or out == "":
            continue
        if out == "[BLOCKED]":
            any_true = True
            continue
        if is_pii_in_text(pii, out):
            any_false = True
        else:
            any_true = True
    if any_true:
        return "TRUE"
    if any_false:
        return "FALSE"
    return "BYPASS"


def stats(cases, layers_set):
    n = len(cases)
    counts = defaultdict(int)
    for c in cases:
        counts[classify(c, layers_set)] += 1
    rb = counts["FALSE"] + counts["BYPASS"]
    return {
        "n": n,
        "TRUE": counts["TRUE"],
        "FALSE": counts["FALSE"],
        "BYPASS": counts["BYPASS"],
        "true_rate": round(100 * counts["TRUE"] / n, 2) if n else 0,
        "real_bypass_rate": round(100 * rb / n, 2) if n else 0,
    }


def slice_by(cases, key, layers_set):
    b = defaultdict(list)
    for c in cases:
        b[c.get(key)].append(c)
    return {str(k): stats(v, layers_set) for k, v in sorted(b.items(), key=lambda kv: str(kv[0]))}


def slice_lang_x_validity(cases, layers_set):
    b = defaultdict(list)
    for c in cases:
        b[f"{c.get('lang')}_{c.get('validity_group')}"].append(c)
    return {k: stats(v, layers_set) for k, v in sorted(b.items())}


def hardest_pii(cases, layers_set, limit=20):
    b = defaultdict(list)
    for c in cases:
        b[c.get("pii_type")].append(c)
    rows = []
    for t, cs in b.items():
        s = stats(cs, layers_set)
        if s["n"] >= 30:
            rows.append((t, s))
    rows.sort(key=lambda x: x[1]["real_bypass_rate"], reverse=True)
    return [{"pii_type": t, **s} for t, s in rows[:limit]]


def main():
    base = json.load(open(FILE_BASELINE, "r", encoding="utf-8"))["results"]
    base_l4 = json.load(open(FILE_BASELINE_L4, "r", encoding="utf-8"))["results"]
    l0 = json.load(open(FILE_L0, "r", encoding="utf-8"))["results"]
    full = json.load(open(FILE_FULL, "r", encoding="utf-8"))["results"]

    configs = [
        ("A_Baseline",      base,     BASE3,     "L1+L2+L3 (prod stack, no LLM)"),
        ("B_Baseline_L4",   base_l4,  BASE3_L4,  "L1+L2+L3+L4 (+ GPT-4o-mini judge)"),
        ("C_With_L0",       l0,       L0_BASE3,  "L0+L1+L2+L3 (Korean normalizer, no LLM)"),
        ("D_Full",          full,     ALL5,      "L0+L1+L2+L3+L4 (everything)"),
    ]

    summary = {"run": "E_final_4way", "n": len(base),
               "overall": {},
               "by_lang": {},
               "by_validity": {},
               "by_lang_x_validity": {},
               "by_mutation_level": {},
               "hardest_pii": {},
               "configs": {k: {"layers": sorted(l), "description": d} for k, _, l, d in configs}}

    for key, data, layers, desc in configs:
        summary["overall"][key] = stats(data, layers)
        summary["by_lang"][key] = slice_by(data, "lang", layers)
        summary["by_validity"][key] = slice_by(data, "validity_group", layers)
        summary["by_lang_x_validity"][key] = slice_lang_x_validity(data, layers)
        summary["by_mutation_level"][key] = slice_by(data, "mutation_level", layers)
        summary["hardest_pii"][key] = hardest_pii(data, layers, 20)

    json.dump(summary, open(OUTPUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print("=" * 96)
    print("  Run E — FINAL 4-way comparison (10k stratified, TRUE detection)")
    print("=" * 96)

    print(f"\n{'Config':25s} {'description':45s} {'TRUE':>10s} {'real_bypass':>14s}")
    print("-" * 96)
    for key, _, _, desc in configs:
        s = summary["overall"][key]
        print(f"  {key:23s} {desc:45s} {s['true_rate']:>9.2f}%  {s['real_bypass_rate']:>13.2f}%")

    a = summary["overall"]["A_Baseline"]
    b = summary["overall"]["B_Baseline_L4"]
    c = summary["overall"]["C_With_L0"]
    d = summary["overall"]["D_Full"]

    print(f"\nKey head-to-heads:")
    print(f"  A → B (add LLM judge):         TRUE {a['true_rate']:.2f}% → {b['true_rate']:.2f}%  ({b['true_rate']-a['true_rate']:+.2f}%p)")
    print(f"  A → C (add Layer 0):           TRUE {a['true_rate']:.2f}% → {c['true_rate']:.2f}%  ({c['true_rate']-a['true_rate']:+.2f}%p)")
    print(f"  B vs C (LLM vs L0):            TRUE {b['true_rate']:.2f}% vs {c['true_rate']:.2f}%  (C-B: {c['true_rate']-b['true_rate']:+.2f}%p)")
    print(f"  C → D (L0 + LLM judge):        TRUE {c['true_rate']:.2f}% → {d['true_rate']:.2f}%  ({d['true_rate']-c['true_rate']:+.2f}%p)")
    print(f"  A → D (both defenses):         TRUE {a['true_rate']:.2f}% → {d['true_rate']:.2f}%  ({d['true_rate']-a['true_rate']:+.2f}%p)")

    # KR_semantic spotlight
    print(f"\n--- KR_semantic (Korean text-type PII, n={summary['by_lang_x_validity']['A_Baseline']['KR_semantic']['n']}) ---")
    for key, _, _, desc in configs:
        s = summary["by_lang_x_validity"][key].get("KR_semantic", {})
        print(f"  {key:23s}  TRUE {s.get('true_rate',0):.2f}%   bypass {s.get('real_bypass_rate',0):.2f}%")

    # Lang table
    print(f"\n--- By language ---")
    print(f"  {'lang':8s} {'A_TRUE':>8s} {'B_TRUE':>8s} {'C_TRUE':>8s} {'D_TRUE':>8s}")
    for lang in ["EN", "KR"]:
        print(f"  {lang:8s} "
              f"{summary['by_lang']['A_Baseline'][lang]['true_rate']:>7.2f}% "
              f"{summary['by_lang']['B_Baseline_L4'][lang]['true_rate']:>7.2f}% "
              f"{summary['by_lang']['C_With_L0'][lang]['true_rate']:>7.2f}% "
              f"{summary['by_lang']['D_Full'][lang]['true_rate']:>7.2f}%")

    # Hardest top 15 across 4 configs
    print(f"\n--- Top 15 hardest PII (baseline-sorted) — 4-way bypass rate ---")
    hard_a = summary["hardest_pii"]["A_Baseline"][:15]
    maps = {k: {r["pii_type"]: r for r in summary["hardest_pii"][k]}
            for k in ["B_Baseline_L4", "C_With_L0", "D_Full"]}
    # For missing (PII dropped from top20 for that config), recompute
    # Not needed for this summary; just show '-' for ones not in top
    print(f"  {'pii_type':14s} {'n':>4s} {'A':>8s} {'B':>8s} {'C':>8s} {'D':>8s}")
    for r in hard_a:
        t = r["pii_type"]
        b_v = maps["B_Baseline_L4"].get(t, {}).get("real_bypass_rate", None)
        c_v = maps["C_With_L0"].get(t, {}).get("real_bypass_rate", None)
        d_v = maps["D_Full"].get(t, {}).get("real_bypass_rate", None)
        def fmt(x): return f"{x:>7.1f}%" if isinstance(x, (int, float)) else "     -  "
        print(f"  {t:14s} {r['n']:>4d} {r['real_bypass_rate']:>7.1f}% {fmt(b_v)} {fmt(c_v)} {fmt(d_v)}")

    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    main()
