"""
Run C — L0+L1~L3 vs L1~L3 baseline comparison on the same 10k stratified sample.
TRUE detection only.
"""
import json
import sys
import re
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

BASELINE_FILE = "eval_10k_l1l3.json"
WITH_L0_FILE = "eval_10k_l0_l1l3.json"
OUTPUT = "run_c_l0_summary.json"

L0_NAME = "korean-layer0"
BASE3 = {"Presidio PII", "Bedrock Guardrail", "Lakera"}
ALL4 = BASE3 | {L0_NAME}


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
    circled_map = {chr(0x2460 + i): str(i + 1) for i in range(9)}
    circled_map["⓪"] = "0"
    text_c = "".join(circled_map.get(c, c) for c in text)
    text_c_digits = re.sub(r"\D", "", text_c)
    if len(pii_digits) >= 6 and pii_digits in text_c_digits:
        return True
    return False


def classify(case, layers_set):
    pii_value = case.get("pii_value", "") or case.get("original", "") or ""
    original = case.get("mutated", "")
    any_true = False
    any_false = False
    for lr in case.get("layer_results", []):
        if lr["layer"] not in layers_set:
            continue
        output = lr.get("output", "")
        if output == original or output == "":
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


def hardest_pii(cases, layers_set, limit=25):
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


def l0_specific_contribution(cases_with_l0):
    """How many cases did L0 single-handedly catch (would have been bypassed without L0)?"""
    l0_solo = 0
    l0_helped = 0  # L0 also caught it but others did too
    l0_only_action = 0  # L0 took an action (BLOCK/MASK)
    l0_blocks = 0
    l0_errors = 0
    for c in cases_with_l0:
        pii = c.get("pii_value", "") or c.get("original", "") or ""
        mutated = c.get("mutated", "")
        l0_neutralized = False
        others_neutralized = False
        for lr in c.get("layer_results", []):
            if lr["layer"] == L0_NAME:
                if lr.get("error") or lr.get("action") == "ERROR":
                    l0_errors += 1
                    continue
                if lr.get("action") in ("BLOCK", "MASK"):
                    l0_only_action += 1
                if lr.get("action") == "BLOCK":
                    l0_blocks += 1
                output = lr.get("output", "")
                if output == "[BLOCKED]" or (output and output != mutated and not is_pii_in_text(pii, output)):
                    l0_neutralized = True
            elif lr["layer"] in BASE3:
                output = lr.get("output", "")
                if output == "[BLOCKED]" or (output and output != mutated and not is_pii_in_text(pii, output)):
                    others_neutralized = True
        if l0_neutralized and not others_neutralized:
            l0_solo += 1
        elif l0_neutralized and others_neutralized:
            l0_helped += 1
    return {
        "l0_solo_catches": l0_solo,
        "l0_redundant_catches": l0_helped,
        "l0_total_actions": l0_only_action,
        "l0_blocks": l0_blocks,
        "l0_errors": l0_errors,
    }


def print_compare_table(title, headers, rows_a, rows_b, key_label):
    """Side-by-side comparison table."""
    print(f"\n== {title} ==")
    keys = sorted(set(rows_a.keys()) | set(rows_b.keys()))
    h = [key_label, "n", "TRUE_base", "rb%_base", "TRUE_l0", "rb%_l0", "delta_TRUE", "delta_rb"]
    rows = []
    for k in keys:
        a = rows_a.get(k, {})
        b = rows_b.get(k, {})
        rows.append([
            k,
            b.get("n", a.get("n", "-")),
            a.get("true_rate", "-"),
            a.get("real_bypass_rate", "-"),
            b.get("true_rate", "-"),
            b.get("real_bypass_rate", "-"),
            f"{(b.get('true_rate', 0) - a.get('true_rate', 0)):+.2f}%p" if a and b else "-",
            f"{(b.get('real_bypass_rate', 0) - a.get('real_bypass_rate', 0)):+.2f}%p" if a and b else "-",
        ])
    widths = [max(len(str(h[i])), max((len(str(r[i])) for r in rows), default=0)) for i in range(len(h))]
    line = " | ".join(str(h[i]).ljust(widths[i]) for i in range(len(h)))
    print(line)
    print("-" * len(line))
    for r in rows:
        print(" | ".join(str(r[i]).ljust(widths[i]) for i in range(len(h))))


def main():
    base_cases = json.load(open(BASELINE_FILE, "r", encoding="utf-8"))["results"]
    l0_cases = json.load(open(WITH_L0_FILE, "r", encoding="utf-8"))["results"]

    summary = {
        "run": "C_L0_vs_baseline",
        "baseline_file": BASELINE_FILE,
        "with_l0_file": WITH_L0_FILE,
        "n_base": len(base_cases),
        "n_l0": len(l0_cases),
        "baseline_layers": sorted(BASE3),
        "with_l0_layers": sorted(ALL4),
        "baseline_overall": stats(base_cases, BASE3),
        "with_l0_overall": stats(l0_cases, ALL4),
        "l0_contribution": l0_specific_contribution(l0_cases),
        "baseline_by_lang": slice_by(base_cases, "lang", BASE3),
        "with_l0_by_lang": slice_by(l0_cases, "lang", ALL4),
        "baseline_by_validity": slice_by(base_cases, "validity_group", BASE3),
        "with_l0_by_validity": slice_by(l0_cases, "validity_group", ALL4),
        "baseline_by_lang_x_validity": slice_lang_x_validity(base_cases, BASE3),
        "with_l0_by_lang_x_validity": slice_lang_x_validity(l0_cases, ALL4),
        "baseline_by_mutation_level": slice_by(base_cases, "mutation_level", BASE3),
        "with_l0_by_mutation_level": slice_by(l0_cases, "mutation_level", ALL4),
        "baseline_hardest_pii": hardest_pii(base_cases, BASE3, 25),
        "with_l0_hardest_pii": hardest_pii(l0_cases, ALL4, 25),
    }

    json.dump(summary, open(OUTPUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print("=" * 80)
    print("  Run C — Layer 0 effect on 10k baseline (TRUE detection)")
    print("=" * 80)

    a, b = summary["baseline_overall"], summary["with_l0_overall"]
    print(f"\nOverall:")
    print(f"  Baseline (L1~L3) :  TRUE {a['TRUE']:>5} ({a['true_rate']:>5.2f}%)   real_bypass {a['FALSE']+a['BYPASS']:>5} ({a['real_bypass_rate']:>5.2f}%)")
    print(f"  With L0 (L0~L3)  :  TRUE {b['TRUE']:>5} ({b['true_rate']:>5.2f}%)   real_bypass {b['FALSE']+b['BYPASS']:>5} ({b['real_bypass_rate']:>5.2f}%)")
    print(f"  Δ                :  TRUE {b['true_rate']-a['true_rate']:+.2f}%p   real_bypass {b['real_bypass_rate']-a['real_bypass_rate']:+.2f}%p")

    print(f"\nLayer 0 contribution:")
    c = summary["l0_contribution"]
    print(f"  L0 solo catches (would have bypassed without L0): {c['l0_solo_catches']}")
    print(f"  L0 redundant catches (others also caught): {c['l0_redundant_catches']}")
    print(f"  L0 BLOCK actions: {c['l0_blocks']}")
    print(f"  L0 errors: {c['l0_errors']}")

    print_compare_table(
        "By language",
        None,
        summary["baseline_by_lang"],
        summary["with_l0_by_lang"],
        "lang",
    )
    print_compare_table(
        "By validity_group",
        None,
        summary["baseline_by_validity"],
        summary["with_l0_by_validity"],
        "group",
    )
    print_compare_table(
        "Lang × Validity",
        None,
        summary["baseline_by_lang_x_validity"],
        summary["with_l0_by_lang_x_validity"],
        "bucket",
    )
    print_compare_table(
        "By mutation_level",
        None,
        summary["baseline_by_mutation_level"],
        summary["with_l0_by_mutation_level"],
        "level",
    )

    # Hardest PII compare (top 25 from baseline view)
    print("\n== Hardest PII (baseline top 25 by real_bypass) — L0 effect ==")
    base_hard = {r["pii_type"]: r for r in summary["baseline_hardest_pii"]}
    l0_map = {r["pii_type"]: r for r in summary["with_l0_hardest_pii"]}
    h = ["pii_type", "n", "rb%_base", "rb%_l0", "delta"]
    rows = []
    for r in summary["baseline_hardest_pii"]:
        t = r["pii_type"]
        l0r = next((x for x in l0_map.values() if x["pii_type"] == t), None)
        # If not in top25 with L0, recompute via slicing all
        if l0r is None:
            # Fall back: compute from raw data
            from collections import defaultdict as dd
            grp = dd(list)
            for cc in l0_cases:
                if cc.get("pii_type") == t:
                    grp[t].append(cc)
            l0_stats = stats(grp[t], ALL4) if grp[t] else {"real_bypass_rate": "-"}
        else:
            l0_stats = l0r
        rows.append([
            t, r["n"],
            f"{r['real_bypass_rate']}%",
            f"{l0_stats.get('real_bypass_rate','-')}%",
            f"{l0_stats.get('real_bypass_rate', 0) - r['real_bypass_rate']:+.2f}%p" if isinstance(l0_stats.get('real_bypass_rate'), (int, float)) else "-",
        ])
    widths = [max(len(str(h[i])), max((len(str(r[i])) for r in rows), default=0)) for i in range(len(h))]
    line = " | ".join(str(h[i]).ljust(widths[i]) for i in range(len(h)))
    print(line)
    print("-" * len(line))
    for r in rows:
        print(" | ".join(str(r[i]).ljust(widths[i]) for i in range(len(h))))

    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    main()
