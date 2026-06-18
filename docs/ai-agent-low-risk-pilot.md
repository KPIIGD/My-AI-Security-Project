# AI Agent Low-Risk Pilot

This document records the stage 5 pilot for introducing AI development
automation through small, low-risk work. The pilot is intentionally
documentation-only unless a later human-approved task brief narrows the scope
to a synthetic-data test.

## Readiness Summary

The repository has enough stage 1-4 automation preparation to run a low-risk
pilot:

- `docs/agent-task-template.md` defines how to convert informal requests into
  scoped Agent Task Briefs.
- `docs/github-agent-workflow.md` defines Issue, branch, PR, review, and CI
  expectations.
- `docs/testing-and-verification-guide.md` defines verification standards by
  change type.
- `AGENTS.md` and `korean_pii_guardrail_v0_2/AGENTS.md` lock the active package
  scope, raw PII safety rules, and v0.2 single-turn boundary.

No missing stage 1-4 blocker was found for a documentation-only pilot.

## Low-Risk Candidate List

| Candidate | Risk | Edit scope | Verification |
|---|---|---|---|
| Add this low-risk pilot note and link it from the documentation index. | Very low | `docs/ai-agent-low-risk-pilot.md`, `docs/index.md` | Manual link/path check and `git diff --check`. |
| Summarize the existing package test structure for agents. | Low | One docs file or a short section in the testing guide | Manual path check; optionally run `cd korean_pii_guardrail_v0_2` and `python -m pytest` if package commands are changed. |
| Add an Agent Task Brief example for documentation-only work. | Low | `docs/agent-task-template.md` | Manual docs review and `git diff --check`. |
| Improve PR template wording for skipped checks and residual risk. | Low | `.github/pull_request_template.md` | Manual template review and `git diff --check`. |
| Add a tiny synthetic-data regression test for an existing documented edge case. | Medium | One test file only | Focused pytest target first, then full package pytest when practical. |

## Selected First Pilot Task

The selected first pilot is:

```text
Create docs/ai-agent-low-risk-pilot.md and link it from docs/index.md.
```

Selection reason:

- It is documentation-only.
- It does not change package behavior, tests, configs, schemas, APIs, CI, or
  generated artifacts.
- It exercises the agent workflow with clear verification.
- It creates the handoff point needed before assigning further low-risk work.

## Agent Task Brief

Task Title: Low-Risk AI Agent Pilot

### Goal

Create a concise low-risk pilot record for AI agent work and link it from the
project documentation index.

### Background

The project already has agent instructions, an Agent Task Brief template, a
GitHub workflow, and a testing/verification guide. Stage 5 should validate that
AI agent work starts with small, reviewable, low-risk tasks rather than broad
implementation.

### Scope

- Add `docs/ai-agent-low-risk-pilot.md`.
- Update `docs/index.md` with a link to the pilot document.
- Record low-risk candidates, selected first task, do-not-touch boundaries,
  verification method, safety checks, next candidates, and lessons learned.

### Out of Scope

- Package code changes.
- Test changes.
- Config, schema, API, or CI behavior changes.
- Release gate or evaluation metric changes.
- Any v0.2 scope expansion.

### Files To Read First

- `README.md`
- `docs/index.md`
- `AGENTS.md`
- `docs/agent-task-template.md`
- `docs/github-agent-workflow.md`
- `docs/testing-and-verification-guide.md`
- `korean_pii_guardrail_v0_2/AGENTS.md`
- `korean_pii_guardrail_v0_2/README.md`
- `korean_pii_guardrail_v0_2/docs/12_SCOPE_CHANGE_NOTE.md`
- `korean_pii_guardrail_v0_2/docs/10_DEVELOPMENT_HANDOFF.md`

### Allowed Files/Areas

- `docs/ai-agent-low-risk-pilot.md`
- `docs/index.md`

### Do Not Touch

- `korean_pii_guardrail_v0_2/src/`
- `korean_pii_guardrail_v0_2/tests/`
- `korean_pii_guardrail_v0_2/configs/`
- `korean_pii_guardrail_v0_2/schemas/`
- `korean_pii_guardrail_v0_2/api/`
- `PII/`
- `output/`, `outputs/`, and `build/`
- production systems, secrets, API keys, credentials, external accounts, and
  destructive commands

### Acceptance Criteria

- The pilot document exists at `docs/ai-agent-low-risk-pilot.md`.
- The document lists 3-5 low-risk candidates with risk, edit scope, and
  verification.
- The selected first pilot task is documented with a brief and safety boundary.
- `docs/index.md` links to the new pilot document.
- Documentation links and paths are manually checked.

### Verification

- Manual link/path check for `docs/ai-agent-low-risk-pilot.md`.
- `git diff --check`.
- No package pytest is required because this is documentation-only and does not
  change commands, code, configs, schemas, or tests.

### Security/PII Rules

- Do not store raw PII in logs, exceptions, metrics, reports, audit events,
  screenshots, public response spans, evidence files, or AI context files.
- Do not commit API keys, tokens, credentials, local account names,
  machine-specific secrets, or private paths.
- Keep v0.2 single-turn only.
- Do not add RAG scanning, retrieval sanitizers, multi-turn monitoring,
  fragment ledgers, subject trackers, Redis TTL stores, full LLM judges, or
  human review dashboards.
- Do not connect `PII/` as an active package dependency.

### Expected Output

- Files read.
- Files changed.
- Pilot summary.
- Verification performed.
- Remaining TODOs.

### Open Questions

- None for this documentation-only pilot.

## Verification Method

For this pilot:

- Check that `docs/index.md` links to this file.
- Check that no code, test, config, schema, API, generated artifact, production
  system, or external account was changed.
- Run `git diff --check`.

For future pilots:

- Documentation-only tasks use manual link/path checks plus `git diff --check`.
- Test-only synthetic data tasks use the smallest focused pytest target first,
  then full package pytest when practical.
- Any config/schema/API task must update paired artifacts and use focused
  contract tests.

## Raw PII And Secret Confirmation

This pilot must not include:

- raw personal data;
- raw detector span values;
- recoverable token maps;
- API keys, tokens, credentials, or local account names;
- private machine paths beyond repository paths already used by the project.

Safe evidence formats are case IDs, entity types, span lengths, aggregate
counts, command names, pass/fail status, and masked or synthetic examples.

## Next Pilot Candidates

Recommended next low-risk tasks:

1. Add one documentation-only Agent Task Brief example to
   `docs/agent-task-template.md`.
2. Add a short existing-test structure summary to
   `docs/testing-and-verification-guide.md`.
3. Review `.github/pull_request_template.md` after the first pilot PR and tune
   only wording that reviewers found unclear.
4. Add a tiny synthetic-data test only if a human selects a specific existing
   documented edge case and approves the focused pytest target.

## Lessons Learned

- Start with documentation-only work when validating agent workflow.
- Keep the first pilot small enough to review in one PR.
- Make the verification command explicit before editing.
- Treat generated artifacts, raw data, and `PII/` as out of scope unless the
  task brief explicitly allows them.
- If a task requires code behavior changes, move it out of the first pilot and
  require a focused test plan first.
