"""Small read models returned by the service layer."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InitResult:
    principal: str
    contour: str
    mandate_public_id: str
    receipt_public_id: str


@dataclass(frozen=True)
class IngestResult:
    message_public_id: str
    task_public_no: str | None
    receipt_public_id: str
    claim_status: str


@dataclass(frozen=True)
class TaskSummary:
    public_no: str
    title: str
    status: str
    contour: str
    receipt_count: int


@dataclass(frozen=True)
class PolicyResult:
    action_class: str
    allowed: bool
    receipt_public_id: str | None
    reason: str


@dataclass(frozen=True)
class DecisionResult:
    public_id: str
    receipt_public_id: str
    claim_status: str


@dataclass(frozen=True)
class DecisionSummary:
    public_id: str
    title: str
    status: str
    contour: str
    created_at: str


@dataclass(frozen=True)
class TaskMutationResult:
    task_public_no: str
    status: str
    receipt_public_id: str
    claim_status: str


@dataclass(frozen=True)
class ReviewResult:
    public_id: str
    receipt_public_id: str
    claim_status: str
    status: str


@dataclass(frozen=True)
class ReviewSummary:
    public_id: str
    title: str
    status: str
    priority: str
    review_type: str
    contour: str
    task_public_no: str | None
    created_at: str
