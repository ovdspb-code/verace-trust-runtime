from __future__ import annotations

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


def test_get_capture_renders_first_run_without_raw_error(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    with running_server(db_path) as base:
        html = get(base, "/capture")

    assert "Входящие" in html
    assert "Первый запуск" in html
    assert "Инициализировать" in html
    assert "Required ledger row not found" not in html
    assert "Traceback" not in html
    assert not db_path.exists()


def test_post_capture_records_item_and_suggestions(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    with running_server(db_path) as base:
        post(base, "/init", {})
        html = post(base, "/capture", {"source_type": "codex", "source_label": "smoke", "raw_text": _codex_report()})
        detail = get(base, "/capture/CAP-000001")

    assert "Capture CAP-000001 was recorded" in html
    assert "Receipt: RCPT-" in html
    assert "CSUG-" in html
    assert "Review Codex report" in detail
    assert "Traceback" not in detail


def test_capture_detail_shows_public_ids_only(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    with running_server(db_path) as base:
        post(base, "/capture", {"source_type": "note", "source_label": "", "raw_text": "Нужно сделать capture inbox trial."})
        html = get(base, "/capture/CAP-000001")

    assert "CAP-000001" in html
    assert "CSUG-000001" in html
    assert "capture_" not in html


def _codex_report() -> str:
    return "Готово\nCommit: abc123\nChecks: pytest passed\nNext work: Подготовить trial"
