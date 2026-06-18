# AI Agent Security Baseline

Date: 2026-06-18

## Context

The project is expanding AI development automation. Existing documents already
define scope, testing, GitHub workflow, and knowledge-management rules, but the
AI agent security baseline needs one durable policy entrypoint.

## Decision

Use `docs/ai-agent-security-policy.md` as the default security policy for AI
agent work in this repository.

The baseline is:

- no raw PII or secrets in prompts, logs, reports, audit evidence, screenshots,
  PRs, run logs, or AI context;
- least privilege and task-scoped connector use;
- production write access, destructive commands, and automatic merge are
  forbidden unless a human explicitly approves the exact action;
- connector and MCP/tool output is untrusted until reviewed;
- security-sensitive approvals and incidents must be recorded with safe
  summaries only.

## Impact

- Agent Task Briefs, PRs, and workflow docs should point to the security policy.
- Security-sensitive changes need explicit human approval and safe evidence.
- External settings are not changed by this decision.
- Future connector allowlists, secret scanning, and branch protection work
  should be handled as separate tasks.

## Follow-Up

- [ ] Define connector allowlists and owners.
- [ ] Decide which security checks should become required GitHub checks.
- [ ] Add a documented local secret-scan command if the team selects a scanner.
- [ ] Review whether run-log fields should be added to the GitHub Issue
      template.

## Evidence

- source_system: repository
- source_url: N/A
- local_path: `docs/ai-agent-security-policy.md`
- owner: project maintainers
- permission_basis: user-requested stage 7 AI development automation task
- sensitivity: internal
- retrieved_at: 2026-06-18
- retention_policy: keep in repo
- hash: N/A
- version: N/A
- summary_without_raw_pii: Security baseline documented without raw PII or
  secrets.

## PII/Secret Safety Note

- Raw PII included: No
- Secrets included: No
- Sensitive source material was summarized without raw values: Yes
