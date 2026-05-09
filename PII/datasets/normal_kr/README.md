# Normal Korean Non-PII Dataset

This folder contains a generator for clean Korean text used to measure false
positive rates of PII detectors and guardrails.

The generator is designed to scale beyond 10k examples by combining:

- domain categories
- writing styles
- topics
- verbs and qualifiers
- sentence templates
- optional benign numeric expressions

It avoids direct PII-like patterns such as names, phone numbers, resident
registration numbers, emails, URLs, addresses, account/card numbers, and access
tokens.

## Generate 10k

```bash
python PII/datasets/normal_kr/generate_normal_kr.py \
  --count 10000 \
  --output PII/results/data/normal_kr_10k.json
```

## Generate larger sets

```bash
python PII/datasets/normal_kr/generate_normal_kr.py \
  --count 100000 \
  --output PII/results/data/normal_kr_100k.json
```

## Schema

```json
{
  "metadata": {
    "dataset": "normal_kr_non_pii",
    "count": 10000,
    "seed": 20260501
  },
  "payloads": [
    {
      "id": "NKR-000000",
      "text": "오늘 논의한 개선 방향은 다음 회의에서 다시 검토합니다.",
      "mutated": "오늘 논의한 개선 방향은 다음 회의에서 다시 검토합니다.",
      "lang": "KR",
      "label": "NO_PII",
      "category": "business",
      "style": "notice",
      "synthetic": true
    }
  ]
}
```

`mutated` is intentionally duplicated for compatibility with existing evaluators
that expect the project payload schema.
