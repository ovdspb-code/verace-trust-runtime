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

The current implementation slice is the local Ledger Seed: a small CLI over SQLite that records founder-project work as durable messages, tasks, events, receipts, and claims.

## Ledger Seed Quickstart

```bash
python -m pip install -e .
python -m verace_runtime.cli init --db .runtime/verace.sqlite3
python -m verace_runtime.cli ingest-message --db .runtime/verace.sqlite3 --principal oleg --contour verace_project --text "Подготовить тестовую задачу"
python -m verace_runtime.cli tasks --db .runtime/verace.sqlite3
python -m verace_runtime.cli status --db .runtime/verace.sqlite3
python -m verace_runtime.cli doctor --db .runtime/verace.sqlite3
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
