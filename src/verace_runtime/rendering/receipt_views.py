"""Read-only receipt/claim views for response rendering."""

from __future__ import annotations

import sqlite3

from verace_runtime.rendering.models import EvidenceView


class RuntimeReceiptViews:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def task_recorded(self, task_ref: str) -> EvidenceView | None:
        row = self.conn.execute(
            """
            SELECT t.public_no AS subject, r.public_id AS receipt_public_id,
                   r.status AS receipt_status, r.policy_result, c.claim_type,
                   c.status AS claim_status
            FROM tasks t
            JOIN receipts r ON r.subject_type = 'task' AND r.subject_id = t.id
            JOIN claims c ON c.receipt_id = r.id AND c.subject_type = 'task'
                 AND c.subject_id = t.id AND c.claim_type = 'task_recorded'
            WHERE t.public_no = ? OR t.id = ?
            ORDER BY r.created_at, r.public_id LIMIT 1
            """,
            (task_ref, task_ref),
        ).fetchone()
        return self._view("task_recorded", "task", row)

    def decision_recorded(self, decision_ref: str) -> EvidenceView | None:
        row = self.conn.execute(
            """
            SELECT d.public_id AS subject, r.public_id AS receipt_public_id,
                   r.status AS receipt_status, r.policy_result, c.claim_type,
                   c.status AS claim_status
            FROM decisions d
            JOIN receipts r ON r.subject_type = 'decision' AND r.subject_id = d.id
            JOIN claims c ON c.receipt_id = r.id AND c.subject_type = 'decision'
                 AND c.subject_id = d.id AND c.claim_type = 'decision_recorded'
            WHERE d.public_id = ? OR d.id = ?
            ORDER BY r.created_at, r.public_id LIMIT 1
            """,
            (decision_ref, decision_ref),
        ).fetchone()
        return self._view("decision_recorded", "decision", row)

    def review_lifecycle(self, review_ref: str, claim_class: str, event_type: str, claim_type: str) -> EvidenceView | None:
        row = self.conn.execute(
            """
            SELECT i.public_id AS subject, r.public_id AS receipt_public_id,
                   r.status AS receipt_status, r.policy_result, c.claim_type,
                   c.status AS claim_status, e.event_type
            FROM review_items i
            JOIN review_events e ON e.review_item_id = i.id AND e.event_type = ?
            JOIN receipts r ON r.id = e.receipt_id
            JOIN claims c ON c.receipt_id = r.id AND c.subject_type = 'review_item'
                 AND c.subject_id = i.id AND c.claim_type = ?
            WHERE i.public_id = ? OR i.id = ?
            ORDER BY e.created_at, e.id LIMIT 1
            """,
            (event_type, claim_type, review_ref, review_ref),
        ).fetchone()
        return self._view(claim_class, "review_item", row)

    def action_blocked(self, action_class: str) -> EvidenceView | None:
        row = self.conn.execute(
            """
            SELECT r.subject_id AS subject, r.public_id AS receipt_public_id,
                   r.status AS receipt_status, r.policy_result, c.claim_type,
                   c.status AS claim_status
            FROM receipts r
            JOIN claims c ON c.receipt_id = r.id AND c.claim_type = 'action_blocked'
            WHERE r.subject_type = 'policy' AND r.subject_id = ?
            ORDER BY r.created_at DESC, r.public_id DESC LIMIT 1
            """,
            (action_class,),
        ).fetchone()
        return self._view("action_blocked", "policy", row)

    def _view(self, claim_class: str, subject_type: str, row: sqlite3.Row | None) -> EvidenceView | None:
        if row is None:
            return None
        return EvidenceView(
            claim_class=claim_class,
            subject=row["subject"],
            subject_type=subject_type,
            receipt_public_id=row["receipt_public_id"],
            receipt_status=row["receipt_status"],
            policy_result=row["policy_result"],
            claim_type=row["claim_type"],
            claim_status=row["claim_status"],
            event_type=row["event_type"] if "event_type" in row.keys() else None,
        )

