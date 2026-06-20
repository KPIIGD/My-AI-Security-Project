# Project Documentation Index

This index is the shared map for people and AI agents working in this
repository. Use it to find the right source of truth before reading many files.

## Agent Entrypoints

- `AGENTS.md`: shared root instructions for all AI agents.
- `CLAUDE.md`: thin Claude adapter that points back to `AGENTS.md`.
- `GEMINI.md`: thin Gemini adapter that points back to `AGENTS.md`.
- `.github/copilot-instructions.md`: thin GitHub Copilot adapter.
- `llms.txt`: compact LLM-oriented index for external tools or documentation crawlers.
- `korean_pii_guardrail_v0_2/AGENTS.md`: package-specific rules for the active v0.2 implementation.

## Repository Areas

- `korean_pii_guardrail_v0_2/`: active Korean PII Guardrail v0.2 single-turn package.
- `PII/`: older five-layer research/evaluation stack and Layer 0 reference material.
- `paper/`: paper, presentation, and publication materials.
- `scripts/`: root helper scripts for generated reports and document artifacts.
- `presentations/`: presentation decks and related notes.
- `images/` if present: images used by reports and presentations.
- `output/`, `outputs/`, `build/`: generated artifacts.

## Active Package Sources

Start here for implementation work:

- `korean_pii_guardrail_v0_2/README.md`
- `korean_pii_guardrail_v0_2/MANIFEST.md`
- `korean_pii_guardrail_v0_2/docs/12_SCOPE_CHANGE_NOTE.md`
- `korean_pii_guardrail_v0_2/docs/10_DEVELOPMENT_HANDOFF.md`
- `korean_pii_guardrail_v0_2/docs/13_GITHUB_OPERATIONS_AND_EVIDENCE_GUIDE.md`

Core package directories:

- `korean_pii_guardrail_v0_2/src/`
- `korean_pii_guardrail_v0_2/tests/`
- `korean_pii_guardrail_v0_2/configs/`
- `korean_pii_guardrail_v0_2/schemas/`
- `korean_pii_guardrail_v0_2/api/`
- `korean_pii_guardrail_v0_2/data/`

## Documentation Routing

- AI agent operating rules: `docs/ai-agent-operating-rules.md`
- Agent task brief template: `docs/agent-task-template.md`
- GitHub agent workflow: `docs/github-agent-workflow.md`
- Testing and verification guide: `docs/testing-and-verification-guide.md`
- AI agent low-risk pilot: `docs/ai-agent-low-risk-pilot.md`
- AI development automation research: `docs/ai-development-automation-research.md`
- AI agent security policy: `docs/ai-agent-security-policy.md`
- AI agent automation expansion plan: `docs/ai-agent-automation-expansion-plan.md`
- Knowledge management workflow: `docs/knowledge-management-workflow.md`
- Decision record guide: `docs/decisions/README.md`
- AI agent security baseline decision: `docs/decisions/2026-06-18-ai-agent-security-baseline.md`
- GitHub org migration decision: `docs/decisions/2026-06-20-github-org-migration.md`
- GitHub org migration runbook (owner steps): `docs/github-org-migration-runbook.md`
- Project plan: `korean_pii_guardrail_v0_2/docs/00_PROJECT_PLAN.md`
- Requirements: `korean_pii_guardrail_v0_2/docs/01_REQUIREMENTS_SPEC.md`
- Architecture: `korean_pii_guardrail_v0_2/docs/02_ARCHITECTURE_SPEC.md`
- Scoring policy: `korean_pii_guardrail_v0_2/docs/03_SCORING_POLICY_SPEC.md`
- Context policy: `korean_pii_guardrail_v0_2/docs/04_CONTEXT_POLICY_SPEC.md`
- Masking policy: `korean_pii_guardrail_v0_2/docs/05_MASKING_POLICY_SPEC.md`
- Interface/API contract: `korean_pii_guardrail_v0_2/docs/06_INTERFACE_SPEC.md`
- Implementation roadmap: `korean_pii_guardrail_v0_2/docs/07_IMPLEMENTATION_ROADMAP.md`
- Evaluation plan: `korean_pii_guardrail_v0_2/docs/08_EVALUATION_PLAN.md`
- Compliance and audit: `korean_pii_guardrail_v0_2/docs/09_COMPLIANCE_AND_AUDIT_SPEC.md`
- Development handoff: `korean_pii_guardrail_v0_2/docs/10_DEVELOPMENT_HANDOFF.md`
- Annotation guide: `korean_pii_guardrail_v0_2/docs/11_ANNOTATION_GUIDELINE.md`
- Scope change note: `korean_pii_guardrail_v0_2/docs/12_SCOPE_CHANGE_NOTE.md`
- GitHub operations: `korean_pii_guardrail_v0_2/docs/13_GITHUB_OPERATIONS_AND_EVIDENCE_GUIDE.md`

## GitHub Templates And Workflows

- Agent Task Issue template: `.github/ISSUE_TEMPLATE/agent-task.yml`
- Pull request template: `.github/pull_request_template.md`
- CODEOWNERS (activated, real handles): `.github/CODEOWNERS`
- Active package pytest workflow draft: `.github/workflows/korean_pii_guardrail_v0_2_tests.yml`

## Decision Records

Use `docs/decisions/` for durable team decisions from professor feedback,
meetings, Slack threads, or review discussions.

Decision records should include:

- Date
- Context
- Decision
- Impact
- Follow-up work

## Suggested Prompt For Agents

```text
This is work in the My-AI-Security-Project repository.
Read AGENTS.md and docs/index.md first.
If the task touches korean_pii_guardrail_v0_2, also read that package's AGENTS.md,
README.md, docs/12_SCOPE_CHANGE_NOTE.md, and docs/10_DEVELOPMENT_HANDOFF.md.
Keep v0.2 single-turn scope, preserve raw offsets, and do not expose raw PII or secrets.
Inspect the relevant docs/configs/schemas/source/tests before editing.
```
