"""Server-rendered pages for the founder workbench."""

from __future__ import annotations

from urllib.parse import quote

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.workbench.context import ProjectContext, read_project_context
from verace_runtime.workbench.html import esc, items, page
from verace_runtime.workbench.suggestions import Suggestion, build_suggestions, codex_task_prompt, find_suggestion


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
        "<p class='actions'><a class='button' href='/plan'>Открыть план</a>"
        "<a class='button' href='/tasks/new'>Добавить задачу</a>"
        "<a class='button' href='/decisions/new'>Записать решение</a>"
        "<a class='button' href='/reviews/new'>Добавить на проверку</a></p></section>"
    )


def plan_page(service: FounderAssistantService, notice: str | None = None, dismissed: set[str] | None = None) -> str:
    context = read_project_context()
    dismissed = dismissed or set()
    suggestions = [item for item in build_suggestions(context) if item.id not in dismissed]
    body = (
        "<section class='hero'><h2>План проекта</h2>"
        f"<p><strong>{esc(context.project_name)}</strong> · {esc(context.current_phase)}</p>"
        f"<p>Поверхность: {esc(context.current_product_surface or 'не указана')}</p>"
        f"<p>Текущая работа: {esc(context.current_work or context.recent_work or 'не указана')}</p>"
        f"<p>Следующий шаг: {esc(context.next_work or 'не указан')}</p></section>"
    )
    body += "<div class='grid'>"
    body += _panel("Открытые риски", [f"<strong>{esc(risk.title)}</strong>: {esc(risk.mitigation)}" for risk in context.open_risks[:5]], "Пока нет открытых рисков.")
    body += _panel("Последние решения", [esc(row) for row in context.latest_decisions], "Пока нет решений в журнале.")
    body += _panel("Последние записи", [esc(row) for row in context.recent_worklog], "Пока нет записей worklog.")
    body += "</div>"
    body += "<section><h2>Предложенные действия</h2>" + (_suggestion_cards(suggestions) if suggestions else "<p class='muted'>Все предложения скрыты для этой сессии.</p>") + "</section>"
    return page("План", body, notice)


def documents_page() -> str:
    context = read_project_context()
    groups: dict[str, list[str]] = {}
    for doc in context.documents:
        status = f" · {esc(doc.status)}" if doc.status else ""
        purpose = f"<p class='muted'>{esc(doc.purpose)}</p>" if doc.purpose else ""
        groups.setdefault(doc.category, []).append(f"<strong>{esc(doc.title)}</strong>{status}<br><code>{esc(doc.path)}</code>{purpose}")
    body = "<section><h2>Документы проекта</h2><p class='muted'>Карта локальных документов, из которых Workbench строит план и предложения.</p></section>"
    body += "<div class='grid'>"
    for title in ("README", "Operations", "ADRs", "Briefs", "Plans"):
        body += _panel(title, groups.get(title, []), "Документы не найдены.")
    body += "</div>"
    return page("Документы", body)


def suggestion_task_form(suggestion_id: str) -> str:
    suggestion = find_suggestion(read_project_context(), suggestion_id)
    body = f"<section><h2>Принять как задачу</h2><form method='post' action='/suggestions/task'><label>Текст задачи</label><textarea name='text' required rows='5'>{esc(suggestion.body)}</textarea><button>Создать задачу</button></form></section>"
    return page("Задача из предложения", body)


def suggestion_review_form(suggestion_id: str) -> str:
    suggestion = find_suggestion(read_project_context(), suggestion_id)
    body = f"""<section><h2>Принять как проверку</h2><form method="post" action="/suggestions/review">
    <label>Название</label><input name="title" required value="{esc(suggestion.title)}">
    <label>Что нужно проверить?</label><textarea name="body" required rows="6">{esc(suggestion.body)}</textarea>
    <label>Тип</label><select name="review_type"><option value="risk">Риск</option><option value="architecture">Архитектура</option><option value="decision">Решение</option><option value="clarification">Уточнение</option></select>
    <label>Приоритет</label><select name="priority"><option value="high">Высокий</option><option value="normal">Обычный</option><option value="critical">Критический</option><option value="low">Низкий</option></select>
    <button>Создать проверку</button></form></section>"""
    return page("Проверка из предложения", body)


def suggestion_decision_form(suggestion_id: str) -> str:
    suggestion = find_suggestion(read_project_context(), suggestion_id)
    body = f"<section><h2>Записать как решение</h2><form method='post' action='/suggestions/decision'><label>Название</label><input name='title' required value='{esc(suggestion.title)}'><label>Текст решения</label><textarea name='text' required rows='6'>{esc(suggestion.body)}</textarea><button>Записать решение</button></form></section>"
    return page("Решение из предложения", body)


def codex_task_page(suggestion_id: str) -> str:
    context = read_project_context()
    suggestion = find_suggestion(context, suggestion_id)
    prompt = codex_task_prompt(context, suggestion)
    return page("Codex task", f"<section><h2>Codex task text</h2><p class='muted'>Сгенерировано детерминированно из локальных документов.</p><pre>{esc(prompt)}</pre></section>")


def _suggestion_cards(suggestions: list[Suggestion]) -> str:
    cards = []
    for item in suggestions:
        key = quote(item.id)
        actions = [f"<a class='button' href='/suggestions/task?key={key}'>Принять как задачу</a>", f"<a class='button' href='/suggestions/review?key={key}'>Принять как review</a>", f"<a class='button' href='/suggestions/decision?key={key}'>Записать как решение</a>", f"<a class='button' href='/suggestions/codex?key={key}'>Codex task</a>"]
        cards.append(
            f"<article class='card'><h3>{esc(item.title)}</h3><p>{esc(item.body)}</p>"
            f"<p class='meta'>тип: {esc(_suggestion_kind(item.kind))} · source: {esc(item.source_file)} · причина: {esc(item.reason)}</p>"
            f"<p class='actions'>{''.join(actions)}</p><form method='post' action='/suggestions/dismiss'><input type='hidden' name='key' value='{esc(item.id)}'><button>Скрыть на эту сессию</button></form></article>"
        )
    return "".join(cards)


def _suggestion_kind(value: str) -> str:
    return {"task": "задача", "review": "проверка", "decision": "решение", "codex_task": "Codex task"}.get(value, value)


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
