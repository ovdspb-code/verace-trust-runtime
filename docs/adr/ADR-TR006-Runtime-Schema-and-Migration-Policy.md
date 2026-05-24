# ADR-TR006: Runtime Schema and Migration Policy

**Status:** Accepted v1.0  
**Date:** 2026-05-24  
**Ratified:** 2026-05-24 by Oleg Dolgikh  
**Owner:** Oleg Dolgikh  
**Project:** Verace — Trust Runtime  
**Scope:** Runtime ledger schema versioning, migration discipline, compatibility and safety policy  
**Governing ADRs:** ADR-TR002, ADR-TR004, ADR-TR005  
**Depends on:** BRIEF-TR001 merged in PR #1; BRIEF-TR002 merged in PR #2  

---

## 1. Decision

Verace Runtime must treat its SQLite ledger schema as a versioned contract, not as incidental implementation state.

From this ADR forward:

1. Every durable runtime database has an explicit schema version.
2. Fresh databases are created from the current schema snapshot.
3. Existing databases are upgraded through ordered migrations.
4. Runtime commands must refuse unsafe or unknown schema states.
5. Schema changes that affect trust invariants require tests and an explicit migration path.
6. No runtime database, backup, log, secret, or private record may be committed to the public repository.

The current post-BRIEF-TR002 schema becomes the first governed baseline for the lightweight runtime.

The goal is not to build a heavy enterprise migration framework. The goal is to prevent silent ledger drift before the assistant begins to hold real project memory.

---

## 2. Context

BRIEF-TR001 created the first executable runtime ledger: persons, contours, mandates, messages, tasks, task events, receipts, claims, outbox, policy, doctor, and restart recovery.

BRIEF-TR002 extended that ledger with project decisions, task status transitions, additional events, and a read-only project brief.

Both changes were correct for pre-policy implementation, but they also exposed the next risk: the runtime schema is already evolving.

A trust runtime cannot rely on informal schema replacement. Once the ledger starts holding real project memory, a schema mistake can corrupt the operational source of truth.

Therefore schema evolution must become governed before further persistent runtime work continues.

---

## 3. Non-Negotiable Invariants

1. **No silent schema drift.**  
   Runtime code must not mutate or depend on undocumented schema changes.

2. **No state without version.**  
   Every runtime database must expose its schema version through a metadata table.

3. **No destructive migration without explicit approval.**  
   Dropping columns, deleting data, rewriting semantic records, or weakening receipt/claim constraints requires founder-level or brief-level approval plus backup instructions.

4. **No downgrade support in MVP.**  
   Downgrades are not required. Rollback is through restoring a backup or recreating disposable local DBs.

5. **No receipt-invariant regression.**  
   Migrations must not weaken `No receipt, no success claim`, doctor coverage, foreign keys, or policy evidence without a new ADR.

6. **Unknown means stop.**  
   If the runtime sees an unknown, newer, corrupted, or unversioned non-empty schema, it must fail closed rather than guess.

---

## 4. Schema Versioning Model

Add a small runtime metadata table to every database:

```text
runtime_meta
```

Minimum fields:

```text
key TEXT PRIMARY KEY
value TEXT NOT NULL
updated_at TEXT NOT NULL
```

Required keys:

```text
schema_version
schema_name
```

Recommended keys:

```text
created_at
last_migrated_at
```

Use monotonic integer schema versions:

```text
1, 2, 3, ...
```

The current post-BRIEF-TR002 schema should be adopted as the first governed baseline.

The exact integer assigned to that baseline is an implementation detail, but it must be explicit, tested, and visible through `doctor`.

---

## 5. Migration Model

Migrations must be ordered and deterministic.

Recommended repository shape:

```text
src/verace_runtime/ledger/migrations/
  0001_baseline.py or .sql
  0002_*.py or .sql
```

The implementation may use SQL files or tiny Python migration modules. The choice is lower-level implementation detail.

Each migration must have:

```text
version_from
version_to
description
kind: additive | transform | destructive
apply function or SQL body
```

Policy:

- `additive` migrations may run automatically in local MVP mode.
- `transform` migrations may run only when covered by tests and explicit implementation brief acceptance.
- `destructive` migrations are blocked by default and require explicit approval plus backup instructions.

Migrations must be idempotent only at the runner level. A migration that has already been applied must not run again.

---

## 6. Fresh Database vs Existing Database

### 6.1 Fresh database

For a new empty runtime DB:

1. create schema from current baseline/snapshot;
2. write `runtime_meta.schema_version`;
3. seed founder/project state only through normal repository/service paths;
4. create receipts and claims required by current policy.

### 6.2 Existing versioned database

For an existing DB with known schema version:

1. verify integrity and foreign keys;
2. apply ordered migrations from current version to target version;
3. update metadata only after successful migration;
4. run doctor invariants after migration.

### 6.3 Existing unversioned database

For an unversioned DB:

- if empty or clearly disposable, implementation may recreate or adopt it under explicit local command behavior;
- if non-empty, runtime must stop and require an explicit migration/adoption command;
- no normal command may silently treat it as current.

This protects early real project memory from accidental overwrite.

---

## 7. Doctor Contract

`doctor` becomes the canonical local schema/audit surface.

It must report at least:

```text
schema_version
schema_known
schema_current
migration_required
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

If schema is unknown, newer than code, or migration is required, doctor must make that visible.

A healthy doctor state is required before future assistant/channel/provider work relies on the DB.

---

## 8. Testing Contract

Every schema or migration change must include tests for:

1. fresh database initialization;
2. current schema version written to metadata;
3. known-version database upgrade;
4. unknown/unversioned non-empty database fail-closed behavior;
5. migration idempotence at runner level;
6. doctor reports correct schema state;
7. receipt/claim/foreign-key invariants survive migration.

Tests must use synthetic local data only.

No test may require network access.

No binary SQLite database fixture should be committed unless a later ADR explicitly permits it. Prefer SQL setup scripts or temporary DB construction in tests.

---

## 9. Repository Safety

The public repository may contain:

- schema SQL;
- migration SQL/Python files;
- synthetic test data;
- documentation;
- source code.

The public repository must not contain:

- `.runtime/` databases;
- SQLite DB/WAL/SHM files;
- personal project data;
- real task history;
- real receipts with private URLs;
- secrets, tokens, OAuth material, or `.env` files;
- logs that contain private data.

This continues the existing public-repo boundary.

---

## 10. Relationship to ADR-TR004 and ADR-TR005

ADR-TR004 defines the Runtime Ledger as operational source of truth.

ADR-TR005 defines receipt and approval policy.

ADR-TR006 adds the missing persistence discipline:

```text
ledger truth requires schema truth
```

If the schema is unknown, the runtime cannot safely claim the ledger state is current.

This ADR does not change the core chain:

```text
mandate → policy → action → receipt → claim → ledger → review/audit
```

It protects the ledger part of that chain.

---

## 11. Consequences

### Positive

- Runtime state becomes safer before real founder/project memory accumulates.
- Future schema changes become testable and reviewable.
- Doctor becomes more useful as a local trust surface.
- Old disposable test DBs cannot accidentally masquerade as current runtime state.
- Migration policy aligns with Verace's evidence-first discipline.

### Costs

- A small migration runner must be implemented.
- Tests become slightly heavier.
- Some local DBs created before ADR-TR006 may need adoption, recreation, or explicit migration.
- Future briefs must account for schema version changes.

### Accepted tradeoff

This complexity is justified now because the runtime has crossed from pure documentation into persistent executable memory.

---

## 12. Non-Goals

This ADR does not approve:

- PostgreSQL migration framework;
- Alembic or heavyweight migration tooling;
- production multi-tenant migration orchestration;
- schema federation with old Verace TruthOps backend;
- down migrations;
- binary DB fixtures in the public repo;
- encryption/key-management design;
- backup product design;
- Telegram/channel/LLM integration.

Those require later ADRs or implementation briefs.

---

## 13. Acceptance Criteria

This ADR is accepted when Oleg confirms:

1. Runtime ledger schema must be explicitly versioned.
2. Unknown/unversioned non-empty DBs must fail closed.
3. The current post-BRIEF-TR002 schema becomes the first governed baseline.
4. Migration tests are mandatory for future schema changes.
5. Doctor must expose schema/migration status.
6. No destructive migration is allowed without explicit approval and backup instructions.
7. No runtime DB, secret, log, or private record may be committed to the public repo.

Once accepted, the next implementation brief should add the migration runner and schema-version doctor checks before new persistent features are added.
