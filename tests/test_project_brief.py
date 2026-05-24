from __future__ import annotations

from verace_runtime.app.service import FounderAssistantService


def test_project_brief_includes_task_state_and_latest_decision(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    task_open = service.ingest_message("oleg", "verace_project", "Open task")
    task_waiting = service.ingest_message("oleg", "verace_project", "Waiting task")
    service.set_task_status(task_waiting.task_public_no, "waiting", "Synthetic waiting")
    decision = service.record_decision("oleg", "verace_project", "Brief decision", "Synthetic decision.")

    brief = service.project_brief()
    task_rows = {(task["public_no"], task["status"]) for task in brief["tasks"]}
    decision_ids = [item["public_id"] for item in brief["decisions"]]

    assert (task_open.task_public_no, "open") in task_rows
    assert (task_waiting.task_public_no, "waiting") in task_rows
    assert decision.public_id in decision_ids
    assert brief["doctor"]["ok"] is True


def test_project_brief_is_read_only_for_status_counts(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    service.ingest_message("oleg", "verace_project", "Open task")
    service.record_decision("oleg", "verace_project", "Decision", "Synthetic decision.")
    before = service.status()

    service.project_brief()
    after = service.status()

    assert after == before
