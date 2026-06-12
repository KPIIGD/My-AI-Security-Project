"""
Guardrail True Detection Analyzer
==================================
"DETECTED" 카운트 자체는 신뢰할 수 없음.
Presidio/Bedrock이 PII 값 자체를 잡았는지 vs 주변 텍스트의 다른 것을 잡았는지
구분하는 질적 분석 도구.

판정 로직:
  - TRUE_DETECT: 원본 PII 값(또는 변이된 형태)이 output에서 마스킹/제거됨
  - FALSE_DETECT: output이 변했지만 PII 값은 그대로 남아있음 (주변만 마스킹)
  - BYPASS: output == input (아무것도 마스킹 안 됨)

Usage:
  python analyze_true_detection.py eval_l1l3.json
  python analyze_true_detection.py eval_l1l3.json --output true_detection_report.json
"""

import argparse
import json
import re
from collections import defaultdict


def is_pii_value_in_text(pii_value: str, text: str) -> bool:
    """
    PII 값이 텍스트에 (변형된 형태라도) 여전히 남아있는지 확인.
    단순 substring + 숫자 패턴 체크.
    """
    if not pii_value or not text:
        return False

    # 1. 원본 그대로 있으면 남아있는 것
    if pii_value in text:
        return True

    # 2. 숫자 시퀀스 추출 (주민번호, 카드번호 등)
    pii_digits = re.sub(r'\D', '', pii_value)
    text_digits = re.sub(r'\D', '', text)
    if len(pii_digits) >= 6 and pii_digits in text_digits:
        return True

    # 3. fullwidth 숫자도 체크
    fullwidth_map = {chr(0xFF10 + i): str(i) for i in range(10)}
    text_normalized = "".join(fullwidth_map.get(c, c) for c in text)
    if pii_value in text_normalized:
        return True
    pii_digits_norm = re.sub(r'\D', '', pii_value)
    text_digits_norm = re.sub(r'\D', '', text_normalized)
    if len(pii_digits_norm) >= 6 and pii_digits_norm in text_digits_norm:
        return True

    # 4. circled 숫자
    circled_map = {chr(0x2460 + i): str(i + 1) for i in range(9)}
    circled_map["⓪"] = "0"
    text_circled = "".join(circled_map.get(c, c) for c in text)
    text_circled_digits = re.sub(r'\D', '', text_circled)
    if len(pii_digits) >= 6 and pii_digits in text_circled_digits:
        return True

    return False


def classify_detection(pii_value: str, original_text: str, layer_output: str) -> str:
    """
    레이어 하나의 출력을 3가지로 분류.
    """
    if layer_output == original_text or layer_output == "":
        return "NO_CHANGE"  # 아무것도 안 바뀜

    if layer_output == "[BLOCKED]":
        return "TRUE_DETECT"  # 차단 = 확실한 탐지

    # output이 변했지만 PII 값이 남아있으면 FALSE_DETECT
    if is_pii_value_in_text(pii_value, layer_output):
        return "FALSE_DETECT"  # 주변만 잡고 PII는 놓침

    return "TRUE_DETECT"  # PII 값이 사라짐


def analyze(results: list) -> dict:
    """전체 분석"""
    stats = {
        "total": len(results),
        "by_classification": defaultdict(int),
        "by_pii_type": defaultdict(lambda: {
            "total": 0,
            "true_detect": 0,
            "false_detect": 0,
            "bypass": 0,
        }),
        "by_layer": defaultdict(lambda: {
            "total": 0,
            "true_detect": 0,
            "false_detect": 0,
            "no_change": 0,
        }),
        "by_level": defaultdict(lambda: {
            "total": 0,
            "true_detect": 0,
            "false_detect": 0,
            "bypass": 0,
        }),
        "by_lang": defaultdict(lambda: {
            "total": 0,
            "true_detect": 0,
            "false_detect": 0,
            "bypass": 0,
        }),
    }

    for r in results:
        pii_value = r.get("pii_value", "") or ""
        original_text = r.get("mutated", "")
        ptype = r.get("pii_type", "unknown")
        level = r.get("mutation_level", 0)
        lang = r.get("lang", "KR")

        # 각 layer 결과 분류
        classifications = []
        for lr in r.get("layer_results", []):
            output = lr.get("output", "")
            cls = classify_detection(pii_value, original_text, output)
            classifications.append((lr["layer"], cls))

            stats["by_layer"][lr["layer"]]["total"] += 1
            if cls == "TRUE_DETECT":
                stats["by_layer"][lr["layer"]]["true_detect"] += 1
            elif cls == "FALSE_DETECT":
                stats["by_layer"][lr["layer"]]["false_detect"] += 1
            else:
                stats["by_layer"][lr["layer"]]["no_change"] += 1

        # 전체 케이스 분류
        any_true = any(c == "TRUE_DETECT" for _, c in classifications)
        any_false = any(c == "FALSE_DETECT" for _, c in classifications)

        if any_true:
            case_cls = "TRUE_DETECT"
        elif any_false:
            case_cls = "FALSE_DETECT_ONLY"
        else:
            case_cls = "BYPASS"

        stats["by_classification"][case_cls] += 1

        # PII 유형별
        stats["by_pii_type"][ptype]["total"] += 1
        if case_cls == "TRUE_DETECT":
            stats["by_pii_type"][ptype]["true_detect"] += 1
        elif case_cls == "FALSE_DETECT_ONLY":
            stats["by_pii_type"][ptype]["false_detect"] += 1
        else:
            stats["by_pii_type"][ptype]["bypass"] += 1

        # 변이 레벨별
        stats["by_level"][level]["total"] += 1
        if case_cls == "TRUE_DETECT":
            stats["by_level"][level]["true_detect"] += 1
        elif case_cls == "FALSE_DETECT_ONLY":
            stats["by_level"][level]["false_detect"] += 1
        else:
            stats["by_level"][level]["bypass"] += 1

        # 언어별
        stats["by_lang"][lang]["total"] += 1
        if case_cls == "TRUE_DETECT":
            stats["by_lang"][lang]["true_detect"] += 1
        elif case_cls == "FALSE_DETECT_ONLY":
            stats["by_lang"][lang]["false_detect"] += 1
        else:
            stats["by_lang"][lang]["bypass"] += 1

    return stats


def print_report(stats: dict):
    total = stats["total"]

    print("=" * 70)
    print("  TRUE DETECTION 분석 — 진짜 탐지 vs 가짜 탐지 vs 우회")
    print("=" * 70)
    print(f"  Total cases: {total:,}")
    print()

    # 전체 분류
    print("  [Case Classification]")
    tdc = stats["by_classification"]["TRUE_DETECT"]
    fdc = stats["by_classification"]["FALSE_DETECT_ONLY"]
    bpc = stats["by_classification"]["BYPASS"]
    print(f"    TRUE_DETECT       : {tdc:>6,} ({tdc/total*100:5.1f}%) — PII 값 실제 탐지")
    print(f"    FALSE_DETECT_ONLY : {fdc:>6,} ({fdc/total*100:5.1f}%) — 주변만 잡고 PII 놓침")
    print(f"    BYPASS            : {bpc:>6,} ({bpc/total*100:5.1f}%) — 완전 우회")
    real_bypass_rate = (fdc + bpc) / total * 100
    print(f"    REAL_BYPASS_RATE  : {fdc+bpc:>6,} ({real_bypass_rate:5.1f}%) — FALSE + BYPASS")
    print()

    # 레이어별
    print("  [Layer-level True Detection]")
    print(f"    {'Layer':20s} {'TRUE':>8s} {'FALSE':>8s} {'NONE':>8s} {'TRUE%':>7s} {'FALSE%':>7s}")
    print(f"    {'-'*20} {'-'*8} {'-'*8} {'-'*8} {'-'*7} {'-'*7}")
    for layer, s in stats["by_layer"].items():
        tt = s["total"]
        td = s["true_detect"]
        fd = s["false_detect"]
        nc = s["no_change"]
        print(f"    {layer:20s} {td:>8,} {fd:>8,} {nc:>8,} "
              f"{td/tt*100:>6.1f}% {fd/tt*100:>6.1f}%")
    print()

    # 언어별
    print("  [Korean vs English]")
    print(f"    {'Lang':6s} {'TRUE':>8s} {'FALSE':>8s} {'BYPASS':>8s} {'Total':>8s} "
          f"{'True%':>7s} {'Real Bypass%':>13s}")
    print(f"    {'-'*6} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*7} {'-'*13}")
    for lang, s in stats["by_lang"].items():
        tt = s["total"]
        td = s["true_detect"]
        fd = s["false_detect"]
        bp = s["bypass"]
        rb = (fd + bp) / tt * 100
        print(f"    {lang:6s} {td:>8,} {fd:>8,} {bp:>8,} {tt:>8,} "
              f"{td/tt*100:>6.1f}% {rb:>12.1f}%")
    print()

    # 변이 레벨별
    print("  [Mutation Level]")
    print(f"    {'Level':8s} {'TRUE':>8s} {'FALSE':>8s} {'BYPASS':>8s} {'Total':>8s} "
          f"{'True%':>7s} {'Real Bypass%':>13s}")
    print(f"    {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*7} {'-'*13}")
    level_names = ["Original", "Character", "Encoding", "Format", "Linguistic", "Context"]
    for lvl in sorted(stats["by_level"].keys()):
        s = stats["by_level"][lvl]
        tt = s["total"]
        td = s["true_detect"]
        fd = s["false_detect"]
        bp = s["bypass"]
        rb = (fd + bp) / tt * 100
        name = level_names[lvl] if lvl < len(level_names) else f"L{lvl}"
        print(f"    L{lvl} {name:6s} {td:>8,} {fd:>8,} {bp:>8,} {tt:>8,} "
              f"{td/tt*100:>6.1f}% {rb:>12.1f}%")
    print()

    # PII 유형별 — TRUE 탐지율 낮은 순 (취약한 것들)
    print("  [PII Type — Top 20 Most Bypassed (by REAL bypass = FALSE + BYPASS)]")
    print(f"    {'PII Type':18s} {'TRUE':>6s} {'FALSE':>6s} {'BYPASS':>7s} {'Total':>6s} "
          f"{'Real Bypass%':>13s}")
    print(f"    {'-'*18} {'-'*6} {'-'*6} {'-'*7} {'-'*6} {'-'*13}")
    sorted_types = sorted(
        stats["by_pii_type"].items(),
        key=lambda x: -(x[1]["false_detect"] + x[1]["bypass"]) / max(x[1]["total"], 1)
    )
    for ptype, s in sorted_types[:20]:
        tt = s["total"]
        td = s["true_detect"]
        fd = s["false_detect"]
        bp = s["bypass"]
        rb = (fd + bp) / tt * 100
        print(f"    {ptype:18s} {td:>6,} {fd:>6,} {bp:>7,} {tt:>6,} {rb:>12.1f}%")
    print()
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="eval results JSON")
    parser.add_argument("--output", "-o", default=None, help="Save stats as JSON")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = data.get("results", [])
    print(f"\n  Loading {len(results):,} results from {args.input}...")

    stats = analyze(results)
    print_report(stats)

    if args.output:
        # defaultdict → dict 변환
        def to_dict(d):
            if isinstance(d, defaultdict):
                d = dict(d)
            if isinstance(d, dict):
                return {k: to_dict(v) for k, v in d.items()}
            return d

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(to_dict(stats), f, ensure_ascii=False, indent=2)
        print(f"  Saved: {args.output}\n")


if __name__ == "__main__":
    main()
