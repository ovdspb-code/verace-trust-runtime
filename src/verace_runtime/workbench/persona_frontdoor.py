"""Persona-first browser front door over the runtime workbench."""

from __future__ import annotations

from dataclasses import dataclass

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.workbench import actions
from verace_runtime.workbench.capture_classifier import classify_capture
from verace_runtime.workbench.context import read_project_context
from verace_runtime.workbench.html import esc, page
from verace_runtime.workbench.persona_provider import (
    DraftOnlyProvider,
    PersonaActionHint,
    PersonaProvider,
    guard_persona_draft,
)


@dataclass(frozen=True)
class PersonaAction:
    intent: str
    label: str
    title: str
    body: str
    reason: str


def front_page(notice: str | None = None, first_run: bool = False, service: FounderAssistantService | None = None) -> str:
    body = _form()
    if first_run:
        body += _first_run_banner()
    body += _backstage(service, first_run)
    return page("Вера", body, notice)


def respond_page(message: str, provider: PersonaProvider | None = None, first_run: bool = False) -> str:
    context = read_project_context()
    proposals = build_actions(message)
    draft_provider = provider or DraftOnlyProvider()
    draft = draft_provider.draft(message, context, _hints(proposals))
    text = guard_persona_draft(draft.text)
    body = _dialog(message, text)
    if first_run:
        body += _first_run_banner()
    body += _actions(proposals)
    body += _backstage()
    return page("Вера", body)


def confirm_action(service: FounderAssistantService, form: dict[str, str]) -> str:
    intent = form.get("intent", "")
    if intent == "todo":
        return actions.create_task(service, form.get("body", ""))
    if intent == "fixation":
        return actions.record_decision(service, form.get("title", ""), form.get("body", ""))
    if intent == "check":
        return actions.create_review(
            service,
            form.get("title", ""),
            form.get("body", ""),
            form.get("review_type", "risk"),
            form.get("priority", "high"),
            None,
        )
    raise RuntimeError("Неизвестное подтверждение")


def build_actions(message: str) -> list[PersonaAction]:
    proposals: list[PersonaAction] = []
    lowered = message.lower()
    if "решили" in lowered or "приняли решение" in lowered:
        proposals.append(
            PersonaAction(
                "fixation",
                "Зафиксировать решение",
                "Решение из разговора",
                _clip(message),
                "В тексте есть формулировка принятого решения",
            )
        )
    for item in classify_capture(message, "note"):
        if item.kind == "ignore":
            continue
        if item.kind in {"task", "codex_task"}:
            proposals.append(PersonaAction("todo", "Записать как задачу", item.title, item.body, item.reason))
        elif item.kind == "decision":
            proposals.append(PersonaAction("fixation", "Зафиксировать решение", item.title, item.body, item.reason))
        elif item.kind in {"review", "risk_review"}:
            proposals.append(PersonaAction("check", "Поставить на проверку", item.title, item.body, item.reason))
    return _dedupe(proposals)


def _hints(actions_: list[PersonaAction]) -> list[PersonaActionHint]:
    return [PersonaActionHint(item.intent, item.title, item.body, item.reason) for item in actions_]


def _form() -> str:
    return (
        "<section class='hero'><h2>Вера</h2>"
        "<p class='muted'>Напишите естественно, что произошло или что нужно разобрать. "
        "Я предложу, что стоит записать, но ledger изменится только после подтверждения.</p>"
        "<form method='post' action='/vera'>"
        "<label>Что произошло?</label><textarea name='message' required rows='9' autofocus></textarea>"
        "<button>Обсудить с Верой</button></form></section>"
    )


def _dialog(message: str, text: str) -> str:
    return (
        "<section class='hero'><h2>Разбор Веры</h2>"
        f"<p class='meta'>Вы написали:</p><blockquote>{esc(message)}</blockquote>"
        f"<p>{esc(text).replace(chr(10), '<br>')}</p></section>"
    )


def _actions(items: list[PersonaAction]) -> str:
    if not items:
        return "<section><h2>Что записать?</h2><p class='muted'>Я бы пока ничего не записывала без уточнения.</p></section>"
    cards = []
    for item in items:
        cards.append(
            "<article class='card'>"
            f"<h3>{esc(item.label)}</h3><p>{esc(item.body)}</p>"
            f"<p class='meta'>Почему: {esc(item.reason)}</p>"
            "<form method='post' action='/vera'>"
            f"<input type='hidden' name='intent' value='{esc(item.intent)}'>"
            f"<input type='hidden' name='title' value='{esc(item.title)}'>"
            f"<label>Можно отредактировать перед подтверждением</label>"
            f"<textarea name='body' required rows='5'>{esc(item.body)}</textarea>"
            "<button>Подтвердить</button></form></article>"
        )
    return "<section><h2>Что можно записать</h2>" + "".join(cards) + "</section>"


def _first_run_banner() -> str:
    return (
        "<section><h2>Первый запуск</h2>"
        "<p>Обсуждать можно уже сейчас. Чтобы что-то записать, сначала подготовьте локальный ledger.</p>"
        "<form method='post' action='/init'><button>Инициализировать</button></form></section>"
    )


def _backstage(service: FounderAssistantService | None = None, first_run: bool = False) -> str:
    snapshot = "" if first_run or service is None else _runtime_snapshot(service)
    return (
        "<section><h2>За кулисами</h2><p class='muted'>Если нужно проверить ledger, документы или диагностику, "
        "это доступно отдельно.</p><p class='actions'><a class='button' href='/plan'>План</a>"
        "<a class='button' href='/documents'>Документы</a><a class='button' href='/capture'>Входящие</a>"
        "<a class='button' href='/reviews'>Проверки</a><a class='button' href='/doctor'>Диагностика</a></p>"
        f"{snapshot}"
        "<details><summary>Ручная коррекция</summary><p class='actions'>"
        "<a class='button' href='/tasks/new'>Задача</a><a class='button' href='/decisions/new'>Решение</a>"
        "<a class='button' href='/reviews/new'>На проверку</a></p>"
        "<p class='actions'><a class='button' href='/tasks/new'>Добавить задачу</a>"
        "<a class='button' href='/decisions/new'>Записать решение</a>"
        "<a class='button' href='/reviews/new'>Добавить на проверку</a></p></details></section>"
    )


def _runtime_snapshot(service: FounderAssistantService) -> str:
    brief = service.session_brief()
    tasks = "".join(f"<li>{esc(row['public_no'])}: {esc(row['title'])}</li>" for row in brief["tasks"][:3])
    decisions = "".join(f"<li>{esc(row['public_id'])}: {esc(row['title'])}</li>" for row in brief["decisions"][:3])
    return (
        "<details><summary>Текущий ledger</summary><p class='status ok'>Система готова</p>"
        f"<h3>Открытые задачи</h3><ul>{tasks or '<li>Пока нет открытых задач.</li>'}</ul>"
        f"<h3>Последние решения</h3><ul>{decisions or '<li>Пока нет записанных решений.</li>'}</ul></details>"
    )


def _dedupe(items: list[PersonaAction]) -> list[PersonaAction]:
    seen: set[tuple[str, str]] = set()
    out: list[PersonaAction] = []
    for item in items:
        key = (item.intent, item.title)
        if key not in seen:
            out.append(item)
            seen.add(key)
    return out


def _clip(text: str, limit: int = 600) -> str:
    return " ".join(text.split())[:limit]
