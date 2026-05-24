from __future__ import annotations

import pytest

from verace_runtime.app.service import FounderAssistantService


def test_valid_status_transition_updates_task_with_receipt_event_claim(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    task = service.ingest_message("oleg", "verace_project", "Synthetic task")

    result = service.set_task_status(task.task_public_no, "waiting", "Synthetic waiting state")
    detail = service.task_detail(task.task_public_no)
    counts = service.status()

    assert result.status == "waiting"
    assert result.receipt_public_id.startswith("RCPT-")
    assert detail["task"]["status"] == "waiting"
    assert counts["task_events"] == 2
    assert counts["receipts"] == 4
    assert counts["claims"] == 4


def test_invalid_status_is_rejected_without_mutation(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    task = service.ingest_message("oleg", "verace_project", "Synthetic task")
    before = service.status()

    with pytest.raises(RuntimeError):
        service.set_task_status(task.task_public_no, "invented", "Bad status")

    after = service.status()
    assert after == before


def test_add_task_event_creates_receipt_and_claim(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    task = service.ingest_message("oleg", "verace_project", "Synthetic task")

    result = service.add_task_event(task.task_public_no, "review.note", "Synthetic event")
    counts = service.status()

    assert result.task_public_no == task.task_public_no
    assert result.status == "open"
    assert result.receipt_public_id.startswith("RCPT-")
    assert counts["task_events"] == 2
    assert counts["receipts"] == 4
    assert counts["claims"] == 4
