from __future__ import annotations

from verace_runtime.app.service import FounderAssistantService


def test_task_decision_and_status_survive_restart(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    task = service.ingest_message("oleg", "verace_project", "Restart task")
    decision = service.record_decision("oleg", "verace_project", "Restart decision", "Synthetic decision.")
    service.set_task_status(task.task_public_no, "blocked", "Synthetic blocker")

    recovered = FounderAssistantService(db_path)
    detail = recovered.task_detail(task.task_public_no)
    brief = recovered.project_brief()
    decisions = recovered.list_decisions()

    assert detail["task"]["status"] == "blocked"
    assert decisions[0].public_id == decision.public_id
    assert brief["tasks"][0]["public_no"] == task.task_public_no
    assert brief["tasks"][0]["status"] == "blocked"
