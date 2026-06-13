"""Quantize ONNX FP32 model to INT8 (dynamic quantization, weights-only).

Usage:
    cd c:/My-AI-Security-Project/PII/ner
    python scripts/quantize_to_int8.py

Why dynamic over static:
    - No calibration data required (static needs representative samples)
    - Activation kept in FP32 at runtime, only weights quantized
    - Smaller accuracy drop on transformers (typically <1%p macro-F1)
    - 4x smaller model file (1.3GB -> ~330MB)
    - 2-3x speedup on AVX2/AVX512 CPUs

Output:
    models/pii_ner_v3/onnx_int8/model.onnx       (INT8 weights)
    models/pii_ner_v3/onnx_int8/config.json      (copy)
    models/pii_ner_v3/onnx_int8/tokenizer.json   (copy)
    ...
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
NER_ROOT = HERE.parent
FP32_DIR = NER_ROOT / "models" / "pii_ner_v3" / "onnx"
INT8_DIR = NER_ROOT / "models" / "pii_ner_v3" / "onnx_int8"


def main() -> int:
    if not FP32_DIR.is_dir():
        print(f"[error] FP32 ONNX not found: {FP32_DIR}", file=sys.stderr)
        print(f"        Run scripts/export_to_onnx.py first.", file=sys.stderr)
        return 2

    fp32_model = FP32_DIR / "model.onnx"
    if not fp32_model.is_file():
        print(f"[error] model.onnx missing under {FP32_DIR}", file=sys.stderr)
        return 2

    print(f"[1/3] Source: {fp32_model} ({fp32_model.stat().st_size / (1024**3):.2f} GB)")
    INT8_DIR.mkdir(parents=True, exist_ok=True)
    int8_model = INT8_DIR / "model.onnx"
    print(f"[1/3] Target: {int8_model}")

    print(f"[2/3] Importing onnxruntime.quantization...")
    from onnxruntime.quantization import quantize_dynamic, QuantType

    print(f"[3/3] Running dynamic quantization (weight_type=QInt8)...")
    t0 = time.time()
    quantize_dynamic(
        model_input=str(fp32_model),
        model_output=str(int8_model),
        weight_type=QuantType.QInt8,
    )
    elapsed = time.time() - t0
    int8_size_mb = int8_model.stat().st_size / (1024**2)
    fp32_size_mb = fp32_model.stat().st_size / (1024**2)
    print(f"\nDone in {elapsed:.1f}s.")
    print(f"  FP32: {fp32_size_mb:>7.1f} MB")
    print(f"  INT8: {int8_size_mb:>7.1f} MB  ({fp32_size_mb / int8_size_mb:.1f}x smaller)")

    # Copy tokenizer/config alongside (so AutoTokenizer.from_pretrained works on INT8 dir)
    for fname in ("config.json", "tokenizer.json", "special_tokens_map.json",
                  "tokenizer_config.json", "vocab.txt"):
        src = FP32_DIR / fname
        if src.is_file():
            shutil.copy2(src, INT8_DIR / fname)
    print(f"  copied tokenizer/config files")

    print(f"\nINT8 model ready at: {INT8_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
