# M4 External Safe Context Word Score Evidence v1

- phase: `Safe context-word evidence for experimental M4 scoring`
- release_eligible: `false`
- config_change_proposed: `false`
- runtime_scoring_behavior_changed: `false`
- m4_score_changed: `false`
- raw_candidate_values_persisted_in_reports: `false`
- raw_text_persisted_in_reports: `false`

## Entity Group Counts

| entity_group | pii | not_pii |
|---|---:|---:|
| PERSON_NAME | 4 | 10 |
| ADDRESS | 317 | 369 |
| PHONE | 286 | 0 |
| EMAIL | 63 | 0 |
| REGISTRATION_IDENTIFIER | 471 | 0 |
| BANK_ACCOUNT | 0 | 0 |

## Top Safe Context Terms

### PERSON_NAME

| term | scope | kind | delta | direction | support | pii | not_pii | confidence |
|---|---|---|---:|---|---:|---:|---:|---|
| content | exact_source_field | source_field_name | 0.0 | review_only_context_conflict | 11 | 1 | 10 | review_only_context_conflict |
| free_text | exact_source_field | source_field_role | 0.0 | review_only_context_conflict | 11 | 1 | 10 | review_only_context_conflict |
| 대표자명 | exact_source_field | source_field_name | 0.0 | insufficient_term_support | 3 | 3 | 0 | low_insufficient_support |
| 대표자명 | exact_source_field | source_field_role | 0.0 | insufficient_term_support | 3 | 3 | 0 | low_insufficient_support |
| 기타필드 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 3 | 3 | 0 | review_only_context_conflict |
| 대표자명 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 3 | 3 | 0 | review_only_context_conflict |
| 법인등록번호 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 3 | 3 | 0 | review_only_context_conflict |
| 사업자등록번호 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 3 | 3 | 0 | review_only_context_conflict |
| 상호/회사명 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 3 | 3 | 0 | review_only_context_conflict |
| 전화번호/연락처 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 3 | 3 | 0 | review_only_context_conflict |
| 주소/소재지 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 3 | 3 | 0 | review_only_context_conflict |
| 홈페이지/URL | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 3 | 3 | 0 | review_only_context_conflict |
| fncoRprNm | exact_source_field | source_field_name | 0.0 | insufficient_term_support | 2 | 2 | 0 | low_insufficient_support |
| enpRprFnm | exact_source_field | source_field_name | 0.0 | insufficient_term_support | 1 | 1 | 0 | low_insufficient_support |

### ADDRESS

| term | scope | kind | delta | direction | support | pii | not_pii | confidence |
|---|---|---|---:|---|---:|---:|---:|---|
| 주소/소재지 | exact_source_field | source_field_role | 0.075 | pii_boost_candidate | 401 | 277 | 124 | medium_same_corpus_not_release |
| 주소 | exact_source_field | source_field_name | 0.075 | pii_boost_candidate | 346 | 237 | 109 | medium_same_corpus_not_release |
| 소재지 | exact_source_field | source_field_name | 0.075 | pii_boost_candidate | 55 | 40 | 15 | medium_same_corpus_not_release |
| 사업장소재지 | exact_source_field | source_field_name | 0.075 | pii_boost_candidate | 50 | 37 | 13 | medium_same_corpus_not_release |
| 기타필드 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 674 | 317 | 357 | review_only_context_conflict |
| 주소/소재지 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 674 | 317 | 357 | review_only_context_conflict |
| 상호/회사명 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 575 | 219 | 356 | review_only_context_conflict |
| 전화번호/연락처 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 497 | 316 | 181 | review_only_context_conflict |
| 대표자명 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 398 | 218 | 180 | review_only_context_conflict |
| 법인등록번호 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 398 | 218 | 180 | review_only_context_conflict |
| 사업자등록번호 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 398 | 218 | 180 | review_only_context_conflict |
| 기관/조직명 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 370 | 190 | 180 | review_only_context_conflict |
| 지역/행정구역 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 338 | 13 | 325 | review_only_context_conflict |
| 홈페이지/URL | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 127 | 126 | 1 | review_only_context_conflict |
| 이메일/전자우편 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 110 | 80 | 30 | review_only_context_conflict |

### PHONE

| term | scope | kind | delta | direction | support | pii | not_pii | confidence |
|---|---|---|---:|---|---:|---:|---:|---|
| 전화번호 | exact_source_field | source_field_name | 0.05 | pii_observed_no_negative_support | 174 | 174 | 0 | low_missing_counterexamples |
| 전화번호/연락처 | exact_source_field | source_field_role | 0.05 | pii_observed_no_negative_support | 174 | 174 | 0 | low_missing_counterexamples |
| 번호 | exact_source_field | source_field_name | 0.05 | pii_observed_no_negative_support | 80 | 80 | 0 | low_missing_counterexamples |
| 의료기관전화번호 | exact_source_field | source_field_name | 0.05 | pii_observed_no_negative_support | 59 | 59 | 0 | low_missing_counterexamples |
| enpTlno | exact_source_field | source_field_name | 0.03 | pii_observed_no_negative_support | 32 | 32 | 0 | low_missing_counterexamples |
| fncoTlno | exact_source_field | source_field_name | 0.03 | pii_observed_no_negative_support | 32 | 32 | 0 | low_missing_counterexamples |
| chrgDeptTelno | exact_source_field | source_field_name | 0.03 | pii_observed_no_negative_support | 28 | 28 | 0 | low_missing_counterexamples |
| 기타필드 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 286 | 286 | 0 | review_only_context_conflict |
| 사업자등록번호 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 227 | 227 | 0 | review_only_context_conflict |
| 전화번호/연락처 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 222 | 222 | 0 | review_only_context_conflict |
| 주소/소재지 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 222 | 222 | 0 | review_only_context_conflict |
| 대표자명 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 163 | 163 | 0 | review_only_context_conflict |
| 법인등록번호 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 163 | 163 | 0 | review_only_context_conflict |
| 상호/회사명 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 163 | 163 | 0 | review_only_context_conflict |
| 기관/조직명 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 111 | 111 | 0 | review_only_context_conflict |

### EMAIL

| term | scope | kind | delta | direction | support | pii | not_pii | confidence |
|---|---|---|---:|---|---:|---:|---:|---|
| 이메일/전자우편 | exact_source_field | source_field_role | 0.03 | pii_observed_no_negative_support | 49 | 49 | 0 | low_missing_counterexamples |
| 전자우편 | exact_source_field | source_field_name | 0.03 | pii_observed_no_negative_support | 49 | 49 | 0 | low_missing_counterexamples |
| 전자우편(E-mail) | exact_source_field | source_field_name | 0.03 | pii_observed_no_negative_support | 49 | 49 | 0 | low_missing_counterexamples |
| 기관/조직명 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 63 | 63 | 0 | review_only_context_conflict |
| 기타필드 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 63 | 63 | 0 | review_only_context_conflict |
| 대표자명 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 63 | 63 | 0 | review_only_context_conflict |
| 법인등록번호 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 63 | 63 | 0 | review_only_context_conflict |
| 사업자등록번호 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 63 | 63 | 0 | review_only_context_conflict |
| 상호/회사명 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 63 | 63 | 0 | review_only_context_conflict |
| 전화번호/연락처 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 63 | 63 | 0 | review_only_context_conflict |
| 주소/소재지 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 63 | 63 | 0 | review_only_context_conflict |
| 이메일 | exact_source_field | source_field_name | 0.0 | review_only_context_conflict | 58 | 58 | 0 | review_only_context_conflict |
| 이메일/전자우편 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 54 | 54 | 0 | review_only_context_conflict |
| rprsvEmladr | exact_source_field | source_field_name | 0.0 | review_only_context_conflict | 9 | 9 | 0 | review_only_context_conflict |
| 주소 | exact_source_field | source_field_name | 0.0 | review_only_context_conflict | 9 | 9 | 0 | review_only_context_conflict |

### REGISTRATION_IDENTIFIER

| term | scope | kind | delta | direction | support | pii | not_pii | confidence |
|---|---|---|---:|---|---:|---:|---:|---|
| 사업자등록번호 | exact_source_field | source_field_name | 0.05 | pii_observed_no_negative_support | 343 | 343 | 0 | low_missing_counterexamples |
| 사업자등록번호 | exact_source_field | source_field_role | 0.05 | pii_observed_no_negative_support | 343 | 343 | 0 | low_missing_counterexamples |
| b_no | exact_source_field | source_field_name | 0.05 | pii_observed_no_negative_support | 185 | 185 | 0 | low_missing_counterexamples |
| bzno | exact_source_field | source_field_name | 0.05 | pii_observed_no_negative_support | 76 | 76 | 0 | low_missing_counterexamples |
| crno | exact_source_field | source_field_name | 0.05 | pii_observed_no_negative_support | 52 | 52 | 0 | low_missing_counterexamples |
| 법인등록번호 | exact_source_field | source_field_name | 0.05 | pii_observed_no_negative_support | 52 | 52 | 0 | low_missing_counterexamples |
| 법인등록번호 | exact_source_field | source_field_role | 0.05 | pii_observed_no_negative_support | 52 | 52 | 0 | low_missing_counterexamples |
| 번호 | exact_source_field | source_field_name | 0.05 | pii_observed_no_negative_support | 50 | 50 | 0 | low_missing_counterexamples |
| brno | exact_source_field | source_field_name | 0.03 | pii_observed_no_negative_support | 32 | 32 | 0 | low_missing_counterexamples |
| 기타필드 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 471 | 471 | 0 | review_only_context_conflict |
| 사업자등록번호 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 426 | 426 | 0 | review_only_context_conflict |
| 상호/회사명 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 286 | 286 | 0 | review_only_context_conflict |
| 주소/소재지 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 286 | 286 | 0 | review_only_context_conflict |
| 대표자명 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 241 | 241 | 0 | review_only_context_conflict |
| 법인등록번호 | record_schema_context | field_context_role | 0.0 | review_only_context_conflict | 241 | 241 | 0 | review_only_context_conflict |

### BANK_ACCOUNT

| term | scope | kind | delta | direction | support | pii | not_pii | confidence |
|---|---|---|---:|---|---:|---:|---:|---|

## Decision

These are safe context-word evidence rows for experimental scoring only.
They do not update runtime scoring, context rules, scoring config, or release gates.
