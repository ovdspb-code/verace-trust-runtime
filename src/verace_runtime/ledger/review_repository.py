"""Review queue repository helpers."""

from __future__ import annotations

import sqlite3

from verace_runtime.ids import new_id, review_public_no
from verace_runtime.ledger.models import ReviewSummary


class ReviewRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create_item(
        self,
        contour_id: str,
        mandate_id: str,
        task_id: str | None,
        title: str,
        body: str,
        review_type: str,
        priority: str,
        now: str,
    ) -> sqlite3.Row:
        review_id = new_id("review")
        seq = self.conn.execute("SELECT COUNT(*) AS n FROM review_items").fetchone()["n"] + 1
        self.conn.execute(
            """
            INSERT INTO review_items
            (id, public_id, contour_id, mandate_id, task_id, title, body, review_type,
             priority, status, resolution_text, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', NULL, ?, ?)
            """,
            (review_id, review_public_no(seq), contour_id, mandate_id, task_id, title, body, review_type, priority, now, now),
        )
        return self.detail(review_id)

    def create_event(self, review_id: str, event_type: str, summary: str, receipt_id: str, now: str) -> str:
        event_id = new_id("review_event")
        self.conn.execute(
            """
            INSERT INTO review_events (id, review_item_id, event_type, summary, receipt_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_id, review_id, event_type, summary, receipt_id, now),
        )
        return event_id

    def resolve(self, review_ref: str, status: str, resolution: str, now: str) -> sqlite3.Row:
        item = self.detail(review_ref)
        if item["status"] != "open":
            raise RuntimeError(f"Review item is already {item['status']}")
        self.conn.execute(
            "UPDATE review_items SET status = ?, resolution_text = ?, updated_at = ? WHERE id = ?",
            (status, resolution, now, item["id"]),
        )
        return self.detail(item["id"])

    def summaries(self, status: str | None = "open") -> list[ReviewSummary]:
        where = "" if status is None else "WHERE i.status = ?"
        params: tuple[str, ...] = () if status is None else (status,)
        rows = self.conn.execute(
            f"""
            SELECT i.public_id, i.title, i.status, i.priority, i.review_type,
                   c.slug AS contour, t.public_no AS task_public_no, i.created_at
            FROM review_items i
            JOIN contours c ON c.id = i.contour_id
            LEFT JOIN tasks t ON t.id = i.task_id
            {where}
            ORDER BY i.created_at, i.public_id
            """,
            params,
        ).fetchall()
        return [ReviewSummary(**dict(row)) for row in rows]

    def recent_events(self, limit: int = 5) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT i.public_id, e.event_type, e.summary, e.created_at
            FROM review_events e JOIN review_items i ON i.id = e.review_item_id
            ORDER BY e.created_at DESC, e.id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def detail(self, review_ref: str) -> sqlite3.Row:
        row = self.conn.execute(
            """
            SELECT i.*, c.slug AS contour, t.public_no AS task_public_no
            FROM review_items i
            JOIN contours c ON c.id = i.contour_id
            LEFT JOIN tasks t ON t.id = i.task_id
            WHERE i.public_id = ? OR i.id = ?
            """,
            (review_ref, review_ref),
        ).fetchone()
        if row is None:
            raise RuntimeError("Review item not found")
        return row
