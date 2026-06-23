# Context Calibration Dataset Card v1

- dataset_id: `context_calibration_v1`
- phase: `Execution Phase 3. Calibration Dataset`
- synthetic_fixture_only: `true`
- public_context_corpus_role: `template coverage only, not score tuning`
- template_level_split: `pass`
- offset_validation_status: `pass`

## Split Counts

| Split | Records |
|---|---:|
| train | 15 |
| dev | 15 |
| test | 15 |

## Bucket Counts

| Bucket | Records |
|---|---:|
| hard_negative_abstract_value | 3 |
| hard_negative_business_name | 3 |
| hard_negative_code_log | 3 |
| hard_negative_order_identifier | 3 |
| hard_negative_placeholder | 3 |
| hard_negative_public_number | 3 |
| positive_address | 3 |
| positive_bank_account | 3 |
| positive_business_identifier | 3 |
| positive_email | 3 |
| positive_medical | 3 |
| positive_name_suffix | 3 |
| positive_organization_affiliation | 3 |
| positive_person_phone | 3 |
| positive_personal_identifier | 3 |

## Label Counts

| Entity | Labels |
|---|---:|
| ADDRESS_FULL | 3 |
| BANK_ACCOUNT | 3 |
| BUSINESS_REG_NO | 3 |
| EMAIL | 3 |
| HOSPITAL | 3 |
| MEDICAL_RECORD_NO | 3 |
| ORGANIZATION | 3 |
| PERSON_NAME | 9 |
| PHONE_MOBILE | 3 |
| RRN | 3 |

## Safety

- raw_value_logged_count: `0`
- production_pii_used: `false`
- offset_validation_error_count: `0`
- suffix_validation_error_count: `0`

Train/dev/test are split by template_id; near-duplicate template ids are not shared across splits.
Positive and hard-negative buckets cover names, public numbers, placeholders, code/log contexts, business names, abstract-value contexts, structured identifiers, and address/account/contact contexts.
