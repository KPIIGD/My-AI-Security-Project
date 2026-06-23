# Testing And Verification Guide

This guide fixes the minimum verification standard an AI agent must satisfy
before claiming work is complete in this repository.

It does not add product functionality. It defines what to run, what to inspect,
and what to record for documentation, package code, config/schema/API, and
security-sensitive guardrail changes.

## Source Of Truth

- Root instructions: `AGENTS.md`
- Agent workflow: `docs/agent-task-template.md`
- GitHub workflow: `docs/github-agent-workflow.md`
- Package rules: `korean_pii_guardrail_v0_2/AGENTS.md`
- Package handoff: `korean_pii_guardrail_v0_2/docs/10_DEVELOPMENT_HANDOFF.md`
- Scope lock: `korean_pii_guardrail_v0_2/docs/12_SCOPE_CHANGE_NOTE.md`
- GitHub/evidence guide:
  `korean_pii_guardrail_v0_2/docs/13_GITHUB_OPERATIONS_AND_EVIDENCE_GUIDE.md`

## Current Test And CI Structure

The active package is `korean_pii_guardrail_v0_2/`.

- Tests live under `korean_pii_guardrail_v0_2/tests/`.
- Pytest configuration lives in `korean_pii_guardrail_v0_2/pyproject.toml`.
- Full local package test command:

```bash
cd korean_pii_guardrail_v0_2
python -m pytest
```

- Focused local package test pattern:

```bash
cd korean_pii_guardrail_v0_2
python -m pytest tests/test_contract_smoke.py
```

The root `Makefile` is for the older `PII/` research/evaluation stack.
`make test` runs `PII/layer_0` tests, and `make all` runs the broad historical
evaluation pipeline. Do not treat those commands as the default verification
path for the active v0.2 package.

Current GitHub workflows:

- `.github/workflows/layer_0_tests.yml`: legacy `PII/layer_0` tests.
- `.github/workflows/claude-review.yml`: optional Claude code review.
- `.github/workflows/security-review.yml`: optional Claude security review.
- `.github/workflows/korean_pii_guardrail_v0_2_tests.yml`: active package
  pytest workflow for v0.2 package changes.

## Verification Matrix

| Change type | Required verification | Recommended command or check | PR record |
|---|---|---|---|
| Documentation only | Manually check edited links and paths. Confirm no code/config/schema behavior changed. Confirm no raw PII, secrets, private paths, or out-of-scope v0.2 feature claims were added. | Manual link/path review. | List edited docs and say links/paths were checked manually. |
| Package code | Run the smallest relevant pytest target first. Run full package pytest when practical. Inspect raw offset, raw PII, secret, and single-turn scope impact. | `cd korean_pii_guardrail_v0_2` then `python -m pytest <target>` and, when practical, `python -m pytest`. | Exact command, pass/fail count, skipped checks with reason and residual risk. |
| Config/schema/API | Update paired artifacts together. Run contract/schema/API-facing focused tests, then full package pytest when practical. | Examples: `python -m pytest tests/test_contract_smoke.py tests/test_console_api.py tests/test_detector_config.py`. | Changed contract files, paired docs/configs/schemas, exact tests and result. |
| Detector/masking/policy/audit | Verify raw span offsets, suffix handling, resolver behavior, public response safety, audit event safety, and config-driven behavior. Run affected focused tests and full package pytest when practical. | Examples: `python -m pytest tests/test_regex_detectors.py tests/test_span_resolver.py tests/test_masker.py tests/test_policy.py tests/test_audit_logger.py tests/test_pipeline.py`. | Entity/policy/audit impact, raw PII safety result, exact tests and result. |
| Release or evaluation claim | Do not rely only on unit tests. Run or cite the relevant release/evaluation artifact. If the command is too slow or environment-bound, explain that. | Escalated command when needed: `python scripts/run_release_gate.py --config-dir configs --progress-interval 500`. | Report artifact path, status, metrics, or why the release gate was not rerun. |
| GitHub workflow/template | Check YAML/template intent manually. If a workflow command is executable locally, run the equivalent local command. | Manual workflow review plus the local package pytest command when relevant. | Workflow name, trigger scope, local command result or reason not run. |

## Required Security And Scope Checks

Every agent completion report and PR must confirm:

- Raw PII is not stored in logs, exceptions, metrics, reports, audit events,
  screenshots, public response spans, comments, evidence files, or AI context.
- Evidence uses safe fields such as case IDs, entity types, score/risk/action,
  reason codes, span lengths, aggregate metrics, masked values, or HMAC hashes.
- No API keys, tokens, credentials, local account names, private machine paths,
  `.env` files, or machine-specific secrets are committed.
- v0.2 remains single-turn.
- RAG scanning, retrieval sanitizers, retrieval document sanitizers, multi-turn
  monitoring, fragment ledgers, subject trackers, Redis TTL stores,
  previous-turn risk accumulation, full LLM judges, production key management
  systems, and human review dashboards are not added unless the user explicitly
  approves a project scope change.
- Detector spans preserve raw text character offsets. Internal spans must keep
  `span.text == raw_text[span.start:span.end]`.
- Entity, scoring, context, and policy behavior stays config-driven when config
  files own that behavior.
- `PII/` remains reference-only for the active package unless integration is
  explicitly requested.

## PR Test Result Requirements

The PR body must record exact verification evidence. Do not write only
`tests passed`.

Use this shape:

```text
Command:
cd korean_pii_guardrail_v0_2
python -m pytest tests/test_contract_smoke.py

Result:
3 passed
```

For manual checks:

```text
Documentation-only:
Manually checked docs/index.md links to docs/testing-and-verification-guide.md.
No package code, config, schema, API, generated artifact, or workflow behavior
was changed.
```

If tests were not run, record:

- the exact command that should have been run;
- why it was not run;
- what was checked instead;
- the remaining risk;
- who should run or confirm the missing check before merge.

## CI Failure Flow

When CI, tests, or security checks fail:

1. Do not merge.
2. Read the failing check summary and logs.
3. Classify the failure as a code regression, test expectation drift,
   environment/flaky failure, dependency issue, or secret/security finding.
4. Fix on the same branch only when the fix is inside the approved task scope.
5. If the fix expands scope, update the Issue or create a new Issue first.
6. Re-run the smallest relevant local check, then the affected CI path.
7. Record the failure cause and new verification result in the PR.

Do not hide failures by deleting tests, weakening security checks, removing
required verification, or marking a failed security finding as accepted without
human approval.

## Agent Completion Gate

Before an AI agent says the task is complete, it must report:

- files read;
- files created or modified;
- current test/CI structure when the task concerns verification;
- change-type verification criteria applied;
- exact commands run and results;
- checks not run, with reason and residual risk;
- raw PII, secret, credential, and v0.2 single-turn scope confirmation;
- remaining TODOs for the next low-risk agent task.
