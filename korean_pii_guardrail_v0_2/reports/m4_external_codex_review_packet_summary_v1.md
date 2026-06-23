# M4 External Codex-Assisted Review Packet Summary

- phase: Phase E. Codex-Assisted Draft Labeling And Human Review Packet Prep
- review_packet_gate_status: blocked_before_score_tuning
- failure_verdicts: codex_labels_only_stop_before_probability_loglr, reviewer_approved_labels_missing_stop_before_probability_loglr
- source_candidate_row_count: 1999
- review_packet_row_count: 500
- label_source: codex_assisted_review
- label_status: review_needed
- score_tuning_allowed_by_this_phase: false
- probability_loglr_computed: false
- m4_score_changed: false
- raw_text_persisted_in_reports: false
- raw_candidate_values_persisted_in_reports: false
- raw_context_terms_persisted_in_reports: false

## Packet Counts

| field | counts |
|---|---|
| candidate_entity | ADDRESS_UNIT:80, BUSINESS_REG_NO:80, PHONE_LANDLINE:80, EMAIL:63, HOSPITAL:60, CORPORATE_REG_NO:43, ORGANIZATION:26, PHONE_MOBILE:20 |
| source_domain | public_business_status:138, public_healthcare_org:102, public_record_commerce:99, public_record_finance:63, public_commercial_org:50, public_record_corporate:25, general_web:23 |
| privacy_context_class | organization_contact:249, public_record_identifier:123, unknown:114, public_figure_news:11, public_record_representative:3 |
| score_role | detect_org_contact_adjust_action:249, detect_public_pii_adjust_action:126, review_needed:125 |
| review_priority | medium:372, low:114, high:14 |

## Stop Conditions

- codex_labels_only_stop_before_probability_loglr
- reviewer_approved_labels_missing_stop_before_probability_loglr
- probability_loglr_not_computed
- m4_score_tuning_not_changed

The review packet is a local draft artifact only. It is not gold-label evidence.
