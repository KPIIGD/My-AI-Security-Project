# M4 Quality Gates Spec

Version: v0.2-single-turn
Stage: 0.3 gate spec lock
Status: Phase artifact

## Purpose

This document locks measurable quality gates for the M4 Korean context score
recalibration plan. It satisfies `Stage 0.3 gate spec lock` in
`docs/18_M4_KOREAN_CONTEXT_CORPUS_SCORE_RECALIBRATION_PLAN.md`.

No score delta, context rule, runtime config, policy behavior, candidate
generation behavior, or NER behavior is changed by this phase.

## Gate Evaluation Rule

Before any score delta or context rule proposal, every applicable gate must be
reported as `pass`. If a gate is not applicable to a phase, the phase review
packet must say why. A non-applicable gate cannot be used as evidence for a
score or context rule proposal.

If any applicable gate fails, M4 score changes stop for that phase and the
result moves to an evidence backlog or redesign verdict instead of a runtime
configuration proposal.

The machine-readable registry for these gates is
`reports/m4_quality_gate_spec_v1.json`.

## Gate Summary

| Gate | Required before score or rule proposal | Primary evidence artifact | Pass condition |
|---|---:|---|---|
| Data Quality Gate | yes | `context_anchor_windows_manifest_v1.yaml` or equivalent manifest | corpus diversity, scale, duplicate, offset, and raw-free criteria pass |
| Label Quality Gate | yes | `context_label_quality_v1.json` or label audit artifact | reviewer-approved labels, agreement, unknown, and disagreement criteria pass |
| Hard Negative Gate | yes | `context_hard_negative_coverage_v1.md` or equivalent report | required hard negative ratios pass by entity group |
| Delta Sweep Gate | yes | `context_delta_optimization_v2.json` or sweep report | grid, objective, split, approval criteria, and action-level constraints pass |
| Independent Reviewer Gate | yes | reviewer verdict in review packet | reviewer returns `APPROVED` |
| Locked Test Gate | yes for final candidate selection | locked-test run report | locked test used once after candidate selection and not for repeated tuning |
| Raw PII Safety Gate | yes | raw PII scan report | raw PII leak count, raw logging count, and invalid offset count are all zero |

## Data Quality Gate

Required measurements:

- raw PII leak count;
- invalid offset count;
- domain count per core entity;
- maximum single-domain ratio per entity;
- realistic input-like material ratio;
- general web or explanatory material ratio;
- example or sample document ratio;
- duplicate anchor-window ratio;
- unknown label ratio when labels are present;
- source manifest fields for source domain, source type, label counts, hard
  negative counts, and raw-free scan results.

Pass criteria:

- raw PII leak count is `0`;
- invalid offset count is `0`;
- each core entity has at least `5` domains;
- no single domain exceeds `0.35` of an entity's anchors;
- realistic input-like material ratio is at least `0.70`;
- general web or explanatory material ratio is at most `0.30`;
- example or sample document ratio is at most `0.15`;
- duplicate anchor-window ratio is at most `0.05`;
- unknown label ratio is at most `0.15` when labels are present.

Failure verdicts:

- `rejected_data_quality_gate`;
- `evidence_backlog`;
- `needs_more_data`;
- `needs_domain_split`.

## Label Quality Gate

Required measurements:

- label source counts for `codex_draft`, `reviewer_approved`, and `unknown`;
- final-probability input label source;
- stratified reviewer sample count by entity, domain, and label;
- agreement score;
- disagreement ratio;
- adjudication or unknown isolation status.

Pass criteria:

- final probability estimation uses only `reviewer_approved` labels;
- independent reviewer sampling is stratified by entity, domain, and label;
- reviewer sample size is at least the larger of `5%` or `1000` rows when
  enough rows exist;
- agreement is at least `0.85`;
- disagreement ratio is at most `0.10`;
- unresolved disagreements are isolated as `unknown` or adjudicated;
- `unknown` labels are excluded from final score tuning.

Failure verdicts:

- `rejected_label_quality_gate`;
- `needs_more_labels`;
- `needs_adjudication`.

## Hard Negative Gate

Required measurements:

- non-PII anchor count by entity group;
- hard negative count by entity group;
- hard negative ratio by entity group;
- false positive replay set update status.

Pass criteria:

- `PERSON_NAME` hard negatives are at least `0.60` of non-PII anchors;
- phone, email, address, account, and registration identifier groups each have
  hard negatives at least `0.50` of non-PII anchors;
- new false positives found during evaluation are added to a raw-free failure
  replay set.

Failure verdicts:

- `rejected_hard_negative_gate`;
- `needs_more_hard_negatives`;
- `evidence_backlog`.

## Delta Sweep Gate

Required pre-sweep locks:

- candidate delta grid;
- objective function;
- train/dev/locked-test split policy;
- approval criteria;
- rejection criteria;
- action-level regression constraints.

Required measurements:

- candidate-level metrics for each score candidate;
- action-level metrics for each score candidate;
- high-risk recall delta;
- actionable high-risk recall delta;
- hard negative actionable false positive delta;
- raw PII leak count;
- raw PII logging count;
- invalid offset count.

Pass criteria:

- sweep locks are recorded before the sweep starts;
- current delta is not automatically selected because it is the configured
  value;
- high-risk recall does not regress;
- actionable high-risk recall does not regress;
- hard negative actionable false positives do not increase;
- raw PII leak count is `0`;
- raw PII logging count is `0`;
- invalid offset count is `0`;
- selected delta has direction, magnitude, and action evidence.

Failure verdicts:

- `rejected_delta_sweep_gate`;
- `needs_delta_redesign`;
- `insufficient_magnitude_evidence`.

## Independent Reviewer Gate

Required measurements:

- review packet includes project direction, M4-only constraints, phase
  acceptance criteria, changed file list, diff, tests, artifacts, gate results,
  raw PII safety result, and locked test statement when applicable;
- reviewer verdict;
- reviewer findings;
- required fixes status.

Pass criteria:

- reviewer returns `APPROVED`;
- reviewer is independent of the main implementation path;
- reviewer checks the diff and artifacts, not only the main agent's intent;
- all required fixes are complete before commit.

Failure verdicts:

- `rejected_reviewer_gate`;
- `changes_requested`.

## Locked Test Gate

Required measurements:

- train/dev/locked-test split identifiers;
- locked-test access count;
- locked-test run timestamp and commit or config hash;
- evidence that locked test n-grams were not used for candidate discovery;
- failure response if locked test fails.

Pass criteria:

- train is used for discovery and initial probability estimation;
- dev is used for delta selection;
- locked test is used only once after final candidate selection;
- locked test results are not used for repeated tuning;
- if locked test fails, the candidate returns to dev redesign instead of being
  patched directly against the locked test.

Failure verdicts:

- `rejected_locked_test_gate`;
- `locked_test_leakage`;
- `needs_dev_redesign`.

## Raw PII Safety Gate

Required measurements:

- raw PII leak count in reports and artifacts;
- raw PII logging count;
- public response raw value logged count;
- audit event raw value logged count;
- report raw text leak count;
- invalid offset count;
- raw URL presence;
- reversible token mapping presence;
- secret or credential pattern matches.

Pass criteria:

- raw PII leak count is `0`;
- raw PII logging count is `0`;
- public response raw value logged count is `0`;
- audit event raw value logged count is `0`;
- report raw text leak count is `0`;
- invalid offset count is `0`;
- raw URLs are absent from artifacts;
- reversible token mappings are absent from artifacts;
- secret and credential scans return no matches.

Failure verdicts:

- `rejected_safety`;
- `raw_pii_safety_failure`;
- `invalid_offset_failure`.

## Stage 0.3 Exit Checklist

- All required M4 gates are listed.
- Each gate has measurable inputs and pass criteria.
- Each gate has failure verdicts.
- Non-applicable gate handling is defined.
- Runtime scoring behavior and config files are unchanged.
- No score delta or context rule change is proposed.
