from __future__ import annotations

from verace_runtime.workbench.context import read_project_context
from verace_runtime.workbench.persona_frontdoor import build_actions
from verace_runtime.workbench.persona_provider import (
    DraftOnlyProvider,
    FakePersonaProvider,
    OpenAIResponsesPersonaProvider,
    PersonaActionDraft,
    PersonaActionHint,
    PersonaRequestContext,
    guard_persona_draft,
    provider_from_env,
)


def test_default_provider_degrades_without_real_model() -> None:
    context = read_project_context()
    actions = build_actions("Надо сделать живую Веру как вход.")

    request = PersonaRequestContext("Надо сделать живую Веру как вход.", context, "ledger unavailable", ())
    draft = DraftOnlyProvider().draft(request)

    assert draft.degraded is True
    assert draft.unavailable is True
    assert "Живой голос Веры пока не подключен" in draft.text
    assert actions


def test_fake_provider_receives_project_context_and_hints() -> None:
    context = read_project_context()
    actions = build_actions("Решили сделать persona-first вход. Надо записать задачу.")
    provider = FakePersonaProvider(
        "Я поняла. Предлагаю подтвердить важное.",
        (PersonaActionDraft("todo", "Сделать вход", "Сделать persona-first вход.", "Из текста"),),
    )
    hints = [PersonaActionHint(item.intent, item.title, item.body, item.reason) for item in actions]

    draft = provider.draft(PersonaRequestContext("message", context, "Open tasks: none", tuple(hints)))

    assert "Предлагаю" in draft.text
    assert draft.proposed_actions
    assert provider.calls[0].project_context.project_name.startswith("Verace")
    assert provider.calls[0].hints
    assert ".sqlite" not in repr(provider.calls[0].project_context)


def test_provider_from_env_is_unavailable_without_openai_config() -> None:
    provider = provider_from_env({})

    assert isinstance(provider, DraftOnlyProvider)


def test_provider_from_env_builds_openai_provider_only_when_configured() -> None:
    provider = provider_from_env(
        {
            "VERACE_PERSONA_PROVIDER": "openai",
            "OPENAI_API_KEY": "secret",
            "VERACE_PERSONA_MODEL": "configured-model",
        }
    )

    assert isinstance(provider, OpenAIResponsesPersonaProvider)


def test_openai_provider_payload_is_privacy_and_tool_safe() -> None:
    context = read_project_context()
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return b'{"output_text":"{\\"human_answer_ru\\":\\"OK\\",\\"proposed_actions\\":[]}"}'

    def opener(request, timeout):
        captured["timeout"] = timeout
        captured["body"] = request.data.decode("utf-8")
        captured["auth"] = request.headers["Authorization"]
        return FakeResponse()

    provider = OpenAIResponsesPersonaProvider("secret", "configured-model", opener=opener, timeout=7)
    request = PersonaRequestContext("Привет", context, "Open tasks: none", ())
    draft = provider.draft(request)

    assert draft.text == "OK"
    assert '"store": false' in captured["body"]
    assert '"tools": []' in captured["body"]
    assert '"parallel_tool_calls": false' in captured["body"]
    assert "configured-model" in captured["body"]
    assert captured["auth"] == "Bearer secret"
    assert captured["timeout"] == 7


def test_openai_provider_failure_degrades_without_secret_leak() -> None:
    context = read_project_context()

    def opener(_request, _timeout):
        raise OSError("network down")

    provider = OpenAIResponsesPersonaProvider("secret", "configured-model", opener=opener)
    draft = provider.draft(PersonaRequestContext("Привет", context, "Open tasks: none", ()))

    assert draft.unavailable is True
    assert draft.degraded is True
    assert "secret" not in draft.text


def test_unsupported_completed_action_claim_is_downgraded() -> None:
    guarded = guard_persona_draft("Я записала задачу и проверила статус.")

    assert "записала" not in guarded
    assert "проверила" not in guarded
    assert "без receipt" in guarded
