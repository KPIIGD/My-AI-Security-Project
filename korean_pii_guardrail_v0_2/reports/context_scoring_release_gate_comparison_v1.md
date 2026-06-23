# Context Reviewed Config Release Gate Comparison v1

- phase: `Execution Phase 5. Reviewed Config Change`
- status: `pass`
- approved_delta_count: `0`
- config_update_applied: `false`
- runtime_scoring_behavior_changed: `false`
- public_corpus_used_for_score_tuning: `false`
- config_change_decision: `no_op_no_approved_deltas`

## Release Gate Checks

| Check | Before | After | Delta | Status |
|---|---:|---:|---:|---|
| raw_pii_logging_count | 0 | 0 | 0 | pass |
| invalid_offset_count | 0 | 0 | 0 | pass |
| high_risk_recall | 0.9645 | 0.9645 | 0.0 | pass |
| actionable_high_risk_recall | 0.9645 | 0.9645 | 0.0 | pass |
| phone_email_actionable_recall | 1.0 | 1.0 | 0.0 | pass |
| bank_account_actionable_recall | 1.0 | 1.0 | 0.0 | pass |
| person_name_hard_negative_candidate_fp | 500 | 500 | 0 | pass |
| hard_negative_actionable_fp_total | 0 | 0 | 0 | pass |
| actionable_overall_precision | 0.9975 | 0.9975 | 0.0 | pass |
| deterministic_latency_p95_ms | 368.1189 | 225.5849 | -142.534 | pass |
| report_raw_text_leak_count | 0 | 0 | 0 | pass |
| after_audit_safety_status | pass | pass | n/a | pass |
| release_gate_overall_status | pass | pass | n/a | pass |
