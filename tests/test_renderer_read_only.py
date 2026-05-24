from __future__ import annotations

from verace_runtime.app.service import FounderAssistantService


def test_render_claim_paths_are_read_only(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    task = service.ingest_message("oleg", "verace_project", "Prepare renderer test")
    decision = service.record_decision("oleg", "verace_project", "Renderer decision", "Synthetic decision.")
    review = service.add_review("oleg", "verace_project", "Renderer review", "Body.", "architecture", "high", task.task_public_no)
    service.resolve_review(review.public_id, "Synthetic resolution.")

    before = service.status()
    assert service.render_claim("task_recorded", task.task_public_no).ok is True
    assert service.render_claim("decision_recorded", decision.public_id).ok is True
    assert service.render_claim("review_resolved", review.public_id).ok is True
    assert service.render_claim("schema_healthy").ok is True
    after = service.status()

    assert after == before

