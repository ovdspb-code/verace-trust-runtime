# BRIEF-TR002: Project Operating Memory

**Status:** Issued v1.0  
**Date:** 2026-05-24  
**Owner:** Oleg Dolgikh  
**Issued by:** Chief Architect  
**Project:** Verace — Trust Runtime  
**Scope:** Phase 1 — Founder Assistant Seed; project memory layer on top of the Ledger Seed  
**Governing ADRs:** ADR-TR002, ADR-TR003, ADR-TR004, ADR-TR005  
**Governing Plan:** PLAN-TR001  
**Depends on:** BRIEF-TR001 merged in PR #1  

---

## 1. Goal

Extend the Ledger Seed into the first useful **Project Operating Memory** for building Verace.

This brief does **not** build a full assistant, Telegram bot, LLM integration, workflow engine, or external-action system.

It makes the local runtime capable of remembering and reporting the project’s operational state:

```text
project message / task / decision
        ↓
ledger-backed event / receipt / claim
        ↓
status transition / decision register
        ↓
project brief
        ↓
restart-safe recall
```

The result must make this fact true:

> Oleg can ask the local runtime what is open, what was decided, and what changed in the Verace project without relying on chat history or model memory.

---

## 2. Context

BRIEF-TR001 created the first executable spine:

```text
local CLI
  → SQLite ledger
  → contour / mandate / task
  → event / receipt / claim
  → status / doctor
  → restart recovery tests
```

BRIEF-TR002 builds the next layer: project operating memory.

The system should start becoming useful for managing the Verace project itself. It should not yet become conversational or autonomous. It should remain local, deterministic, testable, and receipt-backed.

The governing chain remains:

```text
mandate → policy → action → receipt → claim → ledger → review/audit
```

---

## 3. Non-goals

Do not implement:

- Telegram bot;
- web UI;
- LLM provider adapter;
- OpenAI/Claude/Gemini/Kimi integration;
- MCP/A2A/AP2/VC integration;
- Verace Truth backend integration;
- external sending, publishing, GitHub mutation, email, calendar, payments, legal actions;
- autonomous tool execution;
- multi-agent orchestration;
- generic plugin system;
- enterprise RBAC;
- migration framework for production DB upgrades;
- real personal/private project data committed to repository.

Do not import old Verace TruthOps backend code.

Do not create runtime databases, logs, secrets, or private records that are committed to git.

---

## 4. Files / areas

Work only inside:

```text
/Users/ovd/Documents/VERACE/TRUST_RUNTIME
```

Expected implementation areas:

```text
src/verace_runtime/
  cli.py
  app/service.py
  ledger/schema.sql
  ledger/models.py
  ledger/repository.py
  policy/engine.py
  receipts/factory.py

tests/
  test_project_decisions.py
  test_task_status_transitions.py
  test_project_brief.py
  test_project_memory_restart.py
  test_cli_project_memory.py

docs/ops/
  PROJECT_STATE.md
  WORKLOG.md
  RISK_REGISTER.md
```

Allowed if useful:

```text
README.md
docs/briefs/BRIEF-TR002-Project-Operating-Memory.md
```

No other files unless justified in Codex report.

---

## 5. Constraints

### 5.1 Runtime constraints

- Use Python.
- Use SQLite.
- Keep runtime dependencies empty unless a separate architecture decision says otherwise.
- Keep `pytest` in dev optional dependencies only.
- Use raw SQL or small repository methods.
- No network access in tests.
- No provider SDK.
- No secrets.
- No runtime DB committed to git.
- No personal/private records committed to git.
- Test fixtures must be synthetic.

### 5.2 Ledger constraints

The implementation may extend the schema, but must stay minimal.

It must support at least:

- recording project decisions;
- changing task status;
- recording task events;
- generating a project brief from ledger state;
- restart-safe recall of decisions and task transitions.

Recommended minimal additions:

```text
decisions
```

Decision records should include:

```text
id
public_id
contour_id
mandate_id
message_id nullable
title
decision_text
status
created_at
```

The existing tables should continue to carry receipts and claims. Do not create a separate truth system.

### 5.3 Receipt and claim constraints

Every state-changing command must create a receipt.

At minimum:

- `project.decision.recorded` must create receipt + claim;
- `task.status.changed` must create receipt + claim;
- `task.event.recorded` must create receipt + claim;
- `project.brief.generated` may create a receipt only if it writes state; read-only brief generation should not mutate state.

Claims must not be stronger than receipts.

Correct:

```text
Decision recorded: DEC-...
Receipt: RCPT-...
```

Incorrect:

```text
Decision implemented.
```

### 5.4 Policy constraints

Allowed internal actions:

- `internal.decision.record`;
- `internal.task.status_change`;
- `internal.task.event`;
- `internal.project_brief.read`.

Blocked or absent:

- external send/share/publish;
- GitHub push/PR/merge;
- payment;
- legal commitment;
- sensitive data disclosure;
- destructive action;
- external agent delegation.

Policy decisions for evaluated state-changing actions must be represented in ledger state.

### 5.5 Public repository safety

Because the repository is public, do not commit:

- `.env`;
- tokens;
- credentials;
- SQLite DB files;
- logs;
- real personal tasks;
- private documents;
- real messages;
- real receipts with private URLs.

---

## 6. Required behavior

### 6.1 Record a decision

Provide a CLI command:

```bash
python -m verace_runtime.cli record-decision \
  --db .runtime/verace.sqlite3 \
  --principal oleg \
  --contour verace_project \
  --title "Use Verace as umbrella brand" \
  --text "Verace remains the platform umbrella; TruthOps becomes Verace Truth."
```

It must:

- require initialized runtime seed;
- attach to active mandate;
- create a decision record;
- create receipt;
- create bounded claim;
- print public decision id and receipt id.

### 6.2 List decisions

Provide:

```bash
python -m verace_runtime.cli decisions --db .runtime/verace.sqlite3
```

Minimum output:

- public decision id;
- status;
- contour;
- title;
- created timestamp or stable ordering.

### 6.3 Change task status

Provide:

```bash
python -m verace_runtime.cli set-task-status \
  --db .runtime/verace.sqlite3 \
  --task TR-000001 \
  --status done \
  --note "Merged in PR #1"
```

Allowed statuses for this brief:

```text
open
waiting
blocked
done
canceled
```

It must:

- update task status;
- create task event;
- create receipt;
- create claim;
- reject unknown statuses;
- preserve restart-safe state.

### 6.4 Add task event

Provide:

```bash
python -m verace_runtime.cli add-task-event \
  --db .runtime/verace.sqlite3 \
  --task TR-000001 \
  --event-type "review.note" \
  --summary "Needs architecture review before merge"
```

It must:

- attach event to existing task;
- create receipt;
- create claim;
- not imply external completion.

### 6.5 Project brief

Provide:

```bash
python -m verace_runtime.cli project-brief --db .runtime/verace.sqlite3
```

Minimum output:

- runtime status counts;
- open/waiting/blocked task list;
- latest decisions;
- recent task events;
- doctor status;
- no raw stack trace;
- no private data beyond what is already in local DB.

This command should be read-only.

### 6.6 Restart recovery

Tests must prove:

1. initialize DB;
2. create task;
3. record decision;
4. change task status;
5. create new service instance;
6. read project brief / decisions / task detail;
7. verify state survived.

---

## 7. Implementation plan

Codex should implement in this order:

1. Preflight and repo sync check.
2. Copy BRIEF-TR002 into `docs/briefs/`.
3. Create branch `work/brief-tr002-project-operating-memory`.
4. Extend schema minimally with `decisions`.
5. Add repository methods for decisions, task status changes, and task events.
6. Extend policy engine with internal action classes.
7. Extend service layer.
8. Extend CLI.
9. Add tests.
10. Update README only if command quickstart changes materially.
11. Update PROJECT_STATE, WORKLOG, RISK_REGISTER.
12. Commit and push branch.
13. Open PR; do not merge.

---

## 8. Tests

Use `pytest`.

Required tests:

1. `test_project_decisions.py`
   - recording a decision creates decision + receipt + claim;
   - decisions list is stable;
   - decision survives restart.

2. `test_task_status_transitions.py`
   - valid status transition updates task;
   - invalid status rejected;
   - status transition creates event + receipt + claim.

3. `test_project_brief.py`
   - project brief includes open/waiting/blocked task state;
   - project brief includes latest decision;
   - project brief does not mutate receipt/claim counts.

4. `test_project_memory_restart.py`
   - task + decision + status transition survive new service instance.

5. `test_cli_project_memory.py`
   - CLI smoke for `record-decision`, `decisions`, `set-task-status`, `add-task-event`, `project-brief`.

Existing BRIEF-TR001 tests must remain green.

No test may require network access.

No test may use real personal data.

---

## 9. Acceptance criteria

The implementation is accepted only when:

- BRIEF-TR002 is present under `docs/briefs/`;
- CLI can record and list decisions;
- CLI can change task status with receipt-backed event;
- CLI can add task event with receipt-backed claim;
- CLI can produce read-only project brief;
- every state-changing command creates a receipt;
- project brief does not mutate state;
- restart recovery is proven;
- all tests pass locally;
- GitHub Actions passes on PR;
- working tree is clean after commit;
- no secrets, DB files, logs, or real private data are committed;
- ADR-TR002/003/004/005, PLAN-TR001, and BRIEF-TR001 body are unchanged;
- Codex report includes receipts for commands, tests, git state, branch, and PR state.

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
- PR URL;
- changed files;
- commands run;
- test output summary;
- GitHub Actions status;
- final `git status`;
- confirmation that no runtime DB/secrets/logs/private data were committed;
- confirmation that no external actions were implemented;
- known limitations;
- whether acceptance criteria are fully met.

---

## 12. Expected result after this brief

After BRIEF-TR002, Verace Trust Runtime should have its first project operating memory:

```text
local CLI
  → SQLite ledger
  → tasks + decisions + events
  → receipt-backed state transitions
  → read-only project brief
  → restart-safe recall
```

This is still not the conversational assistant.

It is the assistant’s project memory before the assistant gets a mouth.
