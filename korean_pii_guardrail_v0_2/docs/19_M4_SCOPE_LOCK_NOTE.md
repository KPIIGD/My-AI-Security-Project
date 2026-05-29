# M4 Scope Lock Note

Version: v0.2-single-turn
Stage: 0.1 M4 scope lock
Status: Phase artifact

## Purpose

This note locks the M4 recalibration scope before any data collection,
probability estimation, delta sweep, or runtime config proposal. It is a
phase-scoped artifact for `Stage 0.1 M4 scope lock` in
`docs/18_M4_KOREAN_CONTEXT_CORPUS_SCORE_RECALIBRATION_PLAN.md`.

## Locked Scope

M4 is the context score correction layer. It analyzes context around existing
candidates and adjusts candidate scores or context reason evidence. M4 does
not create new candidates, train NER, improve NER recall, improve regex or
validator coverage, use retrieval context, use multi-turn memory, or look up
external databases.

All M4-only evaluation must keep upstream candidate generation fixed. Regex,
dictionary, validator, and NER candidate outputs must be treated as the same
input set across comparison groups. Any improvement that requires new or
better upstream candidates is outside M4 and must be reported as an upstream
dependency, not counted as M4 progress.

## Required Comparison Groups

Every M4-only recalibration experiment that evaluates score behavior must use
the same upstream candidate snapshot across these comparison groups:

| Group | Meaning |
|---|---|
| `no_m4_context` | Context boost, penalty, and composite effects disabled for comparison. |
| `baseline_current_m4` | Current `configs/scoring.yaml` and `configs/context_rules.yaml` behavior. |
| `candidate_m4_delta` | Candidate score deltas derived from approved probability and sweep evidence. |
| `candidate_m4_terms` | Candidate term classes or context rules derived from approved evidence. |

Candidate-level metrics and action-level metrics must be reported separately.
Score changes cannot be approved from candidate metrics alone when final
`pass`, `mask`, `hash`, or `block` behavior does not improve or preserve
release-gate requirements.

## Prior Delta Sweep Interpretation Lock

The existing Phase 4 conservative selection behavior must not be interpreted
as score optimization. In particular, `_select_conservative_candidate` in
`src/pii_guardrail/context_phase4.py` keeps the current delta when that value
appears in the candidate grid. Therefore, `config_changes_proposed=0` means a
conservative no-op result unless a later recalibration phase proves otherwise.
It does not prove that the current delta is optimal, that it is better than
other candidate deltas, or that the magnitude has been validated on realistic
Korean context data.

Later delta selection must fix the candidate grid, objective function, split
policy, approval criteria, and rejection criteria before running the sweep.
The current configured value may be selected only when the evidence shows it
wins or when the result is explicitly reported as insufficient magnitude
evidence with no runtime score change.

## Raw PII Safety Lock

Stage 0.1 introduces no raw text corpus and no runtime output. Later artifacts
must remain raw-PII-free:

- no raw candidate values;
- no raw span text;
- no full source sentences;
- no raw URLs;
- no reversible token mapping;
- no secrets or credentials.

Allowed evidence fields include entity type, domain category, anchor shape,
source class, n-gram or controlled term class, relative position, distance
bucket, counts, probabilities, confidence intervals, score deltas, action
counts, hashes, and explicit `raw_value_logged=false` flags.

Any artifact, log, or report raw PII safety failure blocks score delta and
context rule proposals for that phase.

## Stage 0.1 Exit Checklist

- M4 is locked as a candidate score correction layer, not a candidate
  generation layer.
- Upstream regex, dictionary, validator, and NER candidate generation remain
  fixed for M4-only evaluation.
- `no_m4_context`, `baseline_current_m4`, `candidate_m4_delta`, and
  `candidate_m4_terms` comparison groups are defined.
- Current delta retention is not treated as optimization evidence.
- Runtime scoring behavior and config files are unchanged.
- Raw PII safety expectations are documented for later artifacts.
