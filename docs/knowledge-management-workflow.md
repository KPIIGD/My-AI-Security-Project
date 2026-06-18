# Knowledge Management Workflow

This document defines the stage 6 knowledge-management workflow for AI
development automation in this repository. It documents operating rules only;
it does not configure Slack, Google Drive, Obsidian, GitHub, or any external
service.

The default safety posture is no raw PII and no secrets in notes, prompts,
summaries, evidence, screenshots, logs, reports, or AI context. Use masked,
synthetic, aggregate, or non-reversible summaries whenever project knowledge
needs to be retained.

## Tool Roles

| Tool or location | Primary role | Do not use it for |
|---|---|---|
| GitHub | Code, issues, PRs, CI, review, and the durable execution ledger for agent work. | Private scratch notes, full Slack archives, raw PII, secrets, or unreviewed long-term decisions. |
| Obsidian | Personal or team research notes, experiment logs, prompt notes, evaluation summaries, threat model drafts, and draft decision notes. | Raw PII, API keys, credentials, recoverable token maps, or final project decisions that agents must later rely on. |
| Slack | Real-time requests, notifications, review calls, incident coordination, and deployment or CI alerts. | Long-term decision storage, complete AI memory replication, raw PII sharing, or unbounded task history. |
| Google Drive, Docs, Sheets, Slides | Official deliverables, meeting notes, reports, presentation decks, evaluation tables, cost tracking, permission-based sharing, and version history. | Unbounded AI search space, secret storage, raw production data, or private drafts that have not been summarized safely. |
| `docs/decisions/` | Durable repository decisions that future agents must read, especially scope, security, workflow, and evidence decisions. | Temporary discussion, full meeting transcripts, raw logs, or duplicated external archives. |
| `docs/` | Durable project guidance, workflow rules, indexes, templates, and agent-operating notes. | Generated artifacts, raw evidence dumps, or high-volume experiment output. |

## Information Routing

| Information type | Record in | Supporting location | Retention rule |
|---|---|---|---|
| Code changes, implementation tasks, bugs, review requests | GitHub Issue and PR | Agent Task Brief in issue body or linked doc | Keep in GitHub as the work ledger. |
| CI, test, and verification results | PR body | Safe evidence summary or Drive report when needed | Keep exact commands and pass/fail status, not raw PII. |
| Durable scope or security decision | `docs/decisions/` | PR or meeting note link | Keep a decision record in the repository. |
| Research notes and literature review | Obsidian | Drive/Docs for shared final report | Keep notes safe, cite sources, and promote final conclusions to docs or Drive. |
| Experiment logs | Obsidian first, Drive/Sheets for official tables | PR or report summary when used for project claims | Keep case IDs, aggregate metrics, and masked examples only. |
| Threat model drafts | Obsidian | `docs/decisions/` when a policy or scope decision is made | Keep draft notes separate from durable decisions. |
| Meeting notes | Google Docs | Slack summary or GitHub Issue link | Keep official notes in Drive/Docs. |
| Evaluation tables and cost tracking | Google Sheets | PR summary or report | Use permissioned sharing and version history. |
| Presentation and report artifacts | Google Slides, Docs, or repository `paper/` and `presentations/` areas when requested | `docs/index.md` when the artifact becomes important project context | Keep official deliverables outside informal chat threads. |
| Real-time coordination, unblock requests, incidents | Slack | GitHub Issue, PR, or decision record after triage | Keep Slack as the communication layer, not the archive. |
| AI run summaries | GitHub Issue or PR; short note in Obsidian when exploratory | `docs/decisions/` only when a durable decision was made | Keep prompts and outputs summarized without raw PII. |

## Slack Escalation Rules

Slack is useful for speed, but it is not the system of record. Escalate a Slack
thread when it changes project work, policy, scope, security posture, or
official evidence.

Create or update a GitHub Issue when:

- the Slack request asks for code, tests, configs, schemas, package docs,
  GitHub workflow files, or durable project docs;
- the work needs a branch, PR, review, CI, or test record;
- there are open questions, blockers, or reviewer decisions to track;
- the request affects v0.2 scope, raw PII handling, secrets, policy behavior,
  evaluation evidence, or release claims;
- the thread contains an incident, bug report, or deployment/CI failure that
  requires follow-up.

Create a `docs/decisions/` record when:

- the team accepts, rejects, or changes project scope;
- a security, PII, evidence, retention, or tool-use policy changes;
- professor, reviewer, or stakeholder feedback changes the long-term plan;
- a Slack thread resolves an architectural or workflow question that future
  agents must know;
- a Google Docs meeting note contains a decision that should survive outside
  Drive permissions.

Do not leave important decisions only in Slack. Summarize the decision, link or
cite the source thread when allowed, and remove raw PII, secrets, private logs,
and unrelated conversation.

## Obsidian Experiment Log Structure

Use Obsidian for working notes and exploratory logs. Keep the vault safe enough
that it can be searched by humans without exposing raw PII or credentials.

Recommended folder layout:

```text
ai-automation/
  experiments/
    YYYY-MM-DD-short-topic.md
  prompts/
    YYYY-MM-DD-short-topic.md
  eval-summaries/
    YYYY-MM-DD-short-topic.md
  threat-model/
    YYYY-MM-DD-short-topic.md
  decision-drafts/
    YYYY-MM-DD-short-topic.md
```

Recommended experiment log template:

```md
# Experiment Log: Short Topic

Date: YYYY-MM-DD
Owner:
Related Issue or PR:
Repository area:
Tooling:

## Goal

## Hypothesis

## Inputs

- Dataset or fixture ID:
- Config or command:
- Source metadata:

## Method

## Results

- Aggregate metrics:
- Pass/fail status:
- Notable safe case IDs:

## Interpretation

## Follow-up

## PII/Secret Safety Note

- Raw PII included: No
- Secrets included: No
- Examples are synthetic, masked, aggregate, or non-reversible: Yes
```

Do not paste raw prompts that contain raw PII, secrets, credentials, private
logs, or recoverable token maps. Keep prompt records as intent summaries,
masked examples, or synthetic examples.

## Google Drive And Docs Rules

Use Google Drive, Docs, Sheets, and Slides for official shared artifacts:

- meeting minutes and action items;
- official reports and submission drafts;
- presentation decks;
- evaluation tables and cost tracking;
- stakeholder review documents;
- artifacts that need permission-based sharing and version history.

Operating rules:

- Do not open the entire Drive as an unbounded AI search target.
- Give agents a specific file, folder, URL, or task-scoped search query.
- Record source metadata when a Drive artifact is summarized or used for a
  repository decision.
- Keep raw PII, secrets, credentials, private logs, and token maps out of
  Drive artifacts unless a separate approved secure storage process exists.
- Prefer masked, aggregate, synthetic, or non-reversible summaries.
- Promote official project decisions from meeting notes into
  `docs/decisions/` when future agents must rely on them.

## Decision Record Criteria

Create a repository decision record under `docs/decisions/` when the decision:

- changes v0.2 scope, release criteria, evaluation claims, or milestone order;
- affects raw PII, secret handling, logging, audit, evidence, retention, or
  source access;
- changes GitHub, Slack, Drive, Obsidian, or AI-agent workflow rules;
- creates or changes a policy that future agents must follow;
- resolves a repeated ambiguity in architecture, tests, docs, or project
  operations;
- came from Slack, a meeting, professor feedback, or review discussion and
  should not depend on external chat or Drive access.

Decision records should stay concise. Put detailed background in linked
evidence, meeting notes, or PRs, and keep the repository record focused on the
decision and impact.

## Source Metadata For External Knowledge

When an AI agent uses external knowledge from Slack, Drive, Obsidian, web
pages, papers, reports, or local files outside the immediate edited document,
record source metadata in the output, issue, PR, note, or decision record.

Required fields:

```yaml
source_system:
source_url:
local_path:
owner:
permission_basis:
sensitivity:
retrieved_at:
retention_policy:
hash:
version:
summary_without_raw_pii:
```

Field guidance:

| Field | Meaning |
|---|---|
| `source_system` | GitHub, Obsidian, Slack, Google Drive, Google Docs, Google Sheets, Google Slides, web, local file, or other named source. |
| `source_url` | URL when safe to record. Use `N/A` for local-only sources. |
| `local_path` | Repository-relative or task-scoped local path when safe to record. Use `N/A` for URL-only sources and avoid private account identifiers when not necessary. |
| `owner` | Person, team, repository, or document owner. Use role names when names are not needed. |
| `permission_basis` | Why the agent was allowed to use the source, such as user-provided link, repository file, project Drive folder, or task-scoped Slack thread. |
| `sensitivity` | Public, internal, restricted, secret, or raw-PII-prohibited. Use the most conservative label when unclear. |
| `retrieved_at` | Timestamp or date when the source was read. |
| `retention_policy` | Keep in repo, keep in Drive, keep in GitHub, summarize only, do not retain, or delete after task. |
| `hash` | Commit hash, file hash, message timestamp, or `N/A`. |
| `version` | Document version, Drive revision, release tag, commit ref, or `N/A`. |
| `summary_without_raw_pii` | Safe summary that excludes raw PII, secrets, recoverable token maps, and private logs. |

Never replicate all Slack or all Drive content into AI memory. Use the minimum
source set required for the current task.

## Raw PII And Secret Non-Exposure Rules

The following content must not be stored in Obsidian, Slack summaries, Drive
artifacts, GitHub issues, PRs, decision records, reports, logs, screenshots,
public response spans, evidence files, or AI context:

- raw personal data;
- raw detector span text;
- full unmasked input or output text when it contains PII;
- recoverable token maps;
- API keys, tokens, credentials, cookies, private keys, or secrets;
- local account names or machine-specific secrets;
- full private logs or screenshots containing sensitive values.

Allowed safe substitutes:

- synthetic fixtures;
- case IDs;
- entity types;
- span lengths;
- aggregate counts and metrics;
- risk/action labels and reason codes;
- non-reversible HMAC or hash values;
- masked examples that cannot reconstruct the raw value;
- concise summaries without raw PII.

If raw PII or a secret appears in source material, do not copy it. Summarize the
finding safely and state that the raw value was excluded.

## Agent Run Log Summary

Use this format for a short run summary in a GitHub Issue, PR, or Obsidian note.
Keep it brief and safe.

```md
# Agent Run Summary

Date:
Agent/tool:
Requester:
Related Issue or PR:
Task brief:
Repository state:

## Scope

## Files Read

## Files Changed

## Commands Or Checks

## Result

## Source Metadata

- source_system:
  source_url:
  local_path:
  owner:
  permission_basis:
  sensitivity:
  retrieved_at:
  retention_policy:
  hash:
  version:
  summary_without_raw_pii:

## Safety Confirmation

- Raw PII stored: No
- Secrets stored: No
- v0.2 single-turn scope preserved: Yes
- External services modified: No, unless explicitly approved and recorded

## Follow-up
```

## Decision Record Template

Use `docs/decisions/README.md` as the canonical template. A decision record
should include:

```md
# Decision Title

Date: YYYY-MM-DD

## Context

## Decision

## Impact

## Follow-up

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

## Turning Meetings Or Slack Summaries Into Task Briefs

Use this procedure to convert meeting notes or Slack discussion into an Agent
Task Brief:

1. Identify the concrete requested outcome.
2. Separate facts from opinions, open questions, and decisions.
3. Remove raw PII, secrets, private logs, and unrelated conversation.
4. Add source metadata for the Slack thread, meeting note, or Drive document.
5. Decide whether the result is a GitHub Issue, a decision record, or both.
6. Map the request into `docs/agent-task-template.md`:
   `Goal`, `Background`, `Scope`, `Out of Scope`, `Files To Read First`,
   `Allowed Files/Areas`, `Do Not Touch`, `Acceptance Criteria`,
   `Verification`, `Security/PII Rules`, `Expected Output`, and
   `Open Questions`.
7. Mark unclear requirements as `Unknown` or `Needs confirmation`.
8. Do not start branch work when the brief contains unresolved scope,
   security, production access, destructive command, raw PII, or secret
   questions.
9. Link the resulting GitHub Issue, PR, or decision record back to the safe
   source summary.

## Boundary With v0.2 Scope

This workflow does not change the `korean_pii_guardrail_v0_2` product scope.
It does not add RAG scanning, retrieval sanitization, multi-turn monitoring,
fragment ledgers, subject trackers, Redis TTL stores, full LLM judges,
production key management, or human review dashboards. Any future change to
those exclusions requires an explicit scope decision and must not conflict with
the existing v0.2 scope documents.
