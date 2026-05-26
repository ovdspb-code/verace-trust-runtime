"""Persona language providers for the browser front door."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Callable, Protocol
from urllib.request import Request, urlopen

from verace_runtime.workbench.context import ProjectContext


@dataclass(frozen=True)
class PersonaActionHint:
    kind: str
    title: str
    body: str
    reason: str


@dataclass(frozen=True)
class PersonaActionDraft:
    intent: str
    title: str
    body: str
    reason: str = ""


@dataclass(frozen=True)
class PersonaRequestContext:
    message: str
    project_context: ProjectContext
    ledger_summary: str
    hints: tuple[PersonaActionHint, ...]


@dataclass(frozen=True)
class PersonaDraft:
    text: str
    proposed_actions: tuple[PersonaActionDraft, ...] = ()
    degraded: bool = False
    unavailable: bool = False


class PersonaProvider(Protocol):
    def draft(self, request: PersonaRequestContext) -> PersonaDraft:
        """Draft persona language only; runtime owns state and receipts."""


class UnavailablePersonaProvider:
    def draft(self, request: PersonaRequestContext) -> PersonaDraft:
        return PersonaDraft(
            "Живой голос Веры пока не подключен. Основной разговорный режим недоступен.",
            degraded=True,
            unavailable=True,
        )


DraftOnlyProvider = UnavailablePersonaProvider


class FakePersonaProvider:
    def __init__(self, text: str, actions: tuple[PersonaActionDraft, ...] = ()) -> None:
        self.text = text
        self.actions = actions
        self.calls: list[PersonaRequestContext] = []

    def draft(self, request: PersonaRequestContext) -> PersonaDraft:
        self.calls.append(request)
        return PersonaDraft(self.text, self.actions)


class OpenAIResponsesPersonaProvider:
    endpoint = "https://api.openai.com/v1/responses"

    def __init__(
        self,
        api_key: str,
        model: str,
        opener: Callable[..., object] = urlopen,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.opener = opener
        self.timeout = timeout

    def draft(self, request: PersonaRequestContext) -> PersonaDraft:
        payload = {
            "model": self.model,
            "instructions": _instructions(request),
            "input": request.message,
            "store": False,
            "tools": [],
            "parallel_tool_calls": False,
            "max_output_tokens": 900,
        }
        http_request = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self.opener(http_request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except Exception:
            return PersonaDraft("Живой голос Веры сейчас недоступен: запрос к модели не удался.", degraded=True, unavailable=True)
        return _parse_provider_text(_extract_output_text(data))


def provider_from_env(env: dict[str, str] | None = None) -> PersonaProvider:
    values = env or os.environ
    if values.get("VERACE_PERSONA_PROVIDER", "").strip().lower() != "openai":
        return UnavailablePersonaProvider()
    api_key = values.get("OPENAI_API_KEY", "").strip()
    model = values.get("VERACE_PERSONA_MODEL", "").strip()
    if not api_key or not model:
        return UnavailablePersonaProvider()
    return OpenAIResponsesPersonaProvider(api_key, model)


UNSUPPORTED_COMPLETIONS = (
    "я записала",
    "я записал",
    "записала",
    "записал",
    "создала",
    "создал",
    "смержила",
    "смержил",
    "отправила",
    "отправил",
    "проверила",
    "проверил",
    "i recorded",
    "i created",
    "i merged",
    "i sent",
    "i verified",
)


def guard_persona_draft(text: str, receipt_backed: bool = False) -> str:
    if receipt_backed:
        return text
    lowered = text.lower()
    if not any(marker in lowered for marker in UNSUPPORTED_COMPLETIONS):
        return text
    return (
        "Я не буду утверждать, что действие уже выполнено без receipt. "
        "Могу только предложить, что записать или поставить на проверку."
    )


def _instructions(request: PersonaRequestContext) -> str:
    context = request.project_context
    hints = "\n".join(f"- {h.kind}: {h.title} — {h.reason}" for h in request.hints) or "- нет"
    return f"""Ты Вера, conversational founder assistant для Verace.
Пиши живым русским языком, кратко и по делу. Не звучать как форма или отчет.

Жесткая граница:
- Runtime владеет фактами, разрешениями, receipts и ledger.
- Ты можешь предлагать, объяснять и уточнять.
- Не говори "записала", "создала", "проверила", "смержила" без receipt в контексте.
- Не вызывай инструменты и не обещай внешнее действие.
- Ledger меняется только после явного подтверждения пользователя.

Верни только JSON:
{{"human_answer_ru":"...", "proposed_actions":[{{"intent":"todo|fixation|check", "title":"...", "body":"...", "reason":"..."}}]}}

Verified project context:
- project: {context.project_name}
- phase: {context.current_phase}
- product surface: {context.current_product_surface}
- current work: {context.current_work}
- next work: {context.next_work}
- open risks: {", ".join(r.title for r in context.open_risks[:3]) or "нет в docs"}

Verified runtime summary:
{request.ledger_summary}

Backstage candidate hints, not truth:
{hints}
"""


def _extract_output_text(data: dict[str, object]) -> str:
    direct = data.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    chunks: list[str] = []
    for item in data.get("output", []) if isinstance(data.get("output"), list) else []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) if isinstance(item.get("content"), list) else []:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    return "\n".join(chunks).strip()


def _parse_provider_text(text: str) -> PersonaDraft:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return PersonaDraft(text.strip() or "Не удалось разобрать ответ модели.", ())
    answer = str(payload.get("human_answer_ru") or payload.get("answer") or "").strip()
    actions = []
    for raw in payload.get("proposed_actions", []):
        if not isinstance(raw, dict):
            continue
        intent = str(raw.get("intent", "")).strip()
        if intent not in {"todo", "fixation", "check"}:
            continue
        actions.append(
            PersonaActionDraft(
                intent,
                str(raw.get("title", "")).strip()[:180],
                str(raw.get("body", "")).strip()[:1200],
                str(raw.get("reason", "")).strip()[:300],
            )
        )
    return PersonaDraft(answer or text.strip(), tuple(item for item in actions if item.title and item.body))
