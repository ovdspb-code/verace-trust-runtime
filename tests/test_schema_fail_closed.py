from __future__ import annotations

import sqlite3

import pytest

from verace_runtime.app.service import FounderAssistantService


def test_unversioned_non_empty_db_fails_closed(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE orphan_state(id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO orphan_state(id) VALUES ('x')")

    with pytest.raises(RuntimeError, match="Unsafe runtime schema"):
        FounderAssistantService(db_path).init_runtime()

    with sqlite3.connect(db_path) as conn:
        names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert "runtime_meta" not in names


def test_newer_schema_version_fails_closed(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    _write_meta_db(db_path, "verace_runtime", "4")

    with pytest.raises(RuntimeError, match="Unsafe runtime schema"):
        FounderAssistantService(db_path).status()


def test_malformed_schema_version_fails_closed(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    _write_meta_db(db_path, "verace_runtime", "not-an-int")

    with pytest.raises(RuntimeError, match="Unsafe runtime schema"):
        FounderAssistantService(db_path).init_runtime()


def test_unknown_schema_name_fails_closed(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    _write_meta_db(db_path, "other_runtime", "1")

    with pytest.raises(RuntimeError, match="Unsafe runtime schema"):
        FounderAssistantService(db_path).status()


def _write_meta_db(path, schema_name: str, version: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE runtime_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL)")
        conn.execute("INSERT INTO runtime_meta VALUES ('schema_name', ?, 'now')", (schema_name,))
        conn.execute("INSERT INTO runtime_meta VALUES ('schema_version', ?, 'now')", (version,))
        conn.execute("INSERT INTO runtime_meta VALUES ('created_at', 'now', 'now')")
        conn.execute("INSERT INTO runtime_meta VALUES ('last_migrated_at', 'now', 'now')")
