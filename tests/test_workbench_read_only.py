from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from urllib.parse import urlencode
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


def test_read_only_browser_pages_do_not_mutate_status_counts(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    with running_server(db_path) as base:
        post(base, "/init", {})
        post(base, "/tasks", {"text": "Synthetic task"})
        post(base, "/reviews", {"title": "Review", "body": "Body.", "review_type": "architecture", "priority": "high", "task": ""})
        before = FounderAssistantService(db_path).status()
        get(base, "/")
        get(base, "/reviews")
        get(base, "/doctor")
        after = FounderAssistantService(db_path).status()

    assert after == before


def test_unsafe_db_shows_failure_without_healthy_claim(tmp_path):
    db_path = tmp_path / "unversioned.sqlite3"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE orphan_state(id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO orphan_state(id) VALUES ('x')")

    with running_server(db_path) as base:
        html = get(base, "/doctor")

    assert "Диагностика: <span class='fail'>FAIL</span>" in html
    assert "missing runtime_meta" in html
    assert "Диагностика: <span class='ok'>OK</span>" not in html
    assert "Traceback" not in html
