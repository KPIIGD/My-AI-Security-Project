# Context Rule Inventory v1

- report_type: `ContextRuleInventory`
- phase: `Execution Phase 1. Baseline Evidence MVP`
- runtime_scoring_behavior_changed: `false`
- rule_count: `30`
- raw_value_logged: `false`

| Rule ID | Family | Delta | Risk Upgrade | Effect Scope | Target Entities | Policy Interaction |
|---|---|---:|---|---|---|---|
| context.boost.address_cooccur_for_person | boost | 0.15 | n/a | candidate_score | PERSON_NAME | strong_context_can_enable_policy_context_mask |
| context.boost.bank_cooccur | boost | 0.25 | n/a | candidate_score | BANK_ACCOUNT | strong_context_can_enable_policy_context_mask |
| context.boost.field_label_account | boost | 0.3 | n/a | candidate_score | BANK_ACCOUNT | strong_context_can_enable_policy_context_mask |
| context.boost.field_label_address | boost | 0.2 | n/a | candidate_score | ADDRESS_FULL, ADDRESS_UNIT | strong_context_can_enable_policy_context_mask |
| context.boost.field_label_name | boost | 0.25 | n/a | candidate_score | PERSON_NAME | strong_context_can_enable_policy_context_mask |
| context.boost.field_label_phone | boost | 0.15 | n/a | candidate_score | PHONE_LANDLINE, PHONE_MOBILE | strong_context_can_enable_policy_context_mask |
| context.boost.full_address_detail | boost | 0.2 | n/a | candidate_score | ADDRESS_FULL | strong_context_can_enable_policy_context_mask |
| context.boost.medical_label | boost | 0.2 | n/a | candidate_score | HEALTH_INFO, HOSPITAL, MEDICAL_RECORD_NO | strong_context_can_enable_policy_context_mask |
| context.boost.organization_affiliation_context | boost | 0.25 | n/a | candidate_score | ORGANIZATION | strong_context_can_enable_policy_context_mask |
| context.boost.phone_cooccur_for_person | boost | 0.2 | n/a | candidate_score | PERSON_NAME | strong_context_can_enable_policy_context_mask |
| context.boost.title_after_name | boost | 0.15 | n/a | candidate_score | PERSON_NAME | strong_context_can_enable_policy_context_mask |
| context.composite.ADDRESS_FULL | composite | n/a | P1 | composite_status_and_policy_action | PERSON_NAME | policy.composite.mask via is_composite |
| context.composite.ADDRESS_UNIT | composite | n/a | P1 | composite_status_and_policy_action | DOB, SCHOOL | policy.composite.mask via is_composite |
| context.composite.BANK_ACCOUNT | composite | n/a | P1 | composite_status_and_policy_action | PERSON_NAME | policy.composite.mask via is_composite |
| context.composite.DOB | composite | n/a | P1 | composite_status_and_policy_action | ADDRESS_UNIT, SCHOOL | policy.composite.mask via is_composite |
| context.composite.EMAIL | composite | n/a | P1 | composite_status_and_policy_action | PERSON_NAME | policy.composite.mask via is_composite |
| context.composite.HOSPITAL | composite | n/a | P1 | composite_status_and_policy_action | MEDICAL_RECORD_NO | policy.composite.mask via is_composite |
| context.composite.MEDICAL_RECORD_NO | composite | n/a | P1 | composite_status_and_policy_action | HOSPITAL | policy.composite.mask via is_composite |
| context.composite.PERSON_NAME | composite | n/a | P1 | composite_status_and_policy_action | ADDRESS_FULL, BANK_ACCOUNT, EMAIL, PHONE_LANDLINE, PHONE_MOBILE | policy.composite.mask via is_composite |
| context.composite.PHONE_LANDLINE | composite | n/a | P1 | composite_status_and_policy_action | PERSON_NAME | policy.composite.mask via is_composite |
| context.composite.PHONE_MOBILE | composite | n/a | P1 | composite_status_and_policy_action | PERSON_NAME | policy.composite.mask via is_composite |
| context.composite.SCHOOL | composite | n/a | P1 | composite_status_and_policy_action | ADDRESS_UNIT, DOB | policy.composite.mask via is_composite |
| context.penalty.abstract_value_context_for_person | penalty | -0.2 | n/a | candidate_score | PERSON_NAME | score_only_before_policy_thresholds |
| context.penalty.code_or_log_context | penalty | -0.2 | n/a | candidate_score | ADDRESS_FULL, ADDRESS_UNIT, PERSON_NAME | negative_context_can_enable_policy_pass |
| context.penalty.example_context | penalty | -0.15 | n/a | candidate_score | ALL_CANDIDATES | negative_context_can_enable_policy_pass |
| context.penalty.example_keyword_for_person | penalty | -0.35 | n/a | candidate_score | PERSON_NAME | negative_context_can_enable_policy_pass |
| context.penalty.organization_not_person | penalty | -0.25 | n/a | candidate_score | PERSON_NAME | negative_context_can_enable_policy_pass |
| context.penalty.private_ip | penalty | -0.25 | n/a | candidate_score | IP_ADDRESS | score_only_before_policy_thresholds |
| context.penalty.public_phone_context | penalty | -0.25 | n/a | candidate_score | PHONE_LANDLINE, PHONE_MOBILE | negative_context_can_enable_policy_pass |
| context.penalty.weather_context_for_person | penalty | -0.35 | n/a | candidate_score | PERSON_NAME | negative_context_can_enable_policy_pass |

No raw span text, case text, raw URLs, hashes, or token maps are stored.
