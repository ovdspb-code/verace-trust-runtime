from __future__ import annotations

from verace_runtime.app.service import FounderAssistantService


def test_synthetic_message_creates_task_event_receipt_and_claim(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()

    result = service.ingest_message("oleg", "verace_project", "Подготовить тестовую задачу")
    tasks = service.list_tasks()
    detail = service.task_detail(result.task_public_no)
    counts = service.status()

    assert result.task_public_no is not None
    assert result.task_public_no.startswith("TR-")
    assert result.receipt_public_id.startswith("RCPT-")
    assert len(tasks) == 1
    assert tasks[0].status == "open"
    assert tasks[0].contour == "verace_project"
    assert detail["task"]["public_no"] == result.task_public_no
    assert len(detail["receipts"]) >= 1
    assert counts["task_events"] >= 1
    assert counts["claims"] >= 3


def test_note_message_creates_no_task(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()

    result = service.ingest_message("oleg", "verace_project", "note: просто зафиксировать")
    counts = service.status()

    assert result.task_public_no is None
    assert result.receipt_public_id.startswith("RCPT-")
    assert counts["messages"] == 1
    assert counts["tasks"] == 0
    assert counts["receipts"] == 2
