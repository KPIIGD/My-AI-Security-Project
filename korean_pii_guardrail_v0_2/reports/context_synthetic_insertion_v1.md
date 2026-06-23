# M4 Phase 4 Safe Synthetic True-PII Insertion

This report summarizes non-materialized synthetic insertion. The generated anchor rows store shape and context only; no synthetic value, raw sentence, raw URL, or recoverable value is persisted.

- phase_exit_status: pass
- synthetic_anchor_window_count: 184
- final_anchor_window_count: 1293
- targeted_true_pii_counts: {"ADDRESS": 7, "PERSON_NAME": 7}
- final_by_label: {"non_pii": 1109, "true_pii": 184, "unknown": 0}
- final_data_quality_gate_status: pass
- raw_pii_leak_count: 0
- synthetic_value_materialized: false
- score_tuning_allowed_by_this_phase: false

## Synthetic Rows By Entity Group

| entity_group | count |
| --- | ---: |
| ADDRESS | 7 |
| BANK_ACCOUNT | 99 |
| EMAIL | 71 |
| PERSON_NAME | 7 |

## Synthetic Rows By Source Domain

| source_domain | count |
| --- | ---: |
| customer_support | 30 |
| ecommerce | 2 |
| education | 10 |
| enterprise_internal | 69 |
| finance | 51 |
| healthcare | 12 |
| public_services | 10 |
