# Decision Records

Use this directory for durable team decisions that should survive beyond Slack,
meeting notes, local Obsidian notes, or individual AI chat threads.

Write a decision record when a choice needs to be read by future humans or AI
agents, especially when it changes scope, security posture, raw PII handling,
secret handling, evaluation claims, evidence retention, GitHub workflow,
Slack/Drive/Obsidian workflow, or long-term project operating rules.

Do not use this directory for temporary discussion, full meeting transcripts,
full Slack threads, raw logs, screenshots with sensitive values, raw PII,
recoverable token maps, API keys, tokens, credentials, or private secrets.

## Naming

Use kebab-case filenames:

```text
YYYY-MM-DD-short-topic.md
```

Example:

```text
2026-06-16-agent-context-entrypoints.md
```

## Template

```md
# Decision Title

Date: YYYY-MM-DD

## Context

What happened, who raised it, and why it matters.

## Decision

What the team decided.

## Impact

What changes for code, docs, workflow, or tools.

## Follow-Up

- [ ] Concrete next action

## Evidence

- source_system:
- source_url:
- local_path:
- owner:
- permission_basis:
- sensitivity:
- retrieved_at:
- retention_policy:
- hash:
- version:
- summary_without_raw_pii:

## PII/Secret Safety Note

- Raw PII included: No
- Secrets included: No
- Sensitive source material was summarized without raw values: Yes
```

## Evidence Rules

Evidence should be enough to understand why the decision was made without
copying sensitive source material. Prefer GitHub issues, PRs, safe meeting-note
summaries, repository-relative paths, commit hashes, document versions, case
IDs, aggregate metrics, entity types, span lengths, masked examples, and
non-reversible hashes.

If a decision came from Slack, Google Drive, Obsidian, or another external
source, record source metadata and a safe summary. Do not copy the whole source
into the repository.
