from __future__ import annotations

import pytest

from verace_runtime.app.service import FounderAssistantService


def test_resolve_review_updates_state_event_receipt_and_claim(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    review = service.add_review("oleg", "verace_project", "Resolve me", "Body.", "clarification", "normal")

    result = service.resolve_review(review.public_id, "Reviewed and resolved.")
    doctor = service.doctor()

    assert result.public_id == review.public_id
    assert result.status == "resolved"
    assert result.receipt_public_id.startswith("RCPT-")
    assert result.claim_status == "verified_by_receipt"
    assert service.status()["review_events"] == 2
    assert doctor["review_resolution_ok"] is True
    assert doctor["review_status_ok"] is True


def test_resolved_review_not_in_default_open_list(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    review = service.add_review("oleg", "verace_project", "Resolve me", "Body.", "decision", "low")

    service.resolve_review(review.public_id, "Synthetic resolution.")

    assert service.list_reviews() == []
    assert service.list_reviews(None)[0].status == "resolved"


def test_invalid_review_id_rejected_without_mutation(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    service.add_review("oleg", "verace_project", "Open review", "Body.", "risk", "normal")
    before = service.status()

    with pytest.raises(RuntimeError, match="Review item not found"):
        service.resolve_review("REV-MISSING", "Synthetic resolution.")

    assert service.status() == before
