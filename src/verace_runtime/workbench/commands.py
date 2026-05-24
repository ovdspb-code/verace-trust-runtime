"""Command handlers for the local founder workbench."""

from __future__ import annotations

import argparse
import os

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.workbench.formatting import format_brief, format_doctor, format_reviews, rendered_or_error


DEFAULT_DB = ".runtime/verace.sqlite3"
DEFAULT_PRINCIPAL = "oleg"
DEFAULT_CONTOUR = "verace_project"


def db_path(args: argparse.Namespace) -> str:
    return getattr(args, "db", None) or os.environ.get("VERACE_RUNTIME_DB") or DEFAULT_DB


def service_for(args: argparse.Namespace) -> FounderAssistantService:
    return FounderAssistantService(db_path(args))


def init(args: argparse.Namespace) -> str:
    result = service_for(args).init_runtime()
    return "\n".join(
        [
            f"Runtime DB: {db_path(args)}",
            f"Principal: {result.principal}",
            f"Contour: {result.contour}",
            f"Mandate: {result.mandate_public_id}",
            f"Runtime receipt: {result.receipt_public_id}",
        ]
    )


def brief(args: argparse.Namespace) -> str:
    return format_brief(service_for(args).session_brief())


def add(args: argparse.Namespace) -> str:
    service = service_for(args)
    result = service.ingest_message(args.principal, args.contour, args.text)
    if not result.task_public_no:
        raise RuntimeError("No task was created")
    return rendered_or_error(service.render_claim("task_recorded", result.task_public_no))


def decision(args: argparse.Namespace) -> str:
    service = service_for(args)
    result = service.record_decision(args.principal, args.contour, args.title, args.text)
    return rendered_or_error(service.render_claim("decision_recorded", result.public_id))


def review_add(args: argparse.Namespace) -> str:
    service = service_for(args)
    result = service.add_review(args.principal, args.contour, args.title, args.body, args.review_type, args.priority, args.task)
    return rendered_or_error(service.render_claim("review_created", result.public_id))


def review_list(args: argparse.Namespace) -> str:
    status = None if args.status == "all" else args.status
    return format_reviews(service_for(args).list_reviews(status))


def review_resolve(args: argparse.Namespace) -> str:
    service = service_for(args)
    result = service.resolve_review(args.review, args.resolution, args.status)
    claim_class = "review_dismissed" if result.status == "dismissed" else "review_resolved"
    return rendered_or_error(service.render_claim(claim_class, result.public_id))


def doctor(args: argparse.Namespace) -> str:
    return format_doctor(service_for(args).doctor())
