from __future__ import annotations

import sqlite3

from verace_runtime.app.service import FounderAssistantService


def test_fresh_init_writes_runtime_meta(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)

    service.init_runtime()

    with sqlite3.connect(db_path) as conn:
        meta = dict(conn.execute("SELECT key, value FROM runtime_meta").fetchall())
    assert meta["schema_name"] == "verace_runtime"
    assert meta["schema_version"] == "2"
    assert meta["created_at"]
    assert meta["last_migrated_at"]


def test_init_remains_idempotent_with_schema_metadata(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")

    service.init_runtime()
    service.init_runtime()
    status = service.schema_status()

    assert status["schema_version"] == 2
    assert status["schema_name"] == "verace_runtime"
    assert status["schema_current"] is True
