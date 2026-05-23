# Session Protocol

## Lifecycle

```text
Brief -> Preflight -> Implementation plan -> Approval -> Execution -> Checks -> Report -> Review
```

## Roles

- Oleg sets founder strategy and ratifies strategic ADRs, plans, phase gates, money, legal commitments, and external obligations.
- Chief Architect defines session briefs, phase gates, boundaries, acceptance criteria, and risk gates.
- Codex executes inside the brief, performs preflight, proposes implementation steps, runs checks, and reports receipts.

## Required Preflight

For code or repository changes, Codex must inspect:

```text
pwd
relevant files
git rev-parse --show-toplevel
git status --short
available tests / linters
target files
risks / unknowns
```

## Required Report

Every execution report must include:

```text
Changed files
Commands run
Test/check output
Git status / diff summary
What was not done
Risks / follow-up
```

## Invariant

No receipt, no success claim.

If a command was not run, Codex must not claim its result. If git is unavailable, Codex must state that instead of inventing a diff.
