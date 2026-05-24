"""Conversation capture storage and browser rendering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.ids import new_id
from verace_runtime.ledger.db import apply_schema, connect
from verace_runtime.ledger.repository import LedgerRepository
from verace_runtime.workbench.capture_classifier import CaptureSuggestionCandidate, classify_capture
from verace_runtime.workbench.capture_prompts import codex_prompt_from_capture
from verace_runtime.workbench.context import read_project_context
from verace_runtime.workbench.html import esc, items, page
from verace_runtime.time import utc_now_iso


@dataclass(frozen=True)
class CaptureRecord:
    public_id: str
    source_type: str
    source_label: str | None
    raw_text: str
    status: str
    created_at: str
    receipt_public_id: str


@dataclass(frozen=True)
class CaptureSuggestion:
    public_id: str
    capture_public_id: str
    kind: str
    title: str
    body: str
    reason: str
    source_span: str | None
    status: str


SOURCE_TYPES = ("chatgpt", "codex", "claude", "telegram", "note", "other")


def record_capture(service: FounderAssistantService, source_type: str, source_label: str, raw_text: str) -> tuple[CaptureRecord, list[CaptureSuggestion]]:
    clean_text = raw_text.strip()
    clean_source = source_type if source_type in SOURCE_TYPES else "other"
    if not clean_text:
        raise RuntimeError("Capture text is empty")
    candidates = classify_capture(clean_text, clean_source)
    with connect(service.db_path) as conn:
        apply_schema(conn)
        repo = LedgerRepository(conn)
        now = utc_now_iso()
        decision = service.policy.evaluate("ledger.event")
        if not decision.allowed:
            raise RuntimeError("Capture recording blocked by policy")
        capture_id = new_id("capture")
        public_id = _next_public(conn, "capture_items", "CAP")
        receipt = repo.insert_receipt(service.receipts.build(decision, "ledger.event", "capture_item", capture_id, f"Capture {public_id} recorded"))
        repo.insert_claim("capture_recorded", f"Capture {public_id} was recorded in the ledger", "capture_item", capture_id, receipt["id"], now)
        conn.execute(
            """
            INSERT INTO capture_items
            (id, public_id, source_type, source_label, raw_text, status, created_at, receipt_id)
            VALUES (?, ?, ?, ?, ?, 'processed', ?, ?)
            """,
            (capture_id, public_id, clean_source, source_label.strip() or None, clean_text, now, receipt["id"]),
        )
        for candidate in candidates:
            _insert_suggestion(conn, capture_id, candidate, now)
        conn.commit()
        return capture_detail(conn, public_id)


def list_captures(db_path: str | Path) -> list[CaptureRecord]:
    with connect(db_path) as conn:
        apply_schema(conn)
        rows = conn.execute(
            """
            SELECT c.*, r.public_id AS receipt_public_id FROM capture_items c
            JOIN receipts r ON r.id = c.receipt_id
            ORDER BY c.created_at DESC, c.public_id DESC LIMIT 10
            """
        ).fetchall()
        return [_capture(row) for row in rows]


def list_proposed_suggestions(db_path: str | Path) -> list[CaptureSuggestion]:
    with connect(db_path) as conn:
        apply_schema(conn)
        rows = conn.execute(
            """
            SELECT s.*, c.public_id AS capture_public_id FROM capture_suggestions s
            JOIN capture_items c ON c.id = s.capture_id
            WHERE s.status = 'proposed'
            ORDER BY s.created_at, s.public_id
            """
        ).fetchall()
        return [_suggestion(row) for row in rows]


def capture_detail(conn_or_path, capture_ref: str) -> tuple[CaptureRecord, list[CaptureSuggestion]]:
    close = False
    conn = conn_or_path
    if not hasattr(conn_or_path, "execute"):
        conn = connect(conn_or_path)
        apply_schema(conn)
        close = True
    try:
        row = conn.execute(
            """
            SELECT c.*, r.public_id AS receipt_public_id FROM capture_items c
            JOIN receipts r ON r.id = c.receipt_id
            WHERE c.public_id = ?
            """,
            (capture_ref,),
        ).fetchone()
        if row is None:
            raise RuntimeError("Capture not found")
        suggestions = conn.execute(
            """
            SELECT s.*, c.public_id AS capture_public_id FROM capture_suggestions s
            JOIN capture_items c ON c.id = s.capture_id
            WHERE c.public_id = ? ORDER BY s.created_at, s.public_id
            """,
            (capture_ref,),
        ).fetchall()
        return _capture(row), [_suggestion(item) for item in suggestions]
    finally:
        if close:
            conn.close()


def suggestion_detail(db_path: str | Path, suggestion_ref: str) -> tuple[CaptureRecord, CaptureSuggestion]:
    with connect(db_path) as conn:
        apply_schema(conn)
        row = conn.execute(
            """
            SELECT s.*, c.public_id AS capture_public_id FROM capture_suggestions s
            JOIN capture_items c ON c.id = s.capture_id WHERE s.public_id = ?
            """,
            (suggestion_ref,),
        ).fetchone()
        if row is None:
            raise RuntimeError("Capture suggestion not found")
        capture, _ = capture_detail(conn, row["capture_public_id"])
        return capture, _suggestion(row)


def mark_suggestion(db_path: str | Path, suggestion_ref: str, subject_type: str, subject_ref: str, receipt_public_id: str) -> None:
    with connect(db_path) as conn:
        apply_schema(conn)
        receipt = conn.execute("SELECT id FROM receipts WHERE public_id = ?", (receipt_public_id,)).fetchone()
        if receipt is None:
            raise RuntimeError("Receipt not found for accepted suggestion")
        changed = conn.execute(
            """
            UPDATE capture_suggestions
            SET status = 'accepted', accepted_subject_type = ?, accepted_subject_ref = ?,
                receipt_id = ?, updated_at = ?
            WHERE public_id = ? AND status = 'proposed'
            """,
            (subject_type, subject_ref, receipt["id"], utc_now_iso(), suggestion_ref),
        ).rowcount
        if changed != 1:
            raise RuntimeError("Capture suggestion is not proposed")
        conn.commit()


def dismiss_suggestion(db_path: str | Path, suggestion_ref: str) -> None:
    with connect(db_path) as conn:
        apply_schema(conn)
        changed = conn.execute(
            "UPDATE capture_suggestions SET status = 'dismissed', updated_at = ? WHERE public_id = ? AND status = 'proposed'",
            (utc_now_iso(), suggestion_ref),
        ).rowcount
        if changed != 1:
            raise RuntimeError("Capture suggestion is not proposed")
        conn.commit()


def codex_prompt(db_path: str | Path, suggestion_ref: str) -> str:
    capture, suggestion = suggestion_detail(db_path, suggestion_ref)
    return codex_prompt_from_capture(suggestion.title, suggestion.body, capture.source_type, capture.source_label, read_project_context())


def inbox_page(db_path: str | Path, notice: str | None = None, first_run: bool = False) -> str:
    captures = [] if first_run else list_captures(db_path)
    suggestions = [] if first_run else list_proposed_suggestions(db_path)
    body = _capture_form()
    if first_run:
        body += _first_run_banner()
    body += _suggestion_section(suggestions)
    body += _capture_list(captures)
    return page("Захват", body, notice)


def detail_page(db_path: str | Path, capture_ref: str, notice: str | None = None) -> str:
    capture, suggestions = capture_detail(db_path, capture_ref)
    body = f"<section><h2>{esc(capture.public_id)}</h2><p class='meta'>{esc(capture.source_type)} · Receipt: {esc(capture.receipt_public_id)}</p><pre>{esc(capture.raw_text)}</pre></section>"
    body += _suggestion_section([item for item in suggestions if item.status == "proposed"])
    body += _panel_status("Уже обработано", [f"{esc(item.public_id)} · {esc(_kind(item.kind))} · {esc(item.status)}" for item in suggestions if item.status != "proposed"])
    return page("Захват", body, notice)


def suggestion_form(db_path: str | Path, suggestion_ref: str, target: str) -> str:
    _, suggestion = suggestion_detail(db_path, suggestion_ref)
    if target == "task":
        body = f"<section><h2>Принять как задачу</h2><form method='post' action='/capture/suggestions/{esc(suggestion.public_id)}/task'><label>Текст задачи</label><textarea name='text' required rows='5'>{esc(suggestion.body)}</textarea><button>Создать задачу</button></form></section>"
    elif target == "decision":
        body = f"<section><h2>Записать как решение</h2><form method='post' action='/capture/suggestions/{esc(suggestion.public_id)}/decision'><label>Название</label><input name='title' required value='{esc(suggestion.title)}'><label>Текст решения</label><textarea name='text' required rows='6'>{esc(suggestion.body)}</textarea><button>Записать решение</button></form></section>"
    else:
        body = f"<section><h2>Принять как проверку</h2><form method='post' action='/capture/suggestions/{esc(suggestion.public_id)}/review'><label>Название</label><input name='title' required value='{esc(suggestion.title)}'><label>Что проверить?</label><textarea name='body' required rows='6'>{esc(suggestion.body)}</textarea><label>Тип</label><select name='review_type'><option value='risk'>Риск</option><option value='architecture'>Архитектура</option><option value='decision'>Решение</option><option value='clarification'>Уточнение</option></select><label>Приоритет</label><select name='priority'><option value='high'>Высокий</option><option value='normal'>Обычный</option><option value='critical'>Критический</option><option value='low'>Низкий</option></select><button>Создать проверку</button></form></section>"
    return page("Предложение", body)


def codex_page(db_path: str | Path, suggestion_ref: str) -> str:
    return page("Codex task", f"<section><h2>Codex task text</h2><p class='muted'>Сгенерировано детерминированно из захвата.</p><pre>{esc(codex_prompt(db_path, suggestion_ref))}</pre></section>")


def _insert_suggestion(conn, capture_id: str, item: CaptureSuggestionCandidate, now: str) -> None:
    conn.execute(
        """
        INSERT INTO capture_suggestions
        (id, public_id, capture_id, kind, title, body, reason, source_span, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'proposed', ?)
        """,
        (new_id("capture_suggestion"), _next_public(conn, "capture_suggestions", "CSUG"), capture_id, item.kind, item.title, item.body, item.reason, item.source_span, now),
    )


def _next_public(conn, table: str, prefix: str) -> str:
    seq = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"] + 1
    return f"{prefix}-{seq:06d}"


def _capture(row) -> CaptureRecord:
    return CaptureRecord(row["public_id"], row["source_type"], row["source_label"], row["raw_text"], row["status"], row["created_at"], row["receipt_public_id"])


def _suggestion(row) -> CaptureSuggestion:
    return CaptureSuggestion(row["public_id"], row["capture_public_id"], row["kind"], row["title"], row["body"], row["reason"], row["source_span"], row["status"])


def _capture_form() -> str:
    options = "".join(f"<option value='{item}'>{_source_label(item)}</option>" for item in SOURCE_TYPES)
    return f"<section class='hero'><h2>Входящие</h2><p>Вставьте фрагмент из чата, Codex-отчета, Claude, Telegram или заметок. Workbench предложит действия, но ledger изменится только после подтверждения.</p><form method='post' action='/capture'><label>Источник</label><select name='source_type'>{options}</select><label>Метка источника</label><input name='source_label' placeholder='например: ChatGPT session'><label>Текст</label><textarea name='raw_text' required rows='8'></textarea><button>Разобрать текст</button></form></section>"


def _first_run_banner() -> str:
    return "<section><h2>Первый запуск</h2><p>Чтобы сохранить захват, сначала подготовьте локальный ledger.</p><form method='post' action='/init'><button>Инициализировать</button></form></section>"


def _suggestion_section(suggestions: list[CaptureSuggestion]) -> str:
    cards = []
    for item in suggestions:
        actions = _actions(item)
        cards.append(f"<article class='card'><h3>{esc(item.public_id)} · {esc(item.title)}</h3><p>{esc(item.body)}</p><p class='meta'>{esc(_kind(item.kind))} · причина: {esc(item.reason)} · capture {esc(item.capture_public_id)}</p><p class='actions'>{actions}</p><form method='post' action='/capture/suggestions/{esc(item.public_id)}/dismiss'><button>Скрыть</button></form></article>")
    return "<section><h2>Предложения из захвата</h2>" + ("".join(cards) if cards else "<p class='muted'>Пока нет предложений.</p>") + "</section>"


def _actions(item: CaptureSuggestion) -> str:
    base = f"/capture/suggestions/{esc(item.public_id)}"
    links = []
    if item.kind in {"task", "codex_task"}:
        links.append(f"<a class='button' href='{base}/task'>Принять как задачу</a>")
    if item.kind in {"review", "risk_review"}:
        links.append(f"<a class='button' href='{base}/review'>Принять как проверку</a>")
    if item.kind == "decision":
        links.append(f"<a class='button' href='{base}/decision'>Записать как решение</a>")
    if item.kind == "codex_task":
        links.append(f"<a class='button' href='{base}/codex'>Codex task</a>")
    return "".join(links)


def _capture_list(captures: list[CaptureRecord]) -> str:
    rows = [f"<a href='/capture/{esc(item.public_id)}'>{esc(item.public_id)}</a> · {esc(_source_label(item.source_type))} · {esc(item.created_at)}" for item in captures]
    return "<section><h2>Последние захваты</h2>" + items(rows, "Пока нет захваченных фрагментов.") + "</section>"


def _panel_status(title: str, rows: list[str]) -> str:
    return f"<section><h2>{esc(title)}</h2>{items(rows, 'Пока нет обработанных предложений.')}</section>"


def _source_label(value: str) -> str:
    return {"chatgpt": "ChatGPT", "codex": "Codex", "claude": "Claude", "telegram": "Telegram", "note": "Заметка", "other": "Другое"}.get(value, value)


def _kind(value: str) -> str:
    return {"task": "задача", "decision": "решение", "review": "проверка", "risk_review": "риск", "codex_task": "Codex task", "ignore": "игнорировать"}.get(value, value)
