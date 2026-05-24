from __future__ import annotations

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.workbench import actions, capture


def test_record_capture_creates_receipt_and_public_cap_id(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()

    notice = actions.record_capture(service, "chatgpt", "trial", "РЕШЕНИЕ: Capture inbox остается deterministic.")
    captures = capture.list_captures(service.db_path)

    assert "Capture CAP-000001 was recorded" in notice
    assert "Receipt: RCPT-" in notice
    assert captures[0].public_id == "CAP-000001"


def test_accept_capture_suggestion_as_task_marks_accepted(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    actions.record_capture(service, "note", "", "Нужно подготовить capture smoke.")

    notice = actions.accept_capture_task(service, "CSUG-000001", "Подготовить capture smoke")
    _, suggestions = capture.capture_detail(service.db_path, "CAP-000001")

    assert "Task TR-000001 was recorded" in notice
    assert "Receipt: RCPT-" in notice
    assert suggestions[0].status == "accepted"


def test_accept_capture_suggestion_as_review_marks_accepted(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    actions.record_capture(service, "note", "", "Есть риск: classifier creates noise.")

    notice = actions.accept_capture_review(service, "CSUG-000001", "Review risk", "Check risk.", "risk", "high")
    _, suggestions = capture.capture_detail(service.db_path, "CAP-000001")

    assert "Review REV-000001 was created" in notice
    assert suggestions[0].status == "accepted"


def test_accept_capture_suggestion_as_decision_marks_accepted(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    actions.record_capture(service, "chatgpt", "", "РЕШЕНИЕ: Capture accepts require human approval.")

    notice = actions.accept_capture_decision(service, "CSUG-000001", "Capture approval", "Capture accepts require human approval.")
    _, suggestions = capture.capture_detail(service.db_path, "CAP-000001")

    assert "Decision DEC-000001 was recorded" in notice
    assert suggestions[0].status == "accepted"


def test_dismiss_capture_suggestion_does_not_mutate_task_review_decision_counts(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    actions.record_capture(service, "note", "", "Нужно сделать later.")
    before = service.status()

    capture.dismiss_suggestion(service.db_path, "CSUG-000001")
    after = service.status()
    _, suggestions = capture.capture_detail(service.db_path, "CAP-000001")

    assert suggestions[0].status == "dismissed"
    assert after["tasks"] == before["tasks"]
    assert after["review_items"] == before["review_items"]
    assert after["decisions"] == before["decisions"]


def test_codex_task_generation_is_read_only(tmp_path):
    service = FounderAssistantService(tmp_path / "runtime.sqlite3")
    service.init_runtime()
    actions.record_capture(service, "codex", "", "TASK FOR CODEX\nGoal:\nFix capture.\nAcceptance criteria:\npytest passes")
    before = service.status()

    prompt = capture.codex_prompt(service.db_path, "CSUG-000001")
    after = service.status()

    assert "Goal:" in prompt
    assert "Acceptance criteria:" in prompt
    assert after == before
