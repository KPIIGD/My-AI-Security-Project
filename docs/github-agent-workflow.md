# GitHub Agent Workflow

This document fixes the local workflow for AI-assisted GitHub work in this
repository. It describes templates and operating rules only; it does not change
remote GitHub branch protection, required checks, or reviewer settings.

## Workflow

Use this sequence for user requests, Slack requests, or agent-proposed work:

```text
User or Slack request
-> Agent Task Brief
-> GitHub Issue
-> branch work
-> Pull Request
-> CI, tests, and security checks
-> CODEOWNERS, required reviewer, and human review
-> merge
-> decisions and evidence documented
```

Agents may draft briefs, issues, branches, PR descriptions, and evidence
summaries. Humans own final approval and merge decisions.

Automation expansion follows `docs/ai-agent-automation-expansion-plan.md`.
Start with draft-only summaries, checklists, and link/path checks. Do not
enable code-edit, merge, deploy, production-write, secret-access, raw-PII, or
destructive automation without a separate human-approved scope decision.

## Issue Creation Criteria

Create a GitHub Issue before agent work when any of these are true:

- The task changes code, tests, configs, schemas, APIs, package docs, GitHub
  workflow files, or durable project docs.
- The task is expected to create a branch or PR.
- The request came from Slack or another informal channel and needs durable
  tracking.
- The task has open questions, security risk, generated evidence, or reviewer
  decisions to preserve.
- The task could affect v0.2 scope, raw PII handling, secrets, policy behavior,
  or evaluation evidence.

Tiny read-only inspections may skip an Issue, but the final answer should still
state what was inspected.

## Agent Task Brief To Issue

Use `.github/ISSUE_TEMPLATE/agent-task.yml` for agent-backed work. The Issue
should contain or link the Agent Task Brief from `docs/agent-task-template.md`.

Required mapping:

- Brief `Goal` -> Issue title and original request summary.
- Brief `Scope` -> Issue allowed files or areas.
- Brief `Out of Scope` and `Do Not Touch` -> Issue forbidden work.
- Brief `Acceptance Criteria` -> Issue completion criteria.
- Brief `Verification` -> Issue verification plan.
- Brief `Security/PII Rules` -> Issue safety checklist.
- Brief `Open Questions` -> Issue open questions.

If the brief contains `Unknown` or `Needs confirmation` for goal, scope,
verification, or security-sensitive permissions, do not start branch work until
a human answers or narrows the task.

## Branch Rules

Do not push agent changes directly to `main`. Use branch and PR flow.

Recommended branch names:

- `docs/<short-topic>` for documentation and templates.
- `feature/<short-topic>` for new package functionality.
- `fix/<short-topic>` for bug fixes.
- `chore/<short-topic>` for repository maintenance.

Keep one branch focused on one Issue or closely related brief. Avoid mixing
template work, code behavior changes, generated artifacts, and report writing
in the same branch.

## Pull Request Requirements

Every PR should use `.github/pull_request_template.md` and include:

- Change summary.
- Work scope.
- Related Issue or Agent Task Brief.
- Exact test or verification results.
- Agent security policy confirmation using `docs/ai-agent-security-policy.md`.
- Raw PII non-exposure confirmation.
- Secret, API key, token, and credential non-commit confirmation.
- v0.2 single-turn scope confirmation.
- Out-of-scope feature confirmation for RAG, retrieval sanitizer, multi-turn
  monitoring, dashboards, fragment ledgers, subject trackers, Redis TTL stores,
  and full LLM judges.
- Production write, destructive command, and automatic merge non-use
  confirmation, or exact human approval evidence.
- Connector/MCP/tool output untrusted-data handling confirmation when external
  tools or connectors were used.
- Config-driven principle confirmation when entity, scoring, context, or policy
  behavior changed.
- Documentation update status.
- Reviewer focus and risk points.

PRs should target `main` unless a human explicitly defines a different base.

## Test And Verification Records

Record exact commands and results in the PR body. Do not write vague phrases
such as "tests passed" without the command.

Examples:

```text
python -m pytest tests/test_contract_smoke.py
12 passed
```

```text
Documentation-only: manually checked docs/index.md links to
docs/github-agent-workflow.md and .github/pull_request_template.md exists.
```

For package code changes, run the smallest relevant pytest target first. Run
the full package test suite when practical:

```bash
cd korean_pii_guardrail_v0_2
python -m pytest
```

If tests were not run, the PR must state why and list residual risk.

## Security And Scope Gates

Every Issue and PR must check these gates:

- `docs/ai-agent-security-policy.md` was followed for AI-assisted work.
- No raw PII in logs, exceptions, metrics, reports, audit events, screenshots,
  public response spans, evidence files, comments, or AI context.
- No API keys, tokens, credentials, local account names, machine-specific
  secrets, or private paths committed.
- v0.2 remains single-turn.
- No RAG scanning, retrieval sanitizer, multi-turn monitoring, fragment ledger,
  subject tracker, Redis TTL store, full LLM judge, production key-management
  system, or human review dashboard unless a human explicitly approves a scope
  change.
- Detector spans preserve raw text offsets when detector behavior changes.
- Entity, scoring, context, and policy behavior remain config-driven when
  config owns the behavior.
- `PII/` remains reference-only unless integration is explicitly approved.
- Production write permission was not used.
- Destructive commands were not used, or exact human approval is recorded.
- Slack, Drive, GitHub connector, MCP, browser, web, and terminal output was
  treated as untrusted and retained only as safe summaries.

Production deploys, destructive commands, branch protection changes, repository
settings changes, secret creation, and external account writes are never
automatically approved by an Issue, PR, or AI agent.

## PR And CI Security Flow

Use this security flow for agent-assisted PRs:

1. Confirm the task brief names allowed files, forbidden files, verification,
   and security rules.
2. Inspect the diff for raw PII, secrets, production writes, destructive
   commands, scope expansion, and connector/tool output copied verbatim.
3. Run the required focused tests or manual documentation checks.
4. Run or record the applicable CI/security checks.
5. If a check fails, stop merge and follow the CI failure flow.
6. Record safe run-log evidence only: task or PR link, files changed, commands
   run, test result, approvals requested, security checks, exposure status,
   reviewer decision, and follow-up.

Do not record raw PII, secrets, sensitive terminal output, raw payloads,
recoverable token maps, or screenshots with sensitive values in run logs.

## Human Review And CODEOWNERS

AI agents may prepare changes and review notes, but they do not approve their
own work. A human reviewer is the final approval owner.

`.github/CODEOWNERS` is currently a placeholder because no concrete GitHub
username or team owner is encoded in this repository. To enforce code-owner
review:

1. Replace the placeholder comments with valid GitHub users or teams.
2. Enable branch protection or rulesets for `main`.
3. Require pull request review and code-owner review.
4. Keep CI and security checks required before merge.

Until those remote settings are configured, CODEOWNERS is documentation and
setup guidance, not an active enforcement mechanism.

## CI Failure Flow

When CI, tests, or security checks fail:

1. Do not merge.
2. Read the failing check summary and logs.
3. Classify the failure as code regression, test expectation drift,
   environment/flaky failure, dependency issue, or secret/security finding.
4. Fix on the same branch when the fix is within the Issue scope.
5. If the fix expands scope, update the Issue or create a new Issue.
6. Re-run the smallest relevant check, then the affected CI path.
7. Record the failure cause and new verification result in the PR.

Never hide CI failures by deleting tests, weakening security checks, or
removing required verification without human approval.

## Decisions And Evidence

Record durable decisions or evidence when a task changes project behavior,
review policy, evaluation claims, security posture, or milestone scope.

Use:

- `docs/decisions/` for durable decisions from review, professor feedback,
  Slack, meetings, or scope changes.
- The relevant package docs for implementation contracts and handoff rules.
- PR descriptions for short-lived verification evidence.

Evidence must not include raw PII, secrets, full private logs, recoverable token
maps, or screenshots containing sensitive values. Prefer case IDs, entity
types, counts, masked examples, command names, pass/fail status, and aggregate
metrics.

## Local Template Files

- Issue template: `.github/ISSUE_TEMPLATE/agent-task.yml`
- Pull request template: `.github/pull_request_template.md`
- CODEOWNERS placeholder: `.github/CODEOWNERS`
- Task brief template: `docs/agent-task-template.md`
