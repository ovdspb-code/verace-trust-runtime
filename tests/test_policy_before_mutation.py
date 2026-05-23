from __future__ import annotations

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.policy.engine import Decision, PolicyEngine


class TaskBlockingPolicy(PolicyEngine):
    def evaluate(self, action_class: str) -> Decision:
        if action_class == "internal.task.create":
            return Decision(action_class, False, "blocked", "test denial")
        return super().evaluate(action_class)


def test_denied_task_create_does_not_create_task(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3", policy=TaskBlockingPolicy())
    service.init_runtime()

    result = service.ingest_message("oleg", "verace_project", "Создать задачу")
    counts = service.status()

    assert result.task_public_no is None
    assert result.claim_status == "blocked"
    assert counts["messages"] == 1
    assert counts["tasks"] == 0
    assert counts["task_events"] == 0
    assert counts["receipts"] == 3
