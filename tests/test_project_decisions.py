from __future__ import annotations

from verace_runtime.app.service import FounderAssistantService


def test_record_decision_creates_decision_receipt_and_claim(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()

    result = service.record_decision("oleg", "verace_project", "Test decision", "Synthetic decision.")
    counts = service.status()
    decisions = service.list_decisions()

    assert result.public_id.startswith("DEC-")
    assert result.receipt_public_id.startswith("RCPT-")
    assert result.claim_status == "verified_by_receipt"
    assert counts["decisions"] == 1
    assert counts["receipts"] == 2
    assert counts["claims"] == 2
    assert decisions[0].public_id == result.public_id


def test_decisions_list_is_stable_and_survives_restart(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    first = service.record_decision("oleg", "verace_project", "A decision", "First synthetic decision.")
    second = service.record_decision("oleg", "verace_project", "B decision", "Second synthetic decision.")

    recovered = FounderAssistantService(db_path)
    public_ids = [decision.public_id for decision in recovered.list_decisions()]

    assert public_ids == [second.public_id, first.public_id]
