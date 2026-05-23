# Verace - Trust Runtime

Verace is the trust runtime for AI-mediated work.

Strategic formula:

> Verace makes AI work verifiable.

Governing chain:

```text
mandate -> policy -> action -> receipt -> claim -> ledger -> review/audit
```

This repository is the operating base for the Verace Trust Runtime line. It starts with Oleg's personal assistant as the first runtime canary and grows toward the broader Verace Platform.

## Governing Documents

- [ADR-TR002: Verace as Trust Runtime for AI Work](docs/adr/ADR-TR002-Verace-as-Trust-Runtime-for-AI-Work.md)
- [PLAN-TR001: Verace Work Plan - From Founder Assistant to Trust Runtime](docs/plans/PLAN-TR001-Verace-Work-Plan-From-Founder-Assistant-to-Trust-Runtime.md)

## Product Boundary

Porthos and Vera are interfaces and canaries, not the core architecture.

The core architecture is the durable runtime that owns mandates, policy, receipts, claims, ledger state, evidence, and review/audit flow. Channels such as Telegram, web, email, APIs, and future agent surfaces are adapters around that core.

## Current Phase

Phase 0 - Operating Base.

The current priority is to establish the project spine before implementation: ADRs, plans, briefs, ops memory, decision log, worklog, risk register, session protocol, and known git state.
