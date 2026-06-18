# AGENTS.md

## Scope

These instructions apply only to this project:

`korean_pii_guardrail_v0_2`

Do not treat sibling directories such as `PII/`, `paper/`, `build/`, `outputs/`, or `tmp/` as part of this package unless the user explicitly asks for integration.

Exception: for M1 L0-derived preprocessing work, agents may read `PII/layer_0/korean_normalizer.py`, `PII/layer_0/korean_pii_detector.py`, and their tests as reference material only. Do not edit those files, import them from `korean_pii_guardrail_v0_2`, or copy their code into the package.

## Start Of Work

Before code changes, read:

1. `README.md`
2. `docs/12_SCOPE_CHANGE_NOTE.md`
3. `docs/10_DEVELOPMENT_HANDOFF.md`

For substantial implementation work, use `$korean-pii-guardrail-dev` if available. If the skill is not available, read the task-specific docs listed in `docs/10_DEVELOPMENT_HANDOFF.md`.

For Git, PR, review, or evidence-management work, also read `docs/13_GITHUB_OPERATIONS_AND_EVIDENCE_GUIDE.md`.

Always inspect existing source, tests, schemas, and configs before editing.

## Core Rules

- Keep v0.2 single-turn only.
- Do not implement RAG scanning, retrieval sanitization, multi-turn session monitoring, fragment ledger, subject tracker, Redis TTL store, previous-turn risk accumulation, full LLM judge, or human review dashboard.
- All detector spans must use raw text character offsets.
- Every internal `PIISpan` must satisfy `span.text == raw_text[span.start:span.end]`.
- Detectors produce candidates only; final actions belong to resolver, policy, and masking stages.
- Never write raw PII into logs, exceptions, metrics, reports, audit events, screenshots, public response spans, evidence files, or AI context files.
- Never commit API keys, tokens, credentials, local account names, machine paths that expose private identity, or machine-specific secrets.
- Keep entity, scoring, context, and policy behavior config-driven.
- Do not promote dictionary-only `PERSON_NAME` matches to high confidence without context.
- Preserve Korean suffixes during masking: replace only the PII body and keep josa/honorific/ending text outside the replacement.
- M1 must treat Layer 0 as a reference source for Korean variant-attack coverage, then reimplement the needed behavior as offset-aware normalized text and `TextVariant` outputs.
- L0-derived variants must be restorable to raw spans; reject candidates when raw span restoration cannot prove `span.text == raw_text[span.start:span.end]`.
- Kiwi/kiwipiepy may be used only as an optional reference or benchmark for sentence/token boundaries. Do not copy Kiwi source, models, or dictionaries into this package.

## Change Protocol

When changing contracts, update paired artifacts together:

- Entity changes: `configs/entities.yaml`, `src/pii_guardrail/enums.py`, and `schemas/pii_span.schema.json`
- Score changes: `configs/scoring.yaml` and `docs/03_SCORING_POLICY_SPEC.md`
- Context changes: `configs/context_rules.yaml` and `docs/04_CONTEXT_POLICY_SPEC.md`
- Policy changes: `configs/policy_profiles.yaml` and `docs/05_MASKING_POLICY_SPEC.md`
- API/schema changes: `api/openapi.yaml`, `schemas/*.schema.json`, dataclasses, and `docs/06_INTERFACE_SPEC.md`

## GitHub Workflow

- Start work from the latest `main`.
- Do implementation work on `feature/*`, `docs/*`, or `fix/*` branches.
- Open PRs into `main`; do not push directly to `main`.
- Keep PRs small and focused on one milestone or module when practical.
- Include work summary, reason, test results, impact scope, and review requests in PR descriptions.
- Do not store raw PII in evidence, reports, logs, screenshots, or failure records.

## Tests

Use focused pytest targets while developing, then run the full suite when practical:

```bash
python -m pytest
```

At minimum, cover relevant cases from `data/eval/hard_cases_v0.jsonl`, including boundary, hard negative, context/composite, overlap, and raw-PII safety scenarios.

For M1 preprocessing, also cover L0-derived variant cases such as jamo composition, choseong restoration, yaminjeongeum restoration, romanized Korean restoration, Korean digit restoration, and raw span restoration failures.
