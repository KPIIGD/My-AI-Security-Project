# Phase 6 - Hugging Face Korean PII NER baselines

This phase evaluates external Hugging Face PII/NER models on the project payload
schema.

## Models

- `mncai/Korean-PII-Masking-Model`
- `alphagyuu/Korean-PII-Masking-BertForTokenClassification`
- `ParkJunSeong/PIILOT_NER_Model`
- `seungkukim/korean-pii-masking`
- `YATAV-ENT/aegis-personal-pii-ner`

## Metrics

These models return NER spans, not redacted text. The evaluator reports both:

- `any_detection_rate`: at least one entity was detected in the text.
- `target_hit_rate`: a detected span appears to match the target PII value or a
  payload-provided target field.

`target_bypass_rate` is `100 - target_hit_rate`.

## Prerequisites

```bash
pip install -r requirements-hf.txt
```

Notes:

- `mncai/Korean-PII-Masking-Model` stores the Transformers model under the
  `bert/` subfolder.
- `YATAV-ENT/aegis-personal-pii-ner` publishes ONNX weights, so the evaluator
  uses `onnxruntime`.
- `alphagyuu/Korean-PII-Masking-BertForTokenClassification` publishes
  TensorFlow weights, so the evaluator pins Transformers 4.x plus `tf-keras`.

## Quick smoke test

```bash
python phase6_hf_pii_eval.py \
  --input ../data/payloads_10k.json \
  --output phase6_hf_smoke_50.json \
  --limit 50 \
  --batch-size 8 \
  --device cpu
```

## 10k run

```bash
python phase6_hf_pii_eval.py \
  --input ../data/payloads_10k.json \
  --output phase6_hf_10k.json \
  --batch-size 16 \
  --device cpu \
  --save-every 500
```

## 100k run

Generate or provide a 100k payload file first. The evaluator only requires the
same schema as `../data/payloads_10k.json`. If you need an exact 100k volume run
from the existing 10k benchmark file, use stratified resampling:

```bash
python make_payload_sample.py \
  --input ../data/payloads_10k.json \
  --output ../data/payloads_100k.json \
  --target 100000 \
  --with-replacement
```

```bash
python phase6_hf_pii_eval.py \
  --input ../data/payloads_100k.json \
  --output phase6_hf_100k.json \
  --batch-size 16 \
  --device cpu \
  --save-every 1000
```

Resume an interrupted run:

```bash
python phase6_hf_pii_eval.py \
  --input ../data/payloads_100k.json \
  --output phase6_hf_100k.json \
  --resume phase6_hf_100k.json \
  --batch-size 16 \
  --device cpu
```

## Final 10k result

The consolidated successful run is saved at:

- `phase6_hf_10k_final.json`
- `phase6_hf_10k_report.md`
