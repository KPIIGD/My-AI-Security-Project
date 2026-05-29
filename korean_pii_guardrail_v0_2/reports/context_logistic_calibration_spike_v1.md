# Context Logistic Calibration Spike v1

- phase: `Execution Phase 7. Optional Calibration Spike`
- status: `pass`
- promotion_decision: `research_only_not_promoted`
- deterministic_config_remains_default: `true`
- deterministic_fallback_available: `true`
- runtime_scoring_behavior_changed: `false`
- model_artifact_written: `false`

## ECE Comparison

| Split | Predictions | Deterministic ECE | Calibrated ECE | Delta | Recall Regression |
|---|---:|---:|---:|---:|---|
| train | 12 | 0.134167 | 1.5e-05 | -0.134152 | false |
| dev | 11 | 0.081818 | 0.013411 | -0.068407 | false |
| test | 9 | 0.134444 | 0.05676 | -0.077684 | false |

## Decision

locked test ECE improved without action recall regression, but prediction support is below the promotion threshold

The learned score is evaluated only in shadow mode. Runtime reason codes, policy routing, and deterministic fallback remain unchanged.
