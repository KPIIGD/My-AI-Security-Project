"""
Run A v3 — TRUE detection on the FRESH (4/19) L1~L3 rerun
+ side-by-side comparison vs the 4/16 snapshot.

Inputs:
  - eval_l1l3_v2.json  (4/19 fresh rerun, L1~L3 only)
  - eval_full.json     (4/16 snapshot, used for diff)

Output:
  - run_a_v3_summary.json
"""
import json
import sys
import re
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

FRESH = "eval_l1l3_v2.json"
SNAPSHOT = "eval_full.json"
OUTPUT = "run_a_v3_summary.json"
BASELINE_LAYERS = {"Presidio PII", "Bedrock Guardrail", "Lakera"}


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


def classify(case):
    pii_value = case.get("pii_value", "") or case.get("original", "") or ""
    original = case.get("mutated", "")
    any_true = False
    any_false = False
    for lr in case.get("layer_results", []):
        if lr["layer"] not in BASELINE_LAYERS:
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


def stats(cases):
    n = len(cases)
    counts = defaultdict(int)
    for c in cases:
        counts[classify(c)] += 1
    real_bypass = counts["FALSE"] + counts["BYPASS"]
    return {
        "n": n,
        "TRUE": counts["TRUE"],
        "FALSE": counts["FALSE"],
        "BYPASS": counts["BYPASS"],
        "true_rate": round(100 * counts["TRUE"] / n, 2) if n else 0,
        "real_bypass_rate": round(100 * real_bypass / n, 2) if n else 0,
    }


def per_layer_catch(cases):
    out = {}
    for layer in BASELINE_LAYERS:
        n = 0
        caught = 0  # detected by output_changed (legacy metric)
        true_caught = 0  # actually neutralized
        lat = []
        for c in cases:
            pii = c.get("pii_value", "") or c.get("original", "") or ""
            for lr in c.get("layer_results", []):
                if lr["layer"] != layer:
                    continue
                n += 1
                if lr.get("detected"):
                    caught += 1
                output = lr.get("output", "")
                if output == "[BLOCKED]" or (output and output != c.get("mutated") and not is_pii_in_text(pii, output)):
                    true_caught += 1
                if lr.get("latency_ms") is not None:
                    lat.append(lr["latency_ms"])
        out[layer] = {
            "n": n,
            "any_change_rate": round(100 * caught / n, 2) if n else 0,
            "true_neutralize_rate": round(100 * true_caught / n, 2) if n else 0,
            "avg_latency_ms": round(sum(lat) / len(lat), 1) if lat else 0,
        }
    return out


def slice_by(cases, key):
    buckets = defaultdict(list)
    for c in cases:
        buckets[c.get(key)].append(c)
    return {str(k): stats(v) for k, v in sorted(buckets.items(), key=lambda kv: str(kv[0]))}


def slice_lang_x_validity(cases):
    buckets = defaultdict(list)
    for c in cases:
        buckets[f"{c.get('lang')}_{c.get('validity_group')}"].append(c)
    return {k: stats(v) for k, v in sorted(buckets.items())}


def hardest_pii(cases, limit=20):
    buckets = defaultdict(list)
    for c in cases:
        buckets[c.get("pii_type")].append(c)
    rows = []
    for t, cs in buckets.items():
        s = stats(cs)
        if s["n"] >= 20:
            rows.append((t, s))
    rows.sort(key=lambda x: x[1]["real_bypass_rate"], reverse=True)
    return [{"pii_type": t, **s} for t, s in rows[:limit]]


def print_table(title, rows, headers):
    print(f"\n== {title} ==")
    widths = [max(len(h), max((len(str(r[i])) for r in rows), default=0)) for i, h in enumerate(headers)]
    line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(line)
    print("-" * len(line))
    for r in rows:
        print(" | ".join(str(r[i]).ljust(widths[i]) for i in range(len(headers))))


def main():
    fresh_cases = json.load(open(FRESH, "r", encoding="utf-8"))["results"]
    snap_cases = json.load(open(SNAPSHOT, "r", encoding="utf-8"))["results"]

    summary = {
        "run": "A_v3_TRUE_detection_on_fresh_rerun",
        "fresh_source": FRESH,
        "snapshot_source": SNAPSHOT,
        "baseline_layers": sorted(BASELINE_LAYERS),
        "n_fresh": len(fresh_cases),
        "n_snapshot": len(snap_cases),
        "fresh_overall": stats(fresh_cases),
        "snapshot_overall": stats(snap_cases),
        "fresh_per_layer": per_layer_catch(fresh_cases),
        "snapshot_per_layer": per_layer_catch(snap_cases),
        "fresh_by_lang": slice_by(fresh_cases, "lang"),
        "snapshot_by_lang": slice_by(snap_cases, "lang"),
        "fresh_by_validity_group": slice_by(fresh_cases, "validity_group"),
        "fresh_by_lang_x_validity": slice_lang_x_validity(fresh_cases),
        "snapshot_by_lang_x_validity": slice_lang_x_validity(snap_cases),
        "fresh_by_mutation_level": slice_by(fresh_cases, "mutation_level"),
        "fresh_hardest_pii_top20": hardest_pii(fresh_cases, 20),
    }

    json.dump(summary, open(OUTPUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print("=" * 78)
    print("  Run A v3 — Fresh 4/19 rerun, TRUE detection (L1~L3, GPT-4o excluded)")
    print("=" * 78)

    f, s = summary["fresh_overall"], summary["snapshot_overall"]
    print(f"\nOverall comparison (4/16 → 4/19):")
    print(f"  TRUE detection : {s['TRUE']:>5} ({s['true_rate']}%)  →  {f['TRUE']:>5} ({f['true_rate']}%)   delta={f['true_rate']-s['true_rate']:+.2f}%p")
    print(f"  REAL BYPASS    : {s['FALSE']+s['BYPASS']:>5} ({s['real_bypass_rate']}%)  →  {f['FALSE']+f['BYPASS']:>5} ({f['real_bypass_rate']}%)   delta={f['real_bypass_rate']-s['real_bypass_rate']:+.2f}%p")

    print_table(
        "Fresh per-layer",
        [[k, v["n"], f"{v['any_change_rate']}%", f"{v['true_neutralize_rate']}%", f"{v['avg_latency_ms']}ms"]
         for k, v in summary["fresh_per_layer"].items()],
        ["layer", "n", "any_change%", "true_neutralize%", "avg_lat"],
    )

    print_table(
        "By language (fresh)",
        [[k, v["n"], v["TRUE"], f"{v['true_rate']}%", v["FALSE"]+v["BYPASS"], f"{v['real_bypass_rate']}%"]
         for k, v in summary["fresh_by_lang"].items()],
        ["lang", "n", "TRUE", "true%", "real_bypass", "rb%"],
    )

    print_table(
        "By validity_group (fresh)",
        [[k, v["n"], v["TRUE"], f"{v['true_rate']}%", v["FALSE"]+v["BYPASS"], f"{v['real_bypass_rate']}%"]
         for k, v in summary["fresh_by_validity_group"].items()],
        ["group", "n", "TRUE", "true%", "real_bypass", "rb%"],
    )

    print_table(
        "Lang × Validity comparison (4/16 → 4/19)",
        [[k,
          summary["snapshot_by_lang_x_validity"].get(k, {}).get("n", "-"),
          f"{summary['snapshot_by_lang_x_validity'].get(k, {}).get('true_rate','-')}%",
          f"{summary['fresh_by_lang_x_validity'][k]['true_rate']}%",
          f"{summary['fresh_by_lang_x_validity'][k]['true_rate'] - summary['snapshot_by_lang_x_validity'].get(k,{}).get('true_rate',0):+.2f}%p"]
         for k in summary["fresh_by_lang_x_validity"]],
        ["bucket", "n", "snap_true%", "fresh_true%", "delta"],
    )

    print_table(
        "By mutation_level (fresh)",
        [[k, v["n"], v["TRUE"], f"{v['true_rate']}%", v["FALSE"]+v["BYPASS"], f"{v['real_bypass_rate']}%"]
         for k, v in summary["fresh_by_mutation_level"].items()],
        ["level", "n", "TRUE", "true%", "real_bypass", "rb%"],
    )

    print_table(
        "Hardest PII top 20 (fresh)",
        [[r["pii_type"], r["n"], r["TRUE"], f"{r['true_rate']}%", r["FALSE"]+r["BYPASS"], f"{r['real_bypass_rate']}%"]
         for r in summary["fresh_hardest_pii_top20"]],
        ["pii_type", "n", "TRUE", "true%", "real_bypass", "rb%"],
    )

    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    main()
