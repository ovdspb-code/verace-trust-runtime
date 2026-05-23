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
