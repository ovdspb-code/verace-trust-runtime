"""Browser workbench actions over the runtime service."""

from __future__ import annotations

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.rendering.models import RenderResult


PRINCIPAL = "oleg"
CONTOUR = "verace_project"


def init_runtime(service: FounderAssistantService) -> str:
    result = service.init_runtime()
    return f"Runtime initialized. Receipt: {result.receipt_public_id}."


def create_task(service: FounderAssistantService, text: str) -> str:
    result = service.ingest_message(PRINCIPAL, CONTOUR, text)
    if not result.task_public_no:
        raise RuntimeError("No task was created")
    return _rendered(service.render_claim("task_recorded", result.task_public_no))


def record_decision(service: FounderAssistantService, title: str, text: str) -> str:
    result = service.record_decision(PRINCIPAL, CONTOUR, title, text)
    return _rendered(service.render_claim("decision_recorded", result.public_id))


def create_review(service: FounderAssistantService, title: str, body: str, review_type: str, priority: str, task: str | None) -> str:
    result = service.add_review(PRINCIPAL, CONTOUR, title, body, review_type, priority, task or None)
    return _rendered(service.render_claim("review_created", result.public_id))


def resolve_review(service: FounderAssistantService, review: str, resolution: str, status: str) -> str:
    result = service.resolve_review(review, resolution, status)
    claim_class = "review_dismissed" if result.status == "dismissed" else "review_resolved"
    return _rendered(service.render_claim(claim_class, result.public_id))


def _rendered(result: RenderResult) -> str:
    if not result.ok:
        raise RuntimeError(f"Cannot render {result.claim_class}: {result.reason}")
    return result.text

