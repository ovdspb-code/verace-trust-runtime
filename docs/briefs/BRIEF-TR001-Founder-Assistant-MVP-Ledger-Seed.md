# BRIEF-TR001: Founder Assistant MVP — Ledger Seed

**Status:** Issued v1.0  
**Date:** 2026-05-23  
**Owner:** Oleg Dolgikh  
**Issued by:** Chief Architect  
**Project:** Verace — Trust Runtime  
**Scope:** First implementation brief for Phase 1 — Founder Assistant Seed  
**Governing ADRs:** ADR-TR002, ADR-TR003, ADR-TR004, ADR-TR005  
**Governing Plan:** PLAN-TR001  

---

## 1. Goal

Build the smallest working runtime slice that can serve as the first durable core of Oleg’s Founder Assistant.

This brief does **not** build a full assistant, Telegram bot, LLM integration, workflow engine, or external-action system.

It builds the first boring, testable, restart-safe ledger seed:

```text
principal / contour / mandate
        ↓
inbound message
        ↓
task / event / receipt / claim state
        ↓
status query
        ↓
explicit output
```

The result must make one fact true:

> Oleg can create and inspect ledger-backed work items without relying on model memory.

---

## 2. Context

ADR-TR002 defines Verace as **Trust Runtime for AI Work** and fixes the governing chain:

```text
mandate → policy → action → receipt → claim → ledger → review/audit
```

ADR-TR003 defines Oleg’s Founder Assistant as the first runtime canary, not the final product category.

ADR-TR004 defines the Runtime Ledger as the operational source of truth.

ADR-TR005 defines receipt and approval policy before assistant implementation begins.

This brief starts implementation only where the trust contract is already clear: local durable state, deterministic policy-safe actions, receipts for internal state changes, and testable status reporting.

---

## 3. Non-goals

Do not implement:

- Telegram bot;
- web UI;
- LLM provider adapter;
- OpenAI/Claude/Gemini/Kimi integration;
- MCP/A2A/AP2/VC integration;
- Verace Truth backend integration;
- external sending, publishing, pushing, PR creation, email, calendar, payments, legal actions;
- autonomous tool execution;
- multi-agent orchestration;
- generic plugin system;
- enterprise RBAC;
- final schema or migration framework;
- personal/private real data in repository.

Do not import old Verace TruthOps backend code.

Do not create runtime databases or logs that are committed to git.

---

## 4. Files / areas

Work only inside:

```text
/Users/ovd/Documents/VERACE/TRUST_RUNTIME
```

Expected implementation shape:

```text
pyproject.toml
src/verace_runtime/
  __init__.py
  cli.py
  ids.py
  time.py
  ledger/
    __init__.py
    db.py
    schema.sql
    models.py
    repository.py
  policy/
    __init__.py
    engine.py
  receipts/
    __init__.py
    factory.py
  app/
    __init__.py
    service.py
tests/
  test_ledger_init.py
  test_founder_assistant_seed.py
  test_policy_receipts.py
  test_restart_recovery.py
  test_cli_smoke.py
docs/ops/PROJECT_STATE.md
docs/ops/WORKLOG.md
docs/ops/RISK_REGISTER.md
```

Optional, only if useful:

```text
README.md
```

No other files unless justified in Codex report.

---

## 5. Constraints

### 5.1 Runtime constraints

- Use Python.
- Use SQLite as the first local durable store.
- Use raw SQL or a very small standard-library-first repository layer.
- No web framework.
- No background worker.
- No external API calls.
- No provider SDK.
- No secrets.
- No runtime DB committed to git.
- No personal/private records committed to git.
- Test fixtures must be synthetic.

### 5.2 SQLite constraints

The runtime must enable:

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA busy_timeout=5000;
PRAGMA foreign_keys=ON;
```

The first schema must be sufficient to represent:

- persons;
- contours;
- mandates;
- messages;
- tasks;
- task_events;
- approvals;
- receipts;
- claims;
- outbox_items.

Attachments, artifacts, and scheduled wakeups may be deferred unless the implementation remains small.

### 5.3 Public/private boundary

For this first slice, there is no formal ADR-033-style public-surface enforcement. Still, keep boundaries simple:

- CLI calls service layer.
- Service layer calls repository and policy.
- Repository owns SQL.
- Policy is deterministic and outside the model.
- Receipt creation is explicit.

### 5.4 GitHub/public repo safety

Because the repository is public, do not commit:

- `.env`;
- tokens;
- credentials;
- SQLite DB files;
- logs;
- personal tasks;
- private documents;
- real messages;
- real receipts with private URLs.

---

## 6. Required behavior

### 6.1 Initialization

Provide a CLI command that initializes a local runtime database.

Example command shape:

```bash
python -m verace_runtime.cli init --db .runtime/verace.sqlite3
```

It must:

- create parent directory if needed;
- create schema if missing;
- be idempotent;
- seed at least:
  - principal person `oleg`;
  - contour `verace_project`;
  - initial mandate for managing Verace project work.

The exact internal IDs may be deterministic slugs or generated IDs. Tests must not depend on wall-clock random behavior unless controlled.

### 6.2 Message ingestion

Provide a CLI command to ingest a synthetic inbound message into a contour.

Example command shape:

```bash
python -m verace_runtime.cli ingest-message \
  --db .runtime/verace.sqlite3 \
  --principal oleg \
  --contour verace_project \
  --text "Подготовить BRIEF-TR001 для Codex"
```

It must:

- record the message;
- attach it to the active contour;
- create or reuse an active mandate;
- create a task unless the command explicitly says it is a note/status-only input;
- create task event(s);
- create at least one internal receipt proving ledger write/action;
- create a bounded claim only if supported by receipt.

No LLM classification is required. A deterministic simple rule is enough.

### 6.3 Task status

Provide CLI commands to inspect state:

```bash
python -m verace_runtime.cli status --db .runtime/verace.sqlite3
python -m verace_runtime.cli tasks --db .runtime/verace.sqlite3
python -m verace_runtime.cli task --db .runtime/verace.sqlite3 --task <public_task_no_or_id>
python -m verace_runtime.cli doctor --db .runtime/verace.sqlite3
```

Minimum output requirements:

- human-readable text;
- stable enough for smoke tests;
- no raw stack traces in normal success path;
- task public number or stable ID visible;
- task status visible;
- contour visible;
- receipt count or receipt reference visible for task detail.

### 6.4 Policy-safe default

The first policy engine must default to safety:

Allowed:

- internal message recording;
- task creation;
- task event creation;
- internal status query;
- local ledger receipt.

Blocked or not implemented:

- external send/share/publish;
- GitHub push/PR/merge;
- payment;
- legal commitment;
- sensitive data disclosure;
- destructive action;
- external agent delegation.

Policy decisions must be represented in ledger state for actions that are evaluated.

### 6.5 Receipts and claims

Every successful state-changing command must create a receipt.

At minimum:

- `ledger.event` receipt for internal state change;
- `policy.blocked` receipt for blocked action if such action is requested;
- `tool.failed` or explicit failure receipt if a command fails after attempting a state-changing operation.

Claims must not be stronger than receipts.

Correct:

```text
Task created: #... Receipt: ...
```

Incorrect:

```text
Work completed.
```

The MVP must not claim external completion because no external action exists in this brief.

### 6.6 Restart recovery

State must survive process exit.

A test must prove:

1. initialize DB;
2. ingest message;
3. close connection / create new service instance;
4. read tasks/status;
5. verify created task and receipt are still present.

---

## 7. Implementation plan

Codex should implement in this order:

1. Preflight and repo sync check.
2. Project skeleton and test tooling.
3. SQLite connection/session utility.
4. Minimal schema and idempotent initialization.
5. Repository methods for persons, contours, mandates, messages, tasks, events, receipts, claims, outbox.
6. Deterministic policy engine for MVP action classes.
7. Receipt factory.
8. Service layer for init, ingest message, status/tasks/task detail, doctor.
9. CLI wrapper.
10. Tests.
11. Documentation/update worklog/risk register.
12. Commit and push on an implementation branch or PR branch, not directly to `main` unless explicitly authorized.

---

## 8. Tests

Use `pytest` unless there is a strong reason not to.

Required tests:

1. `test_ledger_init.py`
   - DB initializes idempotently.
   - Required tables exist.
   - Seed principal, contour, and mandate exist.

2. `test_founder_assistant_seed.py`
   - Synthetic Oleg message creates a task in `verace_project` contour.
   - The task has a public reference.
   - The task has at least one event.

3. `test_policy_receipts.py`
   - Internal task creation is allowed and receipted.
   - External send/push/payment/legal/destructive action is blocked or not implemented.
   - Blocked action produces visible policy result or receipt where applicable.

4. `test_restart_recovery.py`
   - Task and receipt survive new service/connection.

5. `test_cli_smoke.py`
   - `init`, `ingest-message`, `tasks`, `status`, `doctor` run successfully against a temp DB.

No test may require network access.

No test may use real personal data.

---

## 9. Acceptance criteria

The implementation is accepted only when:

- the package can be installed or run locally in a documented way;
- CLI `init` creates a SQLite runtime DB outside git-tracked files;
- CLI `ingest-message` creates a ledger-backed task;
- CLI `status` and `tasks` report ledger-backed state;
- every state-changing command creates a receipt;
- external/consequential actions are blocked or absent;
- restart recovery is proven by test;
- all required tests pass;
- working tree is clean after commit;
- no secrets, DB files, logs, or real private data are committed;
- ADR-TR002/003/004/005 and PLAN-TR001 are unchanged;
- Codex report includes receipts for commands, tests, git state, and push/PR state.

---

## 10. Rollback / safety

If implementation becomes larger than this brief, stop and report before continuing.

If external dependencies become necessary, stop and justify before adding them.

If any real private data, DB, secret, or log file appears in the diff, stop before commit.

If tests fail, do not claim completion. Report failure and exact output.

If branch diverges from `origin/main`, stop before merge/rebase unless explicitly instructed.

Rollback path:

- delete implementation files added by this brief;
- keep docs unless they contain incorrect claims;
- do not rewrite published history;
- do not force-push.

---

## 11. Done definition

Codex final report must include:

- branch name;
- commit hash;
- push or PR URL;
- changed files;
- commands run;
- test output summary;
- final `git status`;
- confirmation that no runtime DB/secrets/logs/private data were committed;
- confirmation that no external actions were implemented;
- known limitations;
- whether acceptance criteria are fully met.

---

## 12. Expected result after this brief

After BRIEF-TR001, Verace Trust Runtime should have its first executable spine:

```text
local CLI
  → SQLite ledger
  → contour / mandate / task
  → event / receipt / claim
  → status / doctor
  → tests proving restart recovery
```

This is not yet the assistant.

It is the first bone of the assistant’s spine.
