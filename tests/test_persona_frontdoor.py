from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.workbench.persona_provider import FakePersonaProvider
from verace_runtime.workbench.server import make_server


@contextmanager
def running_server(db_path, provider=None):
    server = make_server(port=0, db_path=db_path, persona_provider=provider)
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


def test_get_vera_renders_conversation_first_ui(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        html = get(base, "/vera")

    assert "Вера" in html
    assert "Что произошло?" in html
    assert "Обсудить с Верой" in html
    assert "capture_suggestion" not in html
    assert "risk_review" not in html
    assert "task / review / decision" not in html


def test_post_vera_with_fake_provider_returns_persona_response(tmp_path):
    provider = FakePersonaProvider("Я поняла. Вот что важно: не делать диспетчерскую главным входом.")
    db_path = tmp_path / "runtime.sqlite3"
    with running_server(db_path, provider) as base:
        post(base, "/init", {})
        html = post(base, "/vera", {"message": "Надо сделать живую Веру как вход."})

    assert "Разбор Веры" in html
    assert "Вот что важно" in html
    assert "Записать как задачу" in html
    assert provider.calls


def test_post_vera_does_not_mutate_without_explicit_confirm(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    service = FounderAssistantService(db_path)
    service.init_runtime()
    before = service.status()

    with running_server(db_path) as base:
        html = post(base, "/vera", {"message": "Надо сделать persona front door."})

    after = FounderAssistantService(db_path).status()
    assert "Что можно записать" in html
    assert after == before


def test_vera_confirm_task_creates_receipt_backed_task(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    with running_server(db_path) as base:
        post(base, "/init", {})
        html = post(base, "/vera", {"intent": "todo", "body": "Сделать живую Веру как вход."})

    assert "Подтверждено receipt-записью" in html
    assert "Task TR-000001 was recorded" in html
    assert "Receipt: RCPT-" in html


def test_vera_confirm_decision_creates_receipt_backed_decision(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    with running_server(db_path) as base:
        post(base, "/init", {})
        html = post(
            base,
            "/vera",
            {"intent": "fixation", "title": "Persona-first UX", "body": "Primary entry is a live persona."},
        )

    assert "Decision DEC-000001 was recorded" in html
    assert "Receipt: RCPT-" in html


def test_vera_confirm_review_creates_receipt_backed_review(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    with running_server(db_path) as base:
        post(base, "/init", {})
        html = post(
            base,
            "/vera",
            {"intent": "check", "title": "Review persona voice", "body": "Check template voice risk."},
        )

    assert "Review REV-000001 was created" in html
    assert "Receipt: RCPT-" in html


def test_vera_blocks_unsupported_completed_action_claim(tmp_path):
    provider = FakePersonaProvider("Я записала задачу и проверила статус.")
    db_path = tmp_path / "runtime.sqlite3"
    with running_server(db_path, provider) as base:
        post(base, "/init", {})
        html = post(base, "/vera", {"message": "Надо записать задачу."})

    assert "Я записала" not in html
    assert "без receipt" in html


def test_vera_first_run_is_clean(tmp_path):
    with running_server(tmp_path / "runtime.sqlite3") as base:
        html = get(base, "/vera")
        response = post(base, "/vera", {"message": "Надо подготовить first run."})
        confirm = post(base, "/vera", {"intent": "todo", "body": "Не должно записаться до init."})

    assert "Первый запуск" in html
    assert "Первый запуск" in response
    assert "Сначала инициализируйте локальный ledger" in confirm
    assert "Required ledger row not found" not in html + response + confirm
    assert "Traceback" not in html + response + confirm


def test_vera_unsafe_db_fails_closed(tmp_path):
    db_path = tmp_path / "unversioned.sqlite3"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE orphan_state(id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO orphan_state(id) VALUES ('x')")

    with running_server(db_path) as base:
        html = get(base, "/vera")

    assert "Unsafe runtime schema" in html
    assert "missing runtime_meta" in html
    assert "Traceback" not in html
