# Context Score Tuning v1

- phase: `Execution Phase 4. Rule Metrics and Delta Sweep`
- runtime_scoring_behavior_changed: `false`
- score_delta_changed: `false`
- public_corpus_used_for_score_tuning: `false`
- eligible_rule_count: `12`
- config_changes_proposed: `0`

Direction evidence comes from LR/logLR and precision_when_fired. Magnitude evidence comes from the delta sweep. Action evidence comes from action-level metrics in the sweep.

## Proposed Config Changes

No runtime scoring config changes are proposed in Phase 4.

## Delta Sweep Summary

| Rule | Current | Selected | Reason | Candidates |
|---|---:|---:|---|---:|
| context.boost.address_cooccur_for_person | 0.15 | 0.15 | conservative_current_delta_kept | 5 |
| context.boost.field_label_address | 0.2 | 0.2 | conservative_current_delta_kept | 4 |
| context.boost.field_label_name | 0.25 | 0.25 | conservative_current_delta_kept | 4 |
| context.boost.field_label_phone | 0.15 | 0.15 | conservative_current_delta_kept | 5 |
| context.boost.organization_affiliation_context | 0.25 | 0.25 | conservative_current_delta_kept | 4 |
| context.boost.phone_cooccur_for_person | 0.2 | 0.2 | conservative_current_delta_kept | 4 |
| context.boost.title_after_name | 0.15 | 0.15 | conservative_current_delta_kept | 5 |
| context.penalty.abstract_value_context_for_person | -0.2 | -0.2 | conservative_current_delta_kept | 5 |
| context.penalty.code_or_log_context | -0.2 | -0.2 | conservative_current_delta_kept | 5 |
| context.penalty.example_context | -0.15 | -0.15 | conservative_current_delta_kept | 5 |
| context.penalty.organization_not_person | -0.25 | -0.25 | conservative_current_delta_kept | 4 |
| context.penalty.weather_context_for_person | -0.35 | -0.35 | conservative_current_delta_kept | 4 |

## Rule Summary

| Rule | Fired | logLR | Precision Lift | Direction Band | Proposed Delta Band | Verdict |
|---|---:|---:|---:|---|---|---|
| context.boost.address_cooccur_for_person | 250 | 5.649217 | 1.566563 | strong_positive | strong_boost | tune_magnitude |
| context.boost.bank_cooccur | 181 | n/a | 1.0 | insufficient_support | insufficient_support | insufficient_support |
| context.boost.field_label_account | 406 | n/a | 1.0 | insufficient_support | insufficient_support | insufficient_support |
| context.boost.field_label_address | 509 | 0.852748 | 1.249887 | weak_positive | small_boost | tune_magnitude |
| context.boost.field_label_name | 411 | 6.145569 | 1.566563 | strong_positive | strong_boost | tune_magnitude |
| context.boost.field_label_phone | 1439 | 6.816376 | 1.316676 | strong_positive | strong_boost | tune_magnitude |
| context.boost.full_address_detail | 389 | n/a | 1.0 | insufficient_support | insufficient_support | insufficient_support |
| context.boost.medical_label | 617 | n/a | 1.0 | insufficient_support | insufficient_support | insufficient_support |
| context.boost.organization_affiliation_context | 126 | 4.402784 | 1.317461 | strong_positive | strong_boost | tune_magnitude |
| context.boost.phone_cooccur_for_person | 172 | 5.27616 | 1.566563 | strong_positive | strong_boost | tune_magnitude |
| context.boost.title_after_name | 52 | 4.086568 | 1.566563 | strong_positive | strong_boost | tune_magnitude |
| context.composite.ADDRESS_FULL | 157 | 5.185188 | 1.566563 | strong_positive | strong_boost | policy_only_rule |
| context.composite.ADDRESS_UNIT | 284 | n/a | 1.0 | insufficient_support | insufficient_support | policy_only_rule |
| context.composite.BANK_ACCOUNT | 129 | 4.989445 | 1.566563 | strong_positive | strong_boost | policy_only_rule |
| context.composite.DOB | 284 | 1.181268 | 1.377906 | positive | normal_boost | policy_only_rule |
| context.composite.EMAIL | 130 | 4.997133 | 1.566563 | strong_positive | strong_boost | policy_only_rule |
| context.composite.HOSPITAL | 143 | n/a | 1.0 | insufficient_support | insufficient_support | policy_only_rule |
| context.composite.MEDICAL_RECORD_NO | 143 | n/a | 1.0 | insufficient_support | insufficient_support | policy_only_rule |
| context.composite.PERSON_NAME | 588 | 5.96206 | 1.329635 | strong_positive | strong_boost | policy_only_rule |
| context.composite.PHONE_LANDLINE | 0 | -0.566604 | n/a | weak_negative | small_penalty | policy_only_rule |
| context.composite.PHONE_MOBILE | 172 | 5.27616 | 1.566563 | strong_positive | strong_boost | policy_only_rule |
| context.composite.SCHOOL | 284 | 1.396317 | 1.508533 | positive | normal_boost | policy_only_rule |
| context.penalty.abstract_value_context_for_person | 153 | -6.293651 | 0.0 | strong_negative | strong_penalty | tune_magnitude |
| context.penalty.code_or_log_context | 100 | -5.895064 | 0.0 | strong_negative | strong_penalty | tune_magnitude |
| context.penalty.example_context | 1232 | -7.418581 | 0.002102 | strong_negative | strong_penalty | tune_magnitude |
| context.penalty.example_keyword_for_person | 0 | -0.566604 | n/a | weak_negative | small_penalty | insufficient_support |
| context.penalty.organization_not_person | 101 | -5.879923 | 0.0 | strong_negative | strong_penalty | tune_magnitude |
| context.penalty.private_ip | 0 | n/a | n/a | insufficient_support | insufficient_support | insufficient_support |
| context.penalty.public_phone_context | 0 | -1.148298 | n/a | negative | normal_penalty | insufficient_support |
| context.penalty.weather_context_for_person | 126 | -6.100387 | 0.0 | strong_negative | strong_penalty | tune_magnitude |
