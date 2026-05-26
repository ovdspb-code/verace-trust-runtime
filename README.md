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

Phase 1 - Founder Assistant Seed.

The current implementation includes the Browser Founder Workbench over the Verace Runtime ledger. CLI commands remain internal/admin surfaces, not founder UX.

## Persona Front Door

Verace founder UX is persona-first:

```text
Persona is the interface.
Runtime is the truth.
Workbench is the audit cockpit.
```

The preferred browser entry is `/vera`. Oleg can write naturally, and Vera proposes what may be worth recording. The runtime still owns facts, permissions, receipts, approvals, and ledger state. Vera may propose actions freely, but she may not claim a task, decision, review, delivery, merge, or check is complete unless that statement is backed by a runtime receipt.

Vera requires a configured persona provider to be founder UX. Without one, `/vera` shows an unavailable state rather than pretending that fallback text is a real assistant.

Persona Provider v0 uses the OpenAI Responses API through environment variables:

```bash
export VERACE_PERSONA_PROVIDER=openai
export VERACE_PERSONA_MODEL=<model>
export OPENAI_API_KEY=<secret>
```

The adapter is replaceable, sets `store=false`, and disables tool/function calling. The model drafts voice and proposed actions only; confirmed task, decision, and review writes still go through receipt-backed runtime paths.

The Workbench remains backstage: plan, documents, capture, reviews, ledger diagnostics, and manual correction.

## Founder Workbench

Oleg's product surface is the browser workbench, not the terminal.

Codex/admin launch command:

```bash
python -m pip install -e ".[dev]"
VERACE_RUNTIME_DB=.runtime/verace.sqlite3 verace-workbench --host 127.0.0.1 --port 8765
```

Then open:

```text
http://127.0.0.1:8765/
```

Oleg's product workflow starts in the browser at the local workbench URL. The launch command is an internal Codex/admin step, not the founder interface.

The workbench shows session brief, doctor/schema state, open tasks, review queue, and latest decisions. It supports browser forms for task, decision, review creation, and review resolution. State-changing confirmations use receipt-rendered runtime prose where supported.

FOUNDER-TRIAL-001 found first-use friction in the browser UI: the dashboard was too technical, review layout was cramped, and several labels looked internal. The browser workbench is being refined from that human trial feedback. CLI remains internal/admin only.

The workbench is not intended to be a manual notebook. It reads local project documentation, shows project context, and suggests next work for Oleg to review, edit, and approve.

### Conversation Capture Inbox

Conversation Capture Inbox is an ingestion capability, not the primary founder workflow. It accepts pasted working text from ChatGPT, Codex reports, Claude notes, Telegram text, or local notes.

The first capture implementation is deterministic and local-only: it stores the pasted text in the runtime DB, proposes editable task/decision/review/risk-review/Codex-task/ignore suggestions, and waits for Oleg to approve before ledger mutation. Accepted task, decision, and review entries use receipt-backed runtime paths. There is no LLM, provider, Telegram, channel, or external API integration yet.

### Workbench launch control

Codex/admin may use:

```bash
verace-workbench-control open
```

This handles stale pid files, reuses a healthy local server, and opens `/vera`. This is internal/admin machinery. Founder UX remains the browser page.

## Ledger Seed Quickstart

```bash
python -m pip install -e .
python -m verace_runtime.cli init --db .runtime/verace.sqlite3
python -m verace_runtime.cli ingest-message --db .runtime/verace.sqlite3 --principal oleg --contour verace_project --text "Подготовить тестовую задачу"
python -m verace_runtime.cli tasks --db .runtime/verace.sqlite3
python -m verace_runtime.cli status --db .runtime/verace.sqlite3
python -m verace_runtime.cli doctor --db .runtime/verace.sqlite3
```

Schema visibility:

```bash
python -m verace_runtime.cli schema-status --db .runtime/verace.sqlite3
```

Project memory commands:

```bash
python -m verace_runtime.cli record-decision --db .runtime/verace.sqlite3 --principal oleg --contour verace_project --title "Test decision" --text "Synthetic decision."
python -m verace_runtime.cli decisions --db .runtime/verace.sqlite3
python -m verace_runtime.cli set-task-status --db .runtime/verace.sqlite3 --task TR-000001 --status waiting --note "Synthetic waiting state"
python -m verace_runtime.cli add-task-event --db .runtime/verace.sqlite3 --task TR-000001 --event-type "review.note" --summary "Synthetic event"
python -m verace_runtime.cli project-brief --db .runtime/verace.sqlite3
```

Runtime DB files live under `.runtime/` by default and must never be committed. The MVP has no Telegram, LLM provider, external API, payment, legal, or external-send integration.
