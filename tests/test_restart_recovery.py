from __future__ import annotations

from verace_runtime.app.service import FounderAssistantService


def test_task_and_receipt_survive_new_service_instance(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    created = service.ingest_message("oleg", "verace_project", "Проверить восстановление")

    recovered = FounderAssistantService(db_path)
    tasks = recovered.list_tasks()
    detail = recovered.task_detail(created.task_public_no)

    assert [task.public_no for task in tasks] == [created.task_public_no]
    assert detail["task"]["title"] == "Проверить восстановление"
    assert len(detail["receipts"]) == 1
