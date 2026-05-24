from __future__ import annotations

import threading
from contextlib import contextmanager
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.workbench.server import make_server


@contextmanager
def running_server(db_path):
    server = make_server(port=0, db_path=db_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def get(base: str, path: str) -> str:
    with urlopen(base + path) as response:
        assert response.status == 200
        return response.read().decode("utf-8")


def post(base: str, path: str, data: dict[str, str]) -> str:
    request = Request(base + path, data=urlencode(data).encode("utf-8"), method="POST")
    with urlopen(request) as response:
        assert response.status == 200
        return response.read().decode("utf-8")


def post_error(base: str, path: str, data: dict[str, str]) -> str:
    request = Request(base + path, data=urlencode(data).encode("utf-8"), method="POST")
    try:
        urlopen(request)
    except HTTPError as exc:
        assert exc.code == 400
        return exc.read().decode("utf-8")
    raise AssertionError("expected HTTP 400")


def test_accept_suggestion_as_task_creates_receipt_backed_task(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        post(base, "/init", {})
        form = get(base, "/suggestions/task?key=next-work-task")
        html = post(base, "/suggestions/task", {"key": "next-work-task", "text": "Synthetic suggested task"})
        plan = get(base, "/plan")

    assert "Synthetic suggested task" in form or "Продолжить" in form
    assert 'name="key"' in form or "name='key'" in form
    assert "Подтверждено receipt-записью" in html
    assert "Task TR-000001 was recorded" in html
    assert "Receipt: RCPT-" in html
    assert "next-work-task" not in html
    assert "next-work-task" not in plan


def test_accept_suggestion_as_review_creates_receipt_backed_review(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        post(base, "/init", {})
        form = get(base, "/suggestions/review?key=risk-1-review")
        html = post(base, "/suggestions/review", {"key": "risk-1-review", "title": "Suggested review", "body": "Check risk.", "review_type": "risk", "priority": "high"})
        plan = get(base, "/plan")

    assert "Принять как проверку" in form
    assert 'name="key"' in form
    assert "Подтверждено receipt-записью" in html
    assert "Review REV-000001 was created" in html
    assert "Receipt: RCPT-" in html
    assert "risk-1-review" not in html
    assert "risk-1-review" not in plan


def test_accept_suggestion_as_decision_creates_receipt_backed_decision(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        post(base, "/init", {})
        form = get(base, "/suggestions/decision?key=product-surface-decision")
        html = post(base, "/suggestions/decision", {"key": "product-surface-decision", "title": "Suggested decision", "text": "Synthetic suggested decision."})
        plan = get(base, "/plan")

    assert "Записать как решение" in form
    assert 'name="key"' in form or "name='key'" in form
    assert "Подтверждено receipt-записью" in html
    assert "Decision DEC-000001 was recorded" in html
    assert "Receipt: RCPT-" in html
    assert "product-surface-decision" not in html
    assert "product-surface-decision" not in plan


def test_codex_task_page_renders_prompt_text(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        html = get(base, "/suggestions/codex?key=next-work-codex")
        plan = get(base, "/plan")

    assert "Codex task text" in html
    assert "Goal:" in html
    assert "Acceptance criteria:" in html
    assert "next-work-codex" in plan
    assert "Traceback" not in html


def test_missing_suggestion_key_fails_without_task_mutation(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    before = service.status()
    with running_server(db_path) as base:
        html = post_error(base, "/suggestions/task", {"text": "Should not be created"})
    after = service.status()

    assert "Suggestion key is required" in html
    assert "Traceback" not in html
    assert after == before


def test_unknown_suggestion_key_fails_without_review_mutation(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    before = service.status()
    with running_server(db_path) as base:
        html = post_error(base, "/suggestions/review", {"key": "missing", "title": "Nope", "body": "Nope", "review_type": "risk", "priority": "high"})
    after = service.status()

    assert "Suggestion not found" in html
    assert "Traceback" not in html
    assert after == before


def test_dismiss_hides_without_ledger_mutation(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    before = service.status()
    with running_server(db_path) as base:
        html = post(base, "/suggestions/dismiss", {"key": "next-work-task"})
        plan = get(base, "/plan")
    after = service.status()

    assert "Предложение скрыто" in html
    assert "next-work-task" not in html
    assert "next-work-task" not in plan
    assert after == before
