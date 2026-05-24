from __future__ import annotations

import sqlite3

from verace_runtime.app.service import FounderAssistantService


def test_init_is_idempotent_and_seeds_founder(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)

    first = service.init_runtime()
    second = service.init_runtime()

    assert first.principal == "oleg"
    assert second.contour == "verace_project"
    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {"runtime_meta", "persons", "contours", "mandates", "messages", "tasks", "receipts", "claims"} <= tables
        assert conn.execute("SELECT COUNT(*) FROM persons WHERE slug = 'oleg'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM contours WHERE slug = 'verace_project'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM mandates WHERE status = 'active'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM receipts").fetchone()[0] == 2
