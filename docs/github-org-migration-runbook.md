# GitHub Organization Migration & Governance Runbook

Owner-only execution steps for the decision in
`docs/decisions/2026-06-20-github-org-migration.md`.

> These steps require the repository **owner** account (`vmaca123`). A teammate
> without owner/billing access cannot perform them. Nothing in this runbook can
> be done by an AI agent — it documents the manual GitHub actions for a human.

## Why this is needed

PR #58 CI fails in 2-4 seconds with:

> "The job was not started because your account is locked due to a billing issue."

The repo is **public**, so Actions/branch-protection/CodeQL/secret-scanning are
free. The block is an **account-level** billing lock (a past failed charge or a
spending limit), which disables Actions for the whole account, public repos
included. Step 1 unblocks CI immediately; Steps 2-6 are the longer-term
hardening the team agreed to.

---

## Step 1 — Clear the billing lock (unblocks CI now)

1. Sign in as `vmaca123`.
2. Go to **Settings → Billing and licensing** (https://github.com/settings/billing).
3. Look for a past-due balance, failed payment, or a spending-limit notice.
4. Update the payment method and pay any outstanding balance; or raise/adjust
   the Actions spending limit if that is what is blocking.
5. Confirm the "account is locked" banner is gone.
6. Re-run PR #58 checks: open the PR → **Checks** → "Re-run all jobs", or push
   an empty commit. Confirm the four checks now run and turn green.

> Sanity check: a public repo using only GitHub-hosted standard runners should
> incur **no** Actions charge. If a charge exists, check for private-repo
> minutes, Codespaces, Copilot, or storage on the same account.

## Step 2 — Create the Organization

1. https://github.com/account/organizations/new → choose the **Free** plan
   (sufficient for a public repo with branch protection).
2. Name it (e.g. `my-ai-security`) and set a billing email.

## Step 3 — Transfer the repository into the org

1. Repo **Settings → General → Danger Zone → Transfer ownership**.
2. Transfer to the new organization.
3. After transfer, update local remotes:
   ```bash
   git remote set-url origin https://github.com/<org>/My-AI-Security-Project.git
   ```
   (GitHub redirects the old URL, but update remotes and links anyway.)

## Step 4 — Owners + billing manager (remove the bus factor)

1. Org **People** → invite a second member and set role **Owner** (≥ 2 owners).
2. Org **Settings → Billing → Billing managers** → add a billing manager so
   billing never blocks the project again.

## Step 5 — Branch protection on `main` (free for public repos)

Repo **Settings → Branches → Add branch ruleset** (or "Add rule") for `main`:

- [x] Require a pull request before merging
- [x] Require approvals (≥ 1)
- [x] Require review from **Code Owners** (activates `.github/CODEOWNERS`)
- [x] Require status checks to pass before merging, and select:
  - `test (3.11)`
  - `test (3.12)`
  - Claude Code Review
  - Claude Security Review
- [x] Require branches to be up to date before merging
- [x] Block force pushes / direct pushes to `main`

> Required status checks only appear in the picker **after** they have run at
> least once on an unblocked account — so do Step 1 and let PR #58 run first.

## Step 6 — Convert CODEOWNERS to teams (after transfer)

`.github/CODEOWNERS` currently names individual handles. After the org exists,
create teams (e.g. `@<org>/maintainers`, `@<org>/security`) and replace the
individual handles. Keep human approval mandatory; do not let AI approve.

## Step 7 — Security hardening (separate PR, all free for public repos)

1. **Secret scanning + push protection**: Settings → Code security → enable.
2. **Dependency graph + Dependabot alerts**: Settings → Code security → enable.
3. **CodeQL code scanning**: Security → Code scanning → "Set up" (default).
4. Once these run, optionally add them to the required-checks list in Step 5.

---

## What is intentionally NOT automated

Per `docs/ai-agent-security-policy.md` and `docs/github-agent-workflow.md`:
production write, billing/account changes, org/admin settings, branch
protection, and merge approval are **human owner actions**. An AI agent may
prepare files (CODEOWNERS, this runbook, the decision record) and draft PRs,
but a human owns every step above.
