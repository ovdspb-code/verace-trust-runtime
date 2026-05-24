from __future__ import annotations

import threading
from contextlib import contextmanager
from urllib.parse import urlencode
from urllib.request import Request, urlopen

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


def test_accept_suggestion_as_task_creates_receipt_backed_task(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        post(base, "/init", {})
        form = get(base, "/suggestions/task?key=next-work-task")
        html = post(base, "/suggestions/task", {"text": "Synthetic suggested task"})

    assert "Synthetic suggested task" in form or "Продолжить" in form
    assert "Подтверждено receipt-записью" in html
    assert "Task TR-000001 was recorded" in html
    assert "Receipt: RCPT-" in html


def test_accept_suggestion_as_review_creates_receipt_backed_review(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        post(base, "/init", {})
        form = get(base, "/suggestions/review?key=risk-1-review")
        html = post(base, "/suggestions/review", {"title": "Suggested review", "body": "Check risk.", "review_type": "risk", "priority": "high"})

    assert "Принять как проверку" in form
    assert "Подтверждено receipt-записью" in html
    assert "Review REV-000001 was created" in html
    assert "Receipt: RCPT-" in html


def test_accept_suggestion_as_decision_creates_receipt_backed_decision(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        post(base, "/init", {})
        form = get(base, "/suggestions/decision?key=product-surface-decision")
        html = post(base, "/suggestions/decision", {"title": "Suggested decision", "text": "Synthetic suggested decision."})

    assert "Записать как решение" in form
    assert "Подтверждено receipt-записью" in html
    assert "Decision DEC-000001 was recorded" in html
    assert "Receipt: RCPT-" in html


def test_codex_task_page_renders_prompt_text(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        html = get(base, "/suggestions/codex?key=next-work-codex")

    assert "Codex task text" in html
    assert "Goal:" in html
    assert "Acceptance criteria:" in html
    assert "Traceback" not in html
