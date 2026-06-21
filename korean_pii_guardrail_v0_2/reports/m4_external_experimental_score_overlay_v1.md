# M4 External Experimental Score Overlay v1

- phase: `Experimental no-release M4 score overlay`
- overlay_mode: `shadow_only_not_runtime`
- release_eligible: `false`
- experimental_proposal_count: `11`
- config_change_proposed: `false`
- runtime_scoring_behavior_changed: `false`
- score_delta_changed: `false`
- previous_code_or_reports_removed: `false`

## Release Blockers

- `delta_sweep_not_executed_for_release`
- `delta_sweep_not_passed`
- `experimental_overlay_only`
- `locked_test_not_used`
- `no_score_candidate_proposals`
- `probability_support_gate_failed`
- `release_gate_not_executed`
- `same_corpus_shadow_eval_only`

## Applicability

- offline_shadow_and_possible_future_shape_rule: `2`
- offline_shadow_external_field_or_source_feature: `4`
- offline_shadow_only_hashed_context_feature: `5`

## Experimental Proposals

| id | group | feature_kind | feature_display | direction | delta | support | pii | not_pii | release_ready |
|---|---|---|---|---|---:|---:|---:|---:|---|
| m4-ext-exp-001 | ADDRESS | candidate_shape | address_unit_2_3 | pii_boost_candidate | 0.1 | 89 | 77 | 12 | false |
| m4-ext-exp-002 | ADDRESS | candidate_shape | address_unit_4_6 | pii_boost_candidate | 0.05 | 90 | 56 | 34 | false |
| m4-ext-exp-003 | ADDRESS | field_context_role | phone | pii_boost_candidate | 0.05 | 342 | 221 | 121 | false |
| m4-ext-exp-004 | ADDRESS | field_context_role | location | not_pii_penalty_candidate | -0.1 | 121 | 13 | 108 | false |
| m4-ext-exp-005 | ADDRESS | right_bigrams | [hashed_context_ngram] | pii_boost_candidate | 0.05 | 15 | 10 | 5 | false |
| m4-ext-exp-006 | ADDRESS | right_unigrams | [hashed_context_ngram] | pii_boost_candidate | 0.05 | 15 | 10 | 5 | false |
| m4-ext-exp-007 | ADDRESS | right_unigrams | [hashed_context_ngram] | pii_boost_candidate | 0.075 | 16 | 12 | 4 | false |
| m4-ext-exp-008 | ADDRESS | right_unigrams | [hashed_context_ngram] | pii_boost_candidate | 0.075 | 61 | 40 | 21 | false |
| m4-ext-exp-009 | ADDRESS | right_unigrams | [hashed_context_ngram] | pii_boost_candidate | 0.1 | 45 | 37 | 8 | false |
| m4-ext-exp-010 | ADDRESS | source_domain | public_record_commerce | not_pii_penalty_candidate | -0.1 | 131 | 12 | 119 | false |
| m4-ext-exp-011 | ADDRESS | source_field_role | address | pii_boost_candidate | 0.1 | 342 | 280 | 62 | false |

## Same-Corpus Shadow Evaluation

- approved_rows_seen: `686`
- evaluated_ready_group_rows: `686`
- affected_rows: `608`
- desirable_direction_rows: `554`
- undesirable_direction_rows: `54`
- neutral_rows: `78`
- maximum_absolute_row_delta: `0.2`

## Decision

This overlay is allowed only as an experimental shadow artifact.
It does not update M4 runtime scoring, configs, context rules, or release gates.
