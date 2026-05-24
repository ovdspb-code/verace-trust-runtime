from __future__ import annotations

import sqlite3

from verace_runtime.app.service import FounderAssistantService


def test_healthy_doctor_includes_schema_state(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()

    result = service.doctor()

    assert result["ok"] is True
    assert result["schema_name"] == "verace_runtime"
    assert result["schema_version"] == 3
    assert result["schema_known"] is True
    assert result["schema_current"] is True
    assert result["migration_required"] is False


def test_unsafe_doctor_reports_schema_failure_without_traceback(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE orphan_state(id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO orphan_state(id) VALUES ('x')")

    result = FounderAssistantService(db_path).doctor()

    assert result["ok"] is False
    assert result["schema_known"] is False
    assert result["schema_current"] is False
    assert result["migration_required"] is True
    assert "Traceback" not in str(result)


def test_healthy_doctor_keeps_receipt_invariants(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    service.ingest_message("oleg", "verace_project", "Проверить doctor")

    result = service.doctor()

    assert result["claim_receipt_ok"] is True
    assert result["task_event_receipt_ok"] is True
    assert result["decision_receipt_ok"] is True
