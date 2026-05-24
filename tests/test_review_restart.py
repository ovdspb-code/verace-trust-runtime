from __future__ import annotations

from verace_runtime.app.service import FounderAssistantService


def test_review_item_and_resolution_survive_restart(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    task = service.ingest_message("oleg", "verace_project", "Restart task")
    review = service.add_review("oleg", "verace_project", "Restart review", "Body.", "evidence", "high", task.task_public_no)
    service.resolve_review(review.public_id, "Synthetic restart resolution.")

    recovered = FounderAssistantService(db_path)
    reviews = recovered.list_reviews(None)
    brief = recovered.session_brief()
    doctor = recovered.doctor()

    assert len(reviews) == 1
    assert reviews[0].public_id == review.public_id
    assert reviews[0].status == "resolved"
    assert brief["counts"]["review_items"] == 1
    assert brief["counts"]["review_events"] == 2
    assert doctor["ok"] is True
