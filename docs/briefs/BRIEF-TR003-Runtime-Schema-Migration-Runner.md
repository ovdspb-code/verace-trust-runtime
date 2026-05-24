# BRIEF-TR003: Runtime Schema Migration Runner

**Status:** Issued v1.0  
**Date:** 2026-05-24  
**Owner:** Oleg Dolgikh  
**Issued by:** Chief Architect  
**Project:** Verace — Trust Runtime  
**Scope:** Phase 1 — Founder Assistant Seed; schema versioning and migration runner for the local runtime ledger  
**Governing ADRs:** ADR-TR002, ADR-TR004, ADR-TR005, ADR-TR006  
**Governing Plan:** PLAN-TR001  
**Depends on:** BRIEF-TR001 merged in PR #1; BRIEF-TR002 merged in PR #2; ADR-TR006 accepted  

---

## 1. Goal

Implement the first schema versioning and migration runner for the local Verace Runtime SQLite ledger.

This brief does **not** add new product features.

It makes the existing runtime safer by ensuring that the ledger schema is explicit, inspectable, and fail-closed when unsafe.

Required outcome:

```text
fresh DB
  → current schema created
  → runtime_meta written
  → doctor reports schema current

current DB
  → accepted

unknown/newer/corrupt DB
  → normal runtime commands fail closed

unversioned non-empty DB
  → normal runtime commands fail closed
  → doctor reports non-current/unknown state
```

The result must make this fact true:

> Verace Runtime can no longer silently treat an unknown or unversioned persistent ledger as current truth.

---

## 2. Context

BRIEF-TR001 created the first executable ledger seed.

BRIEF-TR002 extended that ledger into project operating memory.

ADR-TR006 now governs schema evolution:

- every durable runtime DB must expose an explicit schema version;
- fresh DBs are created from the current schema;
- known-version DBs are upgraded through deterministic migrations;
- unknown, newer, corrupted, or unversioned non-empty DBs fail closed;
- doctor exposes schema and migration state.

This brief implements the first lightweight version of that policy.

The current post-BRIEF-TR002 schema becomes the first governed baseline.

---

## 3. Non-goals

Do not implement:

- Telegram bot;
- web UI;
- LLM/provider integration;
- OpenAI/Claude/Gemini/Kimi integration;
- MCP/A2A/AP2/VC integration;
- Verace Truth backend integration;
- external API calls;
- external sending/publishing/GitHub mutation from runtime;
- payments/legal/sensitive/destructive flows;
- production multi-tenant migration orchestration;
- Alembic/PostgreSQL migration framework;
- encryption/key management;
- backup product design;
- down migrations;
- binary SQLite fixtures in repo.

Do not import old Verace TruthOps backend code.

Do not commit runtime DBs, logs, secrets, private messages, or real receipts.

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
  ledger/
    db.py
    schema.sql
    models.py
    repository.py
    migrations.py

tests/
  test_schema_metadata.py
  test_schema_fail_closed.py
  test_migration_runner.py
  test_doctor_schema_state.py
  test_cli_schema_status.py

docs/ops/
  PROJECT_STATE.md
  WORKLOG.md
  RISK_REGISTER.md
```

Allowed if useful:

```text
README.md
```

No other files unless justified in the Codex report.

---

## 5. Constraints

- Use Python.
- Use SQLite.
- Keep runtime dependencies empty.
- Keep pytest only in dev optional dependencies.
- Use raw SQL / small standard-library-first migration code.
- Keep every code file under 300 lines.
- No network access in tests.
- No provider SDK.
- No secrets.
- No binary DB fixtures.
- Test fixtures must be synthetic.
- Do not change ADR-TR002/003/004/005/006.
- Do not change PLAN-TR001.
- Do not change BRIEF-TR001 or BRIEF-TR002 bodies.
- Do not weaken receipt/claim/foreign-key invariants.
- Push branch and open PR.
- Do not merge PR.

---

## 6. Required behavior

### 6.1 Runtime metadata

Add `runtime_meta` to the schema.

Minimum contract:

```sql
runtime_meta(
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL
)
```

Required keys:

```text
schema_version
schema_name
created_at
last_migrated_at
```

Use:

```text
schema_name = verace_runtime
schema_version = 1
```

The exact constant names are implementation detail, but they must be centralized and tested.

### 6.2 Fresh DB initialization

For a fresh DB:

1. create the full current schema;
2. write runtime metadata;
3. seed founder/project state through existing service paths;
4. preserve existing receipt/claim behavior.

`init` must remain idempotent.

`doctor` must show:

```text
schema_version=1
schema_known=True
schema_current=True
migration_required=False
```

### 6.3 Current DB behavior

For a DB with current metadata:

- normal commands proceed;
- schema is not recreated destructively;
- migrations are not re-applied;
- doctor remains OK if other invariants pass.

### 6.4 Unversioned non-empty DB behavior

For an unversioned non-empty DB:

- normal mutating/runtime commands must fail closed;
- no automatic adoption;
- no silent metadata insertion;
- no destructive recreation;
- doctor must report the unsafe state.

Expected doctor fields:

```text
schema_known=False
schema_current=False
migration_required=True
ok=False
```

CLI normal commands should exit non-zero with an explicit error message, not a raw traceback.

### 6.5 Newer or unknown schema version behavior

For a DB with `schema_version` greater than the code’s current version:

- normal commands fail closed;
- doctor reports not current / unknown newer schema;
- no downgrade attempt.

For non-integer or malformed schema version:

- normal commands fail closed;
- doctor reports schema invalid.

### 6.6 Migration runner

Add a minimal migration runner abstraction.

It must support:

```text
current version detection
target version constant
ordered migration registry
migration_required flag
fail-closed unknown state
idempotent no-op when already current
```

No actual version 2 migration is required in this brief.

However, tests must prove runner discipline using either:

- a small in-memory synthetic migration registered only in tests; or
- a test-only migration hook that does not alter production registry.

The production registry may be empty after baseline version 1.

### 6.7 Doctor schema/audit state

Extend `doctor()` output with at least:

```text
schema_version
schema_known
schema_current
migration_required
schema_name
```

Existing doctor checks must remain:

```text
schema_ok
pragma_ok
integrity_ok
foreign_keys_ok
seed_ok
claim_receipt_ok
task_event_receipt_ok
outbox_receipt_ok
decision_receipt_ok
decision_claim_ok
```

`doctor` should remain read-only except for opening the DB.

If the DB is malformed or unsafe, doctor should return structured failure state rather than crash.

### 6.8 CLI schema visibility

Add a read-only CLI command:

```bash
python -m verace_runtime.cli schema-status --db .runtime/verace.sqlite3
```

Minimum output:

```text
Schema: verace_runtime
Version: 1
Known: True
Current: True
Migration required: False
```

For unsafe DBs, output must be explicit and non-misleading.

No raw stack traces.

### 6.9 Existing commands remain compatible

Existing commands must continue working on fresh/current DBs:

```text
init
ingest-message
tasks
task
status
doctor
record-decision
decisions
set-task-status
add-task-event
project-brief
```

`project-brief` must remain read-only.

All previous tests must remain green.

---

## 7. Suggested implementation shape

This is guidance, not mandatory file-level architecture.

### 7.1 Migration module

Create:

```text
src/verace_runtime/ledger/migrations.py
```

Suggested public objects:

```python
CURRENT_SCHEMA_NAME = "verace_runtime"
CURRENT_SCHEMA_VERSION = 1

class SchemaState(...)
class SchemaError(RuntimeError)
class Migration(...)
def inspect_schema_state(conn) -> SchemaState
def ensure_schema_current(conn, *, allow_create: bool = True) -> SchemaState
def doctor_schema_state(conn) -> dict[str, object]
```

Keep it small.

### 7.2 DB integration

`apply_schema(conn)` should no longer be an unconditional `executescript(schema.sql)` against any DB.

It should:

- create current schema only if DB is empty/fresh;
- accept current versioned DB;
- fail closed on unsafe DB;
- never silently adopt unversioned non-empty DB.

### 7.3 Doctor integration

`doctor()` must not blindly call mutating schema setup before inspection.

It should be able to inspect unsafe DBs and report failure.

For healthy DBs, it may call normal repository checks after schema state is verified.

---

## 8. Tests

Use `pytest`.

Required test coverage:

1. `test_schema_metadata.py`
   - fresh init writes `runtime_meta`;
   - schema version is `1`;
   - schema name is `verace_runtime`;
   - init remains idempotent.

2. `test_schema_fail_closed.py`
   - unversioned non-empty DB fails closed for normal command/service path;
   - newer schema version fails closed;
   - malformed schema version fails closed;
   - no automatic metadata adoption occurs.

3. `test_migration_runner.py`
   - current version is no-op;
   - migration registry applies ordered synthetic migration in test path;
   - migration runner does not reapply already-applied migration;
   - destructive migration kind is blocked by default if represented.

4. `test_doctor_schema_state.py`
   - healthy DB doctor includes schema fields and `ok=True`;
   - unsafe DB doctor returns `ok=False`;
   - schema failure does not produce raw traceback;
   - existing receipt/claim invariant checks still run when schema is healthy.

5. `test_cli_schema_status.py`
   - `schema-status` works on healthy DB;
   - `doctor` output includes schema state;
   - unsafe DB produces explicit failure state.

Existing tests from BRIEF-TR001 and BRIEF-TR002 must remain green.

No test may require network access.

No test may use real personal data.

No binary DB fixture may be committed.

---

## 9. Manual CLI smoke

Use disposable DBs only.

Healthy DB smoke:

```bash
rm -rf .runtime-test
python -m verace_runtime.cli init --db .runtime-test/verace.sqlite3
python -m verace_runtime.cli schema-status --db .runtime-test/verace.sqlite3
python -m verace_runtime.cli ingest-message --db .runtime-test/verace.sqlite3 --principal oleg --contour verace_project --text "Подготовить тестовую задачу"
python -m verace_runtime.cli record-decision --db .runtime-test/verace.sqlite3 --principal oleg --contour verace_project --title "Schema decision" --text "Synthetic schema decision."
python -m verace_runtime.cli project-brief --db .runtime-test/verace.sqlite3
python -m verace_runtime.cli doctor --db .runtime-test/verace.sqlite3
rm -rf .runtime-test
```

Unsafe DB smoke:

```bash
rm -rf .runtime-test
mkdir -p .runtime-test
python - <<'PY'
import sqlite3
conn = sqlite3.connect(".runtime-test/unversioned.sqlite3")
conn.execute("CREATE TABLE orphan_state(id TEXT PRIMARY KEY)")
conn.execute("INSERT INTO orphan_state(id) VALUES ('x')")
conn.commit()
conn.close()
PY
python -m verace_runtime.cli schema-status --db .runtime-test/unversioned.sqlite3
python -m verace_runtime.cli doctor --db .runtime-test/unversioned.sqlite3
rm -rf .runtime-test
```

The unsafe DB commands must not claim healthy/current state.

---

## 10. Forbidden file scan

Run before commit:

```bash
find . -path ./.git -prune -o -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-wal" -o -name "*.db-shm" -o -name "*.log" -o -name ".env" -o -name ".env.*" \) -print | sort
```

Stop if any forbidden file is returned.

---

## 11. Line-count gate

Run before commit:

```bash
python - <<'PY'
from pathlib import Path
bad = []
for p in list(Path("src").rglob("*.py")) + list(Path("tests").rglob("*.py")):
    n = len(p.read_text().splitlines())
    if n > 300:
        bad.append((str(p), n))
print("line_count_violations=", bad)
raise SystemExit(1 if bad else 0)
PY
```

---

## 12. Acceptance criteria

Implementation is accepted only when:

- BRIEF-TR003 exists under `docs/briefs/`;
- runtime metadata table exists;
- fresh DB init writes current schema version;
- normal commands work on current DB;
- unversioned non-empty DB fails closed;
- newer/unknown/malformed schema version fails closed;
- migration runner has ordered/idempotent behavior;
- doctor exposes schema state;
- schema-status CLI works;
- existing ledger/receipt/decision/project-brief tests remain green;
- `python -m pytest` passes;
- manual CLI smoke passes;
- forbidden file scan is empty;
- line-count gate passes;
- GitHub Actions passes on PR or exact failure is reported;
- no runtime DB/log/secret/private data is committed;
- no Telegram/LLM/external API/payment/legal/sensitive/destructive flow is added;
- ADR-TR002/003/004/005/006, PLAN-TR001, BRIEF-TR001, and BRIEF-TR002 bodies are unchanged.

---

## 13. Rollback / safety

If schema handling becomes larger than this brief, stop and report.

If tests fail, do not claim completion.

If an existing local DB would be rejected by the new rules, report clearly. Do not auto-adopt it.

If forbidden files appear, stop before commit.

If branch diverges, stop before merge/rebase.

If push fails, do not force-push.

Do not merge PR.

---

## 14. Done definition

Codex final report must include:

- branch name;
- commit hash;
- PR URL;
- changed files;
- commands run;
- pytest output summary;
- manual CLI smoke output summary;
- unsafe DB smoke output summary;
- forbidden file scan result;
- line-count check result;
- GitHub Actions status;
- final git status;
- confirmation that no runtime DB/secrets/logs/private data were committed;
- confirmation that no external actions or integrations were implemented;
- known limitations;
- whether acceptance criteria are fully met.

---

## 15. Expected result after this brief

After BRIEF-TR003, Verace Trust Runtime should have a governed schema foundation:

```text
SQLite ledger
  → runtime_meta
  → schema version
  → migration runner
  → fail-closed unsafe DB handling
  → doctor/schema-status visibility
  → tests proving the boundary
```

This still does not give the assistant a mouth.

It makes sure the assistant’s memory has a spine and a version number.
