# BRIEF-TR005: Response Claim Renderer

**Status:** Issued v1.0  
**Date:** 2026-05-24  
**Owner:** Oleg Dolgikh  
**Issued by:** Chief Architect  
**Project:** Verace — Trust Runtime  
**Scope:** Phase 1 — Founder Assistant Seed; deterministic human-facing system-action claim rendering boundary  
**Governing ADRs:** ADR-TR002, ADR-TR003, ADR-TR004, ADR-TR005, ADR-TR006, ADR-TR007  
**Governing Plan:** PLAN-TR001  
**Related governance:** FAILURE_CLASS_CLOSURE, SESSION_PROTOCOL  
**Depends on:** BRIEF-TR001 merged in PR #1; BRIEF-TR002 merged in PR #2; BRIEF-TR003 merged in PR #3; BRIEF-TR004 merged in PR #4  

---

## 1. Goal

Implement the first deterministic **Response Claim Renderer** for Verace Runtime.

This brief does **not** build a conversational assistant, Telegram bot, LLM provider adapter, artifact pipeline, external-send system, or arbitrary natural-language truth validator.

It adds the boundary required by ADR-TR007:

```text
ledger / receipt / claim / doctor state
        ↓
allowed visible system-action claim
        ↓
receipt-rendered human-facing prose
```

The result must make this fact true:

> Verace Runtime can produce human-facing statements about its own actions only when those statements are rendered from, or validated against, receipt-backed runtime state.

---

## 2. Context

The current runtime already has:

- SQLite ledger;
- schema versioning and migration runner;
- fail-closed unsafe DB handling;
- tasks;
- decisions;
- review queue;
- session brief;
- receipts;
- claims;
- doctor/audit coverage;
- Failure-Class Closure governance.

ADR-TR007 now requires a deterministic boundary before channel or LLM work.

The LLM may later draft tone and style, but it may not invent operational facts. This implementation must keep LLM entirely out of the path.

The governing chain remains:

```text
mandate → policy → action → receipt → claim → ledger → review/audit
```

BRIEF-TR005 adds the first user-facing rendering step:

```text
ledger → allowed claim → rendered statement
```

---

## 3. Non-goals

Do not implement:

- Telegram bot;
- web UI;
- LLM provider adapter;
- response generation with a model;
- arbitrary natural-language validation;
- validation of all world claims;
- Verace Truth backend integration;
- MCP/A2A/AP2/VC integration;
- external sending, publishing, GitHub mutation, email, calendar, payments, legal actions;
- artifact generation or delivery pipeline;
- approval execution or approval grants;
- multi-agent orchestration;
- old Verace TruthOps backend import;
- backup/restore product design.

Do not create runtime databases, logs, secrets, or private records that are committed to git.

Do not change ADR-TR002/003/004/005/006/007, PLAN-TR001, or BRIEF-TR001/002/003/004 bodies.

---

## 4. Files / areas

Work only inside:

```text
/Users/ovd/Documents/VERACE/TRUST_RUNTIME
```

Expected implementation areas:

```text
src/verace_runtime/
  rendering/__init__.py
  rendering/models.py
  rendering/renderer.py
  app/service.py
  cli.py
  ledger/repository.py
  ledger/review_repository.py

tests/
  test_response_claim_renderer.py
  test_renderer_failure_class_closure.py
  test_renderer_cli.py
  test_renderer_read_only.py

docs/briefs/
  BRIEF-TR005-Response-Claim-Renderer.md

docs/ops/
  PROJECT_STATE.md
  WORKLOG.md
  RISK_REGISTER.md
```

Allowed only if useful to preserve the line-count gate:

```text
src/verace_runtime/rendering/receipt_views.py
src/verace_runtime/rendering/templates.py
```

Allowed only if command quickstart changes materially:

```text
README.md
```

No other files unless justified in Codex report.

---

## 5. Constraints

### 5.1 Runtime constraints

- Use Python.
- Use SQLite.
- Keep runtime dependencies empty.
- Keep `pytest` in dev optional dependencies only.
- Use deterministic code and raw SQL / small repository methods.
- Keep every Python file under 300 lines.
- No network access in tests.
- No provider SDK.
- No secrets.
- No binary DB fixtures.
- Test fixtures must be synthetic.
- Do not weaken receipt/claim/foreign-key/schema/review invariants.

### 5.2 Rendering constraints

The renderer must be deterministic.

The renderer must not ask an LLM to rewrite, repair, validate, or classify.

The renderer must return structured output, not only strings. Minimum shape:

```text
ok: bool
text: str
claim_class: str
source: receipt | doctor | ledger | synthetic_receipt_view | refusal
receipt_public_id: optional str
reason: optional str
```

Exact model names are implementation detail.

### 5.3 Receipt/claim constraints

A system-action statement must be emitted only when the required backing state exists.

Minimum current runtime classes:

| Claim class | Required backing |
|---|---|
| task_recorded | task row + task creation receipt + task claim |
| decision_recorded | decision row + decision receipt + decision claim |
| review_created | review item + creation event + receipt + claim |
| review_resolved | resolved review item + resolution event + receipt + claim |
| review_dismissed | dismissed review item + dismissal event + receipt + claim |
| schema_healthy | doctor/schema state says ok/current |
| action_blocked | blocked policy receipt + blocked claim |

Future/synthetic classes for tests only:

| Claim class | Required backing |
|---|---|
| artifact_created | artifact receipt fields: format/name/status |
| external_send_completed | external send receipt state = sent |
| tests_passed | check receipt state = passed |

If backing is absent or malformed, renderer must fail closed or repair from actual receipt fields.

### 5.4 Prose constraints

Renderer output must not overclaim.

Allowed:

```text
Task TR-000001 recorded. Receipt: RCPT-...
Decision DEC-000001 recorded. Receipt: RCPT-...
Review REV-000001 resolved. Receipt: RCPT-...
Action blocked by policy: external.send. Receipt: RCPT-...
```

Not allowed:

```text
Task completed.
Decision implemented.
Review approved external action.
File sent.
PDF prepared.
Tests passed.
```

unless required backing state exists for those stronger claims.

### 5.5 Failure-Class Closure constraints

This brief must close the class:

```text
human-facing system-action prose diverges from receipt-backed runtime state
```

Required axes:

```text
action class: task / decision / review / schema / artifact / external_send / check
receipt state: ok / missing / malformed / wrong subject / wrong format / draft-vs-sent
claim state: present / missing / wrong subject / wrong type
schema state: current / unsafe
```

Unknown or malformed members must fail closed.

---

## 6. Required behavior

### 6.1 Render task-recorded statement

Provide service-level rendering for a task that was recorded through `ingest-message`.

Example allowed output:

```text
Task TR-000001 recorded. Receipt: RCPT-000001.
```

It must not say:

```text
Task completed.
```

### 6.2 Render decision-recorded statement

Provide rendering for a recorded decision.

Example:

```text
Decision DEC-000001 recorded. Receipt: RCPT-000002.
```

It must not say:

```text
Decision implemented.
```

### 6.3 Render review lifecycle statements

Provide rendering for:

- review created;
- review resolved;
- review dismissed.

A resolved/dismissed statement must require lifecycle event + receipt + claim.

### 6.4 Render schema/doctor statements

Render schema health only from doctor/schema state.

Allowed:

```text
Runtime schema is current: verace_runtime v2.
```

If doctor reports unsafe schema, renderer must not say healthy.

### 6.5 Render blocked action statement

Render blocked policy actions only from blocked policy receipt/claim.

Allowed:

```text
Action blocked by policy: external.send. Receipt: RCPT-...
```

It must not say action was executed.

### 6.6 Synthetic future-class tests

Without adding artifact/external-send/check features to the runtime, implement pure renderer tests that prove:

- receipt says `docx`, proposed/user-visible text cannot say `pdf`;
- external send state `draft` cannot render as `sent`;
- tests/check state missing cannot render as `tests passed`;
- unknown artifact format fails closed.

These may use small in-memory receipt-view objects and must not create product features.

### 6.7 CLI visibility

Add a read-only CLI surface for rendering current runtime state.

Recommended command:

```bash
python -m verace_runtime.cli render-claim --db .runtime/verace.sqlite3 --claim-class task_recorded --subject TR-000001
```

Supported initial claim classes:

```text
task_recorded
decision_recorded
review_created
review_resolved
review_dismissed
schema_healthy
```

If unsupported or under-evidenced, exit non-zero with explicit error and no raw traceback.

The command must be read-only.

---

## 7. Implementation plan

Codex should implement in this order:

1. Preflight and repo sync check.
2. Copy BRIEF-TR005 into `docs/briefs/`.
3. Create branch `work/brief-tr005-response-claim-renderer`.
4. Add small rendering package.
5. Add repository read methods only where required.
6. Add service methods for rendering supported current claim classes.
7. Add read-only CLI `render-claim`.
8. Add Failure-Class Closure tests for current and synthetic future classes.
9. Update PROJECT_STATE, WORKLOG, RISK_REGISTER.
10. Commit and push branch.
11. Open PR; do not merge.

---

## 8. Tests

Use `pytest`.

Required tests:

1. `test_response_claim_renderer.py`
   - renders task recorded only with task receipt + claim;
   - renders decision recorded only with decision receipt + claim;
   - renders review created only with creation event + receipt + claim;
   - renders review resolved/dismissed only with lifecycle event + receipt + claim;
   - renders schema healthy only when doctor says ok/current;
   - renders blocked action only from blocked policy receipt/claim.

2. `test_renderer_failure_class_closure.py`
   - artifact format mismatch repairs or refuses: receipt `docx`, proposed `pdf`;
   - unknown artifact format fails closed;
   - draft external-send receipt cannot render as sent;
   - missing check receipt cannot render tests passed;
   - wrong subject receipt fails closed;
   - wrong claim type fails closed.

3. `test_renderer_cli.py`
   - CLI smoke for `render-claim task_recorded`;
   - CLI smoke for `render-claim decision_recorded`;
   - CLI smoke for `render-claim review_created`;
   - CLI smoke for `render-claim review_resolved`;
   - unsupported claim class exits non-zero without raw traceback.

4. `test_renderer_read_only.py`
   - renderer does not change full `status()` counts;
   - `render-claim` CLI does not create receipts, claims, events, reviews, tasks, or decisions.

Existing BRIEF-TR001/002/003/004 tests must remain green.

No test may require network access.

No test may use real personal data.

---

## 9. Manual CLI smoke

Use a disposable DB:

```bash
rm -rf .runtime-test
python -m verace_runtime.cli init --db .runtime-test/verace.sqlite3
python -m verace_runtime.cli ingest-message --db .runtime-test/verace.sqlite3 --principal oleg --contour verace_project --text "Подготовить тестовую задачу"
python -m verace_runtime.cli record-decision --db .runtime-test/verace.sqlite3 --principal oleg --contour verace_project --title "Renderer decision" --text "Synthetic decision for renderer smoke."
python -m verace_runtime.cli add-review --db .runtime-test/verace.sqlite3 --principal oleg --contour verace_project --title "Renderer review" --body "Synthetic review item." --review-type architecture --priority high --task TR-000001
python -m verace_runtime.cli resolve-review --db .runtime-test/verace.sqlite3 --review REV-000001 --resolution "Synthetic resolution."
python -m verace_runtime.cli render-claim --db .runtime-test/verace.sqlite3 --claim-class task_recorded --subject TR-000001
python -m verace_runtime.cli render-claim --db .runtime-test/verace.sqlite3 --claim-class decision_recorded --subject DEC-000001
python -m verace_runtime.cli render-claim --db .runtime-test/verace.sqlite3 --claim-class review_resolved --subject REV-000001
python -m verace_runtime.cli doctor --db .runtime-test/verace.sqlite3
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
python -m verace_runtime.cli schema-status --db .runtime-test/unversioned.sqlite3
python -m verace_runtime.cli doctor --db .runtime-test/unversioned.sqlite3
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

## 10. Acceptance criteria

The implementation is accepted only when:

- BRIEF-TR005 is present under `docs/briefs/`;
- Response Claim Renderer exists as a deterministic module;
- renderer can render current runtime task/decision/review/schema statements from evidence;
- renderer refuses or repairs unsupported system-action claims;
- renderer includes Failure-Class Closure tests over the required axes;
- read-only render paths do not mutate ledger state;
- CLI `render-claim` works for supported current claim classes;
- CLI `render-claim` fails cleanly for unsupported/under-evidenced claims;
- `python -m pytest` passes;
- GitHub Actions passes on PR;
- healthy manual CLI smoke passes;
- unsafe DB smoke passes without false healthy claim;
- forbidden file scan is empty;
- line-count gate passes;
- no secrets, DB files, logs, or real private data are committed;
- no Telegram/LLM/external API/payment/legal/sensitive/destructive flow is added;
- ADR-TR002/003/004/005/006/007, PLAN-TR001, and BRIEF-TR001/002/003/004 bodies are unchanged;
- Codex report includes receipts for commands, tests, git state, branch, PR state, and Failure-Class Closure.

---

## 11. Required Failure-Class Closure report

Codex final report for this brief must include:

```text
Failure class:
Human-facing system-action prose can diverge from receipt-backed runtime state.

Axis of variation:
claim class, receipt state, claim state, subject match, artifact format, delivery state, schema state.

Invariant:
System-action prose is rendered from runtime evidence or fails closed.

Parametric tests:
List the tests covering the axis.

Ugly/unknown member behavior:
Unsupported claim class, unknown format, missing receipt, wrong subject, draft-vs-sent state.

Receipt/claim boundary:
Which statements can be rendered from which receipt/claim rows or synthetic receipt views.

Residual risk:
What is not covered until artifact/channel/LLM layers exist.
```

---

## 12. Rollback / safety

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

## 13. Done definition

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
- Failure-Class Closure section;
- final `git status`;
- confirmation that no runtime DB/secrets/logs/private data were committed;
- confirmation that no external actions or integrations were implemented;
- known limitations;
- whether acceptance criteria are fully met.

---

## 14. Expected result after this brief

After BRIEF-TR005, Verace Trust Runtime should have its first deterministic human-facing rendering boundary:

```text
local CLI
  → SQLite ledger
  → tasks + decisions + review queue + doctor
  → receipt-backed renderable statements
  → refusal / repair for unsupported system-action prose
```

This is still not the conversational assistant.

It is the assistant's truth-preserving mouthguard before the assistant gets a mouth.
