# GitHub Workflow

GitHub is the canonical shared project state for Verace - Trust Runtime after the initial push.

ChatGPT Project uploads remain useful supporting context snapshots, but they are not the source of truth for repository state. The source of truth is the GitHub repository history, branches, commits, pull requests, and reviewed files.

## Repository

- Repository: `ovdspb-code/verace-trust-runtime`
- Visibility: public
- Canonical branch: `main`
- Remote name: `origin`

## Branch And PR Workflow

- Work starts from a brief or explicit founder instruction.
- Codex performs preflight before changes.
- Routine work happens in bounded commits or branches, depending on the brief.
- Pull requests are used when review is needed before merge.
- No merge happens without explicit instruction.
- No force-push is allowed.
- No branch protection is configured yet.

## Review Model

- The Chief Architect reads files, commits, diffs, and PRs through GitHub.
- Oleg ratifies strategic ADRs, plans, phase gates, legal/money decisions, and external obligations.
- Codex executes inside approved scope and reports receipts.

## Codex Report Requirements

Every execution report must include:

- changed files;
- commands/checks run;
- test or check output;
- git status and diff/commit summary;
- what was not done;
- risks and follow-up.

## Safety Rules

- No secrets in git.
- No `.env`, database, token, credential, or generated runtime state files.
- No force-push.
- No push of unrelated local changes.
- No old Verace TruthOps repository changes from this project.
- No runtime implementation without an approved brief.
