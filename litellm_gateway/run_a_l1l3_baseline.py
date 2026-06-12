"""
Run A — L1~L3 baseline (GPT-4o L4 excluded).
Re-aggregates eval_full.json to measure what production guardrails
(Presidio + Bedrock + Lakera) actually catch WITHOUT an LLM-as-judge.

Outputs:
  - run_a_l1l3_summary.json (full stats for downstream comparison)
  - console tables for immediate inspection
"""
import json
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

INPUT = "eval_full.json"
OUTPUT = "run_a_l1l3_summary.json"
EXCLUDE_LAYER = "gpt4o-pii-judge"
BASELINE_LAYERS = ["Presidio PII", "Bedrock Guardrail", "Lakera"]


def case_detected_l1l3(case):
    """A case is 'detected' if any of L1/L2/L3 flagged it (L4 ignored)."""
    for lr in case["layer_results"]:
        if lr["layer"] in BASELINE_LAYERS and lr.get("detected"):
            return True, lr["layer"]
    return False, None


def bucket_stats(cases):
    n = len(cases)
    detected = sum(1 for c in cases if case_detected_l1l3(c)[0])
    return {
        "total": n,
        "detected": detected,
        "bypassed": n - detected,
        "detection_rate": round(100.0 * detected / n, 2) if n else 0.0,
        "bypass_rate": round(100.0 * (n - detected) / n, 2) if n else 0.0,
    }


def layer_contribution(cases):
    """How many cases did each L1/L2/L3 catch (independently)."""
    out = {}
    for layer in BASELINE_LAYERS:
        caught = 0
        total = 0
        lat = []
        for c in cases:
            for lr in c["layer_results"]:
                if lr["layer"] == layer:
                    total += 1
                    if lr.get("detected"):
                        caught += 1
                    if lr.get("latency_ms") is not None:
                        lat.append(lr["latency_ms"])
        out[layer] = {
            "evaluated": total,
            "caught": caught,
            "catch_rate": round(100.0 * caught / total, 2) if total else 0.0,
            "avg_latency_ms": round(sum(lat) / len(lat), 1) if lat else 0.0,
        }
    return out


def slice_by(cases, key):
    buckets = defaultdict(list)
    for c in cases:
        buckets[c.get(key)].append(c)
    return {str(k): bucket_stats(v) for k, v in sorted(buckets.items(), key=lambda kv: str(kv[0]))}


def slice_by_lang_x_validity(cases):
    buckets = defaultdict(list)
    for c in cases:
        key = f"{c.get('lang')}_{c.get('validity_group')}"
        buckets[key].append(c)
    return {k: bucket_stats(v) for k, v in sorted(buckets.items())}


def top_piitype_hardest(cases, limit=15):
    buckets = defaultdict(list)
    for c in cases:
        buckets[c.get("pii_type")].append(c)
    rows = []
    for t, cs in buckets.items():
        s = bucket_stats(cs)
        if s["total"] >= 20:
            rows.append((t, s))
    rows.sort(key=lambda x: x[1]["bypass_rate"], reverse=True)
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
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)
    cases = data["results"]

    summary = {
        "run": "A_L1L3_baseline",
        "source": INPUT,
        "excluded_layer": EXCLUDE_LAYER,
        "baseline_layers": BASELINE_LAYERS,
        "total_cases": len(cases),
        "overall": bucket_stats(cases),
        "per_layer_contribution": layer_contribution(cases),
        "by_lang": slice_by(cases, "lang"),
        "by_validity_group": slice_by(cases, "validity_group"),
        "by_mutation_level": slice_by(cases, "mutation_level"),
        "by_mutation_name": slice_by(cases, "mutation_name"),
        "by_lang_x_validity": slice_by_lang_x_validity(cases),
        "hardest_pii_types_top15": top_piitype_hardest(cases, 15),
    }

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("=" * 72)
    print(f"  Run A — L1~L3 baseline (GPT-4o excluded)  n={len(cases)}")
    print("=" * 72)

    o = summary["overall"]
    print(f"\nOverall: {o['detected']}/{o['total']} detected "
          f"({o['detection_rate']}%) — bypass {o['bypass_rate']}%")

    print_table(
        "Per-layer catch rate (independent)",
        [[k, v["caught"], v["evaluated"], f"{v['catch_rate']}%", f"{v['avg_latency_ms']}ms"]
         for k, v in summary["per_layer_contribution"].items()],
        ["layer", "caught", "total", "catch_rate", "avg_lat"],
    )

    print_table(
        "By language",
        [[k, v["total"], v["detected"], f"{v['detection_rate']}%", f"{v['bypass_rate']}%"]
         for k, v in summary["by_lang"].items()],
        ["lang", "n", "detected", "detection", "bypass"],
    )

    print_table(
        "By validity_group  (semantic = text-type PII)",
        [[k, v["total"], v["detected"], f"{v['detection_rate']}%", f"{v['bypass_rate']}%"]
         for k, v in summary["by_validity_group"].items()],
        ["group", "n", "detected", "detection", "bypass"],
    )

    print_table(
        "Lang x Validity  (where the gap lives)",
        [[k, v["total"], v["detected"], f"{v['detection_rate']}%", f"{v['bypass_rate']}%"]
         for k, v in summary["by_lang_x_validity"].items()],
        ["bucket", "n", "detected", "detection", "bypass"],
    )

    print_table(
        "By mutation_level",
        [[k, v["total"], v["detected"], f"{v['detection_rate']}%", f"{v['bypass_rate']}%"]
         for k, v in summary["by_mutation_level"].items()],
        ["level", "n", "detected", "detection", "bypass"],
    )

    print_table(
        "Hardest PII types (top 15 by bypass rate, n>=20)",
        [[r["pii_type"], r["total"], r["detected"], f"{r['detection_rate']}%", f"{r['bypass_rate']}%"]
         for r in summary["hardest_pii_types_top15"]],
        ["pii_type", "n", "detected", "detection", "bypass"],
    )

    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    main()
