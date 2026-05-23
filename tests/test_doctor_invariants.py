from __future__ import annotations

import sqlite3

import pytest

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.ids import new_id
from verace_runtime.ledger.db import apply_schema, connect
from verace_runtime.ledger.repository import LedgerRepository
from verace_runtime.time import utc_now_iso


def test_doctor_detects_healthy_seed(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    service.ingest_message("oleg", "verace_project", "Проверить doctor")

    result = service.doctor()

    assert result["ok"] is True
    assert result["schema_ok"] is True
    assert result["pragma_ok"] is True
    assert result["integrity_ok"] is True
    assert result["foreign_keys_ok"] is True
    assert result["claim_receipt_ok"] is True
    assert result["task_event_receipt_ok"] is True


def test_doctor_detects_broken_claim_receipt(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO claims
            (id, claim_type, claim_text, subject_type, subject_id, receipt_id, status, created_at)
            VALUES (?, 'broken', 'broken', 'task', 'missing', 'missing_receipt', 'verified_by_receipt', ?)
            """,
            (new_id("claim"), utc_now_iso()),
        )

    result = service.doctor()

    assert result["ok"] is False
    assert result["foreign_keys_ok"] is False
    assert result["claim_receipt_ok"] is False


def test_claims_require_existing_receipt_when_foreign_keys_are_on(tmp_path):
    with connect(tmp_path / "runtime.sqlite3") as conn:
        apply_schema(conn)
        LedgerRepository(conn).seed_founder(utc_now_iso())
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """
                INSERT INTO claims
                (id, claim_type, claim_text, subject_type, subject_id, receipt_id, status, created_at)
                VALUES (?, 'bad', 'bad', 'task', 'task_missing', NULL, 'verified_by_receipt', ?)
                """,
                (new_id("claim"), utc_now_iso()),
            )
