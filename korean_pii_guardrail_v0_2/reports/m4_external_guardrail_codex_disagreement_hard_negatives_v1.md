# M4 External Guardrail/Codex Disagreement Hard Negatives v1

- phase: `External hard-negative mining from guardrail/Codex disagreement`
- hard_negative_mining_gate_status: `pass`
- approved_label_count: `1999`
- hard_negative_row_count: `832`
- public_pii_excluded_from_hard_negative: `true`
- probability_loglr_computed: `false`
- score_tuning_allowed_by_this_phase: `false`
- runtime_scoring_behavior_changed: `false`
- score_delta_changed: `false`

## Definition

A hard-negative row here means: the existing guardrail produced a candidate, but the user accepted Codex's PII-only judgment that the candidate is not PII.

## Core Entity Group Support

| entity_group | hard_negative_count | minimum | status | gap |
|---|---:|---:|---|---:|
| PERSON_NAME | 10 | 5 | pass | 0 |
| ADDRESS | 391 | 5 | pass | 0 |
| PHONE | 0 | 5 | needs_more_hard_negatives | 5 |
| EMAIL | 0 | 5 | needs_more_hard_negatives | 5 |
| REGISTRATION_IDENTIFIER | 0 | 5 | needs_more_hard_negatives | 5 |
| BANK_ACCOUNT | 0 | 5 | needs_more_hard_negatives | 5 |

## Entity Counts

| entity | count |
|---|---:|
| ADDRESS_UNIT | 391 |
| FAMILY_RELATION | 61 |
| HOSPITAL | 92 |
| ORGANIZATION | 272 |
| PERSON_NAME | 10 |
| SCHOOL | 6 |

## Recommended Collection Targets

- `PHONE`: sample/test/documentation phone-like strings only; public organization phone numbers remain PII and must not be used as not-PII
- `EMAIL`: sample/test/placeholder email-like strings only; public business emails remain PII and must not be used as not-PII
- `REGISTRATION_IDENTIFIER`: sample/test/invalid registration-like strings or unrelated codes that pass candidate extraction but are not real registration identifiers
- `BANK_ACCOUNT`: sample/test/account-like numeric strings and unrelated formatted numbers that are not real bank accounts
