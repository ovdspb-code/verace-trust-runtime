# BRIEF-TR004: Review Queue and Session Brief

**Status:** Issued v1.0  
**Date:** 2026-05-24  
**Owner:** Oleg Dolgikh  
**Issued by:** Chief Architect  
**Project:** Verace — Trust Runtime  
**Scope:** Phase 1 — Founder Assistant Seed; review queue and session-level project recall on top of Ledger Seed, Project Memory, and Schema Safety  
**Governing ADRs:** ADR-TR002, ADR-TR003, ADR-TR004, ADR-TR005, ADR-TR006  
**Governing Plan:** PLAN-TR001  
**Depends on:** BRIEF-TR001 merged in PR #1; BRIEF-TR002 merged in PR #2; BRIEF-TR003 merged in PR #3  

---

## 1. Goal

Extend the local Verace Runtime with the first explicit **Review Queue** and **Session Brief** capability.

This brief does **not** build a conversational assistant, Telegram bot, LLM integration, workflow engine, approval execution system, or external-action system.

It makes the runtime capable of answering, from durable ledger state:

```text
what needs review?
what is waiting?
what changed recently?
what should Oleg look at before the next Codex/task session?
```

The result must make this fact true:

> Oleg can start a Verace work session by asking the local runtime for a review-aware session brief, without relying on chat history or model memory.

---

## 2. Context

BRIEF-TR001 created the first executable ledger spine:

```text
local CLI
  → SQLite ledger
  → contour / mandate / task
  → event / receipt / claim
  → status / doctor
  → restart recovery
```

BRIEF-TR002 added project operating memory:

```text
tasks + decisions + events
  → receipt-backed state transitions
  → read-only project brief
  → restart-safe recall
```

BRIEF-TR003 added schema safety:

```text
runtime_meta
  → schema_version
  → migration runner
  → fail-closed unsafe DB handling
  → doctor/schema-status visibility
```

BRIEF-TR004 adds the missing human-control layer before any channel or LLM work: explicit review items and session-level recall.

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
- approval execution or approval grants;
- multi-agent orchestration;
- generic plugin system;
- enterprise RBAC;
- backup/restore product design;
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
  ledger/migrations.py
  policy/engine.py
  receipts/factory.py

tests/
  test_review_queue.py
  test_review_resolution.py
  test_session_brief.py
  test_review_restart.py
  test_cli_review_session.py

docs/ops/
  PROJECT_STATE.md
  WORKLOG.md
  RISK_REGISTER.md
```

Allowed if useful to preserve the line-count gate:

```text
src/verace_runtime/app/review_queue.py
src/verace_runtime/app/session_brief.py
src/verace_runtime/ledger/review_repository.py
```

Allowed if command quickstart changes materially:

```text
README.md
```

No other files unless justified in the Codex report.

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

### 5.2 Schema and migration constraints

The implementation may extend schema only through the migration discipline introduced by BRIEF-TR003.

Required:

- schema version must advance from `1` to `2` if schema changes;
- new schema metadata must remain visible through `schema-status` and `doctor`;
- current-version fresh DB initialization must create the new tables;
- migration from v1 to v2 must be deterministic and tested;
- unversioned non-empty DB must still fail closed;
- unknown/newer/malformed schema must still fail closed.

Recommended minimal additions:

```text
review_items
review_events
```

`review_items` should represent pending or resolved human review work.

`review_events` should provide receipt-backed lifecycle evidence for review item creation and resolution.

### 5.3 Line-count constraint

Keep every Python code file under 300 lines.

If adding review/session behavior would push `service.py` or `repository.py` over the limit, split review-specific logic into small modules. Do not let the first runtime become a warehouse file with a login prompt.

### 5.4 Receipt and claim constraints

Every state-changing review command must create a receipt.

At minimum:

- `review.item.created` must create receipt + review event + claim;
- `review.item.resolved` must create receipt + review event + claim;
- `review.item.dismissed` must create receipt + review event + claim if dismissal is implemented;
- `session.brief.generated` must **not** create a receipt if it is read-only.

Claims must not be stronger than receipts.

Correct:

```text
Review item created: REV-...
Receipt: RCPT-...
```

Incorrect:

```text
Issue reviewed and approved.
```

A resolved review item does not grant approval for external action. Approval remains a distinct future capability.

### 5.5 Policy constraints

Allowed internal actions:

- `internal.review.create`;
- `internal.review.resolve`;
- `internal.review.read`;
- `internal.session_brief.read`.

Blocked or absent:

- external send/share/publish;
- GitHub push/PR/merge;
- payment;
- legal commitment;
- sensitive data disclosure;
- destructive action;
- external agent delegation.

Policy decisions for evaluated state-changing review actions must be represented in ledger state.

### 5.6 Public repository safety

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

### 6.1 Add a review item

Provide a CLI command:

```bash
python -m verace_runtime.cli add-review \
  --db .runtime/verace.sqlite3 \
  --principal oleg \
  --contour verace_project \
  --title "Review ADR-TR006 migration policy" \
  --body "Check whether fail-closed behavior is sufficient before next persistent feature." \
  --review-type architecture \
  --priority high
```

Optional:

```bash
--task TR-000001
```

Allowed `review_type` values for this brief:

```text
architecture
decision
risk
clarification
evidence
approval_request
```

Allowed `priority` values:

```text
low
normal
high
critical
```

It must:

- require initialized runtime seed;
- attach to active mandate;
- optionally attach to a task;
- create a review item with public id `REV-...`;
- create receipt;
- create review event;
- create bounded claim;
- print public review id and receipt id.

### 6.2 List review items

Provide:

```bash
python -m verace_runtime.cli reviews --db .runtime/verace.sqlite3
```

Optional:

```bash
--status open
```

Minimum output:

- public review id;
- status;
- priority;
- review type;
- contour;
- optional task ref;
- title;
- created timestamp or stable ordering.

Default listing should show open review items.

### 6.3 Resolve a review item

Provide:

```bash
python -m verace_runtime.cli resolve-review \
  --db .runtime/verace.sqlite3 \
  --review REV-000001 \
  --resolution "Reviewed. Proceed with BRIEF-TR003 merge after green CI."
```

It must:

- update review item status to `resolved`;
- store resolution text;
- create review event;
- create receipt;
- create claim;
- preserve restart-safe state.

Optional status values for this brief:

```text
resolved
dismissed
```

If `dismissed` is implemented, it must still create receipt + event + claim.

### 6.4 Session brief

Provide:

```bash
python -m verace_runtime.cli session-brief --db .runtime/verace.sqlite3
```

Minimum output:

- doctor status;
- schema status;
- open/waiting/blocked task list;
- open review item list;
- latest decisions;
- recent task/review events;
- count summary;
- no raw stack trace;
- no private data beyond what is already in local DB.

This command must be read-only.

It must not create receipts, claims, review events, task events, messages, or decisions.

### 6.5 Doctor coverage

`doctor` must check review queue invariants:

- review item creation is receipt-backed;
- review item creation has a claim;
- review events have receipts;
- resolved/dismissed review items have a resolution text;
- review item statuses are valid.

Doctor output should expose compact booleans, for example:

```text
review_event_receipt_ok
review_item_receipt_ok
review_item_claim_ok
review_resolution_ok
```

### 6.6 Restart recovery

Tests must prove:

1. initialize DB;
2. create task;
3. create review item;
4. resolve review item;
5. create new service instance;
6. read reviews / session brief / doctor;
7. verify state survived.

---

## 7. Implementation plan

Codex should implement in this order:

1. Preflight and repo sync check.
2. Copy BRIEF-TR004 into `docs/briefs/`.
3. Create branch `work/brief-tr004-review-queue-session-brief`.
4. Add schema migration from v1 to v2 using the existing migration runner.
5. Add `review_items` and `review_events`.
6. Add repository methods for review queue operations.
7. Extend policy engine with internal review/session action classes.
8. Extend service layer.
9. Extend CLI.
10. Extend doctor.
11. Add tests.
12. Update README only if command quickstart changes materially.
13. Update PROJECT_STATE, WORKLOG, RISK_REGISTER.
14. Commit and push branch.
15. Open PR; do not merge.

---

## 8. Tests

Use `pytest`.

Required tests:

1. `test_review_queue.py`
   - adding a review item creates review item + review event + receipt + claim;
   - review list defaults to open items;
   - review item can be attached to an existing task;
   - invalid priority/type is rejected before mutation.

2. `test_review_resolution.py`
   - resolving a review item updates state;
   - resolution creates review event + receipt + claim;
   - resolved item no longer appears in default open review list;
   - invalid review id is rejected without mutation.

3. `test_session_brief.py`
   - session brief includes open review items;
   - session brief includes open/waiting/blocked tasks;
   - session brief includes latest decisions;
   - session brief is read-only and does not change full `status()` counts.

4. `test_review_restart.py`
   - review item and resolution survive new service instance.

5. `test_cli_review_session.py`
   - CLI smoke for `add-review`, `reviews`, `resolve-review`, `session-brief`, `doctor`.

6. Schema/migration tests
   - fresh DB initializes at schema version `2`;
   - migration from v1 to v2 applies once;
   - v1 DB with synthetic data migrates without weakening receipt/claim/foreign-key invariants;
   - unsafe DB fail-closed tests remain green.

Existing BRIEF-TR001/002/003 tests must remain green.

No test may require network access.

No test may use real personal data.

---

## 9. Acceptance criteria

The implementation is accepted only when:

- BRIEF-TR004 is present under `docs/briefs/`;
- CLI can create, list, and resolve review items;
- CLI can produce read-only session brief;
- every review state-changing command creates a receipt;
- review lifecycle is visible through events and claims;
- doctor checks review queue invariants;
- schema version advances through migration discipline;
- migration from v1 to v2 is tested;
- session brief does not mutate state;
- restart recovery is proven;
- all tests pass locally;
- GitHub Actions passes on PR;
- working tree is clean after commit;
- no secrets, DB files, logs, or real private data are committed;
- ADR-TR002/003/004/005/006, PLAN-TR001, and BRIEF-TR001/002/003 bodies are unchanged;
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

After BRIEF-TR004, Verace Trust Runtime should have its first review-aware project operating surface:

```text
local CLI
  → SQLite ledger
  → tasks + decisions + review queue
  → receipt-backed review lifecycle
  → read-only session brief
  → doctor/audit coverage
  → restart-safe recall
```

This is still not the conversational assistant.

It is the assistant’s review desk before the assistant gets a mouth.
