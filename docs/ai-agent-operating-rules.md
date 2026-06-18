# AI Agent Operating Rules

This checklist is the expanded operating guide for AI agents working in this
repository. `AGENTS.md` remains the shared instruction entrypoint; this document
keeps the longer rule checklist out of agent instruction files.

## Required Reading

- Root tasks: read `README.md`, `docs/index.md`, and `AGENTS.md`.
- Work under `korean_pii_guardrail_v0_2/`: also read
  `korean_pii_guardrail_v0_2/AGENTS.md`,
  `korean_pii_guardrail_v0_2/README.md`,
  `korean_pii_guardrail_v0_2/docs/12_SCOPE_CHANGE_NOTE.md`, and
  `korean_pii_guardrail_v0_2/docs/10_DEVELOPMENT_HANDOFF.md`.
- GitHub, PR, review, or evidence-management work: also read
  `korean_pii_guardrail_v0_2/docs/13_GITHUB_OPERATIONS_AND_EVIDENCE_GUIDE.md`.

## Non-Negotiable Scope

- Keep the v0.2 package single-turn only.
- Do not add RAG scanning, retrieval sanitization, retrieval document
  sanitizers, multi-turn monitoring, fragment ledgers, subject trackers, Redis
  TTL stores, previous-turn risk accumulation, full LLM judges, or human review
  dashboards unless the user explicitly changes project scope.
- Treat `PII/` as reference material for the active package. Do not import it
  from `korean_pii_guardrail_v0_2/` or copy older Layer 0 code into the package.
- Preserve raw text character offsets for detector spans. Internal spans must
  satisfy `span.text == raw_text[span.start:span.end]`.
- Keep entity, scoring, context, and policy behavior config-driven when config
  files own that behavior.

## Privacy And Secret Safety

- Never store raw PII in logs, exceptions, metrics, reports, audit events,
  screenshots, public response spans, evidence files, or AI context files.
- Do not commit API keys, tokens, credentials, local account names, machine
  paths that expose private identity, or machine-specific secrets.
- Evidence should use entity types, scores, reason codes, span lengths, masked
  examples, aggregate counts, and HMAC hashes instead of recoverable raw values.

## Change Checks

- Inspect existing docs, configs, schemas, source, and tests before editing.
- If a contract changes, update paired artifacts in the same task. Examples:
  entity config plus enum plus schema; scoring config plus scoring docs; policy
  config plus masking docs.
- For documentation-only changes, manually check links and paths before
  finishing.
- For package code changes, run the smallest relevant pytest target first; run
  the full package suite when practical with `python -m pytest`.

## Handoff Checklist

- Scope remains single-turn and excludes RAG/retrieval/multi-turn/dashboard work.
- No raw PII or secrets were introduced into code, docs, reports, logs, images,
  screenshots, or AI context.
- Detector spans preserve raw offsets.
- Config-owned behavior stayed config-driven.
- Documentation links and paths were checked, or relevant pytest targets were
  run for code changes.
