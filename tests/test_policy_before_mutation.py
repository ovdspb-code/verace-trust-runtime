from __future__ import annotations

import sqlite3

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.policy.engine import Decision, PolicyEngine


class TaskBlockingPolicy(PolicyEngine):
    def evaluate(self, action_class: str) -> Decision:
        if action_class == "internal.task.create":
            return Decision(action_class, False, "blocked", "test denial")
        return super().evaluate(action_class)


class FlippingMessagePolicy(PolicyEngine):
    def __init__(self) -> None:
        self.message_calls = 0

    def evaluate(self, action_class: str) -> Decision:
        if action_class == "internal.message.record":
            self.message_calls += 1
            if self.message_calls == 1:
                return Decision(action_class, True, "allowed", "first authorization")
            return Decision(action_class, False, "blocked", "second denial")
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


def test_message_receipt_reuses_authorizing_policy_decision(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    policy = FlippingMessagePolicy()
    service = FounderAssistantService(db_path, policy=policy)
    service.init_runtime()

    service.ingest_message("oleg", "verace_project", "Проверить receipt decision")

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT r.status, r.policy_result
            FROM receipts r
            JOIN messages m ON m.id = r.subject_id
            WHERE r.subject_type = 'message'
            """
        ).fetchone()
    assert policy.message_calls == 1
    assert row == ("ok", "allowed")
