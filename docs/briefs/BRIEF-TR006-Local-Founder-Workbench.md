# BRIEF-TR006: Local Founder Workbench

**Status:** Issued v1.0  
**Date:** 2026-05-24  
**Owner:** Oleg Dolgikh  
**Issued by:** Chief Architect  
**Project:** Verace — Trust Runtime  
**Scope:** Phase 1 — Founder Assistant Seed; local daily-use founder workbench on top of ledger, project memory, review queue, schema safety, and response claim rendering  
**Governing ADRs:** ADR-TR002, ADR-TR003, ADR-TR004, ADR-TR005, ADR-TR006, ADR-TR007  
**Governing Plan:** PLAN-TR001  
**Related governance:** FAILURE_CLASS_CLOSURE, SESSION_PROTOCOL  
**Depends on:** BRIEF-TR001 merged in PR #1; BRIEF-TR002 merged in PR #2; BRIEF-TR003 merged in PR #3; BRIEF-TR004 merged in PR #4; BRIEF-TR005 merged in PR #5

---

## 1. Goal

Implement the first **Local Founder Workbench** for Oleg.

This brief changes the project mode from foundation-building to product-loop proof.

The result must make this true:

> Oleg can use Verace Runtime locally as a daily working tool without remembering the internal `python -m verace_runtime.cli ...` command surface.

The workbench is a thin local product layer over existing runtime capabilities. It must expose a short, practical command surface for:

```text
current session brief
capturing a task
recording a decision
creating / listing / resolving review items
checking runtime health
rendering receipt-backed human-facing statements
```

This is still not Telegram, not LLM, not a channel adapter, and not an autonomous assistant.

It is the first usable local operating surface for the founder loop.

---

## 2. Product Effect

After this brief, Oleg should be able to run:

```bash
verace init
verace brief
verace add "Подготовить план следующей Codex-сессии"
verace decision "Product mode" --text "After BRIEF-TR005, work shifts to founder daily-use loop."
verace review add "Check next workbench output" --body "Confirm output is useful for Oleg." --type architecture --priority high
verace review list
verace review resolve REV-000001 --resolution "Reviewed. Proceed."
verace doctor
```

without needing to know internal table names, claim classes, or receipt implementation details.

The workbench must use receipt-rendered prose for state-changing success statements.

---

## 3. Non-goals

Do not implement:

- Telegram bot;
- web UI;
- LLM provider adapter;
- model-generated responses;
- arbitrary natural-language validation;
- Verace Truth backend integration;
- MCP/A2A/AP2/VC integration;
- external sending, publishing, GitHub mutation, email, calendar, payments, legal actions;
- artifact generation or delivery pipeline;
- approval execution or approval grants;
- multi-agent orchestration;
- old Verace TruthOps backend import;
- backup/restore product design.

Do not create runtime databases, logs, secrets, or private records that are committed to git.

Do not change ADR-TR002/003/004/005/006/007, PLAN-TR001, or BRIEF-TR001/002/003/004/005 bodies.

---

## 4. Files / areas

Work only inside:

```text
/Users/ovd/Documents/VERACE/TRUST_RUNTIME
```

Expected implementation areas:

```text
src/verace_runtime/workbench/__init__.py
src/verace_runtime/workbench/cli.py
src/verace_runtime/workbench/formatting.py
src/verace_runtime/app/service.py
pyproject.toml
README.md

tests/test_workbench_cli.py
tests/test_workbench_product_loop.py
tests/test_workbench_rendered_outputs.py
tests/test_workbench_read_only.py

docs/briefs/BRIEF-TR006-Local-Founder-Workbench.md
docs/ops/PROJECT_STATE.md
docs/ops/WORKLOG.md
docs/ops/RISK_REGISTER.md
```

Allowed only if needed to preserve line-count gate:

```text
src/verace_runtime/workbench/commands.py
src/verace_runtime/workbench/session.py
```

No other files unless justified in the Codex report.

---

## 5. Constraints

### 5.1 Runtime constraints

- Use Python.
- Use SQLite.
- Keep runtime dependencies empty.
- Keep `pytest` in dev optional dependencies only.
- Use deterministic code.
- Keep every Python file under 300 lines.
- No network access in tests.
- No provider SDK.
- No secrets.
- No binary DB fixtures.
- Test fixtures must be synthetic.
- Do not weaken receipt/claim/foreign-key/schema/review/rendering invariants.

### 5.2 Product constraints

The workbench must be usable with short commands.

Default DB path:

```text
.runtime/verace.sqlite3
```

Environment override:

```text
VERACE_RUNTIME_DB=/path/to/verace.sqlite3
```

Default principal and contour:

```text
principal = oleg
contour = verace_project
```

These defaults may be overridden by flags, but the normal founder path should not require flags.

### 5.3 Rendering constraints

State-changing workbench commands must print receipt-rendered success statements through the Response Claim Renderer whenever supported.

At minimum:

- task creation uses `task_recorded`;
- decision recording uses `decision_recorded`;
- review creation uses `review_created`;
- review resolution uses `review_resolved` or `review_dismissed`.

If renderer cannot produce a statement, the workbench must fail closed or print an explicit failure, not invent prose.

### 5.4 UX constraints

The workbench output should be human-readable and compact.

Normal output must not expose raw internal IDs unless the public ID is intended for user reference:

Allowed:

```text
TR-000001
DEC-000001
REV-000001
RCPT-...
```

Avoid exposing raw UUID-like internal IDs in normal workbench output.

Diagnostics belong in `verace doctor`, not in every normal command.

---

## 6. Required behavior

### 6.1 Console command

Add a console script:

```text
verace
```

through `pyproject.toml`, for example:

```toml
[project.scripts]
verace = "verace_runtime.workbench.cli:main"
```

The existing `python -m verace_runtime.cli` remains available as the lower-level diagnostic CLI.

### 6.2 `verace init`

Initializes the runtime DB and prints compact state:

```text
Verace Runtime initialized.
Principal: oleg
Contour: verace_project
Mandate: MANDATE-FOUNDING-001
Receipt: RCPT-...
```

### 6.3 `verace brief`

Produces a founder-useful session brief.

Minimum sections:

```text
Verace Session Brief
Doctor: OK / FAIL
Schema: verace_runtime vN current=True/False
Open reviews
Open / waiting / blocked tasks
Latest decisions
Recent events
Counts
```

If doctor is not OK, the brief must say so clearly and include the compact reason.

The command must be read-only.

### 6.4 `verace add "..."`

Captures a task/note through existing runtime ingestion.

For a task, output must use receipt-rendered prose, for example:

```text
Task TR-000001 was recorded in the ledger. Receipt: RCPT-...
```

For note/status-only ingestion, output may report message receipt without overclaiming task creation.

### 6.5 `verace decision "TITLE" --text "..."`

Records a project decision.

Output must use receipt-rendered prose:

```text
Decision DEC-000001 was recorded in the ledger. Receipt: RCPT-...
```

### 6.6 `verace review add ...`

Creates a review item.

Required flags:

```text
--body
--type
--priority
```

Optional:

```text
--task TR-000001
```

Output must use receipt-rendered prose:

```text
Review REV-000001 was created. Receipt: RCPT-...
```

### 6.7 `verace review list`

Lists open review items by default.

Optional:

```text
--status open|resolved|dismissed|all
```

Output should show:

```text
REV-000001 | high | architecture | task=TR-000001 | title
```

### 6.8 `verace review resolve REV-... --resolution "..."`

Resolves a review item.

Optional:

```text
--status resolved|dismissed
```

Output must use receipt-rendered prose:

```text
Review REV-000001 was resolved. Receipt: RCPT-...
```

### 6.9 `verace doctor`

Runs existing doctor and prints compact health.

This is allowed to be more diagnostic than normal product commands.

---

## 7. Tests

Use `pytest`.

Required tests:

1. `test_workbench_cli.py`
   - `verace init` works against temp DB;
   - `verace brief` works;
   - `verace add` works;
   - `verace decision` works;
   - `verace review add/list/resolve` works;
   - `verace doctor` works.

2. `test_workbench_product_loop.py`
   - full founder loop:
     1. init;
     2. add task;
     3. record decision;
     4. add review attached to task;
     5. resolve review;
     6. brief shows current state;
     7. doctor OK.

3. `test_workbench_rendered_outputs.py`
   - state-changing outputs are receipt-rendered;
   - task output contains `Task TR-... was recorded` and `Receipt: RCPT-...`;
   - decision output contains `Decision DEC-... was recorded` and receipt;
   - review output contains `Review REV-... was created/resolved` and receipt;
   - no unsupported completion prose is emitted.

4. `test_workbench_read_only.py`
   - `verace brief`, `verace review list`, and `verace doctor` do not mutate full `status()` counts.

Existing BRIEF-TR001/002/003/004/005 tests must remain green.

No test may require network access.

No test may use real personal data beyond synthetic strings and the default seed `oleg` / `verace_project`.

---

## 8. Manual CLI smoke

Use a disposable DB:

```bash
rm -rf .runtime-test
export VERACE_RUNTIME_DB=.runtime-test/verace.sqlite3
verace init
verace brief
verace add "Подготовить тестовую задачу"
verace decision "Workbench decision" --text "Synthetic decision for local workbench smoke."
verace review add "Review workbench output" --body "Synthetic review item." --type architecture --priority high --task TR-000001
verace review list
verace review resolve REV-000001 --resolution "Synthetic resolution."
verace brief
verace doctor
unset VERACE_RUNTIME_DB
rm -rf .runtime-test
```

Unsafe DB smoke must remain green:

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
VERACE_RUNTIME_DB=.runtime-test/unversioned.sqlite3 verace doctor
rm -rf .runtime-test
```

Forbidden file scan:

```bash
find . -path ./.git -prune -o -type f \( -name "*.sqlite" -o -name "*.sqlite3" -o -name "*.db" -o -name "*.db-wal" -o -name "*.db-shm" -o -name "*.log" -o -name ".env" -o -name ".env.*" \) -print | sort
```

Line-count gate:

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

## 9. Acceptance criteria

The implementation is accepted only when:

- BRIEF-TR006 is present under `docs/briefs/`;
- console command `verace` exists;
- `verace init` works;
- `verace brief` produces a useful founder session brief;
- `verace add` records a task and prints receipt-rendered prose;
- `verace decision` records a decision and prints receipt-rendered prose;
- `verace review add/list/resolve` works;
- `verace doctor` works;
- read-only commands do not mutate ledger state;
- all state-changing workbench success statements are rendered from receipts where supported;
- `python -m pytest` passes;
- GitHub Actions passes on PR;
- healthy manual CLI smoke passes;
- unsafe DB smoke passes without false healthy claim;
- forbidden file scan is empty;
- line-count gate passes;
- no secrets, DB files, logs, or real private data are committed;
- no Telegram/LLM/external API/payment/legal/sensitive/destructive flow is added;
- ADR-TR002/003/004/005/006/007, PLAN-TR001, and BRIEF-TR001/002/003/004/005 bodies are unchanged;
- Codex report includes receipts for commands, tests, git state, branch, and PR state.

---

## 10. Product gate

This brief is accepted only if it produces a local tool Oleg can realistically use.

Engineering success alone is not sufficient.

Product acceptance requires that the workbench supports this real loop:

```text
start session
see current state
add task
record decision
create review
resolve review
see updated session brief
```

The system must become easier to use, not merely more correct internally.

---

## 11. Rollback / safety

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

## 12. Done definition

Codex final report must include:

- branch name;
- commit hash;
- PR URL;
- changed files;
- commands run;
- test output summary;
- GitHub Actions status;
- manual CLI smoke summary;
- unsafe DB smoke summary;
- forbidden file scan result;
- line-count result;
- final `git status`;
- confirmation that no runtime DB/secrets/logs/private data were committed;
- confirmation that no external actions or integrations were implemented;
- product effect summary: what Oleg can now do that he could not do before;
- known limitations;
- whether acceptance criteria are fully met.

---

## 13. Expected result after this brief

After BRIEF-TR006, Verace Trust Runtime should have its first local daily-use surface:

```text
verace
  → init
  → brief
  → add task
  → record decision
  → review queue
  → resolve review
  → doctor
```

This is still not the conversational assistant.

It is the first working founder workbench: small, local, boring, and useful.
