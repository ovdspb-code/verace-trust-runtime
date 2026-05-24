from __future__ import annotations

import pytest

from verace_runtime.app.service import FounderAssistantService


def test_add_review_creates_item_event_receipt_and_claim(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()

    result = service.add_review(
        "oleg",
        "verace_project",
        "Review test",
        "Synthetic review body.",
        "architecture",
        "high",
    )
    counts = service.status()
    doctor = service.doctor()

    assert result.public_id.startswith("REV-")
    assert result.receipt_public_id.startswith("RCPT-")
    assert result.claim_status == "verified_by_receipt"
    assert result.status == "open"
    assert counts["review_items"] == 1
    assert counts["review_events"] == 1
    assert doctor["review_item_receipt_ok"] is True
    assert doctor["review_item_claim_ok"] is True
    assert doctor["review_event_receipt_ok"] is True


def test_review_list_defaults_to_open_items(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    open_item = service.add_review("oleg", "verace_project", "Open review", "Body.", "risk", "normal")
    resolved = service.add_review("oleg", "verace_project", "Resolved review", "Body.", "risk", "normal")
    service.resolve_review(resolved.public_id, "Synthetic resolution.")

    open_reviews = service.list_reviews()
    all_reviews = service.list_reviews(None)

    assert [item.public_id for item in open_reviews] == [open_item.public_id]
    assert {item.public_id for item in all_reviews} == {open_item.public_id, resolved.public_id}


def test_review_item_can_attach_to_existing_task(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    task = service.ingest_message("oleg", "verace_project", "Task needing review")

    review = service.add_review("oleg", "verace_project", "Attached review", "Body.", "evidence", "high", task.task_public_no)
    summary = service.list_reviews()[0]

    assert review.public_id == summary.public_id
    assert summary.task_public_no == task.task_public_no


def test_invalid_review_type_or_priority_rejected_before_mutation(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    before = service.status()

    with pytest.raises(RuntimeError, match="Invalid review type"):
        service.add_review("oleg", "verace_project", "Bad", "Body.", "invalid", "high")
    with pytest.raises(RuntimeError, match="Invalid review priority"):
        service.add_review("oleg", "verace_project", "Bad", "Body.", "risk", "urgent")

    assert service.status() == before
