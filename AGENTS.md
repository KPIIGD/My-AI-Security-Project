# Project Agent Instructions

## Scope

These instructions apply to the repository root:

`C:\Users\andyw\Desktop\My-AI-Security-Project`

The primary active package is:

`korean_pii_guardrail_v0_2/`

Do not reorganize folders or move files unless the user explicitly asks for a
structure migration. Prefer adding indexes and routing notes over moving
existing artifacts.

## Repository Map

- `korean_pii_guardrail_v0_2/`: active Korean PII Guardrail v0.2 single-turn package.
- `PII/`: older five-layer research/evaluation stack. Treat as reference only unless integration is explicitly requested.
- `paper/`: paper, presentation, and publication materials.
- `scripts/`: root-level helper scripts for reports, HWP/PPT artifacts, and project outputs.
- `presentations/`: presentation decks and related notes.
- `images/` if present: images used by reports or presentations.
- `output/`, `outputs/`, `build/`: generated artifacts. Do not edit by default.

## Start Of Work

For any task started from the repository root, read:

1. `README.md`
2. `docs/index.md`
3. This `AGENTS.md`

For code, tests, configs, schemas, or package docs under
`korean_pii_guardrail_v0_2/`, also read:

1. `korean_pii_guardrail_v0_2/AGENTS.md`
2. `korean_pii_guardrail_v0_2/README.md`
3. `korean_pii_guardrail_v0_2/docs/12_SCOPE_CHANGE_NOTE.md`
4. `korean_pii_guardrail_v0_2/docs/10_DEVELOPMENT_HANDOFF.md`

For GitHub, PR, review, or evidence-management tasks, also read:

`korean_pii_guardrail_v0_2/docs/13_GITHUB_OPERATIONS_AND_EVIDENCE_GUIDE.md`

## Core Project Rules

- Keep the v0.2 package single-turn only.
- Do not implement RAG scanning, retrieval sanitization, multi-turn session monitoring, fragment ledger, subject tracker, Redis TTL store, full LLM judge, or human review dashboard unless the user explicitly changes scope.
- Never store raw PII in logs, exceptions, metrics, reports, audit events, screenshots, public response spans, or AI context files.
- Never commit API keys, tokens, credentials, local account names, or machine-specific secrets.
- Preserve raw text character offsets for detector spans.
- Treat `PII/` as reference material for the active package, not as an import dependency.
- Keep behavior config-driven when configs own the entity, scoring, context, or policy behavior.

## Documentation Rules

- Use Markdown for durable project knowledge.
- Use `docs/ai-agent-operating-rules.md` for the expanded AI agent operating checklist.
- Keep AI instruction files lean. Put detailed explanations in `docs/`, then link to them.
- Use one H1 per Markdown file.
- Prefer kebab-case for new human-facing documentation filenames.
- Record durable project decisions in `docs/decisions/`.
- Update `docs/index.md` when adding important docs, decisions, or agent workflow files.

## Tool-Specific Agent Files

This `AGENTS.md` is the source of truth for shared agent behavior.

Tool-specific files such as `CLAUDE.md`, `GEMINI.md`, Cursor rules, or
`.github/copilot-instructions.md` should stay thin and point back to this file.
Do not copy long instructions into every tool-specific file.

## Verification

Before finishing changes:

- For documentation-only changes, check links and paths manually.
- For package code changes, run the smallest relevant pytest target first.
- Run the full package test suite when practical:

```bash
cd korean_pii_guardrail_v0_2
python -m pytest
```
