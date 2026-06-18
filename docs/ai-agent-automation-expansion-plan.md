# AI Agent Automation Expansion Plan

This document defines how to expand AI development automation after the initial
safety, workflow, testing, knowledge-management, and security baselines are in
place. It is a roadmap and operating standard only. It does not implement code,
enable external integrations, change GitHub settings, or configure Slack,
Drive, Obsidian, MCP, deployment, or production systems.

## Readiness Summary

The repository is ready for a controlled expansion plan because it now has:

- shared agent entrypoints in `AGENTS.md` and `docs/index.md`;
- scoped work conversion in `docs/agent-task-template.md`;
- GitHub work rules in `docs/github-agent-workflow.md`;
- verification rules in `docs/testing-and-verification-guide.md`;
- a low-risk pilot record in `docs/ai-agent-low-risk-pilot.md`;
- knowledge routing in `docs/knowledge-management-workflow.md`;
- a security baseline in `docs/ai-agent-security-policy.md`;
- an active package pytest workflow for `korean_pii_guardrail_v0_2/`;
- a PR template and Agent Task Issue template.

Expansion should start with summary, draft, checklist, and validation helpers.
Automation that writes code, changes policy/config, accesses secrets, changes
external settings, or acts on production remains out of scope until a separate
human-approved task changes that boundary.

## Expansion Principles

- Automate suggestions before actions.
- Keep every automation task brief-scoped.
- Prefer documentation-only and PR/Issue helper automation first.
- Require human review for AI-generated summaries, risk calls, and test
  suggestions.
- Treat CI failure analysis as hypotheses, not final root cause.
- Keep code modification automation disabled until explicitly approved.
- Keep `korean_pii_guardrail_v0_2/` single-turn only.
- Keep RAG scanning, retrieval sanitizers, multi-turn monitoring, dashboards,
  fragment ledgers, subject trackers, Redis TTL stores, full LLM judges, and
  production key management out of automation candidates.
- Never include raw PII, secrets, API keys, tokens, credentials, or private
  values in automation inputs, outputs, logs, PRs, or run summaries.
- Do not auto-merge, auto-deploy, use production write permissions, access
  secrets, or auto-approve destructive commands.

## Candidate Automation Inventory

| Candidate | Risk | Inputs | Output | Verification |
|---|---|---|---|---|
| GitHub Issue to Agent Task Brief draft | Low | Issue text, repository docs, allowed files | Draft brief with scope, out-of-scope, verification, security checks | Human confirms no `Unknown` or `Needs confirmation` blocks before work starts. |
| PR summary draft | Low | PR diff, PR template, task brief | Draft summary, scope, tests, risk points | Human reviewer checks against diff before posting or merging. |
| PR review checklist draft | Low | PR diff, package rules, testing guide | Checklist of files, risks, tests, security gates | Human reviewer verifies completeness. |
| CI failure log summary | Medium | CI check name, safe log summary, changed files | Failure classification and likely causes | Human confirms against CI logs; no auto-fix. |
| Missing test candidate suggestions | Medium | Diff, test tree, testing guide | Suggested focused test targets or test gaps | Human selects tests; no automatic code or test edit by default. |
| Documentation link/path freshness check | Low | Docs index and changed docs | Broken or stale path list | Manual path check; no content rewrite unless scoped. |
| Release note draft | Low | Merged PR summaries, safe changelog inputs | Draft release note | Human verifies scope, claims, and metrics. |
| Evaluation result summary | Medium | Safe reports, aggregate metrics, artifact paths | Summary without raw values | Human verifies report source and no raw PII. |
| Agent run log summary | Low | Task brief, commands, tests, changed files | Safe run log with exposure fields | Check against `docs/ai-agent-security-policy.md`. |
| Decision record draft | Low | Safe source summary, PR/Issue context | Draft decision record | Human confirms decision wording and evidence. |

## Risk-Based Operating Rules

| Risk level | Allowed by default | Restrictions | Required approval |
|---|---|---|---|
| Low | Drafts, summaries, checklists, link/path checks, release-note drafts, safe run logs, decision drafts | No automatic posting if the destination is external unless the user asks. No raw PII or secrets. | Human review before treating output as official. |
| Medium | CI failure hypotheses, test gap suggestions, small docs/test PR planning | No auto-fix. No code/test edit unless the task brief explicitly allows it. | Human selection of follow-up action and verification target. |
| High | Code auto-fix, config/policy/schema/API edits, security/auth/data changes | Disabled by default. Must be narrowed to a branch/PR task with tests and reviewer focus. | Explicit human approval before work starts. |
| Prohibited by default | Auto merge, auto deploy, production write, secret access, raw PII handling, destructive command auto-approval, out-of-scope feature implementation | Do not run or plan as autonomous automation. | Requires a separate scope and security decision before consideration. |

## Phase 1: Documentation And Summary Automation

First automation targets:

1. Documentation link/path freshness check.
2. PR summary draft.
3. Agent run log summary.

Phase 1 output is advisory only. It may create drafts or findings, but a human
must approve official use.

Phase 1 allowed files and surfaces:

- `docs/`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/`
- PR descriptions and comments when explicitly requested by the user

Phase 1 validation:

- manual link/path check;
- `git diff --check` for repository document edits;
- raw PII and secret pattern review when summaries include evidence;
- human review before posting externally.

## Phase 2: PR And Issue Helper Automation

Phase 2 may add:

- GitHub Issue to Agent Task Brief draft;
- PR review checklist draft;
- decision record draft;
- release note draft from already-reviewed PR summaries.

Phase 2 remains draft-only. It must not merge, approve, label as final, or edit
remote settings automatically.

## Phase 3: CI Failure Analysis Helper

Phase 3 may summarize CI failures and suggest likely causes.

Limits:

- The output must say "candidate cause" or equivalent.
- It must not claim final root cause without human confirmation.
- It must not auto-edit code or tests.
- It must not paste full logs if logs contain sensitive output.
- It must include the check name, safe error category, likely affected files,
  suggested next command, and residual risk.

## Phase 4: Test Suggestion And Small Test Assistance

Phase 4 may suggest missing tests and, with explicit task scope, assist with
small synthetic-data test additions.

Limits:

- Use synthetic data only.
- Prefer one focused test file and one focused pytest target.
- Do not touch production data, generated artifacts, or broad evaluation
  pipelines.
- Run focused pytest first and full package pytest when practical.
- Keep raw offset, raw PII safety, config-driven behavior, and v0.2 single-turn
  scope in the acceptance criteria.

## Phase 5: Limited Code Modification Assistance

Phase 5 is not enabled by this document. It is a future option only.

Before Phase 5 can start, the team must create a separate decision or task
brief that defines:

- allowed modules;
- forbidden modules;
- maximum file count or diff size;
- required focused and full tests;
- rollback plan;
- reviewer owner;
- security gates;
- explicit exclusion of production writes, secrets, raw PII, and out-of-scope
  features.

## Do Not Automate

Do not automate these actions by default:

- auto merge;
- auto deploy;
- production write;
- destructive command approval;
- secret access, creation, rotation, or printing;
- raw PII collection, copying, summarization, or storage;
- broad Slack, Drive, browser, or MCP ingestion;
- GitHub repository settings or branch protection changes;
- authentication, authorization, billing, data migration, or security policy
  changes;
- config/policy/schema/API behavior edits without an explicit scoped task;
- RAG scanning, retrieval sanitizers, multi-turn monitoring, dashboards,
  fragment ledgers, subject trackers, Redis TTL stores, full LLM judges, or
  production key management.

## Input, Output, And Validation Standard

Each automation must define:

- allowed input sources;
- forbidden input sources;
- output format;
- where the output may be stored;
- required human review point;
- verification command or manual check;
- raw PII and secret safety check;
- stop condition.

Safe default output locations:

- PR body draft;
- GitHub Issue draft;
- safe run log summary;
- docs-only Markdown file;
- decision record draft.

Unsafe default output locations:

- production systems;
- external account writes;
- unreviewed Slack or Drive posts;
- generated reports containing raw values;
- AI memory or context files containing raw source material.

## Raw PII And Secret Non-Exposure Standard

Automation inputs and outputs must not include:

- raw personal data;
- raw detector span text;
- full sensitive terminal output;
- API keys, tokens, credentials, cookies, or private keys;
- local account names or private machine-specific identifiers;
- recoverable token maps;
- unredacted screenshots;
- non-synthetic test payloads.

Allowed substitutes:

- synthetic examples;
- case IDs;
- entity types;
- span lengths;
- aggregate metrics;
- command names and pass/fail status;
- masked or non-reversible summaries.

If sensitive material appears in an input, the automation must stop copying it
and report only `blocked` or `redacted` status in the run log.

## Human Approval Criteria

Human approval is required before:

- converting a draft into an official PR comment, release note, decision, or
  merge signal;
- opening or updating external service content;
- creating a branch or PR from an automation proposal;
- adding or modifying tests;
- editing code, config, schema, API, workflow, security, authentication, data,
  or policy files;
- running destructive commands;
- using production write access;
- accessing or handling secrets;
- expanding v0.2 scope.

Approval must be explicit, task-specific, and recorded without raw PII or
secrets.

## Failure, Rollback, And Stop Criteria

Stop automation when:

- raw PII or a secret is detected in input or output;
- the requested task requires production write access;
- a destructive command is needed;
- the automation needs broad connector access;
- the output would change code, tests, config, schema, API, policy, or CI
  without explicit scope;
- CI logs contain sensitive values;
- the automation cannot identify a safe verification method;
- the task would add out-of-scope v0.2 features.

Rollback for documentation-only automation is reverting the draft or follow-up
edit before merge. For PR/Issue drafts, mark the output as draft and do not
publish externally until reviewed. For any suspected sensitive exposure, follow
`docs/ai-agent-security-policy.md`.

## Agent Run Log Standard

Every automation run that produces a durable draft should record:

- task or issue/PR link;
- automation type;
- agent/tool name;
- started and completed time;
- input sources as safe summaries;
- files read summary;
- files changed list, if any;
- commands or checks run;
- tests or manual verification result;
- approvals requested;
- security checks;
- `raw_pii_exposure`: `none`, `blocked`, or `redacted`;
- `secrets_exposure`: `none`, `blocked`, or `redacted`;
- reviewer decision;
- follow-up.

Do not record raw PII, secrets, full sensitive logs, recoverable token maps, or
private values in the run log.

## Success Metrics

Track success with safe aggregate metrics:

- PR description drafting time decreases.
- CI failure triage time decreases.
- documentation link errors decrease.
- missing test-result records decrease.
- reviewer risk focus becomes clearer.
- raw PII exposure count remains `0`.
- secret exposure count remains `0`.
- scope violation count remains `0`.
- automation output rejection rate stays visible and decreases over time.

## Next Pilot Tasks

Recommended next executable pilots:

1. Documentation link/path freshness check for `docs/index.md` and the new AI
   automation docs.
2. PR summary draft template trial on one documentation-only PR.
3. Agent run log summary draft using an existing safe task brief and command
   result summary.

Each pilot should be documentation-only or draft-only, record verification, and
avoid external service writes unless a human explicitly requests the write.
