from __future__ import annotations

import sqlite3
from importlib import resources

import pytest

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.ledger.db import apply_schema
from verace_runtime.ledger.repository import LedgerRepository
from verace_runtime.ledger.migrations import Migration, SchemaError, inspect_schema_state, run_migrations, write_meta
from verace_runtime.time import utc_now_iso


def test_current_version_migration_is_noop(tmp_path):
    with sqlite3.connect(tmp_path / "runtime.sqlite3") as conn:
        _create_meta(conn, "2")
        state = inspect_schema_state(conn)
        result = run_migrations(conn, state, 2, [])

    assert result.schema_current is True
    assert result.schema_version == 2


def test_ordered_synthetic_migrations_apply_once(tmp_path):
    applied = []
    with sqlite3.connect(tmp_path / "runtime.sqlite3") as conn:
        _create_meta(conn, "0")
        state = inspect_schema_state(conn, target_version=2)
        migrations = [
            Migration(1, "create marker", lambda c: (applied.append(1), c.execute("CREATE TABLE marker(id TEXT)"))),
            Migration(2, "insert marker", lambda c: (applied.append(2), c.execute("INSERT INTO marker(id) VALUES ('ok')"))),
        ]

        result = run_migrations(conn, state, 2, migrations)
        again = run_migrations(conn, result, 2, migrations)
        rows = conn.execute("SELECT COUNT(*) FROM marker WHERE id = 'ok'").fetchone()[0]

    assert result.schema_current is True
    assert again.schema_version == 2
    assert applied == [1, 2]
    assert rows == 1


def test_destructive_migration_is_blocked(tmp_path):
    with sqlite3.connect(tmp_path / "runtime.sqlite3") as conn:
        _create_meta(conn, "0")
        state = inspect_schema_state(conn)
        migration = Migration(1, "drop everything", lambda c: None, destructive=True)
        with pytest.raises(SchemaError, match="Destructive migration blocked"):
            run_migrations(conn, state, 1, [migration])


def test_production_migration_from_v1_adds_review_tables_once(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    schema = resources.files("verace_runtime.ledger").joinpath("schema.sql").read_text()
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.executescript(schema)
        conn.execute("DROP TABLE review_events")
        conn.execute("DROP TABLE review_items")
        write_meta(conn, {"schema_name": "verace_runtime", "schema_version": "1", "created_at": "now", "last_migrated_at": "now"})
        LedgerRepository(conn).seed_founder(utc_now_iso())

    with sqlite3.connect(db_path) as conn:
        apply_schema(conn)
        apply_schema(conn)
        names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        meta = dict(conn.execute("SELECT key, value FROM runtime_meta").fetchall())

    assert {"review_items", "review_events"} <= names
    assert meta["schema_version"] == "2"
    assert FounderAssistantService(db_path).doctor()["ok"] is True


def _create_meta(conn: sqlite3.Connection, version: str) -> None:
    conn.execute("CREATE TABLE runtime_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL)")
    write_meta(conn, {"schema_name": "verace_runtime", "schema_version": version, "created_at": "now", "last_migrated_at": "now"})
