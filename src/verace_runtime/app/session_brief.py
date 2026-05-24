"""Read-only project and session brief builders."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from verace_runtime.ledger.db import apply_schema, connect
from verace_runtime.ledger.repository import LedgerRepository
from verace_runtime.ledger.review_repository import ReviewRepository
from verace_runtime.policy.engine import PolicyEngine


def build_project_brief(db_path: str | Path, policy: PolicyEngine, doctor: Callable[[], dict[str, object]]) -> dict[str, object]:
    decision = policy.evaluate("internal.project_brief.read")
    if not decision.allowed:
        raise RuntimeError(decision.reason)
    with connect(db_path) as conn:
        apply_schema(conn)
        repo = LedgerRepository(conn)
        return {
            "doctor": doctor(),
            "counts": repo.counts(),
            "tasks": [dict(row) for row in repo.brief_tasks()],
            "decisions": [item.__dict__ for item in repo.decision_summaries(limit=5)],
            "events": [dict(row) for row in repo.recent_task_events(limit=5)],
        }


def build_session_brief(db_path: str | Path, policy: PolicyEngine, doctor: Callable[[], dict[str, object]]) -> dict[str, object]:
    decision = policy.evaluate("internal.session_brief.read")
    if not decision.allowed:
        raise RuntimeError(decision.reason)
    with connect(db_path) as conn:
        apply_schema(conn)
        repo = LedgerRepository(conn)
        reviews = ReviewRepository(conn)
        doctor_result = doctor()
        return {
            "doctor": doctor_result,
            "schema": {
                "schema_name": doctor_result["schema_name"],
                "schema_version": doctor_result["schema_version"],
                "schema_current": doctor_result["schema_current"],
                "schema_reason": doctor_result["schema_reason"],
            },
            "counts": repo.counts(),
            "tasks": [dict(row) for row in repo.brief_tasks()],
            "reviews": [item.__dict__ for item in reviews.summaries("open")],
            "decisions": [item.__dict__ for item in repo.decision_summaries(limit=5)],
            "task_events": [dict(row) for row in repo.recent_task_events(limit=5)],
            "review_events": [dict(row) for row in reviews.recent_events(limit=5)],
        }
