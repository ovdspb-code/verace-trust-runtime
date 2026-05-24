"""Read models for receipt-rendered prose."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceView:
    claim_class: str
    subject: str
    subject_type: str
    receipt_public_id: str
    receipt_status: str
    policy_result: str
    claim_type: str
    claim_status: str
    event_type: str | None = None


@dataclass(frozen=True)
class SyntheticReceiptView:
    claim_class: str
    subject: str
    receipt_public_id: str
    receipt_status: str = "ok"
    claim_type: str = ""
    artifact_format: str | None = None
    delivery_state: str | None = None
    check_state: str | None = None


@dataclass(frozen=True)
class RenderResult:
    ok: bool
    text: str
    claim_class: str
    receipt_public_id: str | None = None
    reason: str | None = None

