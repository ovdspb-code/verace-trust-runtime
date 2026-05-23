# Project State

**Project:** Verace - Trust Runtime  
**Current phase:** Phase 0 - Operating Base  
**Updated:** 2026-05-23  

## Accepted ADRs

- ADR-TR002: Verace as Trust Runtime for AI Work — Accepted v1.0, ratified 2026-05-23 by Oleg Dolgikh.

## Proposed ADRs

- ADR-TR003: Founder Assistant as First Runtime Canary — Proposed v1.0.

## Accepted Plans

- PLAN-TR001: Verace Work Plan - From Founder Assistant to Trust Runtime — Accepted v1.0, ratified 2026-05-23 by Oleg Dolgikh.

## Next Intended Document

- ADR-TR004: Runtime Ledger Minimal Contract.

## Current Repository Fact

`TRUST_RUNTIME` was not covered by a parent git repository during Session TR-001 preflight. A new git repository was initialized at:

```text
/Users/ovd/Documents/VERACE/TRUST_RUNTIME
```

Baseline commit: created in Session TR-002. The current commit hash is intentionally not embedded in the committed tree because amending a commit changes its hash; use `git rev-parse --short HEAD` / `git log --oneline -1` as the operational receipt.

## Operating Rule

Do not start runtime implementation until a session brief has been issued and accepted through the Session Protocol.
