"""
Korean PII Guardrail Evaluator v1.0
====================================
퍼저 v4가 생성한 payloads를 읽어서 4계층 가드레일 평가를 수행.

Pipeline:
  1. korean_pii_fuzzer_v4.py → payloads_v4.json (인풋 생성)
  2. guardrail_evaluator.py → eval_results.json (가드레일 평가)

Usage:
  # Step 1: 페이로드 생성
  python korean_pii_fuzzer_v4.py --count 5 --output payloads.json

  # Step 2: 전체 4계층 평가
  python guardrail_evaluator.py --input payloads.json --output eval_results.json

  # Step 2 변형: Layer 1~3만 (GPT-4o 비용 절약)
  python guardrail_evaluator.py --input payloads.json --layers "Presidio PII,Bedrock Guardrail,Lakera"

  # Step 2 변형: 처음 50건만 빠른 테스트
  python guardrail_evaluator.py --input payloads.json --limit 50

  # Step 2 변형: 이어서 평가 (중단 지점부터)
  python guardrail_evaluator.py --input payloads.json --resume eval_results.json
"""

import argparse
import asyncio
import json
import time
import sys
import os
from datetime import datetime
from collections import defaultdict

try:
    import httpx
except ImportError:
    print("ERROR: httpx 필요 — pip install httpx")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════

LITELLM_BASE = os.getenv("LITELLM_BASE", "http://localhost:4000")
LITELLM_KEY = os.getenv("LITELLM_KEY", "sk-1234")

DEFAULT_LAYERS = [
    "Presidio PII",       # Layer 1
    "Bedrock Guardrail",  # Layer 2
    "Lakera",             # Layer 3
    "gpt4o-pii-judge",    # Layer 4
]


# ═══════════════════════════════════════════════════════════
# Guardrail API Caller
# ═══════════════════════════════════════════════════════════

async def call_guardrail(
    client: httpx.AsyncClient,
    guardrail_name: str,
    text: str,
) -> dict:
    """단일 가드레일 호출 → 결과 dict 반환"""
    start = time.time()
    try:
        resp = await client.post(
            f"{LITELLM_BASE}/guardrails/apply_guardrail",
            headers={
                "Authorization": f"Bearer {LITELLM_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "guardrail_name": guardrail_name,
                "text": text,
            },
            timeout=60.0,
        )
        latency_ms = int((time.time() - start) * 1000)

        if resp.status_code in (400, 500):
            # 가드레일이 차단 (HTTPException raise — 4xx 또는 5xx 둘 다 가능)
            try:
                body = resp.json()
                detail = body.get("detail") or body.get("error", {}).get("message", "") or ""
            except Exception:
                detail = resp.text[:300]
            return {
                "layer": guardrail_name,
                "detected": True,
                "action": "BLOCK",
                "output": "[BLOCKED]",
                "detail": str(detail)[:300],
                "latency_ms": latency_ms,
                "error": None,
            }
        elif resp.status_code == 200:
            data = resp.json()
            output = data.get("response_text", text)
            detected = (output != text)
            return {
                "layer": guardrail_name,
                "detected": detected,
                "action": "MASK" if detected else "PASS",
                "output": output,
                "detail": None,
                "latency_ms": latency_ms,
                "error": None,
            }
        else:
            return {
                "layer": guardrail_name,
                "detected": False,
                "action": "ERROR",
                "output": text,
                "detail": None,
                "latency_ms": int((time.time() - start) * 1000),
                "error": f"HTTP {resp.status_code}",
            }
    except Exception as e:
        return {
            "layer": guardrail_name,
            "detected": False,
            "action": "ERROR",
            "output": text,
            "detail": None,
            "latency_ms": int((time.time() - start) * 1000),
            "error": str(e)[:200],
        }


async def evaluate_payload(
    client: httpx.AsyncClient,
    payload: dict,
    layers: list[str],
) -> dict:
    """단일 payload에 대해 모든 계층 평가"""
    # v4 퍼저: "mutated" 필드에 변이된 텍스트, "original"에 원본 PII 값
    text = payload.get("mutated") or payload.get("text", "")
    layer_results = []

    for layer in layers:
        result = await call_guardrail(client, layer, text)
        layer_results.append(result)

        # GPT-4o Judge rate limit 방지
        if "gpt4o" in layer:
            await asyncio.sleep(1.5)

    # 집계
    any_detected = any(r["detected"] for r in layer_results)
    detected_by = [r["layer"] for r in layer_results if r["detected"]]
    total_latency = sum(r["latency_ms"] for r in layer_results)

    return {
        # 원본 payload 메타데이터 (v4 퍼저 필드명 호환)
        "id": payload.get("id", ""),
        "pii_type": payload.get("pii_type", ""),
        "pii_value": payload.get("original", ""),       # v4: "original" = PII 원본 값
        "mutation_level": payload.get("mutation_level", 0),
        "mutation_name": payload.get("mutation_name", ""),
        "mutated": text,                                 # v4: "mutated" = 변이된 전체 텍스트
        "lang": payload.get("lang", "KR"),
        "name_tier": payload.get("name_tier", ""),
        "validity_group": payload.get("validity_group", ""),
        "cat": payload.get("cat", ""),

        # 평가 결과
        "any_detected": any_detected,
        "all_bypassed": not any_detected,
        "detected_by": detected_by,
        "layer_results": layer_results,
        "total_latency_ms": total_latency,
        "evaluated_at": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════
# Main Evaluator
# ═══════════════════════════════════════════════════════════

async def run_evaluator(
    input_file: str,
    output_file: str,
    layers: list[str],
    limit: int = 0,
    resume_file: str = None,
):
    # 1. 페이로드 로드
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    payloads = data.get("payloads", [])
    if not payloads:
        print("ERROR: payloads가 비어있습니다.")
        return

    # 이어서 평가 (resume)
    already_done = set()
    existing_results = []
    if resume_file and os.path.exists(resume_file):
        with open(resume_file, "r", encoding="utf-8") as f:
            prev = json.load(f)
            existing_results = prev.get("results", [])
            for r in existing_results:
                key = f"{r.get('pii_type')}|{r.get('mutation_name')}|{r.get('mutated', '')[:50]}"
                already_done.add(key)
        print(f"  Resume: {len(already_done)} already evaluated, skipping...")

    # limit 적용
    if limit > 0:
        payloads = payloads[:limit]

    total = len(payloads)
    results = list(existing_results)
    evaluated = 0
    detected_count = 0
    bypassed_count = 0
    error_count = 0

    print(f"\n{'='*70}")
    print(f"  Korean PII Guardrail Evaluator v1.0")
    print(f"{'='*70}")
    print(f"  Input:     {input_file} ({total} payloads)")
    print(f"  Layers:    {', '.join(layers)}")
    print(f"  Output:    {output_file}")
    if limit > 0:
        print(f"  Limit:     {limit}")
    if already_done:
        print(f"  Resumed:   {len(already_done)} skipped")
    print(f"{'='*70}\n")

    consecutive_error_cases = 0
    ERROR_ABORT_THRESHOLD = 30

    async with httpx.AsyncClient() as client:
        for i, payload in enumerate(payloads):
            # Resume 스킵 체크
            key = f"{payload.get('pii_type')}|{payload.get('mutation_name')}|{payload.get('mutated', '')[:50]}"
            if key in already_done:
                continue

            # 평가
            result = await evaluate_payload(client, payload, layers)
            results.append(result)
            evaluated += 1

            # 연속 ERROR 감시 — 인프라 다운/정책 변경 시 데이터 오염 방지
            had_error = any(lr.get("error") or lr.get("action") == "ERROR"
                            for lr in result["layer_results"])
            if had_error:
                consecutive_error_cases += 1
                if consecutive_error_cases >= ERROR_ABORT_THRESHOLD:
                    _save_results(output_file, results, layers, input_file, evaluated, detected_count, bypassed_count)
                    print(f"\n{'!'*70}")
                    print(f"  ABORT: {ERROR_ABORT_THRESHOLD} consecutive cases had layer errors.")
                    print(f"  Likely cause: gateway/guardrail down or rate-limited.")
                    print(f"  Saved progress so far. Resume after fixing infra.")
                    print(f"{'!'*70}")
                    return
            else:
                consecutive_error_cases = 0

            if result["any_detected"]:
                detected_count += 1
                status = "DETECTED"
            else:
                bypassed_count += 1
                status = "BYPASSED"

            # 에러 체크
            errors = [r for r in result["layer_results"] if r.get("error")]
            if errors:
                error_count += 1

            # 진행 상황
            pii_type = result["pii_type"][:12]
            mut_name = result["mutation_name"][:12]
            detected_by = ",".join(r["layer"][:8] for r in result["layer_results"] if r["detected"])
            latency = result["total_latency_ms"]

            print(
                f"  [{evaluated:4d}/{total}] {status:8s} | "
                f"{pii_type:12s} | L{result['mutation_level']} {mut_name:12s} | "
                f"{latency:5d}ms | {detected_by or 'none'}"
            )

            # 중간 저장 (매 50건)
            if evaluated % 50 == 0:
                _save_results(output_file, results, layers, input_file, evaluated, detected_count, bypassed_count)

    # 최종 저장
    _save_results(output_file, results, layers, input_file, evaluated, detected_count, bypassed_count)

    # 통계 출력
    print_stats(results, layers)


def _save_results(output_file, results, layers, input_file, evaluated, detected, bypassed):
    """중간/최종 결과 저장"""
    total = len(results)
    output = {
        "metadata": {
            "evaluator": "Korean PII Guardrail Evaluator v1.0",
            "timestamp": datetime.now().isoformat(),
            "input_file": input_file,
            "layers": layers,
            "total_evaluated": total,
            "total_detected": sum(1 for r in results if r["any_detected"]),
            "total_bypassed": sum(1 for r in results if r["all_bypassed"]),
            "detection_rate": round(sum(1 for r in results if r["any_detected"]) / total * 100, 1) if total > 0 else 0,
            "bypass_rate": round(sum(1 for r in results if r["all_bypassed"]) / total * 100, 1) if total > 0 else 0,
        },
        "results": results,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def print_stats(results, layers):
    """통계 요약 출력"""
    total = len(results)
    if total == 0:
        print("  No results.")
        return

    detected = sum(1 for r in results if r["any_detected"])
    bypassed = sum(1 for r in results if r["all_bypassed"])

    print(f"\n{'='*70}")
    print(f"  EVALUATION SUMMARY")
    print(f"{'='*70}")
    print(f"  Total evaluated: {total}")
    print(f"  Detected (any):  {detected} ({detected/total*100:.1f}%)")
    print(f"  Bypassed (all):  {bypassed} ({bypassed/total*100:.1f}%)")

    # 계층별 탐지율
    print(f"\n  --- Detection Rate by Layer ---")
    for layer in layers:
        layer_detected = 0
        layer_total = 0
        layer_latency = []
        for r in results:
            for lr in r["layer_results"]:
                if lr["layer"] == layer:
                    layer_total += 1
                    if lr["detected"]:
                        layer_detected += 1
                    layer_latency.append(lr["latency_ms"])
        rate = round(layer_detected / layer_total * 100, 1) if layer_total > 0 else 0
        avg_lat = round(sum(layer_latency) / len(layer_latency)) if layer_latency else 0
        print(f"  {layer:20s}: {layer_detected:4d}/{layer_total:4d} ({rate:5.1f}%) | avg {avg_lat}ms")

    # 변이 레벨별 우회율
    print(f"\n  --- Bypass Rate by Mutation Level ---")
    for level in range(6):
        level_results = [r for r in results if r.get("mutation_level") == level]
        if not level_results:
            continue
        level_bypassed = sum(1 for r in level_results if r["all_bypassed"])
        level_total = len(level_results)
        rate = round(level_bypassed / level_total * 100, 1)
        print(f"  L{level} ({['Original','Character','Encoding','Format','Linguistic','Context'][level]:12s}): "
              f"{level_bypassed:4d}/{level_total:4d} ({rate:5.1f}%)")

    # PII 유형별 우회율
    print(f"\n  --- Bypass Rate by PII Type (Top 10) ---")
    type_stats = defaultdict(lambda: {"total": 0, "bypassed": 0})
    for r in results:
        ptype = r.get("pii_type", "unknown")
        type_stats[ptype]["total"] += 1
        if r["all_bypassed"]:
            type_stats[ptype]["bypassed"] += 1

    sorted_types = sorted(type_stats.items(), key=lambda x: x[1]["bypassed"]/max(x[1]["total"],1), reverse=True)
    for ptype, stats in sorted_types[:10]:
        rate = round(stats["bypassed"] / stats["total"] * 100, 1)
        print(f"  {ptype:16s}: {stats['bypassed']:4d}/{stats['total']:4d} ({rate:5.1f}%)")

    # 한국어 vs 영어 비교
    print(f"\n  --- Korean vs English ---")
    for lang in ["KR", "EN"]:
        lang_results = [r for r in results if r.get("lang", "KR") == lang]
        if not lang_results:
            continue
        lang_bypassed = sum(1 for r in lang_results if r["all_bypassed"])
        lang_total = len(lang_results)
        rate = round(lang_bypassed / lang_total * 100, 1)
        print(f"  {lang}: {lang_bypassed:4d}/{lang_total:4d} bypassed ({rate:5.1f}%)")

    print(f"\n{'='*70}\n")


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Korean PII Guardrail Evaluator")
    parser.add_argument("--input", "-i", required=True, help="Input payloads JSON (from fuzzer v4)")
    parser.add_argument("--output", "-o", default="eval_results.json", help="Output results JSON")
    parser.add_argument("--layers", "-l", default=",".join(DEFAULT_LAYERS), help="Comma-separated layer names")
    parser.add_argument("--limit", type=int, default=0, help="Max payloads to evaluate (0=all)")
    parser.add_argument("--resume", "-r", default=None, help="Resume from previous results file")
    parser.add_argument("--base-url", default="http://localhost:4000", help="LiteLLM base URL")
    parser.add_argument("--api-key", default="sk-1234", help="LiteLLM master key")

    args = parser.parse_args()

    global LITELLM_BASE, LITELLM_KEY
    LITELLM_BASE = args.base_url
    LITELLM_KEY = args.api_key

    layers = [l.strip() for l in args.layers.split(",")]

    asyncio.run(run_evaluator(
        input_file=args.input,
        output_file=args.output,
        layers=layers,
        limit=args.limit,
        resume_file=args.resume,
    ))


if __name__ == "__main__":
    main()
