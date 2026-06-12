"""
Run D — The decisive 4-way comparison.

Configurations (each on the same 10k stratified sample):
  A. Baseline       L1+L2+L3              (Presidio + Bedrock + Lakera)
  B. Baseline+L4    L1+L2+L3+L4           (+ GPT-4o-mini judge cascade)
  C. With L0        L0+L1+L2+L3           (Korean normalizer + dictionary)
  D. Full           L0+L1+L2+L3+L4_proxy  (C with L4 effect projected from B)

Note: D is a *projection* using Baseline+L4 cascade behavior since we did
not run L4 on the L0+L1~L3 outputs separately. We can either skip D or
project conservatively as L0~L3 ∪ L4(remaining bypass) — but only if we
have L4 results for those specific cases. We DO have L4 results only for
the 2099 baseline-bypass cases. Among the 602 L0~L3 bypass cases, some
overlap with the 2099. We can compute D = L0~L3 caught ∪ (L4 caught from
that overlap).
"""
import json
import sys
import re
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

BASELINE_FILE = "eval_10k_l1l3.json"
BASELINE_L4_FILE = "eval_10k_baseline_l4.json"
WITH_L0_FILE = "eval_10k_l0_l1l3.json"
OUTPUT = "run_d_4way_summary.json"

L0_NAME = "korean-layer0"
L4_NAME = "gpt4o-pii-judge"
BASE3 = {"Presidio PII", "Bedrock Guardrail", "Lakera"}
BASE3_L4 = BASE3 | {L4_NAME}
L0_BASE3 = BASE3 | {L0_NAME}
ALL5 = L0_BASE3 | {L4_NAME}


def is_pii_in_text(pii_value, text):
    if not pii_value or not text:
        return False
    if pii_value in text:
        return True
    pii_digits = re.sub(r"\D", "", pii_value)
    text_digits = re.sub(r"\D", "", text)
    if len(pii_digits) >= 6 and pii_digits in text_digits:
        return True
    fullwidth_map = {chr(0xFF10 + i): str(i) for i in range(10)}
    text_norm = "".join(fullwidth_map.get(c, c) for c in text)
    if pii_value in text_norm:
        return True
    text_digits_norm = re.sub(r"\D", "", text_norm)
    if len(pii_digits) >= 6 and pii_digits in text_digits_norm:
        return True
    return False


def neutralized(lr, mutated, pii):
    if lr.get("error") or lr.get("action") == "ERROR":
        return False
    output = lr.get("output", "")
    if output == "[BLOCKED]":
        return True
    if not output or output == mutated:
        return False
    return not is_pii_in_text(pii, output)


def classify(case, layers_set):
    pii_value = case.get("pii_value", "") or case.get("original", "") or ""
    mutated = case.get("mutated", "")
    any_true = False
    any_false = False
    for lr in case.get("layer_results", []):
        if lr["layer"] not in layers_set:
            continue
        if lr.get("error") or lr.get("action") == "ERROR":
            continue
        output = lr.get("output", "")
        if output == mutated or output == "":
            continue
        if output == "[BLOCKED]":
            any_true = True
            continue
        if is_pii_in_text(pii_value, output):
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
    real_bypass = counts["FALSE"] + counts["BYPASS"]
    return {
        "n": n,
        "TRUE": counts["TRUE"],
        "FALSE": counts["FALSE"],
        "BYPASS": counts["BYPASS"],
        "true_rate": round(100 * counts["TRUE"] / n, 2) if n else 0,
        "real_bypass_rate": round(100 * real_bypass / n, 2) if n else 0,
    }


def slice_by(cases, key, layers_set):
    buckets = defaultdict(list)
    for c in cases:
        buckets[c.get(key)].append(c)
    return {str(k): stats(v, layers_set) for k, v in sorted(buckets.items(), key=lambda kv: str(kv[0]))}


def slice_lang_x_validity(cases, layers_set):
    buckets = defaultdict(list)
    for c in cases:
        buckets[f"{c.get('lang')}_{c.get('validity_group')}"].append(c)
    return {k: stats(v, layers_set) for k, v in sorted(buckets.items())}


def hardest_pii(cases, layers_set, limit=20):
    buckets = defaultdict(list)
    for c in cases:
        buckets[c.get("pii_type")].append(c)
    rows = []
    for t, cs in buckets.items():
        s = stats(cs, layers_set)
        if s["n"] >= 30:
            rows.append((t, s))
    rows.sort(key=lambda x: x[1]["real_bypass_rate"], reverse=True)
    return [{"pii_type": t, **s} for t, s in rows[:limit]]


def main():
    base = json.load(open(BASELINE_FILE, "r", encoding="utf-8"))["results"]
    base_l4 = json.load(open(BASELINE_L4_FILE, "r", encoding="utf-8"))["results"]
    with_l0 = json.load(open(WITH_L0_FILE, "r", encoding="utf-8"))["results"]

    summary = {
        "run": "D_4way_comparison",
        "n": len(base),
        "configs": {
            "A_Baseline_L1L3":      sorted(BASE3),
            "B_Baseline_L1L4":      sorted(BASE3_L4),
            "C_With_L0_L0L3":       sorted(L0_BASE3),
        },
        "overall": {
            "A_Baseline_L1L3":   stats(base, BASE3),
            "B_Baseline_L1L4":   stats(base_l4, BASE3_L4),
            "C_With_L0_L0L3":    stats(with_l0, L0_BASE3),
        },
        "by_lang": {
            "A": slice_by(base, "lang", BASE3),
            "B": slice_by(base_l4, "lang", BASE3_L4),
            "C": slice_by(with_l0, "lang", L0_BASE3),
        },
        "by_validity": {
            "A": slice_by(base, "validity_group", BASE3),
            "B": slice_by(base_l4, "validity_group", BASE3_L4),
            "C": slice_by(with_l0, "validity_group", L0_BASE3),
        },
        "by_lang_x_validity": {
            "A": slice_lang_x_validity(base, BASE3),
            "B": slice_lang_x_validity(base_l4, BASE3_L4),
            "C": slice_lang_x_validity(with_l0, L0_BASE3),
        },
        "by_mutation_level": {
            "A": slice_by(base, "mutation_level", BASE3),
            "B": slice_by(base_l4, "mutation_level", BASE3_L4),
            "C": slice_by(with_l0, "mutation_level", L0_BASE3),
        },
        "hardest_pii": {
            "A": hardest_pii(base, BASE3, 20),
            "B": hardest_pii(base_l4, BASE3_L4, 20),
            "C": hardest_pii(with_l0, L0_BASE3, 20),
        },
    }

    json.dump(summary, open(OUTPUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print("=" * 90)
    print("  Run D — 4-way comparison (10k, TRUE detection)")
    print("=" * 90)

    a = summary["overall"]["A_Baseline_L1L3"]
    b = summary["overall"]["B_Baseline_L1L4"]
    c = summary["overall"]["C_With_L0_L0L3"]
    print(f"\n{'Config':30s} {'TRUE':>10s} {'real_bypass':>14s}  {'note'}")
    print(f"{'-'*90}")
    print(f"{'A) Baseline (L1~L3)':30s} {a['true_rate']:>9.2f}%  {a['real_bypass_rate']:>13.2f}%  ← prod stack, no LLM judge")
    print(f"{'B) Baseline + L4 (L1~L4)':30s} {b['true_rate']:>9.2f}%  {b['real_bypass_rate']:>13.2f}%  ← + GPT-4o-mini judge cascade")
    print(f"{'C) With L0 (L0~L3)':30s} {c['true_rate']:>9.2f}%  {c['real_bypass_rate']:>13.2f}%  ← Korean normalizer + dict, no LLM")

    print(f"\nKey deltas:")
    print(f"  C vs A (L0 effect alone)         : TRUE {c['true_rate']-a['true_rate']:+.2f}%p  /  bypass {c['real_bypass_rate']-a['real_bypass_rate']:+.2f}%p")
    print(f"  B vs A (LLM judge effect alone)  : TRUE {b['true_rate']-a['true_rate']:+.2f}%p  /  bypass {b['real_bypass_rate']-a['real_bypass_rate']:+.2f}%p")
    print(f"  C vs B (L0 vs LLM judge head-to-head): TRUE {c['true_rate']-b['true_rate']:+.2f}%p  /  bypass {c['real_bypass_rate']-b['real_bypass_rate']:+.2f}%p")

    # KR semantic head-to-head
    a_sem = summary["by_lang_x_validity"]["A"].get("KR_semantic", {})
    b_sem = summary["by_lang_x_validity"]["B"].get("KR_semantic", {})
    c_sem = summary["by_lang_x_validity"]["C"].get("KR_semantic", {})
    print(f"\n--- KR_semantic (Korean text-type PII, 1302 cases) ---")
    print(f"  A) Baseline:        TRUE {a_sem['true_rate']:.2f}%  bypass {a_sem['real_bypass_rate']:.2f}%")
    print(f"  B) Baseline + L4:   TRUE {b_sem['true_rate']:.2f}%  bypass {b_sem['real_bypass_rate']:.2f}%")
    print(f"  C) With L0:         TRUE {c_sem['true_rate']:.2f}%  bypass {c_sem['real_bypass_rate']:.2f}%")
    print(f"  → C beats B by {c_sem['true_rate']-b_sem['true_rate']:+.2f}%p (TRUE)")

    # Per-PII head-to-head — top 20 hardest in baseline
    print(f"\n--- Top 20 hardest PII (baseline view) — A vs B vs C real_bypass ---")
    hard_a = summary["hardest_pii"]["A"]
    b_map = {r["pii_type"]: r for r in summary["hardest_pii"]["B"]}
    c_map = {r["pii_type"]: r for r in summary["hardest_pii"]["C"]}
    print(f"  {'pii_type':14s} {'n':>4s} {'A_bypass':>10s} {'B_bypass':>10s} {'C_bypass':>10s}  {'C beats B?'}")
    for r in hard_a:
        t = r["pii_type"]
        ba = r["real_bypass_rate"]
        bb = b_map.get(t, {}).get("real_bypass_rate", "-")
        cb = c_map.get(t, {}).get("real_bypass_rate", "-")
        better = ""
        if isinstance(bb, (int, float)) and isinstance(cb, (int, float)):
            better = "✓" if cb < bb else (" =" if cb == bb else "✗")
        print(f"  {t:14s} {r['n']:>4d} {ba:>9.1f}% {bb if isinstance(bb,str) else f'{bb:>9.1f}%'} {cb if isinstance(cb,str) else f'{cb:>9.1f}%'}  {better}")

    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    main()
