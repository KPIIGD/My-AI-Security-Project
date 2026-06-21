# Context Policy Interaction v1

- phase: `Execution Phase 4. Rule Metrics and Delta Sweep`
- score deltas and policy overrides are separated.
- policy-only rules are not forced into score calibration.

| Rule | Effect Scope | Policy Interaction | Action Counts | Calibration Domains |
|---|---|---|---|---|
| context.boost.address_cooccur_for_person | candidate_score | strong_context_can_enable_policy_context_mask | mask:250 | none |
| context.boost.bank_cooccur | candidate_score | strong_context_can_enable_policy_context_mask | mask:181 | none |
| context.boost.field_label_account | candidate_score | strong_context_can_enable_policy_context_mask | mask:406 | finance |
| context.boost.field_label_address | candidate_score | strong_context_can_enable_policy_context_mask | mask:253, pass:256 | ecommerce |
| context.boost.field_label_name | candidate_score | strong_context_can_enable_policy_context_mask | mask:411 | ecommerce, enterprise_internal, generic |
| context.boost.field_label_phone | candidate_score | strong_context_can_enable_policy_context_mask | mask:1439 | ecommerce |
| context.boost.full_address_detail | candidate_score | strong_context_can_enable_policy_context_mask | mask:389 | ecommerce |
| context.boost.medical_label | candidate_score | strong_context_can_enable_policy_context_mask | mask:617 | healthcare |
| context.boost.organization_affiliation_context | candidate_score | strong_context_can_enable_policy_context_mask | mask:126 | enterprise_internal |
| context.boost.phone_cooccur_for_person | candidate_score | strong_context_can_enable_policy_context_mask | mask:172 | ecommerce |
| context.boost.title_after_name | candidate_score | strong_context_can_enable_policy_context_mask | mask:52 | generic |
| context.composite.ADDRESS_FULL | composite_status_and_policy_action | policy.composite.mask via is_composite | mask:157 | none |
| context.composite.ADDRESS_UNIT | composite_status_and_policy_action | policy.composite.mask via is_composite | mask:284 | none |
| context.composite.BANK_ACCOUNT | composite_status_and_policy_action | policy.composite.mask via is_composite | mask:129 | none |
| context.composite.DOB | composite_status_and_policy_action | policy.composite.mask via is_composite | mask:284 | none |
| context.composite.EMAIL | composite_status_and_policy_action | policy.composite.mask via is_composite | mask:130 | none |
| context.composite.HOSPITAL | composite_status_and_policy_action | policy.composite.mask via is_composite | mask:143 | none |
| context.composite.MEDICAL_RECORD_NO | composite_status_and_policy_action | policy.composite.mask via is_composite | mask:143 | none |
| context.composite.PERSON_NAME | composite_status_and_policy_action | policy.composite.mask via is_composite | mask:588 | ecommerce |
| context.composite.PHONE_LANDLINE | composite_status_and_policy_action | policy.composite.mask via is_composite | none | none |
| context.composite.PHONE_MOBILE | composite_status_and_policy_action | policy.composite.mask via is_composite | mask:172 | ecommerce |
| context.composite.SCHOOL | composite_status_and_policy_action | policy.composite.mask via is_composite | mask:284 | none |
| context.penalty.abstract_value_context_for_person | candidate_score | score_only_before_policy_thresholds | pass:153 | generic |
| context.penalty.code_or_log_context | candidate_score | negative_context_can_enable_policy_pass | pass:100 | none |
| context.penalty.example_context | candidate_score | negative_context_can_enable_policy_pass | mask:2, pass:1230 | enterprise_internal |
| context.penalty.example_keyword_for_person | candidate_score | negative_context_can_enable_policy_pass | none | none |
| context.penalty.organization_not_person | candidate_score | negative_context_can_enable_policy_pass | pass:101 | generic |
| context.penalty.private_ip | candidate_score | score_only_before_policy_thresholds | none | none |
| context.penalty.public_phone_context | candidate_score | negative_context_can_enable_policy_pass | none | none |
| context.penalty.weather_context_for_person | candidate_score | negative_context_can_enable_policy_pass | pass:126 | none |
