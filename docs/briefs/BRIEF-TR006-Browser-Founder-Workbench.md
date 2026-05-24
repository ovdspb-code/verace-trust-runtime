# BRIEF-TR006: Browser Founder Workbench

**Status:** Implementation brief  
**Date:** 2026-05-24  
**Owner:** Oleg Dolgikh  
**Scope:** Human-facing local founder workbench

## Goal

Implement the first browser-based human interface for the Founder Assistant runtime.

The terminal remains an internal engineering/admin surface for Codex. It is not counted as founder product UX.

## Context

BRIEF-TR005 added the Response Claim Renderer. The runtime can now render human-facing system-action statements from receipt-backed state.

The next product step is a local browser workbench that lets Oleg inspect and update Verace project state without using the internal CLI.

## Product Effect

Oleg can open a local browser UI and:

- see Verace session brief;
- see open tasks;
- see open review items;
- see latest decisions;
- add a task;
- record a decision;
- add a review item;
- resolve or dismiss a review item;
- see doctor/schema state;
- receive receipt-rendered confirmations.

## Non-Goals

- Telegram integration.
- LLM/provider integration.
- External APIs.
- Verace Truth integration.
- MCP/A2A/AP2/VC integrations.
- Payments, legal commitments, sensitive/destructive/external-send flows.
- Artifact generation or delivery.
- Approval execution.
- Web framework or frontend build step.
- Terminal as founder UX.

## Required Interface

Use a local browser UI served from `127.0.0.1`.

Default port: `8765`.

Default DB path: `.runtime/verace.sqlite3`.

DB override:

- `VERACE_RUNTIME_DB`;
- optional admin/server argument.

No authentication is required for this MVP because the server binds to localhost only.

## Required Pages

- `GET /` dashboard/session brief.
- `GET /tasks/new`.
- `POST /tasks`.
- `GET /decisions/new`.
- `POST /decisions`.
- `GET /reviews`.
- `GET /reviews/new`.
- `POST /reviews`.
- `POST /reviews/{public_id}/resolve`.
- `GET /doctor`.

## Output Rules

State-changing confirmations for tasks, decisions, and reviews must use the Response Claim Renderer where supported.

Browser errors must not expose raw tracebacks.

Unsafe schema state must display failure and must not claim healthy state.

## Acceptance Criteria

- Browser workbench exists.
- UI is local-only by default.
- Dashboard/session brief page works.
- Task, decision, review create, review list, review resolve/dismiss, and doctor flows work.
- State-changing confirmations are receipt-rendered where supported.
- Read-only pages do not mutate ledger state.
- Existing tests remain green.
- No runtime DBs, logs, secrets, or private data are committed.

