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


def post(base: str, path: str, data: dict[str, str]) -> str:
    request = Request(base + path, data=urlencode(data).encode("utf-8"), method="POST")
    with urlopen(request) as response:
        assert response.status == 200
        return response.read().decode("utf-8")


def test_state_changing_browser_confirmations_are_receipt_rendered(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        post(base, "/init", {})
        task = post(base, "/tasks", {"text": "Synthetic task"})
        decision = post(base, "/decisions", {"title": "Rendered decision", "text": "Synthetic decision."})
        review = post(base, "/reviews", {"title": "Rendered review", "body": "Body.", "review_type": "risk", "priority": "normal", "task": ""})
        dismissed = post(base, "/reviews/REV-000001/resolve", {"resolution": "Not needed.", "status": "dismissed"})

    for html in (task, decision, review, dismissed):
        assert "Подтверждено receipt-записью" in html
        assert "Receipt: RCPT-" in html
    assert "Task TR-000001 was recorded in the ledger." in task
    assert "Decision DEC-000001 was recorded in the ledger." in decision
    assert "Review REV-000001 was created." in review
    assert "Review REV-000001 was dismissed." in dismissed


def test_browser_pages_do_not_emit_private_internal_ids(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        post(base, "/init", {})
        html = post(base, "/tasks", {"text": "Synthetic task"})

    assert "task_" not in html
    assert "message_" not in html


def test_review_page_uses_cards_and_human_review_copy(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        post(base, "/init", {})
        post(base, "/reviews", {"title": "Review without task", "body": "Body.", "review_type": "risk", "priority": "normal", "task": ""})
        html = post(base, "/reviews", {"title": "Review with task", "body": "Body.", "review_type": "architecture", "priority": "high", "task": ""})

    assert "review-card" in html
    assert "Закрыть проверку" in html
    assert "без задачи" in html
    assert "task=--" not in html
    assert "class='inline'" not in html
    assert ">resolved<" not in html
    assert "Решено" in html
