# M4 Phase 3 Raw-Free Template Inventory

This report summarizes controlled field-label templates only. It stores no raw names, raw addresses, raw sentences, raw URLs, or recoverable values.

- phase_exit_status: pass
- template_count: 14
- PERSON_NAME_templates: 7
- ADDRESS_templates: 7
- PERSON_NAME_domain_count: 7
- ADDRESS_domain_count: 7
- raw_pii_leak_count: 0
- raw_sentence_logged_count: 0
- score_tuning_allowed_by_this_phase: false

## Template Entity Mappings

| template_id | entity_group | anchor_entity | anchor_shape | source_domain |
| --- | --- | --- | --- | --- |
| tpl_person_customer_support_001 | PERSON_NAME | PERSON_NAME | korean_name_3_syllable | customer_support |
| tpl_person_ecommerce_001 | PERSON_NAME | PERSON_NAME | korean_name_3_syllable | ecommerce |
| tpl_person_healthcare_001 | PERSON_NAME | PERSON_NAME | korean_name_3_syllable | healthcare |
| tpl_person_finance_001 | PERSON_NAME | PERSON_NAME | korean_name_3_syllable | finance |
| tpl_person_education_001 | PERSON_NAME | PERSON_NAME | korean_name_3_syllable | education |
| tpl_person_public_services_001 | PERSON_NAME | PERSON_NAME | korean_name_3_syllable | public_services |
| tpl_person_enterprise_internal_001 | PERSON_NAME | PERSON_NAME | korean_name_3_syllable | enterprise_internal |
| tpl_address_customer_support_001 | ADDRESS | ADDRESS_FULL | road_address_shape | customer_support |
| tpl_address_ecommerce_001 | ADDRESS | ADDRESS_FULL | road_address_shape | ecommerce |
| tpl_address_healthcare_001 | ADDRESS | ADDRESS_FULL | road_address_shape | healthcare |
| tpl_address_finance_001 | ADDRESS | ADDRESS_FULL | road_address_shape | finance |
| tpl_address_education_001 | ADDRESS | ADDRESS_FULL | road_address_shape | education |
| tpl_address_public_services_001 | ADDRESS | ADDRESS_FULL | road_address_shape | public_services |
| tpl_address_enterprise_internal_001 | ADDRESS | ADDRESS_UNIT | address_unit_shape | enterprise_internal |
