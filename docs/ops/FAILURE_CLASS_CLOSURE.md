# Failure-Class Closure

## Purpose

This document defines the Verace engineering rule for bugfixes, hardening changes, review-fixes, and any future assistant/channel output that states facts about the system's own actions.

It exists because a green demonstrated case is not evidence that the failure class is closed.

## Source

This doctrine is distilled from the internal Porthos memo `PORTHOS_MEMO_patch-vs-class-closure_2026-05-24` and is now adopted as Verace Trust Runtime governance.

The raw memo is not committed to the public repository unless Oleg explicitly approves it.

## Core Rule

A fix is not accepted because the demonstrated case is green.

A fix is accepted only when the relevant failure class is named, bounded, tested across its axis of variation, and either made impossible or made fail-closed.

## Definition: Patch

A patch is a change that fixes the demonstrated instance while leaving the failure class open.

Patches are not accepted as fixes.

## Failure-Class Closure Gate

Every bugfix, hardening change, and review-fix must report:

- failure class;
- axis of variation;
- invariant that closes the class;
- parametric tests over the axis;
- ugly or malformed variant behavior;
- fail-closed behavior for unknown members;
- receipt/claim boundary for user-visible system-action statements;
- residual risk.

## Demonstrated Case Is Not Acceptance

The following is not sufficient:

```text
the reported bug no longer reproduces
```

The following is required:

```text
the failure class is closed or fails closed across the named axis of variation
```

## System-Action Prose Invariant

Human-facing factual statements about the system's own actions must be rendered from receipts or validated against receipts.

This applies to statements such as:

- created;
- generated;
- rendered;
- attached;
- uploaded;
- sent;
- scheduled;
- extracted;
- checked;
- pushed;
- merged;
- delivered.

The LLM may draft tone and style. It may not invent operational facts.

## Receipt-Rendered Prose Rule

A human-facing statement like:

```text
PDF prepared
```

is allowed only if the ledger/receipt state supports:

```text
artifact exists
artifact format = PDF
status = ok
visibility/delivery state permits the claim
```

If the receipt says `DOCX`, the user-facing statement must not say `PDF`.

If the statement does not follow from receipt-backed state, the runtime must:

- fail closed;
- repair from receipt fields;
- ask for clarification;
- or downgrade the statement to an explicitly non-completion claim.

## Relationship to No Receipt, No Success Claim

`No receipt, no success claim` prevents claims without evidence.

`No receipt-rendered prose, no system-action statement` prevents prose from contradicting evidence.

Together:

```text
No receipt, no success claim.
No class closure, no fix accepted.
No receipt-rendered prose, no system-action statement.
```

## Review Responsibility

Codex must not submit a bugfix/hardening PR without a Failure-Class Closure section.

The Chief Architect must not approve a bugfix/hardening PR unless the class closure is credible.

## Required PR Section For Fixes

Every bugfix/hardening PR must include:

```text
## Failure-Class Closure

Failure class:
Axis of variation:
Invariant:
Parametric tests:
Ugly/unknown member behavior:
Receipt/claim boundary:
Residual risk:
```

## Examples

Bad:

```text
Fixed the PDF case.
```

Good:

```text
Failure class: human-facing artifact format claim can diverge from delivered artifact receipt.
Axis: artifact format = pdf/docx/txt/unknown.
Invariant: visible artifact-format prose is rendered from receipt.artifact_format.
Tests: parameterized over pdf/docx/txt; unknown format fails closed.
```

## Current Scope

This doctrine is immediately binding for:

- Verace Trust Runtime bugfixes;
- review-fixes requested by Chief Architect;
- doctor/audit invariant hardening;
- future response rendering and channel/LLM work.

It does not require validating arbitrary natural-language claims about the world. It applies specifically to system-action statements and engineering fixes.
