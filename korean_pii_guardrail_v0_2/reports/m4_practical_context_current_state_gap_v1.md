# M4 Practical Context Current-State Gap Report

Version: v0.2-single-turn
Phase: 0 current-state audit
Status: raw-free phase artifact

## Purpose

This report records the current repository evidence for the practical Korean
M4 context data goal before continuing into later phases. It is raw-free and
does not approve a score delta, context rule change, runtime behavior change,
NER change, candidate-generation change, RAG feature, retrieval feature, or
multi-turn feature.

## Scope Check

- Project root: `korean_pii_guardrail_v0_2`
- Branch observed: `feature/m4-context-evidence-upgrade`
- M4 scope: context around existing PII candidates only
- Runtime scoring behavior changed by this phase: false
- Score delta changed by this phase: false
- Context rule changed by this phase: false
- Public corpus used for score tuning: false

## Source Documents Read

- `README.md`
- `docs/12_SCOPE_CHANGE_NOTE.md`
- `docs/10_DEVELOPMENT_HANDOFF.md`
- `docs/13_GITHUB_OPERATIONS_AND_EVIDENCE_GUIDE.md`
- `docs/18_M4_KOREAN_CONTEXT_CORPUS_SCORE_RECALIBRATION_PLAN.md`
- `docs/19_M4_SCOPE_LOCK_NOTE.md`
- `docs/20_M4_PRIOR_SWEEP_AUDIT.md`
- `docs/21_M4_QUALITY_GATES_SPEC.md`
- `docs/M4_PRACTICAL_CONTEXT_DATA_GOAL_DETAILS.md`

## Existing Phase 0 Evidence

The repository already contains tracked Stage 0 artifacts:

- `docs/19_M4_SCOPE_LOCK_NOTE.md`
- `docs/20_M4_PRIOR_SWEEP_AUDIT.md`
- `docs/21_M4_QUALITY_GATES_SPEC.md`
- `reports/m4_quality_gate_spec_v1.json`

These artifacts lock M4 as a score-correction layer, document that the prior
delta sweep was a conservative no-op rather than magnitude evidence, and define
the measurable data, label, hard-negative, delta, reviewer, locked-test, and raw
PII safety gates.

## Current Generated Artifact Snapshot

Observed from `data/context_corpus/context_anchor_windows_manifest_v1.yaml`,
`data/context_corpus/context_anchor_windows_v1.jsonl`,
`reports/context_anchor_corpus_safety_v1.json`, and
`reports/korean_context_terms_safety_v1.json`.

| Measurement | Value |
|---|---:|
| Anchor windows | 1,109 |
| Context terms | 19,458 |
| `true_pii` anchors | 0 |
| `non_pii` anchors | 1,109 |
| `unknown` anchors | 0 |
| `PERSON_NAME` anchors | 0 |
| `ADDRESS` anchors | 0 |
| Raw PII leak count | 0 |
| Raw URL logged count | 0 |
| Raw value logged count | 0 |
| Invalid offset count | 0 |
| Duplicate anchor-window ratio | 0.0 |
| Realistic input-like material ratio | 0.87376 |
| General web or explanatory material ratio | 0.12624 |
| Example or sample material ratio | 0.0 |

Entity coverage currently exists for `PHONE_LANDLINE`, `PHONE_MOBILE`, `EMAIL`,
`BANK_ACCOUNT`, and `BUSINESS_REG_NO`. It does not exist for `PERSON_NAME` or
`ADDRESS`.

## Data Quality Gate Status

Current manifest status: fail.

Failure verdicts:

- `needs_more_data`
- `needs_domain_split`

Important gate details:

- Raw PII safety passes.
- `PHONE` and `REGISTRATION_IDENTIFIER` pass the current domain-ratio gate.
- `BANK_ACCOUNT` and `EMAIL` exceed the maximum single-domain ratio.
- `PERSON_NAME` and `ADDRESS` have zero domains and zero anchors.
- Public-web-only rows remain evidence for discovery and hard-negative
  analysis only.

## Practical Schema Gap

The current anchor rows do not yet carry the practical evidence-lane and review
fields required by the goal:

- `evidence_lane`
- `label_source`
- `label_status`
- `material_type`
- `mvp_target`
- `current_count`
- `gap_reason`
- `gap_verdict`

This makes Phase 1 incomplete. The existing `material_class` field is useful
but does not fully satisfy the practical manifest/schema requirement.

## Known Gaps To Preserve

These gaps are explicit blockers, not hidden successes:

- `true_pii` anchors remain 0, so score tuning is not allowed.
- `PERSON_NAME` anchors remain 0, so the entity needs template extraction and
  synthetic true-PII insertion before probability estimation.
- `ADDRESS` anchors remain 0, so the entity needs template extraction and
  synthetic true-PII insertion before probability estimation.
- Reviewer-approved labels are absent, so final probability/logLR estimation is
  not allowed.
- Hard-negative quotas have not passed, so boost proposals are not allowed.
- Delta sweep and locked-test gates have not run for any practical candidate
  config change.

Required current verdicts:

- `needs_more_data`
- `needs_domain_split`
- `needs_synthetic_true_pii`
- `needs_template_extraction`
- `needs_reviewer_labels`
- `evidence_backlog`

## Worktree Audit

In-scope M4-related uncommitted files were present before this Phase 0 report,
including the generated anchor corpus, context terms, source plan, goal details,
collector manifest, and safety reports. They are not staged by this phase
unless explicitly required by the current phase commit gate.

Unrelated untracked files also exist outside the M4 evidence scope. They remain
untouched.

## Resume Decision

Phase 0 current-state audit is complete once this report passes independent
review. The next incomplete phase is Phase 1, Manifest And Schema Upgrade.

Phase 1 must make the corpus schema and manifest represent practical evidence
lanes, label source/status, material type, target/current counts, and gap
verdicts before any later public-web expansion, template extraction, synthetic
insertion, hard-negative analysis, label review, probability estimation, delta
sweep, or score/config proposal.
