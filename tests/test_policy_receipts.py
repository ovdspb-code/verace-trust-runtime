from __future__ import annotations

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.policy.engine import PolicyEngine


def test_policy_allows_internal_and_blocks_consequential_actions():
    policy = PolicyEngine()

    assert policy.evaluate("internal.task.create").allowed is True
    for action in ["external.send", "github.push", "payment", "legal.commitment", "destructive.action"]:
        decision = policy.evaluate(action)
        assert decision.allowed is False
        assert decision.result == "blocked"


def test_task_creation_and_blocked_action_are_receipted(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()

    task_result = service.ingest_message("oleg", "verace_project", "Сделать внутреннюю задачу")
    block_result = service.request_action("external.send", '{"to":"synthetic@example.test"}')
    counts = service.status()

    assert task_result.receipt_public_id.startswith("RCPT-")
    assert block_result.allowed is False
    assert block_result.receipt_public_id is not None
    assert counts["receipts"] >= 4
    assert counts["claims"] >= 4


def test_unknown_action_is_blocked_with_receipt(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()

    result = service.request_action("unknown.future.action")

    assert result.allowed is False
    assert result.receipt_public_id is not None
    assert service.status()["outbox_items"] == 1


def test_allowed_policy_probe_gets_receipt(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()

    result = service.request_action("internal.status.query")

    assert result.allowed is True
    assert result.receipt_public_id is not None
    assert service.status()["claims"] == 2
