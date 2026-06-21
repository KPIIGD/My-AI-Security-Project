# M4 External Codex PII Silver Summary

- label_source: codex_pii_silver
- label_status: silver_not_gold
- review_question: pii_or_not_pii_only
- row_count: 500
- pii: 317
- not_pii: 183
- unsure: 0
- raw_values_in_repo_report: false
- raw_context_in_repo_report: false
- probability_loglr_computed: false
- score_tuning_allowed_by_this_phase: false
- m4_score_changed: false

## Entity Verdict Counts

| entity | pii | not_pii | unsure |
|---|---:|---:|---:|
| ADDRESS_FULL | 18 | 0 | 0 |
| ADDRESS_UNIT | 0 | 80 | 0 |
| BUSINESS_REG_NO | 80 | 0 | 0 |
| CORPORATE_REG_NO | 43 | 0 | 0 |
| EMAIL | 63 | 0 | 0 |
| FAMILY_RELATION | 0 | 7 | 0 |
| FRN | 3 | 0 | 0 |
| HOSPITAL | 0 | 60 | 0 |
| ORGANIZATION | 0 | 26 | 0 |
| PERSON_NAME | 4 | 10 | 0 |
| PHONE_LANDLINE | 80 | 0 | 0 |
| PHONE_MOBILE | 20 | 0 | 0 |
| RRN | 6 | 0 | 0 |

## Stop Conditions

- codex_silver_labels_not_gold_stop_before_probability_loglr
- reviewer_approved_labels_missing_stop_before_probability_loglr
- probability_loglr_not_computed
- m4_score_tuning_not_changed

This artifact is a Codex-silver PII-only classification. It is useful for review triage and exploratory planning, but it is not reviewer-approved gold evidence and must not be used for final probability/logLR or M4 score tuning.
