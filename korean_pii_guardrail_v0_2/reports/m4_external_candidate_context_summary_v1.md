# M4 External Candidate Context Summary

- phase: Phase C/D/E. Existing Detector Candidate And Context Extraction
- workflow_gate_status: blocked_before_score_tuning
- failure_verdicts: reviewer_approved_labels_missing_stop_before_probability_loglr
- candidate_row_count: 1999
- invalid_offset_count: 0
- source_domain_count: 7
- max_single_source_domain_ratio: 0.250125
- score_tuning_allowed_by_this_phase: false
- probability_loglr_computed: false
- m4_score_changed: false
- raw_text_persisted_in_reports: false
- raw_candidate_values_persisted_in_reports: false
- raw_context_terms_persisted_in_reports: false

## Candidate Counts By Entity

| entity | count |
|---|---:|
| ADDRESS_FULL | 18 |
| ADDRESS_UNIT | 668 |
| BUSINESS_REG_NO | 419 |
| CORPORATE_REG_NO | 43 |
| CREDIT_CARD | 48 |
| EMAIL | 63 |
| FAMILY_RELATION | 61 |
| FRN | 3 |
| HOSPITAL | 92 |
| ORGANIZATION | 272 |
| PERSON_NAME | 14 |
| PHONE_LANDLINE | 266 |
| PHONE_MOBILE | 20 |
| RRN | 6 |
| SCHOOL | 6 |

## Source Domain Counts

| source_domain | count |
|---|---:|
| general_web | 250 |
| public_business_status | 249 |
| public_commercial_org | 250 |
| public_healthcare_org | 250 |
| public_record_commerce | 500 |
| public_record_corporate | 250 |
| public_record_finance | 250 |

## Draft Label Counts

| field | counts |
|---|---|
| privacy_context_class | organization_contact:1023, unknown:511, public_record_identifier:462, public_record_representative:3 |
| score_role | detect_org_contact_adjust_action:1023, review_needed:511, detect_public_pii_adjust_action:465 |
| label_source | source_field_rule:1488, detector_candidate:511 |
| label_status | review_needed:1488, candidate:511 |

## Context Extraction Aggregate

| feature | count |
|---|---:|
| field_context_names | 45989 |
| field_context_roles | 10998 |
| left_bigrams | 1262 |
| left_trigrams | 923 |
| left_unigrams | 1634 |
| right_bigrams | 2066 |
| right_trigrams | 1372 |
| right_unigrams | 2854 |

## Stop Conditions

- reviewer_approved_labels_missing_stop_before_probability_loglr
- detector_outputs_are_candidate_only
- probability_loglr_not_computed
- m4_score_tuning_not_changed

Detailed candidate rows are written outside the repository under the local raw staging root. Those rows preserve offsets, source file hashes, field context, and local context n-grams for later human review.

This phase does not compute probabilities, logLR, score deltas, or M4 tuning changes.
