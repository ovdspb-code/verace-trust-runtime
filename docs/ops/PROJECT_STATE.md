# Project State

**Project:** Verace - Trust Runtime  
**Current phase:** Phase 1 - Founder Assistant Seed  
**Updated:** 2026-05-24  

## Accepted ADRs

- ADR-TR002: Verace as Trust Runtime for AI Work — Accepted v1.0, ratified 2026-05-23 by Oleg Dolgikh.
- ADR-TR003: Founder Assistant as First Runtime Canary — Accepted v1.0, ratified 2026-05-23 by Oleg Dolgikh.
- ADR-TR004: Runtime Ledger Minimal Contract — Accepted v1.0, ratified 2026-05-23 by Oleg Dolgikh.
- ADR-TR005: Receipt and Approval Policy — Accepted v1.0, ratified 2026-05-23 by Oleg Dolgikh.
- ADR-TR006: Runtime Schema and Migration Policy — Accepted v1.0, ratified 2026-05-24 by Oleg Dolgikh.

## Accepted Plans

- PLAN-TR001: Verace Work Plan - From Founder Assistant to Trust Runtime — Accepted v1.0, ratified 2026-05-23 by Oleg Dolgikh.

## Active Implementation Brief

- BRIEF-TR001: Founder Assistant MVP — Ledger Seed — merged in PR #1.
- BRIEF-TR002: Project Operating Memory — merged in PR #2.
- BRIEF-TR003: Runtime Schema Migration Runner — merged in PR #3.
- BRIEF-TR004: Review Queue and Session Brief — merged in PR #4.

## Next Intended Document

- ADR-TR007: Human-Facing System-Action Claim Rendering.

## Current Repository Fact

`TRUST_RUNTIME` was not covered by a parent git repository during Session TR-001 preflight. A new git repository was initialized at:

```text
/Users/ovd/Documents/VERACE/TRUST_RUNTIME
```

Baseline commit: created in Session TR-002. The current commit hash is intentionally not embedded in the committed tree because amending a commit changes its hash; use `git rev-parse --short HEAD` / `git log --oneline -1` as the operational receipt.

## GitHub Remote Status

- Repository full name: `ovdspb-code/verace-trust-runtime`
- Visibility: public
- Remote name: `origin`
- Remote URL: `https://github.com/ovdspb-code/verace-trust-runtime.git`
- GitHub is intended to be the canonical repository state after successful push.
- ChatGPT Project uploads remain supporting context snapshots, not repository truth.

## Operating Rule

Runtime implementation may proceed only inside an issued implementation brief and must report receipts for tests, git state, and push state.

## Recently Merged Implementation

- PR #1 merged `work/brief-tr001-ledger-seed` into `main` with merge commit `67b28cb`.
- PR #2 merged `work/brief-tr002-project-operating-memory` into `main` with merge commit `e2a2dc6`.
- PR #3 merged `work/brief-tr003-schema-migration-runner` into `main` with merge commit `bb5ee0c`.
- PR #4 merged `work/brief-tr004-review-queue-session-brief` into `main` with merge commit `01c3a46`.
