"""Measure INT8 quantization accuracy degradation vs FP32 baseline.

Usage:
    cd c:/My-AI-Security-Project/PII/ner
    python scripts/measure_quantization_accuracy.py

What is measured:
    - Token-level prediction agreement: P(INT8 == FP32) per subword token
    - Per-label agreement: where FP32 said 'B-NAME', INT8 still says 'B-NAME'?
    - Disagreement samples: which sentences trigger any divergence?

Why FP32-as-reference (not gold labels):
    Gold labels in pii_ner_v3.json are word-level; transformer predictions are
    subword-level. Subword <-> word alignment is non-trivial. We treat FP32
    as the truth and measure how much INT8 deviates from it. Absolute model
    quality vs. reference labels is measured separately by evaluation_harness
    (M10) on the FP32 model.

Output:
    reports/quantization_accuracy.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
NER_ROOT = HERE.parent
FP32_DIR = NER_ROOT / "models" / "pii_ner_v3" / "onnx"
INT8_DIR = NER_ROOT / "models" / "pii_ner_v3" / "onnx_int8"
DATA_FILE = NER_ROOT / "data" / "pii_ner_v3.json"
REPORT_PATH = NER_ROOT / "reports" / "quantization_accuracy.json"

N_SAMPLES = 200  # subset of test split


def main() -> int:
    for path in (FP32_DIR, INT8_DIR, DATA_FILE):
        if not path.exists():
            print(f"[error] missing: {path}", file=sys.stderr)
            return 2

    try:
        import onnxruntime as ort
        from transformers import AutoTokenizer
    except ImportError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 2

    print(f"[1/4] Loading test data from {DATA_FILE.name}...")
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    id2label = {int(k): v for k, v in data["id2label"].items()}
    test_examples = data["test"][:N_SAMPLES]
    print(f"      sampled {len(test_examples)} / {len(data['test'])} test examples")

    print(f"[2/4] Loading sessions...")
    tokenizer = AutoTokenizer.from_pretrained(str(FP32_DIR))
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess_fp32 = ort.InferenceSession(
        str(FP32_DIR / "model.onnx"), sess_options=sess_options,
        providers=["CPUExecutionProvider"],
    )
    sess_int8 = ort.InferenceSession(
        str(INT8_DIR / "model.onnx"), sess_options=sess_options,
        providers=["CPUExecutionProvider"],
    )
    fp32_inputs = {inp.name for inp in sess_fp32.get_inputs()}
    int8_inputs = {inp.name for inp in sess_int8.get_inputs()}

    def predict(session, input_names, text: str):
        encoded = tokenizer(text, return_tensors="np", truncation=True, max_length=512)
        onnx_in = {k: v.astype(np.int64) for k, v in encoded.items() if k in input_names}
        logits = session.run(None, onnx_in)[0][0]
        return logits.argmax(axis=-1), encoded["attention_mask"][0]

    print(f"[3/4] Running inference on {len(test_examples)} examples (FP32 + INT8)...")
    t0 = time.time()
    total_tokens = 0
    agree_tokens = 0
    per_label_total: dict[str, int] = {}
    per_label_agree: dict[str, int] = {}
    disagreement_samples: list[dict] = []

    for idx, ex in enumerate(test_examples):
        text = ex["sentence"]
        pred_fp32, mask_fp32 = predict(sess_fp32, fp32_inputs, text)
        pred_int8, mask_int8 = predict(sess_int8, int8_inputs, text)

        L = min(len(pred_fp32), len(pred_int8))
        sample_disagreements = []
        for i in range(L):
            if mask_fp32[i] == 0:
                continue
            label_name = id2label[int(pred_fp32[i])]
            per_label_total[label_name] = per_label_total.get(label_name, 0) + 1
            total_tokens += 1
            if pred_fp32[i] == pred_int8[i]:
                per_label_agree[label_name] = per_label_agree.get(label_name, 0) + 1
                agree_tokens += 1
            else:
                int8_label = id2label[int(pred_int8[i])]
                sample_disagreements.append({
                    "token_idx": i,
                    "fp32": label_name,
                    "int8": int8_label,
                })
        if sample_disagreements:
            disagreement_samples.append({
                "idx": idx,
                "sentence": text[:80] + ("..." if len(text) > 80 else ""),
                "n_disagree": len(sample_disagreements),
                "first_disagreement": sample_disagreements[0],
            })

    elapsed = time.time() - t0
    print(f"      done in {elapsed:.1f}s")

    print(f"\n[4/4] Results:")
    overall_agreement = agree_tokens / total_tokens if total_tokens else 0.0
    print(f"  Total tokens (non-pad): {total_tokens}")
    print(f"  Overall agreement:      {overall_agreement * 100:.3f}%")
    print(f"\n  Per-label agreement (FP32 prediction -> INT8 same?):")
    print(f"    {'label':25s} {'agree':>8s} / {'total':>6s}  {'rate':>7s}")
    per_label_summary = {}
    for label in sorted(per_label_total.keys()):
        total = per_label_total[label]
        agree = per_label_agree.get(label, 0)
        rate = agree / total if total else 0.0
        per_label_summary[label] = {
            "total": total, "agree": agree, "rate": round(rate, 4),
        }
        print(f"    {label:25s} {agree:>8d} / {total:>6d}  {rate * 100:>6.2f}%")

    print(f"\n  Sentences with any disagreement: {len(disagreement_samples)} / {len(test_examples)}")
    for s in disagreement_samples[:5]:
        d = s["first_disagreement"]
        print(f"    [{s['idx']:>3d}] {s['n_disagree']:>2d} disagrees  ({d['fp32']} -> {d['int8']})  {s['sentence']}")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "n_test_samples": len(test_examples),
        "total_tokens": total_tokens,
        "agree_tokens": agree_tokens,
        "overall_agreement": round(overall_agreement, 6),
        "per_label": per_label_summary,
        "n_sentences_with_disagreement": len(disagreement_samples),
        "sample_disagreements": disagreement_samples[:10],
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport written: {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
