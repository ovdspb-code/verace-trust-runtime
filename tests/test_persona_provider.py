from __future__ import annotations

from verace_runtime.workbench.context import read_project_context
from verace_runtime.workbench.persona_frontdoor import build_actions
from verace_runtime.workbench.persona_provider import (
    DraftOnlyProvider,
    FakePersonaProvider,
    PersonaActionHint,
    guard_persona_draft,
)


def test_default_provider_degrades_without_real_model() -> None:
    context = read_project_context()
    actions = build_actions("Надо сделать живую Веру как вход.")

    draft = DraftOnlyProvider().draft("Надо сделать живую Веру как вход.", context, [])

    assert draft.degraded is True
    assert "Модель персонажа не подключена" in draft.text
    assert actions


def test_fake_provider_receives_project_context_and_hints() -> None:
    context = read_project_context()
    actions = build_actions("Решили сделать persona-first вход. Надо записать задачу.")
    provider = FakePersonaProvider("Я поняла. Предлагаю подтвердить важное.")
    hints = [PersonaActionHint(item.intent, item.title, item.body, item.reason) for item in actions]

    draft = provider.draft("message", context, hints)

    assert "Предлагаю" in draft.text
    assert provider.calls[0][1].project_name.startswith("Verace")
    assert provider.calls[0][2]
    assert ".sqlite" not in repr(provider.calls[0][1])


def test_unsupported_completed_action_claim_is_downgraded() -> None:
    guarded = guard_persona_draft("Я записала задачу и проверила статус.")

    assert "записала" not in guarded
    assert "проверила" not in guarded
    assert "без receipt" in guarded
