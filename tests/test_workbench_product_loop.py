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


def test_browser_founder_product_loop(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        post(base, "/init", {})
        task = post(base, "/tasks", {"text": "Подготовить тестовую задачу"})
        decision = post(base, "/decisions", {"title": "Browser decision", "text": "Synthetic decision."})
        review = post(
            base,
            "/reviews",
            {"title": "Review browser output", "body": "Synthetic review.", "review_type": "architecture", "priority": "high", "task": "TR-000001"},
        )
        reviews = get(base, "/reviews")
        resolved = post(base, "/reviews/REV-000001/resolve", {"resolution": "Synthetic resolution.", "status": "resolved"})
        dashboard = get(base, "/")
        doctor = get(base, "/doctor")

    assert "Task TR-000001 was recorded in the ledger. Receipt: RCPT-" in task
    assert "Decision DEC-000001 was recorded in the ledger. Receipt: RCPT-" in decision
    assert "Review REV-000001 was created. Receipt: RCPT-" in review
    assert "REV-000001" in reviews
    assert "Review REV-000001 was resolved. Receipt: RCPT-" in resolved
    assert "Подготовить тестовую задачу" in dashboard
    assert "Browser decision" in dashboard
    assert "Doctor: <span class='ok'>OK</span>" in doctor

