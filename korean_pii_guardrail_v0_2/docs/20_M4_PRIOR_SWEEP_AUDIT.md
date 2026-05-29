# M4 Prior Sweep Audit

Version: v0.2-single-turn
Stage: 0.2 prior sweep audit
Status: Phase artifact

## Purpose

This audit records the limitation of the existing Phase 4 context delta sweep.
It satisfies the `Stage 0.2 prior sweep audit` artifact in
`docs/18_M4_KOREAN_CONTEXT_CORPUS_SCORE_RECALIBRATION_PLAN.md`.

## Inputs Audited

| Input | Use |
|---|---|
| `src/pii_guardrail/context_phase4.py` | Confirms `_select_conservative_candidate` keeps the current delta when that value is present in the candidate grid. |
| `reports/context_delta_sweep_v1.json` | Confirms the previous sweep proposed no config changes and retained current deltas conservatively. |
| `reports/context_score_tuning_v1.md` | Confirms the previous report was a no-runtime-change evidence report, not a score optimization approval. |

## Audit Findings

The previous Phase 4 sweep is useful as a raw-free conservative evidence
report, but it is not sufficient magnitude evidence for runtime score changes.

Observed raw-free summary from `reports/context_delta_sweep_v1.json`:

| Field | Value |
|---|---:|
| `swept_rule_count` | 12 |
| `config_changes_proposed` count | 0 |
| `selection_reason=conservative_current_delta_kept` count | 12 |
| `runtime_scoring_behavior_changed` | false |
| `score_delta_changed` | false |
| `public_corpus_used_for_score_tuning` | false |

Because every swept rule used `conservative_current_delta_kept`, the prior
result must be interpreted as a conservative no-op. It does not establish that
the current delta is optimal, that the current delta beats other candidates,
or that the current magnitude is validated by realistic Korean context data.

## Unsupported Claims Prohibited

The following claims are not supported by the prior sweep and must not be used
as M4 recalibration evidence:

- current deltas are optimal;
- `config_changes_proposed=0` means score tuning is complete;
- current deltas beat the alternative candidate grid;
- keeping a current value is equivalent to reviewer-approved magnitude
  evidence;
- public or unlabeled corpus evidence alone can approve a runtime score delta.

## Required Later Fix

A later candidate sweep must fix these items before execution:

- candidate delta grid;
- objective function;
- train/dev/locked-test split use;
- approval and rejection criteria;
- action-level regression constraints;
- raw PII safety checks.

If the current value is retained later, the report must say whether it was
retained because it won the fixed comparison, or because the evidence remains
insufficient and no runtime score change is approved.

## Stage 0.2 Exit Checklist

- `_select_conservative_candidate` limitation is documented.
- `config_changes_proposed=0` is not treated as optimization evidence.
- The existing report is classified as a conservative no-op evidence report.
- No score delta or context rule change is proposed.
- Runtime config files remain unchanged.
- Raw PII safety expectations remain in force.
