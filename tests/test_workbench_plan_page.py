from __future__ import annotations

import threading
from contextlib import contextmanager
from urllib.request import urlopen

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


def test_plan_page_renders_project_status_and_suggestions(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        html = get(base, "/plan")

    assert "План проекта" in html
    assert "Browser Founder Workbench" in html
    assert "Следующий шаг" in html
    assert "Предложенные действия" in html
    assert "source:" in html
    assert "Принять как задачу" in html
    assert "Codex task" in html
    assert "Инициализировать" in html
    assert "Required ledger row not found" not in html
    assert "Traceback" not in html


def test_documents_page_renders_documentation_map(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        html = get(base, "/documents")

    assert "Документы проекта" in html
    assert "README.md" in html
    assert "docs/ops/PROJECT_STATE.md" in html
    assert "ADRs" in html
    assert "Briefs" in html
    assert "Plans" in html
    assert "Traceback" not in html


def test_plan_and_documents_are_read_only(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    before = service.status()
    with running_server(db_path) as base:
        get(base, "/plan")
        get(base, "/documents")
    after = service.status()

    assert after == before
