"""Deterministic prompts derived from capture suggestions."""

from __future__ import annotations

from verace_runtime.workbench.context import ProjectContext


def codex_prompt_from_capture(title: str, body: str, source_type: str, source_label: str | None, context: ProjectContext) -> str:
    label = source_label or "не указан"
    return f"""CODEX — {title}

Goal:
{body}

Context:
- Project: {context.project_name}
- Current phase: {context.current_phase}
- Product surface: {context.current_product_surface or 'unknown'}
- Capture source: {source_type}
- Source label: {label}

Non-goals:
- Do not add LLM/provider integration unless explicitly requested.
- Do not call external APIs.
- Do not commit runtime DB, logs, secrets, or private capture text.

Files:
- Work only inside /Users/ovd/Documents/VERACE/TRUST_RUNTIME.

Constraints:
- Keep changes deterministic and local-only.
- Preserve receipt-backed system-action statements.
- Keep browser UI as the founder product surface.

Implementation:
1. Read the relevant local project context.
2. Implement the smallest change needed for the goal.
3. Add focused tests for changed behavior.
4. Do not expand scope beyond the accepted prompt.

Tests:
- Run python -m pip install -e ".[dev]".
- Run python -m pytest.
- Run relevant browser or run-control smoke checks.

Acceptance criteria:
- The requested outcome is visible in the browser workbench or docs.
- No forbidden integrations or private artifacts are added.
- Tests and safety scans pass.

Rollback:
- If tests fail, do not claim completion.
- If forbidden files appear, stop before commit.

Done definition:
- Report changed files, tests, smoke checks, git status, and remaining limitations.
"""
