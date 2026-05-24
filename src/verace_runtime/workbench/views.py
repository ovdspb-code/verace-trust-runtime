"""Server-rendered pages for the founder workbench."""

from __future__ import annotations

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.workbench.html import esc, items, page


def dashboard(service: FounderAssistantService, notice: str | None = None) -> str:
    doctor = service.doctor()
    body = _hero(doctor)
    if not doctor["ok"]:
        return page("Verace", body + _init_form(), notice)
    brief = service.session_brief()
    body += "<div class='grid'>"
    body += _panel("Открытые задачи", _task_rows(brief["tasks"]), "Пока нет открытых задач.")
    body += _panel("На проверке", _review_rows(brief["reviews"]), "Пока нет вопросов на проверке.")
    body += _panel("Последние решения", _decision_rows(brief["decisions"]), "Пока нет записанных решений.")
    events = _event_rows(brief["task_events"], "public_no") + _event_rows(brief["review_events"], "public_id")
    body += _panel("Последние события", events, "Пока нет событий.")
    body += "</div>"
    return page("Verace", body, notice)


def task_form() -> str:
    return page("Задача", "<section><h2>Добавить задачу</h2><form method='post' action='/tasks'><label>Что нужно сделать?</label><textarea name='text' required rows='4'></textarea><button>Добавить задачу</button></form></section>")


def decision_form() -> str:
    return page("Решение", "<section><h2>Записать решение</h2><form method='post' action='/decisions'><label>Название</label><input name='title' required><label>Текст решения</label><textarea name='text' required rows='5'></textarea><button>Записать решение</button></form></section>")


def reviews(service: FounderAssistantService, notice: str | None = None) -> str:
    open_items = service.list_reviews("open")
    rows = []
    for item in open_items:
        task = f"задача {esc(item.task_public_no)}" if item.task_public_no else "без задачи"
        detail = f"<p>{esc(getattr(item, 'body', ''))}</p>" if getattr(item, "body", "") else ""
        rows.append(
            f"<article class='card review-card'><h3>{esc(item.public_id)} · {esc(item.title)}</h3>"
            f"<p class='meta'>{esc(_review_type(item.review_type))} · {esc(_priority(item.priority))} · {task}</p>"
            f"{detail}"
            f"<form method='post' action='/reviews/{esc(item.public_id)}/resolve'>"
            "<label>Решение по проверке</label><textarea name='resolution' required rows='3'></textarea>"
            "<label>Статус</label><select name='status'><option value='resolved'>Решено</option><option value='dismissed'>Отклонено</option></select>"
            "<button>Закрыть проверку</button></form></article>"
        )
    body = "<section><h2>На проверке</h2>" + "".join(rows) if rows else "<section><h2>На проверке</h2>" + items([], "Пока нет вопросов на проверке.")
    body += "<p><a class='button' href='/reviews/new'>Добавить на проверку</a></p></section>"
    return page("Проверки", body, notice)


def review_form() -> str:
    body = """
    <section><h2>Добавить на проверку</h2><form method="post" action="/reviews">
    <label>Название</label><input name="title" required>
    <label>Что нужно проверить?</label><textarea name="body" required rows="5"></textarea>
    <label>Тип</label><select name="review_type"><option value="architecture">Архитектура</option><option value="decision">Решение</option><option value="risk">Риск</option><option value="clarification">Уточнение</option><option value="evidence">Доказательство</option><option value="approval_request">Запрос на approval</option></select>
    <label>Приоритет</label><select name="priority"><option value="normal">Обычный</option><option value="high">Высокий</option><option value="critical">Критический</option><option value="low">Низкий</option></select>
    <label>Связанная задача</label><input name="task" placeholder="TR-000001">
    <button>Добавить на проверку</button></form></section>
    """
    return page("На проверку", body)


def doctor_page(service: FounderAssistantService) -> str:
    return page("Диагностика", _doctor_block(service.doctor()))


def error_page(message: str, status: int = 400) -> tuple[int, str]:
    return status, page("Ошибка", "", error=message)


def _hero(doctor: dict[str, object]) -> str:
    ready = bool(doctor["ok"])
    css = "ok" if ready else "fail"
    text = "Система готова" if ready else "Требуется инициализация или проверка"
    return (
        "<section class='hero'><h2>Рабочая панель проекта</h2>"
        f"<p><span class='status {css}'>{text}</span></p>"
        "<p class='muted'>Здесь видно, что открыто по Verace и что требует внимания.</p>"
        "<p class='actions'><a class='button' href='/tasks/new'>Добавить задачу</a>"
        "<a class='button' href='/decisions/new'>Записать решение</a>"
        "<a class='button' href='/reviews/new'>Добавить на проверку</a></p></section>"
    )


def _doctor_block(doctor: dict[str, object]) -> str:
    status = "OK" if doctor["ok"] else "FAIL"
    css = "ok" if doctor["ok"] else "fail"
    return (
        f"<section><h2>Диагностика: <span class='{css}'>{status}</span></h2>"
        f"<p>Schema: {esc(doctor['schema_name'] or 'unknown')} v{esc(doctor['schema_version'] if doctor['schema_version'] is not None else 'unknown')} "
        f"current={esc(doctor['schema_current'])}</p><p>Reason: {esc(doctor['schema_reason'])}</p></section>"
    )


def _init_form() -> str:
    return "<section><h2>Первый запуск</h2><p>Нужно подготовить локальный ledger перед работой.</p><form method='post' action='/init'><button>Инициализировать</button></form></section>"


def _panel(title: str, rows: list[str], empty: str) -> str:
    return f"<section><h2>{esc(title)}</h2>{items(rows, empty)}</section>"


def _task_rows(rows: list[dict[str, object]]) -> list[str]:
    return [f"<strong>{esc(row['public_no'])}</strong> [{esc(_task_status(str(row['status'])))}] {esc(row['title'])}" for row in rows]


def _review_rows(rows: list[dict[str, object]]) -> list[str]:
    return [f"<strong>{esc(row['public_id'])}</strong> [{esc(_priority(str(row['priority'])))}/{esc(_review_type(str(row['review_type'])))}] {esc(row['title'])}" for row in rows]


def _decision_rows(rows: list[dict[str, object]]) -> list[str]:
    return [f"<strong>{esc(row['public_id'])}</strong> [{esc(_decision_status(str(row['status'])))}] {esc(row['title'])}" for row in rows]


def _event_rows(rows: list[dict[str, object]], id_key: str) -> list[str]:
    return [f"{esc(row[id_key])} {esc(_event_type(str(row['event_type'])))}: {esc(row['summary'])}" for row in rows]


def _priority(value: str) -> str:
    return {"low": "низкий", "normal": "обычный", "high": "высокий", "critical": "критический"}.get(value, value)


def _review_type(value: str) -> str:
    labels = {
        "architecture": "архитектура",
        "decision": "решение",
        "risk": "риск",
        "clarification": "уточнение",
        "evidence": "доказательство",
        "approval_request": "запрос на approval",
    }
    return labels.get(value, value)


def _task_status(value: str) -> str:
    return {"open": "открыта", "waiting": "ждет", "blocked": "заблокирована", "done": "готово", "canceled": "отменена"}.get(value, value)


def _decision_status(value: str) -> str:
    return {"active": "активно"}.get(value, value)


def _event_type(value: str) -> str:
    labels = {
        "task.created": "задача создана",
        "task.status.changed": "статус задачи изменен",
        "review.item.created": "проверка создана",
        "review.item.resolved": "проверка решена",
        "review.item.dismissed": "проверка отклонена",
    }
    return labels.get(value, value)
