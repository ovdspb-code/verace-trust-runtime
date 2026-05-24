"""Review queue application operations."""

from __future__ import annotations

from pathlib import Path

from verace_runtime.ledger.db import apply_schema, connect
from verace_runtime.ledger.models import ReviewResult, ReviewSummary
from verace_runtime.ledger.repository import LedgerRepository
from verace_runtime.ledger.review_repository import ReviewRepository
from verace_runtime.policy.engine import PolicyEngine
from verace_runtime.receipts.factory import ReceiptFactory
from verace_runtime.time import utc_now_iso


REVIEW_TYPES = frozenset({"architecture", "decision", "risk", "clarification", "evidence", "approval_request"})
PRIORITIES = frozenset({"low", "normal", "high", "critical"})
REVIEW_STATUSES = frozenset({"open", "resolved", "dismissed"})
RESOLUTION_STATUSES = frozenset({"resolved", "dismissed"})


def add_review_item(
    db_path: str | Path,
    policy: PolicyEngine,
    receipts: ReceiptFactory,
    principal: str,
    contour: str,
    title: str,
    body: str,
    review_type: str,
    priority: str,
    task_ref: str | None = None,
) -> ReviewResult:
    clean_title = title.strip()
    clean_body = body.strip()
    clean_type = review_type.strip()
    clean_priority = priority.strip()
    if not clean_title or not clean_body:
        raise RuntimeError("Review title and body are required")
    if clean_type not in REVIEW_TYPES:
        raise RuntimeError(f"Invalid review type: {review_type}")
    if clean_priority not in PRIORITIES:
        raise RuntimeError(f"Invalid review priority: {priority}")
    with connect(db_path) as conn:
        apply_schema(conn)
        repo = LedgerRepository(conn)
        review_repo = ReviewRepository(conn)
        now = utc_now_iso()
        contour_row = repo.find_contour(contour)
        mandate = repo.active_mandate(principal, contour)
        task_id = _task_id(repo, task_ref, contour) if task_ref else None
        decision = policy.evaluate("internal.review.create")
        if not decision.allowed:
            receipt = _blocked_receipt(repo, receipts, decision, now)
            return ReviewResult("blocked", receipt["public_id"], "blocked", "blocked")
        item = review_repo.create_item(contour_row["id"], mandate["id"], task_id, clean_title, clean_body, clean_type, clean_priority, now)
        receipt = repo.insert_receipt(receipts.build(decision, "ledger.event", "review_item", item["id"], f"Review {item['public_id']} created"))
        review_repo.create_event(item["id"], "review.item.created", f"Review {item['public_id']} created", receipt["id"], now)
        repo.insert_claim("review_item_created", f"Review item {item['public_id']} was recorded", "review_item", item["id"], receipt["id"], now)
        return ReviewResult(item["public_id"], receipt["public_id"], "verified_by_receipt", item["status"])


def list_review_items(db_path: str | Path, policy: PolicyEngine, status: str | None = "open") -> list[ReviewSummary]:
    if status not in REVIEW_STATUSES and status is not None:
        raise RuntimeError(f"Invalid review status: {status}")
    decision = policy.evaluate("internal.review.read")
    if not decision.allowed:
        raise RuntimeError(decision.reason)
    with connect(db_path) as conn:
        apply_schema(conn)
        return ReviewRepository(conn).summaries(status)


def resolve_review_item(
    db_path: str | Path,
    policy: PolicyEngine,
    receipts: ReceiptFactory,
    review_ref: str,
    resolution: str,
    status: str = "resolved",
) -> ReviewResult:
    clean_resolution = resolution.strip()
    clean_status = status.strip()
    if clean_status not in RESOLUTION_STATUSES:
        raise RuntimeError(f"Invalid review resolution status: {status}")
    if not clean_resolution:
        raise RuntimeError("Review resolution text is required")
    with connect(db_path) as conn:
        apply_schema(conn)
        repo = LedgerRepository(conn)
        review_repo = ReviewRepository(conn)
        now = utc_now_iso()
        item = review_repo.detail(review_ref)
        decision = policy.evaluate("internal.review.resolve")
        if not decision.allowed:
            receipt = _blocked_receipt(repo, receipts, decision, now, "review_item", item["id"])
            return ReviewResult(item["public_id"], receipt["public_id"], "blocked", item["status"])
        updated = review_repo.resolve(item["id"], clean_status, clean_resolution, now)
        event_type = f"review.item.{clean_status}"
        receipt = repo.insert_receipt(receipts.build(decision, "ledger.event", "review_item", item["id"], f"Review {item['public_id']} {clean_status}"))
        review_repo.create_event(item["id"], event_type, clean_resolution, receipt["id"], now)
        repo.insert_claim(event_type.replace(".", "_"), f"Review item {item['public_id']} was {clean_status}", "review_item", item["id"], receipt["id"], now)
        return ReviewResult(updated["public_id"], receipt["public_id"], "verified_by_receipt", updated["status"])


def _task_id(repo: LedgerRepository, task_ref: str, contour: str) -> str:
    task = repo.task_detail(task_ref)
    if task["contour"] != contour:
        raise RuntimeError("Review task belongs to another contour")
    return task["id"]


def _blocked_receipt(repo: LedgerRepository, receipts: ReceiptFactory, decision, now: str, subject_type: str = "policy", subject_id: str | None = None):
    subject = subject_id or decision.action_class
    receipt = repo.insert_receipt(receipts.build(decision, "policy.blocked", subject_type, subject, decision.reason))
    repo.insert_claim("action_blocked", f"Action {decision.action_class} was blocked by policy", subject_type, subject, receipt["id"], now)
    return receipt
