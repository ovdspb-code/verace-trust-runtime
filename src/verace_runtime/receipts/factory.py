"""Receipt payload factory."""

from __future__ import annotations

from dataclasses import dataclass

from verace_runtime.ids import new_id, new_public_id
from verace_runtime.policy.engine import Decision
from verace_runtime.time import utc_now_iso


@dataclass(frozen=True)
class ReceiptPayload:
    id: str
    public_id: str
    receipt_type: str
    action_class: str
    subject_type: str
    subject_id: str
    status: str
    policy_result: str
    note: str
    created_at: str


class ReceiptFactory:
    def build(
        self,
        decision: Decision,
        receipt_type: str,
        subject_type: str,
        subject_id: str,
        note: str,
    ) -> ReceiptPayload:
        return ReceiptPayload(
            id=new_id("receipt"),
            public_id=new_public_id("RCPT"),
            receipt_type=receipt_type,
            action_class=decision.action_class,
            subject_type=subject_type,
            subject_id=subject_id,
            status="ok" if decision.allowed else "blocked",
            policy_result=decision.result,
            note=note,
            created_at=utc_now_iso(),
        )
