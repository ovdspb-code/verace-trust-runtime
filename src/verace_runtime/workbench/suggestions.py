"""Deterministic suggested work queue for the browser workbench."""

from __future__ import annotations

from dataclasses import dataclass

from verace_runtime.workbench.context import ProjectContext


@dataclass(frozen=True)
class Suggestion:
    id: str
    kind: str
    title: str
    body: str
    source_file: str
    reason: str


def build_suggestions(context: ProjectContext) -> list[Suggestion]:
    suggestions: list[Suggestion] = []
    if context.next_work:
        suggestions.append(
            Suggestion(
                "next-work-task",
                "task",
                context.next_work,
                f"Продолжить следующий заявленный шаг проекта: {context.next_work}.",
                "docs/ops/PROJECT_STATE.md",
                "Next Intended Work",
            )
        )
        suggestions.append(
            Suggestion(
                "next-work-codex",
                "codex_task",
                f"Codex task: {context.next_work}",
                f"Подготовить рабочую задачу Codex для: {context.next_work}.",
                "docs/ops/PROJECT_STATE.md",
                "Next Intended Work needs an executable session prompt",
            )
        )
    else:
        suggestions.append(Suggestion("clarify-next-work", "review", "Уточнить следующий шаг", "В PROJECT_STATE не найден Next Intended Work.", "docs/ops/PROJECT_STATE.md", "No next work found"))

    if context.current_product_surface:
        suggestions.append(
            Suggestion(
                "product-surface-decision",
                "decision",
                "Зафиксировать текущую продуктовую поверхность",
                f"Текущая продуктовая поверхность: {context.current_product_surface}.",
                "docs/ops/PROJECT_STATE.md",
                "Current product surface is present in project state",
            )
        )

    for index, risk in enumerate(context.open_risks[:3], start=1):
        suggestions.append(
            Suggestion(
                f"risk-{index}-review",
                "review",
                f"Проверить риск: {risk.title}",
                risk.mitigation,
                risk.source_file,
                "Open risk in risk register",
            )
        )

    if any("trial" in entry.lower() for entry in context.recent_worklog):
        suggestions.append(
            Suggestion(
                "trial-followup-review",
                "review",
                "Проверить результат human trial",
                "Сверить, стал ли Browser Workbench полезным для реальной Verace-сессии после UX cleanup.",
                "docs/ops/WORKLOG.md",
                "Recent worklog mentions a human trial",
            )
        )
    return _unique(suggestions)


def find_suggestion(context: ProjectContext, suggestion_id: str) -> Suggestion:
    for suggestion in build_suggestions(context):
        if suggestion.id == suggestion_id:
            return suggestion
    raise RuntimeError("Suggestion not found")


def codex_task_prompt(context: ProjectContext, suggestion: Suggestion) -> str:
    return f"""CODEX — {suggestion.title}

Goal:
{suggestion.body}

Context:
- Project: {context.project_name}
- Current phase: {context.current_phase}
- Product surface: {context.current_product_surface or 'unknown'}
- Recent work: {context.recent_work or 'not recorded'}
- Source: {suggestion.source_file}
- Reason: {suggestion.reason}

Non-goals:
- Do not add LLM/provider integration.
- Do not add Telegram/channel integration.
- Do not call external APIs.
- Do not commit runtime DB/log/secret/private files.
- Do not treat terminal as founder UX.

Files:
- Work only inside /Users/ovd/Documents/VERACE/TRUST_RUNTIME.

Constraints:
- Keep changes deterministic and local-only.
- Preserve receipt-backed system-action statements.
- Keep browser UI as the founder product surface.

Implementation:
1. Read the current project docs.
2. Implement the smallest change needed for the goal.
3. Keep read-only views read-only.
4. Add focused tests for changed behavior.

Tests:
- Run python -m pip install -e ".[dev]".
- Run python -m pytest.
- Run relevant browser smoke checks.

Acceptance criteria:
- The goal is satisfied from local project state.
- No forbidden integrations or private artifacts are added.
- Tests and safety scans pass.

Rollback:
- If tests fail, do not claim completion.
- If forbidden files appear, stop before commit.

Done definition:
- Report changed files, tests, smoke checks, git status, and remaining limitations.
"""


def _unique(suggestions: list[Suggestion]) -> list[Suggestion]:
    seen: set[str] = set()
    out: list[Suggestion] = []
    for item in suggestions:
        if item.id not in seen:
            out.append(item)
            seen.add(item.id)
    return out
