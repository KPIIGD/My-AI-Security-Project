# M4 External Context Probability v1

- phase: `Phase G. Probability And logLR Evidence`
- probability_loglr_computed: `true`
- probability_support_gate_status: `fail`
- approved_input_row_count: `1999`
- final_probability_label_source: `reviewer_approved`
- raw_context_feature_values_in_repo_report: `false`
- score_tuning_allowed_by_this_phase: `false`

## Entity Group Counts

| entity_group | pii | not_pii |
|---|---:|---:|
| ADDRESS | 295 | 391 |
| EMAIL | 63 | 0 |
| FAMILY_RELATION | 0 | 61 |
| ORGANIZATION | 0 | 370 |
| PAYMENT_IDENTIFIER | 48 | 0 |
| PERSON_NAME | 4 | 10 |
| PHONE | 286 | 0 |
| REGISTRATION_IDENTIFIER | 471 | 0 |

## Support Gate

- failure_verdicts: insufficient_non_pii_support, insufficient_total_support

## Top Hashed Feature Rows

| entity_group | feature_kind | feature_display | support | pii | not_pii | logLR | direction |
|---|---|---|---:|---:|---:|---:|---|
| REGISTRATION_IDENTIFIER | field_context_role | other | 464 | 464 | 0 | 0.676089 | neutral_or_insufficient_support |
| REGISTRATION_IDENTIFIER | offset_scope | field_value | 464 | 464 | 0 | 0.676089 | neutral_or_insufficient_support |
| REGISTRATION_IDENTIFIER | field_context_role | business_registration | 419 | 419 | 0 | 0.574307 | neutral_or_insufficient_support |
| REGISTRATION_IDENTIFIER | candidate_shape | business_registration_shape | 412 | 412 | 0 | 0.557499 | neutral_or_insufficient_support |
| ADDRESS | field_context_role | other | 387 | 222 | 165 | 0.575261 | neutral_or_insufficient_support |
| ADDRESS | field_context_role | address | 387 | 222 | 165 | 0.575261 | neutral_or_insufficient_support |
| ADDRESS | offset_scope | field_value | 387 | 222 | 165 | 0.575261 | neutral_or_insufficient_support |
| REGISTRATION_IDENTIFIER | source_field_role | business_registration | 343 | 343 | 0 | 0.374693 | neutral_or_insufficient_support |
| ADDRESS | source_field_role | address | 342 | 280 | 62 | 1.775297 | pii_boost_candidate |
| ADDRESS | field_context_role | phone | 342 | 221 | 121 | 0.878734 | pii_boost_candidate |
| ADDRESS | field_context_role | company_name | 288 | 124 | 164 | 0.002446 | neutral_or_insufficient_support |
| REGISTRATION_IDENTIFIER | field_context_role | address | 279 | 279 | 0 | 0.168841 | neutral_or_insufficient_support |
| REGISTRATION_IDENTIFIER | field_context_role | company_name | 279 | 279 | 0 | 0.168841 | neutral_or_insufficient_support |
| PHONE | field_context_role | other | 253 | 253 | 0 | 0.567521 | neutral_or_insufficient_support |
| PHONE | offset_scope | field_value | 253 | 253 | 0 | 0.567521 | neutral_or_insufficient_support |
| ADDRESS | field_context_role | business_registration | 243 | 123 | 120 | 0.304568 | neutral_or_insufficient_support |
| ADDRESS | field_context_role | corporate_registration | 243 | 123 | 120 | 0.304568 | neutral_or_insufficient_support |
| ADDRESS | field_context_role | representative_name | 243 | 123 | 120 | 0.304568 | neutral_or_insufficient_support |
| REGISTRATION_IDENTIFIER | field_context_role | corporate_registration | 234 | 234 | 0 | -0.006363 | neutral_or_insufficient_support |
| REGISTRATION_IDENTIFIER | field_context_role | phone | 234 | 234 | 0 | -0.006363 | neutral_or_insufficient_support |
| REGISTRATION_IDENTIFIER | field_context_role | representative_name | 234 | 234 | 0 | -0.006363 | neutral_or_insufficient_support |
| PHONE | candidate_shape | landline_phone_shape | 233 | 233 | 0 | 0.485508 | neutral_or_insufficient_support |
| ADDRESS | field_context_role | organization | 230 | 110 | 120 | 0.193817 | neutral_or_insufficient_support |
| PHONE | field_context_role | business_registration | 194 | 194 | 0 | 0.303186 | neutral_or_insufficient_support |
| PHONE | field_context_role | phone | 189 | 189 | 0 | 0.277211 | neutral_or_insufficient_support |
