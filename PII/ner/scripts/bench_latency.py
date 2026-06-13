"""Measure CPU inference latency: PyTorch FP32 vs ONNX FP32.

Usage:
    cd c:/My-AI-Security-Project/PII/ner
    python scripts/bench_latency.py

Output:
    Console table: p50 / p95 / p99 / mean / std (ms) for each backend
    JSON file:     reports/latency_bench.json

spec docs/14 §11 targets:
    PyTorch CPU FP32:  150~250 ms (256 char)
    ONNX CPU FP32:      60~120 ms (target — 3-4x speedup)
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
NER_ROOT = HERE.parent
PT_MODEL_DIR = NER_ROOT / "models" / "pii_ner_v3" / "final"
ONNX_MODEL_DIR = NER_ROOT / "models" / "pii_ner_v3" / "onnx"
ONNX_INT8_DIR = NER_ROOT / "models" / "pii_ner_v3" / "onnx_int8"
REPORT_PATH = NER_ROOT / "reports" / "latency_bench.json"

# Korean adversarial text approx 256 chars (real PII payload mix)
SAMPLE_TEXT = (
    "안녕하세요 저는 김민우라고 합니다. 서울특별시 강남구 테헤란로 123-45 우리집에 살고 있고요 "
    "회사는 강남역 근처 ABC주식회사 이고 부서는 데이터팀입니다. "
    "주민번호는 900101-1234567 핸드폰 010-1234-5678 이메일 minwoo123@example.com "
    "이고 통장은 신한은행 110-123-456789 가족으로는 어머니 박정희(1965년생) 아버지 "
    "김철수(1960년생)가 있고 최근 처방받은 약은 아토르바스타틴 20mg 입니다."
)
# Ensure ~256 chars
SAMPLE_TEXT = SAMPLE_TEXT[:256] if len(SAMPLE_TEXT) >= 256 else SAMPLE_TEXT.ljust(256, " ")

WARMUP_ITERS = 30
MEASURE_ITERS = 100


def _percentile(values: list[float], pct: float) -> float:
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def _summarize(timings_ms: list[float], label: str) -> dict:
    summary = {
        "backend": label,
        "n": len(timings_ms),
        "mean_ms": round(statistics.mean(timings_ms), 2),
        "std_ms": round(statistics.stdev(timings_ms), 2) if len(timings_ms) > 1 else 0.0,
        "p50_ms": round(_percentile(timings_ms, 50), 2),
        "p95_ms": round(_percentile(timings_ms, 95), 2),
        "p99_ms": round(_percentile(timings_ms, 99), 2),
        "min_ms": round(min(timings_ms), 2),
        "max_ms": round(max(timings_ms), 2),
    }
    print(
        f"  {label:20s} n={summary['n']:>3}  p50={summary['p50_ms']:>6.1f}  "
        f"p95={summary['p95_ms']:>6.1f}  p99={summary['p99_ms']:>6.1f}  "
        f"mean={summary['mean_ms']:>6.1f}±{summary['std_ms']:>5.1f}"
    )
    return summary


def bench_pytorch(text: str) -> dict | None:
    print(f"\n[PyTorch CPU FP32]")
    if not PT_MODEL_DIR.is_dir():
        print(f"  skip: {PT_MODEL_DIR} not found")
        return None
    try:
        import torch
        from transformers import AutoModelForTokenClassification, AutoTokenizer
    except ImportError as exc:
        print(f"  skip: {exc}")
        return None

    print(f"  loading model from {PT_MODEL_DIR}...")
    tokenizer = AutoTokenizer.from_pretrained(str(PT_MODEL_DIR))
    model = AutoModelForTokenClassification.from_pretrained(str(PT_MODEL_DIR))
    model.eval()

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    print(f"  input tokens: {inputs['input_ids'].shape[1]}")

    # warmup
    with torch.no_grad():
        for _ in range(WARMUP_ITERS):
            _ = model(**inputs)

    # measure
    timings = []
    with torch.no_grad():
        for _ in range(MEASURE_ITERS):
            t0 = time.perf_counter()
            _ = model(**inputs)
            t1 = time.perf_counter()
            timings.append((t1 - t0) * 1000.0)

    return _summarize(timings, "PyTorch CPU FP32")


def _bench_onnx_dir(text: str, model_dir: Path, label: str) -> dict | None:
    print(f"\n[{label}]")
    if not model_dir.is_dir():
        print(f"  skip: {model_dir} not found")
        return None
    try:
        import numpy as np
        import onnxruntime as ort
        from transformers import AutoTokenizer
    except ImportError as exc:
        print(f"  skip: {exc}")
        return None

    import os
    print(f"  loading session from {model_dir}...")
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    physical_cores = os.cpu_count() or 4
    sess_options.intra_op_num_threads = max(1, physical_cores // 2)
    sess_options.inter_op_num_threads = 1
    print(f"  intra_op_threads: {sess_options.intra_op_num_threads}  inter_op_threads: 1")
    session = ort.InferenceSession(
        str(model_dir / "model.onnx"),
        sess_options=sess_options,
        providers=["CPUExecutionProvider"],
    )
    input_names = {inp.name for inp in session.get_inputs()}

    encoded = tokenizer(text, return_tensors="np", truncation=True, max_length=512)
    onnx_inputs = {k: v.astype(np.int64) for k, v in encoded.items() if k in input_names}
    print(f"  input tokens: {onnx_inputs['input_ids'].shape[1]}")

    for _ in range(WARMUP_ITERS):
        _ = session.run(None, onnx_inputs)

    timings = []
    for _ in range(MEASURE_ITERS):
        t0 = time.perf_counter()
        _ = session.run(None, onnx_inputs)
        t1 = time.perf_counter()
        timings.append((t1 - t0) * 1000.0)

    return _summarize(timings, label)


def bench_onnx(text: str) -> dict | None:
    return _bench_onnx_dir(text, ONNX_MODEL_DIR, "ONNX CPU FP32")


def bench_onnx_int8(text: str) -> dict | None:
    return _bench_onnx_dir(text, ONNX_INT8_DIR, "ONNX CPU INT8")


def main() -> int:
    print(f"text length: {len(SAMPLE_TEXT)} chars")
    print(f"warmup: {WARMUP_ITERS}  measure: {MEASURE_ITERS}")

    pt_summary = bench_pytorch(SAMPLE_TEXT)
    onnx_summary = bench_onnx(SAMPLE_TEXT)
    int8_summary = bench_onnx_int8(SAMPLE_TEXT)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "sample_text_length": len(SAMPLE_TEXT),
        "warmup_iters": WARMUP_ITERS,
        "measure_iters": MEASURE_ITERS,
        "pytorch": pt_summary,
        "onnx_fp32": onnx_summary,
        "onnx_int8": int8_summary,
    }
    if pt_summary and onnx_summary:
        speedup = pt_summary["p50_ms"] / onnx_summary["p50_ms"]
        report["speedup_fp32_p50"] = round(speedup, 2)
        print(f"\nFP32 Speedup (p50): {speedup:.2f}x  (PyTorch {pt_summary['p50_ms']:.1f}ms -> ONNX {onnx_summary['p50_ms']:.1f}ms)")
    if pt_summary and int8_summary:
        speedup_int8 = pt_summary["p50_ms"] / int8_summary["p50_ms"]
        report["speedup_int8_p50"] = round(speedup_int8, 2)
        print(f"INT8 Speedup (p50): {speedup_int8:.2f}x  (PyTorch {pt_summary['p50_ms']:.1f}ms -> ONNX INT8 {int8_summary['p50_ms']:.1f}ms)")

    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport written: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
