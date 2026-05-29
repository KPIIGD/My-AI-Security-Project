# Existing Context Rule Evidence v1

- report_type: `ContextRuleEvidenceExistingData`
- phase: `Execution Phase 1. Baseline Evidence MVP`
- runtime_scoring_behavior_changed: `false`
- score_delta_changed: `false`
- minimum_support: `50`
- raw_pii_safety_status: `pass`
- report_raw_text_leak_count: `0`

## Dataset Summary

| Dataset | Records | Spans | Masked | Context Firings | Raw PII Logs | Invalid Offsets | NER Mode |
|---|---:|---:|---:|---:|---:|---:|---|
| hard_cases_v0 | 20 | 21 | 17 | 17 | 0 | 0 | mock |
| stage1_person_name_expanded | 800 | 752 | 300 | 825 | 0 | 0 | mock |
| stage2_contact_expanded | 1200 | 1240 | 500 | 864 | 0 | 0 | mock |
| stage3_address_expanded | 600 | 520 | 200 | 460 | 0 | 0 | mock |
| stage4_corporate_rrn_expanded | 400 | 400 | 400 | 0 | 0 | 0 | mock |
| stage5_numeric_identifier_expanded | 900 | 640 | 600 | 500 | 0 | 0 | mock |
| release_gate_v0_2_5000 | 5000 | 5971 | 4459 | 5873 | 0 | 0 | mock |

## Rule Evidence

| Rule ID | Family | Delta | Fired | TP | FP | Actionable TP | Actionable FP | Verdict |
|---|---|---:|---:|---:|---:|---:|---:|---|
| context.boost.address_cooccur_for_person | boost | 0.15 | 250 | 250 | 0 | 250 | 0 | tune_magnitude |
| context.boost.bank_cooccur | boost | 0.25 | 181 | 181 | 0 | 181 | 0 | insufficient_support |
| context.boost.field_label_account | boost | 0.3 | 403 | 403 | 0 | 403 | 0 | insufficient_support |
| context.boost.field_label_address | boost | 0.2 | 506 | 414 | 92 | 251 | 0 | tune_magnitude |
| context.boost.field_label_name | boost | 0.25 | 402 | 402 | 0 | 402 | 0 | tune_magnitude |
| context.boost.field_label_phone | boost | 0.15 | 1436 | 1436 | 0 | 1436 | 0 | tune_magnitude |
| context.boost.full_address_detail | boost | 0.2 | 388 | 388 | 0 | 388 | 0 | insufficient_support |
| context.boost.medical_label | boost | 0.2 | 614 | 614 | 0 | 614 | 0 | insufficient_support |
| context.boost.organization_affiliation_context | boost | 0.25 | 125 | 125 | 0 | 125 | 0 | tune_magnitude |
| context.boost.phone_cooccur_for_person | boost | 0.2 | 169 | 169 | 0 | 169 | 0 | tune_magnitude |
| context.boost.title_after_name | boost | 0.15 | 50 | 50 | 0 | 50 | 0 | tune_magnitude |
| context.composite.ADDRESS_FULL | composite | n/a | 157 | 157 | 0 | 157 | 0 | policy_only_rule |
| context.composite.ADDRESS_UNIT | composite | n/a | 284 | 284 | 0 | 284 | 0 | policy_only_rule |
| context.composite.BANK_ACCOUNT | composite | n/a | 129 | 129 | 0 | 129 | 0 | policy_only_rule |
| context.composite.DOB | composite | n/a | 284 | 237 | 47 | 237 | 47 | policy_only_rule |
| context.composite.EMAIL | composite | n/a | 130 | 130 | 0 | 130 | 0 | policy_only_rule |
| context.composite.HOSPITAL | composite | n/a | 143 | 143 | 0 | 143 | 0 | policy_only_rule |
| context.composite.MEDICAL_RECORD_NO | composite | n/a | 143 | 143 | 0 | 143 | 0 | policy_only_rule |
| context.composite.PERSON_NAME | composite | n/a | 585 | 585 | 0 | 585 | 0 | policy_only_rule |
| context.composite.PHONE_LANDLINE | composite | n/a | 0 | 0 | 0 | 0 | 0 | policy_only_rule |
| context.composite.PHONE_MOBILE | composite | n/a | 169 | 169 | 0 | 169 | 0 | policy_only_rule |
| context.composite.SCHOOL | composite | n/a | 284 | 237 | 47 | 237 | 47 | policy_only_rule |
| context.penalty.abstract_value_context_for_person | penalty | -0.2 | 151 | 0 | 151 | 0 | 0 | tune_magnitude |
| context.penalty.code_or_log_context | penalty | -0.2 | 100 | 0 | 100 | 0 | 0 | tune_magnitude |
| context.penalty.example_context | penalty | -0.15 | 1230 | 0 | 1230 | 0 | 0 | tune_magnitude |
| context.penalty.example_keyword_for_person | penalty | -0.35 | 0 | 0 | 0 | 0 | 0 | insufficient_support |
| context.penalty.organization_not_person | penalty | -0.25 | 100 | 0 | 100 | 0 | 0 | tune_magnitude |
| context.penalty.private_ip | penalty | -0.25 | 0 | 0 | 0 | 0 | 0 | insufficient_support |
| context.penalty.public_phone_context | penalty | -0.25 | 0 | 0 | 0 | 0 | 0 | insufficient_support |
| context.penalty.weather_context_for_person | penalty | -0.35 | 126 | 0 | 126 | 0 | 0 | tune_magnitude |

Direction evidence is based on aggregate candidate TP/FP split.
Magnitude evidence is intentionally not evaluated in Phase 1; no score delta changed.
Action evidence is limited to observed action counts; no action delta sweep was performed.
