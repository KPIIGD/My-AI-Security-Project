# GitHub Organization Migration and Governance Hardening

Date: 2026-06-20

## Context

PR #58 ("AI automation baseline governance") added the AI-agent operating
rules, templates, security policy, and CI workflows. However, every CI run on
the repository is failing before any job starts.

Verified evidence (PR #58, run 27789008615):

> "The job was not started because your account is locked due to a billing
> issue." (`test (3.11)`; the build matrix is then cancelled)

All four checks (`test (3.11)`, `test (3.12)`, Claude Code Review,
Claude Security Review) fail in 2-4 seconds, which is the signature of a
runner that never started — not a code failure. The repository is **public**,
so GitHub Actions, branch protection, CodeQL, secret scanning, and dependency
review are all free; the block is an **account-level billing lock** on the
owner account (`vmaca123`, a personal user account), which disables Actions
across the whole account including public repos.

Yangyusang (yangyu0330) raised that a single personal-account owner with no
billing manager and no branch protection is a governance and bus-factor risk,
and asked the owner to either clear the billing lock or move the repository to
a GitHub Organization.

## Decision

Migrate `My-AI-Security-Project` to a **GitHub Organization** and harden
governance:

- Clear the account billing lock first so CI is unblocked immediately.
- Create a GitHub Organization (Free plan is sufficient for this public repo)
  and transfer the repository into it.
- Have **at least two organization owners/admins** and assign a **billing
  manager** so the project is not blocked by one person.
- Enable **branch protection on `main`**: require a pull request, require
  status checks to pass, require review from Code Owners, and disallow direct
  pushes.
- Make the existing checks **required**: `test (3.11)`, `test (3.12)`,
  Claude Code Review, Claude Security Review (selectable only after they have
  run at least once on an unblocked account).
- Activate `CODEOWNERS` with real handles (done in this change); convert
  individual handles to org teams after the transfer.
- Keep human approval and merge mandatory, per
  `docs/ai-agent-security-policy.md` (no automatic merge).

Security hardening (CodeQL, dependency review, secret-scan push protection)
is in scope as a follow-up; all three are free for this public repository.

## Impact

- Unblocks CI for PR #58 and all future PRs.
- Removes the single-owner bus factor and adds a billing manager.
- `main` becomes protected; merges require green checks and code-owner review.
- `.github/CODEOWNERS` now names real reviewers and auto-requests them.
- Repository URL changes on transfer; GitHub redirects the old path, but local
  remotes and any links should be updated to the org path.
- The execution steps are owner/admin actions and are documented in
  `docs/github-org-migration-runbook.md`. This decision record does not itself
  change any GitHub account, billing, or remote protection settings.

## Follow-Up

- [ ] Owner clears the billing lock (GitHub Settings -> Billing and licensing).
- [ ] Re-run PR #58 checks and confirm green.
- [ ] Create the Organization and transfer the repository.
- [ ] Add a second org owner/admin and assign a billing manager.
- [ ] Enable `main` branch protection with required checks + code-owner review.
- [ ] Update `CODEOWNERS` individual handles to org teams after transfer.
- [ ] Update local git remotes and doc links to the new org path.
- [ ] Separate hardening PR: enable CodeQL, dependency review, and secret-scan
      push protection (all free for public repos).

## Evidence

- source_system: github_actions
- source_url: https://github.com/vmaca123/My-AI-Security-Project/actions/runs/27789008615
- local_path: `docs/github-org-migration-runbook.md`
- owner: repository owner (`vmaca123`)
- permission_basis: owner-requested governance task (relayed from yangyu0330)
- sensitivity: internal
- retrieved_at: 2026-06-20
- retention_policy: keep in repo
- hash: N/A
- version: N/A
- summary_without_raw_pii: CI billing-lock diagnosis and org-migration decision
  recorded without raw PII, payment data, or secrets.

## PII/Secret Safety Note

- Raw PII included: No
- Secrets included: No
- Sensitive source material was summarized without raw values: Yes
