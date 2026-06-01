# M4 Phase 6 Label Review Packet

This packet separates Codex draft labels from reviewer-approved gold labels. It stores only raw-free anchor metadata and reviewer workflow fields.

- phase_exit_status: fail
- draft_label_count: 1307
- reviewer_packet_sample_count: 1000
- reviewer_sample_required: 1000
- reviewer_approved_label_count: 0
- final_probability_input_label_source: none_missing_reviewer_approved_labels
- unknown_ratio: 0.0
- score_tuning_allowed_by_this_phase: false

## Label Source Counts

| source | count |
| --- | ---: |
| codex_draft | 1123 |
| safe_synthetic_generator | 184 |

## Draft Label Counts

| label | count |
| --- | ---: |
| true_pii | 184 |
| non_pii | 1123 |
| unknown | 0 |

## Stratification Summary

| entity_group | source_domain | draft_label | draft_rows | packet_rows |
| --- | --- | --- | ---: | ---: |
| ADDRESS | customer_support | non_pii | 1 | 1 |
| ADDRESS | customer_support | true_pii | 1 | 1 |
| ADDRESS | ecommerce | non_pii | 1 | 1 |
| ADDRESS | ecommerce | true_pii | 1 | 1 |
| ADDRESS | education | non_pii | 1 | 1 |
| ADDRESS | education | true_pii | 1 | 1 |
| ADDRESS | enterprise_internal | non_pii | 1 | 1 |
| ADDRESS | enterprise_internal | true_pii | 1 | 1 |
| ADDRESS | finance | non_pii | 1 | 1 |
| ADDRESS | finance | true_pii | 1 | 1 |
| ADDRESS | healthcare | non_pii | 1 | 1 |
| ADDRESS | healthcare | true_pii | 1 | 1 |
| ADDRESS | public_services | non_pii | 1 | 1 |
| ADDRESS | public_services | true_pii | 1 | 1 |
| BANK_ACCOUNT | customer_support | non_pii | 28 | 28 |
| BANK_ACCOUNT | customer_support | true_pii | 15 | 15 |
| BANK_ACCOUNT | developer_docs | non_pii | 3 | 3 |
| BANK_ACCOUNT | ecommerce | non_pii | 145 | 56 |
| BANK_ACCOUNT | education | non_pii | 57 | 56 |
| BANK_ACCOUNT | enterprise_internal | non_pii | 1 | 1 |
| BANK_ACCOUNT | enterprise_internal | true_pii | 41 | 41 |
| BANK_ACCOUNT | finance | non_pii | 18 | 18 |
| BANK_ACCOUNT | finance | true_pii | 25 | 25 |
| BANK_ACCOUNT | general_web | non_pii | 17 | 17 |
| BANK_ACCOUNT | healthcare | non_pii | 33 | 33 |
| BANK_ACCOUNT | healthcare | true_pii | 10 | 10 |
| BANK_ACCOUNT | public_services | non_pii | 34 | 34 |
| BANK_ACCOUNT | public_services | true_pii | 8 | 8 |
| EMAIL | customer_support | non_pii | 14 | 14 |
| EMAIL | customer_support | true_pii | 13 | 13 |
| EMAIL | developer_docs | non_pii | 5 | 5 |
| EMAIL | ecommerce | non_pii | 92 | 56 |
| EMAIL | education | non_pii | 18 | 18 |
| EMAIL | education | true_pii | 8 | 8 |
| EMAIL | enterprise_internal | true_pii | 26 | 26 |
| EMAIL | finance | non_pii | 3 | 3 |
| EMAIL | finance | true_pii | 24 | 24 |
| EMAIL | general_web | non_pii | 27 | 27 |
| EMAIL | healthcare | non_pii | 35 | 35 |
| EMAIL | public_services | non_pii | 30 | 30 |
| PERSON_NAME | customer_support | non_pii | 1 | 1 |
| PERSON_NAME | customer_support | true_pii | 1 | 1 |
| PERSON_NAME | ecommerce | non_pii | 1 | 1 |
| PERSON_NAME | ecommerce | true_pii | 1 | 1 |
| PERSON_NAME | education | non_pii | 1 | 1 |
| PERSON_NAME | education | true_pii | 1 | 1 |
| PERSON_NAME | enterprise_internal | non_pii | 1 | 1 |
| PERSON_NAME | enterprise_internal | true_pii | 1 | 1 |
| PERSON_NAME | finance | non_pii | 1 | 1 |
| PERSON_NAME | finance | true_pii | 1 | 1 |
| PERSON_NAME | healthcare | non_pii | 1 | 1 |
| PERSON_NAME | healthcare | true_pii | 1 | 1 |
| PERSON_NAME | public_services | non_pii | 1 | 1 |
| PERSON_NAME | public_services | true_pii | 1 | 1 |
| PHONE | customer_support | non_pii | 9 | 9 |
| PHONE | developer_docs | non_pii | 3 | 3 |
| PHONE | ecommerce | non_pii | 32 | 32 |
| PHONE | education | non_pii | 94 | 56 |
| PHONE | enterprise_internal | non_pii | 1 | 1 |
| PHONE | finance | non_pii | 25 | 25 |
| PHONE | general_web | non_pii | 74 | 56 |
| PHONE | healthcare | non_pii | 127 | 56 |
| PHONE | public_services | non_pii | 110 | 56 |
| REGISTRATION_IDENTIFIER | customer_support | non_pii | 8 | 8 |
| REGISTRATION_IDENTIFIER | developer_docs | non_pii | 1 | 1 |
| REGISTRATION_IDENTIFIER | ecommerce | non_pii | 20 | 20 |
| REGISTRATION_IDENTIFIER | education | non_pii | 11 | 11 |
| REGISTRATION_IDENTIFIER | enterprise_internal | non_pii | 6 | 6 |
| REGISTRATION_IDENTIFIER | finance | non_pii | 4 | 4 |
| REGISTRATION_IDENTIFIER | general_web | non_pii | 10 | 10 |
| REGISTRATION_IDENTIFIER | healthcare | non_pii | 14 | 14 |

## Gate Verdict

- label_quality_gate_status: fail
- failure_verdicts: label_quality_failed, needs_adjudication, needs_more_labels, needs_reviewer_labels

Codex draft labels remain draft-only. Probability/logLR estimation and score tuning remain blocked until a valid reviewer-approved label artifact exists.
