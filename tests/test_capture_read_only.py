from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.ledger.migrations import write_meta
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


def test_capture_read_only_pages_do_not_mutate_status_counts(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    with running_server(db_path) as base:
        post(base, "/capture", {"source_type": "codex", "source_label": "", "raw_text": "TASK FOR CODEX\nGoal:\nFix.\nAcceptance criteria:\nDone."})
        before = service.status()
        get(base, "/capture")
        get(base, "/capture/CAP-000001")
        get(base, "/capture/suggestions/CSUG-000001/codex")
        after = service.status()

    assert after == before


def test_capture_accept_before_init_fails_gracefully(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    with running_server(db_path) as base:
        html = post(base, "/capture/suggestions/CSUG-000001/task", {"text": "Should not create"})

    assert "Сначала инициализируйте локальный ledger." in html
    assert "Required ledger row not found" not in html
    assert "Traceback" not in html
    assert not db_path.exists()


def test_capture_unsafe_db_fails_closed(tmp_path):
    db_path = tmp_path / "unsafe.sqlite3"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE orphan_state(id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO orphan_state(id) VALUES ('x')")
        conn.commit()

    with running_server(db_path) as base:
        html = get(base, "/capture")

    assert "Unsafe runtime schema" in html
    assert "missing runtime_meta" in html
    assert "Traceback" not in html


def test_non_empty_v2_runtime_migrates_to_v3_without_losing_rows(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    service.ingest_message("oleg", "verace_project", "Preserve existing task")
    service.record_decision("oleg", "verace_project", "Preserve decision", "Existing decision")
    service.add_review("oleg", "verace_project", "Preserve review", "Existing review", "risk", "high")
    with sqlite3.connect(db_path) as conn:
        conn.execute("DROP TABLE capture_suggestions")
        conn.execute("DROP TABLE capture_items")
        write_meta(conn, {"schema_version": "2", "last_migrated_at": "legacy"})
        conn.commit()

    with running_server(db_path) as base:
        home = get(base, "/")
        inbox = get(base, "/capture")

    assert "Unsafe runtime schema" not in home
    assert "Входящие" in inbox
    doctor = FounderAssistantService(db_path).doctor()
    assert doctor["ok"] is True
    assert doctor["schema_version"] == 3
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM review_items").fetchone()[0] == 1
        names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"capture_items", "capture_suggestions"} <= names


def test_browser_repeated_capture_accept_is_clean_error_without_mutation(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    with running_server(db_path) as base:
        post(base, "/init", {})
        post(base, "/capture", {"source_type": "note", "source_label": "", "raw_text": "Нужно проверить duplicate accept."})
        post(base, "/capture/suggestions/CSUG-000001/task", {"text": "Проверить duplicate accept"})
        before = service.status()
        html = post_error(base, "/capture/suggestions/CSUG-000001/task", {"text": "Duplicate"})
        after = service.status()

    assert "Capture suggestion is not proposed" in html
    assert "Traceback" not in html
    assert after["tasks"] == before["tasks"]
    assert after["messages"] == before["messages"]
