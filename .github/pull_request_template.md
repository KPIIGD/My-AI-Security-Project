## Change Summary

-

## Scope

-

## Related Issue / Task Brief

- Issue:
- Agent Task Brief:

## Tests / Verification

Record the exact command or manual check and the result.

- Command(s):
- Result:
- Not run / skipped checks:
- Reason and residual risk:

For package changes, run the smallest relevant pytest target first. Run the
full package suite when practical:

```bash
cd korean_pii_guardrail_v0_2
python -m pytest
```

## Security And PII Checklist

- [ ] No raw PII is exposed in logs, exceptions, metrics, reports, audit events, screenshots, evidence files, public response spans, comments, or AI context.
- [ ] No API keys, tokens, credentials, local account names, machine-specific secrets, or private paths are committed.
- [ ] v0.2 single-turn scope is preserved.
- [ ] No RAG scanning, retrieval sanitizer, multi-turn monitoring, fragment ledger, subject tracker, Redis TTL store, full LLM judge, or human review dashboard was added unless explicitly approved as a scope change.
- [ ] No production write permission was used.
- [ ] No destructive command was used, or exact human approval is recorded.
- [ ] Connector, MCP, and tool outputs used in this PR were treated as untrusted and summarized safely.
- [ ] Detector spans preserve raw text offsets, if detector behavior changed.
- [ ] Entity, scoring, context, and policy behavior remain config-driven when config owns the behavior.
- [ ] Config, schema, API, and package docs were updated together when a contract changed.
- [ ] Detector, masking, policy, audit, or public response changes were checked for raw PII non-exposure.
- [ ] If tests or checks were not run, the reason, alternative check, and residual risk are recorded above.
- [ ] `docs/ai-agent-security-policy.md` was followed for AI-assisted work.

## Documentation Checklist

- [ ] Relevant docs were updated, or no documentation change was needed.
- [ ] Links and paths were checked manually for documentation-only changes.
- [ ] Decisions or evidence were recorded in `docs/decisions/` or the relevant project document when needed.

## Reviewer Focus

Ask reviewers to inspect the highest-risk parts of this PR.

-

## Human Approval

- [ ] I understand that AI-generated changes require human review and approval before merge.
- [ ] This PR is not a production deploy and does not rely on an automatically approved destructive command.
