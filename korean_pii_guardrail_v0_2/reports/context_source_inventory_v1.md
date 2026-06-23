# Context Source Inventory v1

- stage: `1.1 source inventory`
- evidence_role: `source_domain_inventory_only`
- runtime_scoring_behavior_changed: `false`
- score_delta_changed: `false`
- context_rule_changed: `false`
- public_corpus_used_for_score_tuning: `false`
- raw_value_logged: `false`
- raw_url_logged: `false`

## Source Domains

| Domain | Material Class | Description |
|---|---|---|
| customer_support | realistic_input_like | support, contact, inquiry, and issue-resolution guidance |
| ecommerce | realistic_input_like | ordering, delivery, refund, account, and checkout flows |
| healthcare | realistic_input_like | appointment, reception, patient, and medical-record guidance |
| finance | realistic_input_like | deposit, transfer, refund, account, and identity guidance |
| education | realistic_input_like | school, application, student, and registration guidance |
| public_services | realistic_input_like | public institution application and civil-service guidance |
| enterprise_internal | realistic_input_like | employee, HR, internal request, and organization workflows |
| developer_docs | general_web_or_explanatory | technical examples, logs, schemas, and API documentation |
| general_web | general_web_or_explanatory | general explanatory or policy-like text |
| sample_forms | example_or_sample | safe sample forms and synthetic templates |

## Source Types

| Source Type | Domain | Collector Supported |
|---|---|---:|
| customer_support_help | customer_support | false |
| ecommerce_help | ecommerce | true |
| healthcare_guide | healthcare | true |
| finance_guide | finance | false |
| education_application | education | true |
| institution_application | public_services | true |
| enterprise_internal | enterprise_internal | true |
| developer_docs | developer_docs | true |
| privacy_policy | general_web | true |
| synthetic_safe_template | sample_forms | true |

## Core Entity Domain Plan

| Entity Group | Planned Domains | Current Observed Domains | Current Status |
|---|---:|---:|---|
| ADDRESS | 6 | 2 | insufficient_current_data |
| BANK_ACCOUNT | 6 | 2 | insufficient_current_data |
| EMAIL | 6 | 2 | insufficient_current_data |
| PERSON_NAME | 6 | 2 | insufficient_current_data |
| PHONE | 6 | 2 | insufficient_current_data |
| REGISTRATION_IDENTIFIER | 6 | 2 | insufficient_current_data |

## Current Safe Context Window Summary

- row_count: `26`
- current_data_quality_status: `insufficient_for_score_tuning`

Current rows remain coverage evidence only. They are not sufficient for score tuning.

## Data Quality Gate Draft

| Measurement | Pass Criteria |
|---|---|
| `raw_pii_leak_count` | `0` |
| `invalid_offset_count` | `0` |
| `min_domain_count_by_core_entity` | `5` |
| `max_single_domain_ratio` | `0.35` |
| `min_realistic_input_like_ratio` | `0.7` |
| `max_general_web_or_explanatory_ratio` | `0.3` |
| `max_example_or_sample_document_ratio` | `0.15` |
| `max_duplicate_anchor_window_ratio` | `0.05` |
| `max_unknown_label_ratio_when_labels_present` | `0.15` |
