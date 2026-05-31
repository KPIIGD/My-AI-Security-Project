# M4 Phase 2 Public Web Context Gap Report

Version: v0.2-single-turn
Phase: 2 public web context expansion
Status: data-quality-gate-stop

## Purpose

This report records the Phase 2 gate assessment for the current raw-free public
web context corpus. It is a stop report, not a score tuning approval. It does
not change runtime scoring, context rules, policy behavior, NER behavior,
candidate generation, RAG behavior, retrieval behavior, or multi-turn behavior.

## Inputs

- `data/context_corpus/context_anchor_windows_v1.jsonl`
- `data/context_corpus/korean_context_terms_v1.jsonl`
- `data/context_corpus/context_anchor_windows_manifest_v1.yaml`
- `reports/context_anchor_corpus_safety_v1.json`
- `reports/korean_context_terms_safety_v1.json`

## Public Web Corpus Snapshot

| Measurement | Value |
|---|---:|
| Anchor windows | 1,109 |
| Context terms | 19,458 |
| Evidence lane `public_web_context` | 1,109 |
| Label source `codex_draft` | 1,109 |
| Label status `review_needed` | 1,109 |
| `true_pii` anchors | 0 |
| `non_pii` anchors | 1,109 |
| `unknown` anchors | 0 |
| `PERSON_NAME` anchors | 0 |
| `ADDRESS` anchors | 0 |

Entity coverage:

| Entity | Count |
|---|---:|
| `PHONE_LANDLINE` | 461 |
| `PHONE_MOBILE` | 14 |
| `EMAIL` | 224 |
| `BANK_ACCOUNT` | 336 |
| `BUSINESS_REG_NO` | 74 |

Material mix:

| Material Type | Count | Ratio |
|---|---:|---:|
| `realistic_input_like` | 969 | 0.87376 |
| `general_web_or_explanatory` | 140 | 0.12624 |
| `example_or_sample` | 0 | 0.0 |

## Data Diversity Gate

Current manifest status: fail.

Failing checks:

- `min_domain_count_by_core_entity`
- `max_single_domain_ratio_by_core_entity`

Passing checks:

- anchor input exists;
- anchor windows exist;
- practical metadata is present;
- public-web-only rows are blocked from score evidence;
- raw PII leak count is 0;
- raw URL logged count is 0;
- raw value logged count is 0;
- invalid offset count is 0;
- duplicate anchor-window ratio is within limit;
- realistic input-like material ratio is at least 70%;
- general web or explanatory material ratio is at most 30%;
- example or sample material ratio is at most 15%.

Domain counts by core entity:

| Core Entity | Domain Count | Required |
|---|---:|---:|
| `PERSON_NAME` | 0 | 5 |
| `ADDRESS` | 0 | 5 |
| `PHONE` | 9 | 5 |
| `EMAIL` | 8 | 5 |
| `BANK_ACCOUNT` | 9 | 5 |
| `REGISTRATION_IDENTIFIER` | 8 | 5 |

Maximum single-domain ratios by core entity:

| Core Entity | Max Ratio | Limit |
|---|---:|---:|
| `PERSON_NAME` | 0.0 | 0.35 |
| `ADDRESS` | 0.0 | 0.35 |
| `PHONE` | 0.267368 | 0.35 |
| `EMAIL` | 0.410714 | 0.35 |
| `BANK_ACCOUNT` | 0.431548 | 0.35 |
| `REGISTRATION_IDENTIFIER` | 0.27027 | 0.35 |

## Gap Verdicts

Required current verdicts:

- `needs_more_data`
- `needs_domain_split`
- `needs_synthetic_true_pii`
- `needs_template_extraction`
- `needs_reviewer_labels`
- `evidence_backlog`

Entity-level verdicts:

| Core Entity | Verdicts |
|---|---|
| `PERSON_NAME` | `needs_more_data`, `needs_synthetic_true_pii`, `needs_template_extraction`, `needs_reviewer_labels`, `evidence_backlog` |
| `ADDRESS` | `needs_more_data`, `needs_synthetic_true_pii`, `needs_template_extraction`, `needs_reviewer_labels`, `evidence_backlog` |
| `PHONE` | `needs_more_data`, `needs_synthetic_true_pii`, `needs_reviewer_labels`, `evidence_backlog` |
| `EMAIL` | `needs_more_data`, `needs_synthetic_true_pii`, `needs_reviewer_labels`, `evidence_backlog` |
| `BANK_ACCOUNT` | `needs_more_data`, `needs_synthetic_true_pii`, `needs_reviewer_labels`, `evidence_backlog` |
| `REGISTRATION_IDENTIFIER` | `needs_more_data`, `needs_synthetic_true_pii`, `needs_reviewer_labels`, `evidence_backlog` |

## Safety

Raw-free safety status: pass.

| Safety Measurement | Value |
|---|---:|
| Raw PII leak count | 0 |
| Raw URL logged count | 0 |
| Raw value logged count | 0 |
| Contains raw PII true count | 0 |
| Invalid offset count | 0 |
| Page body stored | false |
| Candidate value stored | false |

## Stop Decision

Phase 2 must stop at the Data Quality Gate. Public-web collection produced
useful raw-free discovery and hard-negative evidence, but it is not score
tuning evidence and must not feed probability estimation, logLR estimation,
delta sweep, locked-test selection, or config proposals.

The next allowed work is not score tuning. It is Phase 3 template extraction for
`PERSON_NAME` and `ADDRESS`, followed later by safe synthetic true-PII
insertion and reviewer-approved labels if those phases pass their own gates.
