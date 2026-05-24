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
Failure-Class Closure section when applicable
```

## Invariant

No receipt, no success claim.

If a command was not run, Codex must not claim its result. If git is unavailable, Codex must state that instead of inventing a diff.

## Failure-Class Closure Gate

For bugfixes, hardening changes, and review-fixes, a green demonstrated case is not sufficient.

Every fix report must include:

```text
Failure class:
Axis of variation:
Invariant:
Parametric tests:
Ugly/unknown member behavior:
Receipt/claim boundary:
Residual risk:
```

A fix that only repairs the shown instance is a patch and must not be accepted.

## Receipt-Rendered Prose Gate

Human-facing factual statements about the system's own actions must be rendered from ledger/receipt fields or validated against receipts.

The LLM may draft tone and style. It may not invent operational facts about created, sent, uploaded, rendered, attached, checked, pushed, merged, scheduled, extracted, or delivered actions.

If a statement does not follow from receipt-backed state, the runtime must fail closed, repair from receipts, ask for clarification, or downgrade the statement.
