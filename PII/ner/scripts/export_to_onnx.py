"""Export Korean PII NER v3 model to ONNX FP32 for CPU inference.

Usage:
    cd c:/My-AI-Security-Project/PII/ner
    python scripts/export_to_onnx.py

Outputs:
    models/pii_ner_v3/onnx/model.onnx          (ONNX graph)
    models/pii_ner_v3/onnx/config.json         (model config)
    models/pii_ner_v3/onnx/tokenizer.json      (tokenizer)
    models/pii_ner_v3/onnx/special_tokens_map.json
    models/pii_ner_v3/onnx/tokenizer_config.json
    models/pii_ner_v3/onnx/vocab.txt

Why ONNX:
    spec docs/14 NER_DESIGN §11 target: 60~120ms (256 char, CPU FP32)
    vs PyTorch native CPU: 150~250ms expected
    Reference aegis: ONNX CPU 37ms (Phase 6 comparison)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
NER_ROOT = HERE.parent
SOURCE_MODEL = NER_ROOT / "models" / "pii_ner_v3" / "final"
ONNX_OUTPUT = NER_ROOT / "models" / "pii_ner_v3" / "onnx"


def main() -> int:
    if not SOURCE_MODEL.is_dir():
        print(f"[error] source model not found: {SOURCE_MODEL}", file=sys.stderr)
        return 2

    print(f"[1/3] Source: {SOURCE_MODEL}")
    print(f"[1/3] Target: {ONNX_OUTPUT}")
    ONNX_OUTPUT.mkdir(parents=True, exist_ok=True)

    print(f"[2/3] Importing optimum.exporters.onnx...")
    from optimum.exporters.onnx import main_export

    print(f"[3/3] Exporting (opset=18, task=token-classification)...")
    t0 = time.time()
    main_export(
        model_name_or_path=str(SOURCE_MODEL),
        output=str(ONNX_OUTPUT),
        task="token-classification",
        opset=18,
        framework="pt",
        device="cpu",
    )
    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s. Output:")
    for path in sorted(ONNX_OUTPUT.iterdir()):
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"  {path.name:40s} {size_mb:>7.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
