# Phase 6 Hugging Face Korean PII NER 10k Result

Input: `PII/results/data/payloads_10k.json`

Metric note: these models return NER spans rather than redacted text. `target_hit_rate`
means at least one detected entity matched the target PII value or a
payload-provided target field. `any_detection_rate` means the model detected any
entity in the input text, even if it did not match the target PII.

| Rank | Model | Target hit | Any detection | Target bypass | Avg latency | P95 latency |
|---:|---|---:|---:|---:|---:|---:|
| 1 | `alphagyuu/Korean-PII-Masking-BertForTokenClassification` | 74.35% | 100.00% | 25.65% | 221 ms | 420 ms |
| 2 | `mncai/Korean-PII-Masking-Model` | 62.94% | 77.81% | 37.06% | 178 ms | 279 ms |
| 3 | `YATAV-ENT/aegis-personal-pii-ner` | 44.73% | 69.53% | 55.27% | 37 ms | 61 ms |
| 4 | `ParkJunSeong/PIILOT_NER_Model` | 28.61% | 49.85% | 71.39% | 46 ms | 81 ms |
| 5 | `seungkukim/korean-pii-masking` | 16.30% | 64.36% | 83.70% | 55 ms | 91 ms |

## Interpretation

`alphagyuu` had the highest target hit rate, but its 100% any-detection rate
suggests it may over-label broad spans. It should be reviewed for false positives
before using it as a blocking guardrail.

`mncai` was the strongest PyTorch/Transformers candidate and had a better balance
between any detection and target matching than `alphagyuu`.

`aegis` was the fastest model by a wide margin because it uses quantized ONNX
weights. Its target hit rate is lower than `alphagyuu` and `mncai`, but latency is
much better for real-time guardrail use.

`piilot` and `seungkukim` completed without errors, but their target hit rates are
too low to use alone on this dataset.

## Artifacts

- Consolidated result: `phase6_hf_10k_final.json`
- Original successful runs:
  - `phase6_hf_10k_alphagyuu.json`
  - `phase6_hf_10k_mncai.json`
  - `phase6_hf_10k_retry_mncai_aegis.json`
  - `phase6_hf_10k.json`
