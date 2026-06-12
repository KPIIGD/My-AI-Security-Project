"""
Cascade Evaluator — Layer 4 GPT-4o Judge
==========================================
Layer 1~3에서 우회(bypass) 또는 false detect된 케이스만 Layer 4에 투입.
비용/시간을 80% 절감하면서 cascade 구조의 실효성을 측정.

입력: Layer 1~3 평가 결과 (eval_l1l3.json)
출력: 각 케이스에 Layer 4 결과를 추가한 통합 결과

Logic:
  - TRUE_DETECT (Layer 1~3가 정확히 잡음) → Layer 4 스킵
  - FALSE_DETECT (주변만 잡음)           → Layer 4 투입
  - BYPASS (완전 우회)                   → Layer 4 투입

Usage:
  python cascade_evaluator.py -i eval_l1l3.json -o eval_full.json
  python cascade_evaluator.py -i eval_l1l3.json -o eval_full.json --limit 100
"""

import argparse
import asyncio
import json
import time
import sys
import os
import re
from datetime import datetime

try:
    import httpx
except ImportError:
    print("ERROR: pip install httpx")
    sys.exit(1)


LITELLM_BASE = os.getenv("LITELLM_BASE", "http://localhost:4000")
LITELLM_KEY = os.getenv("LITELLM_KEY", "sk-1234")
L4_GUARDRAIL = "gpt4o-pii-judge"


# ═══════════════════════════════════════════════════════════
# True Detection classifier (matches analyze_true_detection.py)
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


def classify_case(result):
    """케이스를 TRUE / FALSE / BYPASS로 분류"""
    pii_value = result.get("pii_value", "") or ""
    original = result.get("mutated", "")

    any_true = False
    any_false = False
    for lr in result.get("layer_results", []):
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
# Layer 4 API call
# ═══════════════════════════════════════════════════════════

async def call_l4(client, text):
    start = time.time()
    try:
        resp = await client.post(
            f"{LITELLM_BASE}/guardrails/apply_guardrail",
            headers={
                "Authorization": f"Bearer {LITELLM_KEY}",
                "Content-Type": "application/json",
            },
            json={"guardrail_name": L4_GUARDRAIL, "text": text},
            timeout=60.0,
        )
        latency = int((time.time() - start) * 1000)

        if resp.status_code == 500:
            try:
                detail = resp.json().get("detail", "")
            except Exception:
                detail = resp.text[:300]
            return {
                "layer": L4_GUARDRAIL,
                "detected": True,
                "action": "BLOCK",
                "output": "[BLOCKED]",
                "detail": str(detail)[:400],
                "latency_ms": latency,
                "error": None,
            }
        elif resp.status_code == 200:
            data = resp.json()
            output = data.get("response_text", text)
            return {
                "layer": L4_GUARDRAIL,
                "detected": (output != text),
                "action": "MASK" if (output != text) else "PASS",
                "output": output,
                "detail": None,
                "latency_ms": latency,
                "error": None,
            }
        else:
            return {
                "layer": L4_GUARDRAIL,
                "detected": False,
                "action": "ERROR",
                "output": text,
                "latency_ms": latency,
                "error": f"HTTP {resp.status_code}",
            }
    except Exception as e:
        return {
            "layer": L4_GUARDRAIL,
            "detected": False,
            "action": "ERROR",
            "output": text,
            "latency_ms": int((time.time() - start) * 1000),
            "error": str(e)[:200],
        }


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

async def run_cascade(input_file, output_file, limit=0, sleep_s=1.5, concurrency=1):
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = data.get("results", [])

    # 분류: Layer 1~3 결과로 TRUE/FALSE/BYPASS 나누기
    true_cases = []
    false_cases = []
    bypass_cases = []

    for r in results:
        cls = classify_case(r)
        if cls == "TRUE":
            true_cases.append(r)
        elif cls == "FALSE":
            false_cases.append(r)
        else:
            bypass_cases.append(r)

    # Layer 4에 투입할 케이스: 기본은 FALSE + BYPASS (cascade 최적화)
    # --all 모드면 TRUE도 포함 (풀 4계층 평가)
    if getattr(run_cascade, "_force_all", False):
        l4_targets = true_cases + false_cases + bypass_cases
    else:
        l4_targets = false_cases + bypass_cases

    # Resume 체크
    resume_ids = set()
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                prev = json.load(f)
            for r in prev.get("results", []):
                if any(lr.get("layer") == L4_GUARDRAIL for lr in r.get("layer_results", [])):
                    resume_ids.add(r.get("id", "") or r.get("mutated", "")[:50])
        except Exception:
            pass

    if limit > 0:
        l4_targets = l4_targets[:limit]

    total = len(l4_targets)

    print(f"\n{'='*70}")
    print(f"  Cascade Evaluator — Layer 4 GPT-4o Judge")
    print(f"{'='*70}")
    print(f"  Input:       {input_file}")
    print(f"  Total cases: {len(results):,}")
    print(f"  TRUE (skip): {len(true_cases):,} ({len(true_cases)/len(results)*100:.1f}%)")
    print(f"  FALSE:       {len(false_cases):,} ({len(false_cases)/len(results)*100:.1f}%)  → Layer 4")
    print(f"  BYPASS:      {len(bypass_cases):,} ({len(bypass_cases)/len(results)*100:.1f}%)  → Layer 4")
    print(f"  L4 targets:  {total:,}")
    if limit > 0:
        print(f"  Limit:       {limit}")
    if resume_ids:
        print(f"  Resume:      {len(resume_ids)} already done")
    print(f"  Sleep:       {sleep_s}s between calls (rate limit)")
    print(f"  Est. time:   ~{int(total * sleep_s / 60)}min")
    print(f"{'='*70}\n")

    # Layer 4 평가 실행 — Semaphore로 동시성 제어 (정확도 100% 유지)
    l4_count = 0
    l4_detected = 0
    l4_still_bypass = 0
    evaluated_results = list(results)
    id_to_idx = {(r.get("id", "") or r.get("mutated", "")[:50]): idx
                 for idx, r in enumerate(evaluated_results)}
    sem = asyncio.Semaphore(concurrency)
    lock = asyncio.Lock()
    save_lock = asyncio.Lock()

    async def process_one(client, target, total):
        nonlocal l4_count, l4_detected, l4_still_bypass
        target_id = target.get("id", "") or target.get("mutated", "")[:50]
        if target_id in resume_ids:
            return
        text = target.get("mutated", "")
        if not text or len(text.strip()) < 5:
            return

        async with sem:
            l4_result = await call_l4(client, text)
            await asyncio.sleep(sleep_s)  # gentle pacing inside the slot

        async with lock:
            l4_count += 1
            cur = l4_count
            if l4_result["detected"]:
                l4_detected += 1
            else:
                l4_still_bypass += 1

            idx = id_to_idx.get(target_id)
            if idx is not None:
                new_layers = [lr for lr in evaluated_results[idx].get("layer_results", [])
                              if lr.get("layer") != L4_GUARDRAIL]
                new_layers.append(l4_result)
                evaluated_results[idx]["layer_results"] = new_layers

            status = "DETECT" if l4_result["detected"] else "BYPASS"
            prev_cls = classify_case(target)
            ptype = target.get("pii_type", "")[:14]
            mut = target.get("mutation_name", "")[:14]
            lat = l4_result["latency_ms"]
            print(f"  [{cur:4d}/{total}] {status:6s} | prev={prev_cls:6s} | {ptype:14s} | "
                  f"L{target.get('mutation_level',0)} {mut:14s} | {lat:4d}ms", flush=True)

        if cur % 25 == 0:
            async with save_lock:
                _save(output_file, evaluated_results, data.get("metadata", {}), cur)

    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[process_one(client, t, total) for t in l4_targets])

    # 최종 저장
    _save(output_file, evaluated_results, data.get("metadata", {}), l4_count)

    # 요약
    print(f"\n{'='*70}")
    print(f"  CASCADE RESULTS")
    print(f"{'='*70}")
    print(f"  L4 evaluated:        {l4_count:,}")
    print(f"  L4 detected:         {l4_detected:,} ({l4_detected/max(l4_count,1)*100:.1f}%)")
    print(f"  L4 still bypass:     {l4_still_bypass:,} ({l4_still_bypass/max(l4_count,1)*100:.1f}%)")
    print(f"")
    final_bypass_count = l4_still_bypass  # L4도 못 잡은 것만 최종 bypass
    total_cases = len(results)
    original_bypass_pct = (len(false_cases) + len(bypass_cases)) / total_cases * 100
    final_bypass_pct = final_bypass_count / total_cases * 100
    print(f"  BEFORE Layer 4:      {len(false_cases)+len(bypass_cases):,} / {total_cases:,} bypass ({original_bypass_pct:.1f}%)")
    print(f"  AFTER  Layer 4:      {final_bypass_count:,} / {total_cases:,} bypass ({final_bypass_pct:.1f}%)")
    print(f"  Defense-in-depth gain: {original_bypass_pct - final_bypass_pct:.1f}%p")
    print(f"{'='*70}\n")
    print(f"  Saved to: {output_file}")
    print(f"  다음 단계: python analyze_true_detection.py {output_file}\n")


def _save(output_file, results, prev_meta, l4_count):
    output = {
        "metadata": {
            **prev_meta,
            "cascade_timestamp": datetime.now().isoformat(),
            "layer_4_added": True,
            "layer_4_evaluated_count": l4_count,
            "layers": prev_meta.get("layers", []) + ([L4_GUARDRAIL] if L4_GUARDRAIL not in prev_meta.get("layers", []) else []),
        },
        "results": results,
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", required=True, help="Layer 1~3 eval JSON")
    parser.add_argument("--output", "-o", default="eval_full.json", help="Output JSON")
    parser.add_argument("--limit", type=int, default=0, help="Max L4 calls (0=all)")
    parser.add_argument("--sleep", type=float, default=1.5, help="Seconds between L4 calls (per slot)")
    parser.add_argument("--concurrency", "-c", type=int, default=1, help="Concurrent L4 calls (gpt-4o-mini handles 5-8 well)")
    parser.add_argument("--all", action="store_true", help="Run L4 on ALL cases (not just bypassed ones) — for fair full-stack comparison")
    parser.add_argument("--base-url", default="http://localhost:4000")
    parser.add_argument("--api-key", default="sk-1234")
    args = parser.parse_args()

    global LITELLM_BASE, LITELLM_KEY
    LITELLM_BASE = args.base_url
    LITELLM_KEY = args.api_key

    run_cascade._force_all = args.all
    asyncio.run(run_cascade(
        input_file=args.input,
        output_file=args.output,
        limit=args.limit,
        sleep_s=args.sleep,
        concurrency=args.concurrency,
    ))


if __name__ == "__main__":
    main()
