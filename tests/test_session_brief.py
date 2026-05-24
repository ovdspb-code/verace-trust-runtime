from __future__ import annotations

from verace_runtime.app.service import FounderAssistantService


def test_session_brief_includes_reviews_tasks_and_decisions(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    open_task = service.ingest_message("oleg", "verace_project", "Open task")
    waiting_task = service.ingest_message("oleg", "verace_project", "Waiting task")
    service.set_task_status(waiting_task.task_public_no, "waiting", "Synthetic waiting")
    decision = service.record_decision("oleg", "verace_project", "Session decision", "Synthetic decision.")
    review = service.add_review("oleg", "verace_project", "Session review", "Body.", "architecture", "high", open_task.task_public_no)

    brief = service.session_brief()
    task_rows = {(task["public_no"], task["status"]) for task in brief["tasks"]}
    review_ids = [item["public_id"] for item in brief["reviews"]]
    decision_ids = [item["public_id"] for item in brief["decisions"]]

    assert (open_task.task_public_no, "open") in task_rows
    assert (waiting_task.task_public_no, "waiting") in task_rows
    assert review.public_id in review_ids
    assert decision.public_id in decision_ids
    assert brief["doctor"]["ok"] is True
    assert brief["schema"]["schema_current"] is True


def test_session_brief_is_read_only_for_status_counts(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    service.ingest_message("oleg", "verace_project", "Open task")
    service.record_decision("oleg", "verace_project", "Decision", "Synthetic decision.")
    service.add_review("oleg", "verace_project", "Review", "Body.", "risk", "normal")
    before = service.status()

    service.session_brief()
    after = service.status()

    assert after == before
