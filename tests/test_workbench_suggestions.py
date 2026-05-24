from __future__ import annotations

from pathlib import Path

from verace_runtime.workbench.context import read_project_context
from verace_runtime.workbench.suggestions import build_suggestions, codex_task_prompt, find_suggestion


def test_suggestions_include_next_work_task_and_codex_prompt():
    context = read_project_context(Path.cwd())
    suggestions = build_suggestions(context)
    kinds = {item.kind for item in suggestions}

    assert "task" in kinds
    assert "codex_task" in kinds
    assert any(item.source_file == "docs/ops/PROJECT_STATE.md" for item in suggestions)


def test_suggestions_include_open_risk_reviews():
    context = read_project_context(Path.cwd())
    suggestions = build_suggestions(context)

    assert any(item.kind == "review" and item.source_file == "docs/ops/RISK_REGISTER.md" for item in suggestions)


def test_codex_task_generator_renders_structured_prompt():
    context = read_project_context(Path.cwd())
    suggestion = find_suggestion(context, "next-work-codex")
    prompt = codex_task_prompt(context, suggestion)

    for heading in ("Goal:", "Context:", "Non-goals:", "Files:", "Constraints:", "Implementation:", "Tests:", "Acceptance criteria:", "Rollback:", "Done definition:"):
        assert heading in prompt
    assert suggestion.title in prompt
