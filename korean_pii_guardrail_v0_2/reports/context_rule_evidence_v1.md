# Context Rule Evidence v1

- phase: `Execution Phase 4. Rule Metrics and Delta Sweep`
- rule_count: `30`
- raw_pii_safety_status: `pass`
- report_raw_text_leak_count: `0`

| Rule | Fired | TP | FP | LR | logLR | Precision | Precision Lift | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| context.boost.address_cooccur_for_person | 250 | 250 | 0 | 284.068915 | 5.649217 | 1.0 | 1.566563 | tune_magnitude |
| context.boost.bank_cooccur | 181 | 181 | 0 | n/a | n/a | 1.0 | 1.0 | insufficient_support |
| context.boost.field_label_account | 406 | 406 | 0 | n/a | n/a | 1.0 | 1.0 | insufficient_support |
| context.boost.field_label_address | 509 | 415 | 94 | 2.346084 | 0.852748 | 0.815324 | 1.249887 | tune_magnitude |
| context.boost.field_label_name | 411 | 411 | 0 | 466.645161 | 6.145569 | 1.0 | 1.566563 | tune_magnitude |
| context.boost.field_label_phone | 1439 | 1439 | 0 | 912.671233 | 6.816376 | 1.0 | 1.316676 | tune_magnitude |
| context.boost.full_address_detail | 389 | 389 | 0 | n/a | n/a | 1.0 | 1.0 | insufficient_support |
| context.boost.medical_label | 617 | 617 | 0 | n/a | n/a | 1.0 | 1.0 | insufficient_support |
| context.boost.organization_affiliation_context | 126 | 126 | 0 | 81.677983 | 4.402784 | 1.0 | 1.317461 | tune_magnitude |
| context.boost.phone_cooccur_for_person | 172 | 172 | 0 | 195.617302 | 5.27616 | 1.0 | 1.566563 | tune_magnitude |
| context.boost.title_after_name | 52 | 52 | 0 | 59.535191 | 4.086568 | 1.0 | 1.566563 | tune_magnitude |
| context.composite.ADDRESS_FULL | 157 | 157 | 0 | 178.607038 | 5.185188 | 1.0 | 1.566563 | policy_only_rule |
| context.composite.ADDRESS_UNIT | 284 | 284 | 0 | n/a | n/a | 1.0 | 1.0 | policy_only_rule |
| context.composite.BANK_ACCOUNT | 129 | 129 | 0 | 146.854839 | 4.989445 | 1.0 | 1.566563 | policy_only_rule |
| context.composite.DOB | 284 | 237 | 47 | 3.258502 | 1.181268 | 0.834507 | 1.377906 | policy_only_rule |
| context.composite.EMAIL | 130 | 130 | 0 | 147.98827 | 4.997133 | 1.0 | 1.566563 | policy_only_rule |
| context.composite.HOSPITAL | 143 | 143 | 0 | n/a | n/a | 1.0 | 1.0 | policy_only_rule |
| context.composite.MEDICAL_RECORD_NO | 143 | 143 | 0 | n/a | n/a | 1.0 | 1.0 | policy_only_rule |
| context.composite.PERSON_NAME | 588 | 588 | 0 | 388.409524 | 5.96206 | 1.0 | 1.329635 | policy_only_rule |
| context.composite.PHONE_LANDLINE | 0 | 0 | 0 | 0.567449 | -0.566604 | n/a | n/a | policy_only_rule |
| context.composite.PHONE_MOBILE | 172 | 172 | 0 | 195.617302 | 5.27616 | 1.0 | 1.566563 | policy_only_rule |
| context.composite.SCHOOL | 284 | 237 | 47 | 4.040292 | 1.396317 | 0.834507 | 1.508533 | policy_only_rule |
| context.penalty.abstract_value_context_for_person | 153 | 0 | 153 | 0.001848 | -6.293651 | 0.0 | 0.0 | tune_magnitude |
| context.penalty.code_or_log_context | 100 | 0 | 100 | 0.002753 | -5.895064 | 0.0 | 0.0 | tune_magnitude |
| context.penalty.example_context | 1232 | 2 | 1230 | 0.0006 | -7.418581 | 0.001623 | 0.002102 | tune_magnitude |
| context.penalty.example_keyword_for_person | 0 | 0 | 0 | 0.567449 | -0.566604 | n/a | n/a | insufficient_support |
| context.penalty.organization_not_person | 101 | 0 | 101 | 0.002795 | -5.879923 | 0.0 | 0.0 | tune_magnitude |
| context.penalty.private_ip | 0 | 0 | 0 | n/a | n/a | n/a | n/a | insufficient_support |
| context.penalty.public_phone_context | 0 | 0 | 0 | 0.317176 | -1.148298 | n/a | n/a | insufficient_support |
| context.penalty.weather_context_for_person | 126 | 0 | 126 | 0.002242 | -6.100387 | 0.0 | 0.0 | tune_magnitude |
