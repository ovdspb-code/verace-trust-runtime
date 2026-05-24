from __future__ import annotations

import threading
from contextlib import contextmanager
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import pytest

from verace_runtime.workbench.server import DEFAULT_HOST, make_server


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


def get(base: str, path: str = "/") -> str:
    with urlopen(base + path) as response:
        assert response.status == 200
        return response.read().decode("utf-8")


def post(base: str, path: str, data: dict[str, str]) -> str:
    body = urlencode(data).encode("utf-8")
    request = Request(base + path, data=body, method="POST")
    try:
        with urlopen(request) as response:
            assert response.status == 200
            return response.read().decode("utf-8")
    except HTTPError as exc:
        return exc.read().decode("utf-8")


def test_server_binds_to_localhost_by_default(tmp_path):
    assert DEFAULT_HOST == "127.0.0.1"
    server = make_server(port=0, db_path=tmp_path / "runtime.sqlite3")
    try:
        assert server.server_address[0] == "127.0.0.1"
    finally:
        server.server_close()


def test_server_refuses_non_localhost_bind(tmp_path):
    with pytest.raises(RuntimeError, match="127.0.0.1"):
        make_server(host="0.0.0.0", port=0, db_path=tmp_path / "runtime.sqlite3")


def test_dashboard_renders_on_fresh_and_initialized_db(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        fresh = get(base)
        initialized = post(base, "/init", {})

    assert "Рабочая панель проекта" in fresh
    assert "Требуется инициализация или проверка" in fresh
    assert "Инициализировать" in fresh
    assert "Runtime initialized. Receipt: RCPT-" in initialized
    assert "Система готова" in initialized
    assert "Пока нет открытых задач." in initialized
    assert "Пока нет вопросов на проверке." in initialized
    assert "Пока нет записанных решений." in initialized
    assert "Пока нет событий." in initialized
    assert "current=True" not in initialized
    assert "Reason: current" not in initialized
    assert "receipts=" not in initialized
    assert "claims=" not in initialized


def test_dashboard_navigation_and_primary_actions_are_russian(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        post(base, "/init", {})
        html = get(base)

    for label in ("Обзор", "Задача", "Решение", "Проверки", "На проверку", "Диагностика"):
        assert label in html
    for label in ("Добавить задачу", "Записать решение", "Добавить на проверку"):
        assert label in html


def test_browser_error_has_no_raw_traceback(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        post(base, "/init", {})
        html = post(base, "/tasks", {"text": ""})

    assert "Ошибка" in html
    assert "Message text is empty" in html
    assert "Traceback" not in html
