from __future__ import annotations

from verace_runtime.workbench.capture_classifier import classify_capture


def test_founder_decision_text_creates_decision_suggestion():
    suggestions = classify_capture("РЕШЕНИЕ: Browser UI остается founder UX.", "chatgpt")

    assert suggestions[0].kind == "decision"
    assert "Browser UI" in suggestions[0].body


def test_codex_report_creates_review_and_next_work_task():
    text = "Готово\nCommit: abc123\nChecks: pytest passed\nNext work: Run founder trial"

    kinds = [item.kind for item in classify_capture(text, "codex")]

    assert "review" in kinds
    assert "task" in kinds


def test_blocker_text_creates_risk_review_suggestion():
    suggestions = classify_capture("Есть blocker: запуск ломается после init.", "note")

    assert any(item.kind == "risk_review" for item in suggestions)


def test_task_like_text_creates_task_suggestion():
    suggestions = classify_capture("Нужно подготовить план следующей сессии.", "telegram")

    assert any(item.kind == "task" for item in suggestions)


def test_task_for_codex_text_creates_codex_task_suggestion():
    suggestions = classify_capture("TASK FOR CODEX\nGoal:\nFix inbox.\nAcceptance criteria:\npytest passes", "chatgpt")

    assert any(item.kind == "codex_task" for item in suggestions)


def test_noise_text_creates_ignore_suggestion():
    suggestions = classify_capture("Спасибо, понял.", "other")

    assert len(suggestions) == 1
    assert suggestions[0].kind == "ignore"
    assert "No actionable signal" in suggestions[0].reason
