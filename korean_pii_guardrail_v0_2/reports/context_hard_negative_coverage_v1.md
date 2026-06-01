# M4 Phase 5 Hard Negative Coverage

This report measures raw-free non-PII lookalike coverage. It does not promote Codex draft labels to gold labels and does not change runtime scoring.

- phase_exit_status: pass
- final_anchor_window_count: 1307
- generated_hard_negative_anchor_count: 14
- raw_pii_leak_count: 0
- raw_url_logged_count: 0
- raw_value_logged_count: 0
- score_tuning_allowed_by_this_phase: false

## Coverage By Entity Group

| entity_group | non_pii | hard_negative | required_ratio | actual_ratio | status |
| --- | ---: | ---: | ---: | ---: | --- |
| PERSON_NAME | 7 | 7 | 0.60 | 1.0000 | pass |
| PHONE | 475 | 475 | 0.50 | 1.0000 | pass |
| EMAIL | 224 | 224 | 0.50 | 1.0000 | pass |
| ADDRESS | 7 | 7 | 0.50 | 1.0000 | pass |
| BANK_ACCOUNT | 336 | 336 | 0.50 | 1.0000 | pass |
| REGISTRATION_IDENTIFIER | 74 | 74 | 0.50 | 1.0000 | pass |

## Gate Verdict

- hard_negative_gate_status: pass
- failure_verdicts: hard_negative_gate_pass
