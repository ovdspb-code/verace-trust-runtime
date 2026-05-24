from __future__ import annotations

import sqlite3

from verace_runtime.app.service import FounderAssistantService


def test_renderer_renders_current_runtime_claims_from_evidence(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    task = service.ingest_message("oleg", "verace_project", "Prepare renderer test")
    decision = service.record_decision("oleg", "verace_project", "Renderer decision", "Synthetic decision.")
    review = service.add_review("oleg", "verace_project", "Renderer review", "Body.", "architecture", "high", task.task_public_no)
    service.resolve_review(review.public_id, "Synthetic resolution.")

    task_render = service.render_claim("task_recorded", task.task_public_no)
    decision_render = service.render_claim("decision_recorded", decision.public_id)
    review_render = service.render_claim("review_resolved", review.public_id)
    schema_render = service.render_claim("schema_healthy")

    assert task_render.ok is True
    assert task_render.source == "receipt"
    assert f"Task {task.task_public_no} was recorded" in task_render.text
    assert decision_render.ok is True
    assert f"Decision {decision.public_id} was recorded" in decision_render.text
    assert review_render.ok is True
    assert f"Review {review.public_id} was resolved" in review_render.text
    assert schema_render.ok is True
    assert schema_render.source == "doctor"
    assert "Runtime schema is healthy" in schema_render.text


def test_renderer_renders_review_created_and_dismissed(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    created = service.add_review("oleg", "verace_project", "Created review", "Body.", "risk", "normal")
    dismissed = service.add_review("oleg", "verace_project", "Dismissed review", "Body.", "risk", "normal")
    service.resolve_review(dismissed.public_id, "Not needed.", "dismissed")

    created_render = service.render_claim("review_created", created.public_id)
    dismissed_render = service.render_claim("review_dismissed", dismissed.public_id)

    assert created_render.ok is True
    assert f"Review {created.public_id} was created" in created_render.text
    assert dismissed_render.ok is True
    assert f"Review {dismissed.public_id} was dismissed" in dismissed_render.text


def test_renderer_refuses_missing_task_claim(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    task = service.ingest_message("oleg", "verace_project", "Prepare renderer test")
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM claims WHERE claim_type = 'task_recorded'")

    result = service.render_claim("task_recorded", task.task_public_no)

    assert result.ok is False
    assert result.source == "refusal"
    assert result.reason == "receipt-backed evidence not found"


def test_wrong_action_class_receipt_fails_closed(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    task = service.ingest_message("oleg", "verace_project", "Prepare renderer test")
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE receipts SET action_class = 'internal.task.status_change' WHERE subject_type = 'task'")

    result = service.render_claim("task_recorded", task.task_public_no)

    assert result.ok is False
    assert result.source == "refusal"
    assert result.reason == "receipt action class mismatch"


def test_wrong_receipt_type_fails_closed(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    task = service.ingest_message("oleg", "verace_project", "Prepare renderer test")
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE receipts SET receipt_type = 'policy.allowed' WHERE subject_type = 'task'")

    result = service.render_claim("task_recorded", task.task_public_no)

    assert result.ok is False
    assert result.source == "refusal"
    assert result.reason == "receipt type mismatch"


def test_renderer_refuses_wrong_subject_receipt(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    task = service.ingest_message("oleg", "verace_project", "Prepare renderer test")
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE receipts SET subject_id = 'wrong_task' WHERE subject_type = 'task'")

    result = service.render_claim("task_recorded", task.task_public_no)

    assert result.ok is False
    assert result.source == "refusal"
    assert result.reason == "receipt-backed evidence not found"


def test_renderer_renders_action_blocked_when_policy_receipt_exists(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    service.request_action("external.send")

    result = service.render_claim("action_blocked", "external.send")

    assert result.ok is True
    assert result.source == "receipt"
    assert "Action external.send was blocked by policy" in result.text


def test_renderer_refuses_unsafe_schema_healthy_claim(tmp_path):
    db_path = tmp_path / "unversioned.sqlite3"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE orphan_state(id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO orphan_state(id) VALUES ('x')")

    result = FounderAssistantService(db_path).render_claim("schema_healthy")

    assert result.ok is False
    assert result.source == "refusal"
    assert result.reason == "doctor/schema state is not healthy"
