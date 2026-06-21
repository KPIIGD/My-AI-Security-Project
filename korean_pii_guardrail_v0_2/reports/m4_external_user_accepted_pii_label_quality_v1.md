# M4 External User-Accepted PII Label Quality v1

- phase: `Phase F. Human Review Gold Label Packet`
- label_quality_gate_status: `pass`
- candidate_row_count: `1999`
- reviewer_approved_label_count: `1999`
- required_reviewer_sample_count: `1000`
- agreement_score_against_codex_silver_rows: `1.0`
- final_probability_label_source: `reviewer_approved`
- review_question: `pii_or_not_pii_only`
- raw_candidate_values_persisted_in_reports: `false`
- raw_text_persisted_in_reports: `false`
- recoverable_context_terms_persisted_in_reports: `false`
- runtime_scoring_behavior_changed: `false`
- score_delta_changed: `false`

## Entity Group Verdict Counts

| entity_group | pii | not_pii | unsure |
|---|---:|---:|---:|
| ADDRESS | 295 | 391 | 0 |
| EMAIL | 63 | 0 | 0 |
| FAMILY_RELATION | 0 | 61 | 0 |
| ORGANIZATION | 0 | 370 | 0 |
| PAYMENT_IDENTIFIER | 48 | 0 | 0 |
| PERSON_NAME | 4 | 10 | 0 |
| PHONE | 286 | 0 | 0 |
| REGISTRATION_IDENTIFIER | 471 | 0 | 0 |

## Gate

- failure_verdicts: label_quality_gate_pass

Codex-assisted classifications were not treated as gold by themselves. This artifact records the user's explicit bulk approval as the reviewer-approved source for the PII-only question.
