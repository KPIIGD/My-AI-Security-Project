"""
Layer 0 A/B Test — 정규화 전/후 우회율 비교
=============================================
eval_full.json에서 bypass/false_detect 케이스를 골라
Korean Normalizer로 전처리한 뒤 동일 가드레일에 재투입.
정규화가 우회율을 얼마나 감소시키는지 측정.

Before: Layer 1~4 (No normalization)
After:  Layer 0 (Normalize) → Layer 1~4

Usage:
  python layer0_ab_test.py -i eval_full.json -o ab_results.json
  python layer0_ab_test.py -i eval_full.json -o ab_results.json --limit 100
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from collections import defaultdict

try:
    import httpx
except ImportError:
    print("ERROR: pip install httpx")
    sys.exit(1)

from korean_normalizer import KoreanNormalizer


LITELLM_BASE = os.getenv("LITELLM_BASE", "http://localhost:4000")
LITELLM_KEY = os.getenv("LITELLM_KEY", "sk-1234")

# 재평가할 가드레일 (Lakera는 PII 미지원이라 제외)
RE_EVAL_LAYERS = ["Presidio PII", "Bedrock Guardrail"]


# ═══════════════════════════════════════════════════════════
# True Detection classifier (same as analyze_true_detection.py)
# ═══════════════════════════════════════════════════════════

def is_pii_in_text(pii_value, text):
    if not pii_value or not text: return False
    if pii_value in text: return True
    pii_digits = re.sub(r'\D', '', pii_value)
    text_digits = re.sub(r'\D', '', text)
    if len(pii_digits) >= 6 and pii_digits in text_digits: return True
    fullwidth_map = {chr(0xFF10 + i): str(i) for i in range(10)}
    text_norm = "".join(fullwidth_map.get(c, c) for c in text)
    if pii_value in text_norm: return True
    text_digits_norm = re.sub(r'\D', '', text_norm)
    if len(pii_digits) >= 6 and pii_digits in text_digits_norm: return True
    circled_map = {chr(0x2460 + i): str(i + 1) for i in range(9)}
    circled_map["⓪"] = "0"
    text_c = "".join(circled_map.get(c, c) for c in text)
    text_c_digits = re.sub(r'\D', '', text_c)
    if len(pii_digits) >= 6 and pii_digits in text_c_digits: return True
    return False


def classify_case(pii_value, original, layer_outputs):
    """케이스를 TRUE / FALSE / BYPASS로 분류."""
    any_true = False
    any_false = False
    for lr in layer_outputs:
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


# ═══════════════════════════════════════════════════════════
# Guardrail API call
# ═══════════════════════════════════════════════════════════

async def call_guardrail(client, layer, text):
    start = time.time()
    try:
        resp = await client.post(
            f"{LITELLM_BASE}/guardrails/apply_guardrail",
            headers={
                "Authorization": f"Bearer {LITELLM_KEY}",
                "Content-Type": "application/json",
            },
            json={"guardrail_name": layer, "text": text},
            timeout=30.0,
        )
        latency = int((time.time() - start) * 1000)

        if resp.status_code == 500:
            try:
                detail = resp.json().get("detail", "")
            except Exception:
                detail = resp.text[:200]
            return {"layer": layer, "detected": True, "output": "[BLOCKED]",
                    "detail": str(detail)[:200], "latency_ms": latency, "error": None}
        elif resp.status_code == 200:
            data = resp.json()
            output = data.get("response_text", text)
            return {"layer": layer, "detected": (output != text),
                    "output": output, "detail": None, "latency_ms": latency, "error": None}
        else:
            return {"layer": layer, "detected": False, "output": text,
                    "latency_ms": latency, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"layer": layer, "detected": False, "output": text,
                "latency_ms": int((time.time() - start) * 1000), "error": str(e)[:200]}


async def evaluate_all_layers(client, text, layers):
    results = []
    for layer in layers:
        r = await call_guardrail(client, layer, text)
        results.append(r)
    return results


# ═══════════════════════════════════════════════════════════
# Main A/B test
# ═══════════════════════════════════════════════════════════

async def run_ab_test(input_file, output_file, limit=0):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = data.get("results", [])

    # bypassed/false_detect 케이스만 추려내기 (Before 기준)
    targets = []
    for r in results:
        pii_value = r.get("pii_value", "") or ""
        mutated = r.get("mutated", "")
        layer_outputs = r.get("layer_results", [])
        cls = classify_case(pii_value, mutated, layer_outputs)
        if cls in ("FALSE", "BYPASS"):
            r["_before_class"] = cls
            targets.append(r)

    if limit > 0:
        targets = targets[:limit]

    total = len(targets)
    nm = KoreanNormalizer()

    print(f"\n{'='*70}")
    print(f"  Layer 0 A/B Test — Korean Normalizer Effectiveness")
    print(f"{'='*70}")
    print(f"  Input:         {input_file}")
    print(f"  Total cases:   {len(results):,}")
    print(f"  Target cases:  {total:,} (BYPASS + FALSE_DETECT)")
    print(f"  Re-eval layers: {', '.join(RE_EVAL_LAYERS)}")
    print(f"  Est. time:     ~{int(total * len(RE_EVAL_LAYERS) * 0.5 / 60)}min")
    print(f"{'='*70}\n")

    # 실행
    ab_results = []
    stats = {
        "before": {"TRUE": 0, "FALSE": 0, "BYPASS": 0},
        "after":  {"TRUE": 0, "FALSE": 0, "BYPASS": 0},
        "unchanged": 0,   # 정규화로 안 바뀐 경우
        "improved": 0,    # Before=BYPASS/FALSE, After=TRUE
        "unchanged_bad": 0,  # 정규화 후에도 여전히 bypass
    }

    async with httpx.AsyncClient() as client:
        for idx, r in enumerate(targets):
            pii_value = r.get("pii_value", "") or ""
            original = r.get("mutated", "")
            before_class = r["_before_class"]

            # 정규화
            normalized = nm.normalize(original)
            text_changed = (normalized != original)

            if not text_changed:
                # 정규화로 아무 것도 안 바뀜 → 재평가할 필요 없음
                stats["unchanged"] += 1
                stats["before"][before_class] += 1
                stats["after"][before_class] += 1
                ab_results.append({
                    "id": r.get("id", ""),
                    "pii_type": r.get("pii_type", ""),
                    "pii_value": pii_value,
                    "mutation_level": r.get("mutation_level", 0),
                    "mutation_name": r.get("mutation_name", ""),
                    "lang": r.get("lang", "KR"),
                    "original_text": original,
                    "normalized_text": normalized,
                    "text_changed": False,
                    "before_class": before_class,
                    "after_class": before_class,
                    "before_layers": r.get("layer_results", []),
                    "after_layers": None,
                })
                continue

            # 재평가
            after_layers = await evaluate_all_layers(client, normalized, RE_EVAL_LAYERS)
            after_class = classify_case(pii_value, normalized, after_layers)

            stats["before"][before_class] += 1
            stats["after"][after_class] += 1

            if before_class != "TRUE" and after_class == "TRUE":
                stats["improved"] += 1
            elif after_class != "TRUE":
                stats["unchanged_bad"] += 1

            ab_results.append({
                "id": r.get("id", ""),
                "pii_type": r.get("pii_type", ""),
                "pii_value": pii_value,
                "mutation_level": r.get("mutation_level", 0),
                "mutation_name": r.get("mutation_name", ""),
                "lang": r.get("lang", "KR"),
                "original_text": original,
                "normalized_text": normalized,
                "text_changed": True,
                "before_class": before_class,
                "after_class": after_class,
                "before_layers": r.get("layer_results", []),
                "after_layers": after_layers,
            })

            # 진행 로그
            arrow = "→"
            change_tag = "✓" if after_class == "TRUE" else ("=" if after_class == before_class else "↓")
            ptype = r.get("pii_type", "")[:14]
            mut = r.get("mutation_name", "")[:14]
            print(f"  [{idx+1:4d}/{total}] {change_tag} {before_class:6s}{arrow}{after_class:6s} | {ptype:14s} | L{r.get('mutation_level',0)} {mut:14s}")

            # 중간 저장
            if (idx + 1) % 50 == 0:
                _save(output_file, ab_results, stats, targets, idx + 1)

    # 최종 저장
    _save(output_file, ab_results, stats, targets, len(ab_results))

    # 요약
    print_summary(stats, total, ab_results)


def _save(output_file, results, stats, targets, processed):
    output = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_targets": len(targets),
            "processed": processed,
            "layers_re_evaluated": RE_EVAL_LAYERS,
        },
        "stats": stats,
        "results": results,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def print_summary(stats, total, ab_results):
    print(f"\n{'='*70}")
    print(f"  A/B TEST RESULTS — LAYER 0 EFFECTIVENESS")
    print(f"{'='*70}")
    print(f"  Total targets: {total:,}")
    print(f"  Unchanged (no normalization applied): {stats['unchanged']:,}")
    print(f"  Improved (BYPASS/FALSE → TRUE):       {stats['improved']:,}  🎯")
    print(f"  Still bypass:                          {stats['unchanged_bad']:,}")
    print()
    print(f"  [Classification Distribution]")
    print(f"  {'Class':10s}  {'Before':>8s}  {'After':>8s}  {'Change':>10s}")
    print(f"  {'-'*10}  {'-'*8}  {'-'*8}  {'-'*10}")
    for cls in ["TRUE", "FALSE", "BYPASS"]:
        b = stats["before"][cls]
        a = stats["after"][cls]
        diff = a - b
        sign = "+" if diff > 0 else ""
        print(f"  {cls:10s}  {b:>8,}  {a:>8,}  {sign}{diff:>9,}")

    # Real bypass rate
    before_bypass = stats["before"]["FALSE"] + stats["before"]["BYPASS"]
    after_bypass = stats["after"]["FALSE"] + stats["after"]["BYPASS"]
    before_pct = before_bypass / total * 100 if total else 0
    after_pct = after_bypass / total * 100 if total else 0
    print()
    print(f"  [REAL BYPASS RATE (within target cases)]")
    print(f"  Before: {before_pct:5.1f}% ({before_bypass}/{total})")
    print(f"  After:  {after_pct:5.1f}% ({after_bypass}/{total})")
    print(f"  Improvement: {before_pct - after_pct:+5.1f}%p")

    # Per-PII-type improvements
    pii_improved = defaultdict(lambda: {"total": 0, "improved": 0})
    for r in ab_results:
        ptype = r["pii_type"]
        pii_improved[ptype]["total"] += 1
        if r["before_class"] != "TRUE" and r["after_class"] == "TRUE":
            pii_improved[ptype]["improved"] += 1

    top_improved = sorted(
        [(p, s) for p, s in pii_improved.items() if s["improved"] > 0],
        key=lambda x: -x[1]["improved"]
    )[:15]

    if top_improved:
        print()
        print(f"  [TOP 15 PII Types Most Recovered by Layer 0]")
        print(f"  {'PII Type':18s} {'Improved':>10s} {'Total':>8s} {'Rate':>8s}")
        print(f"  {'-'*18} {'-'*10} {'-'*8} {'-'*8}")
        for ptype, s in top_improved:
            rate = s["improved"] / s["total"] * 100
            print(f"  {ptype:18s} {s['improved']:>10d} {s['total']:>8d} {rate:>7.1f}%")

    # Per-mutation-level
    level_improved = defaultdict(lambda: {"total": 0, "improved": 0})
    for r in ab_results:
        lvl = r["mutation_level"]
        level_improved[lvl]["total"] += 1
        if r["before_class"] != "TRUE" and r["after_class"] == "TRUE":
            level_improved[lvl]["improved"] += 1

    print()
    print(f"  [Per-Mutation-Level Recovery]")
    level_names = ["Original", "Character", "Encoding", "Format", "Linguistic", "Context"]
    print(f"  {'Level':12s} {'Improved':>10s} {'Total':>8s} {'Rate':>8s}")
    print(f"  {'-'*12} {'-'*10} {'-'*8} {'-'*8}")
    for lvl in sorted(level_improved.keys()):
        s = level_improved[lvl]
        rate = s["improved"] / s["total"] * 100 if s["total"] else 0
        name = f"L{lvl} {level_names[lvl] if lvl < len(level_names) else ''}"
        print(f"  {name:12s} {s['improved']:>10d} {s['total']:>8d} {rate:>7.1f}%")

    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True, help="eval_full.json from cascade")
    parser.add_argument("--output", "-o", default="ab_results.json")
    parser.add_argument("--limit", type=int, default=0, help="Limit cases (0=all)")
    parser.add_argument("--base-url", default="http://localhost:4000")
    parser.add_argument("--api-key", default="sk-1234")
    args = parser.parse_args()

    global LITELLM_BASE, LITELLM_KEY
    LITELLM_BASE = args.base_url
    LITELLM_KEY = args.api_key

    asyncio.run(run_ab_test(args.input, args.output, args.limit))


if __name__ == "__main__":
    main()
