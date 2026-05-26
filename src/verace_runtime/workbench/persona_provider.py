"""Persona language boundary for the browser front door."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from verace_runtime.workbench.context import ProjectContext


@dataclass(frozen=True)
class PersonaActionHint:
    kind: str
    title: str
    body: str
    reason: str


@dataclass(frozen=True)
class PersonaDraft:
    text: str
    degraded: bool = False


class PersonaProvider(Protocol):
    def draft(self, message: str, context: ProjectContext, hints: list[PersonaActionHint]) -> PersonaDraft:
        """Draft persona language only; runtime still owns state and receipts."""


class DraftOnlyProvider:
    def draft(self, message: str, context: ProjectContext, hints: list[PersonaActionHint]) -> PersonaDraft:
        lines = ["Модель персонажа не подключена; могу показать только черновой разбор."]
        if context.next_work:
            lines.append(f"Контекст проекта: следующий шаг сейчас - {context.next_work}.")
        lines.append("Я поняла фрагмент и вижу, что можно вынести на подтверждение.")
        if hints:
            lines.append("Предлагаю выбрать, что действительно стоит записать.")
        else:
            lines.append("Пока не вижу надежного действия для записи.")
        return PersonaDraft("\n".join(lines), degraded=True)


class FakePersonaProvider:
    def __init__(self, text: str) -> None:
        self.text = text
        self.calls: list[tuple[str, ProjectContext, list[PersonaActionHint]]] = []

    def draft(self, message: str, context: ProjectContext, hints: list[PersonaActionHint]) -> PersonaDraft:
        self.calls.append((message, context, hints))
        return PersonaDraft(self.text)


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
