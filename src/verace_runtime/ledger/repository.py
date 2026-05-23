"""Raw-SQL repository for the runtime ledger."""

from __future__ import annotations

import sqlite3

from verace_runtime.ids import new_id, new_public_id, task_public_no
from verace_runtime.ledger.models import TaskSummary


class LedgerRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def seed_founder(self, now: str) -> dict[str, str]:
        person_id = self._ensure_person("oleg", "Oleg Dolgikh", now)
        contour_id = self._ensure_contour("verace_project", "Verace Project", now)
        self.conn.execute(
            """
            INSERT OR IGNORE INTO contour_memberships
            (person_id, contour_id, role, created_at) VALUES (?, ?, ?, ?)
            """,
            (person_id, contour_id, "principal", now),
        )
        mandate_id = self._ensure_mandate(person_id, contour_id, now)
        return {"person_id": person_id, "contour_id": contour_id, "mandate_id": mandate_id}

    def active_mandate(self, principal: str, contour: str) -> sqlite3.Row:
        row = self.conn.execute(
            """
            SELECT m.* FROM mandates m
            JOIN persons p ON p.id = m.principal_person_id
            JOIN contours c ON c.id = m.contour_id
            WHERE p.slug = ? AND c.slug = ? AND m.status = 'active'
            ORDER BY m.created_at LIMIT 1
            """,
            (principal, contour),
        ).fetchone()
        if row is None:
            raise RuntimeError(f"No active mandate for {principal}/{contour}")
        return row

    def find_person(self, slug: str) -> sqlite3.Row:
        return self._required("SELECT * FROM persons WHERE slug = ?", (slug,))

    def find_contour(self, slug: str) -> sqlite3.Row:
        return self._required("SELECT * FROM contours WHERE slug = ?", (slug,))

    def create_message(self, person_id: str, contour_id: str, text: str, now: str) -> sqlite3.Row:
        msg_id = new_id("message")
        public_id = new_public_id("MSG")
        self.conn.execute(
            """
            INSERT INTO messages
            (id, public_id, contour_id, principal_person_id, text, kind, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (msg_id, public_id, contour_id, person_id, text, "synthetic_inbound", now),
        )
        return self._required("SELECT * FROM messages WHERE id = ?", (msg_id,))

    def create_task(self, mandate_id: str, contour_id: str, message_id: str, title: str, now: str) -> sqlite3.Row:
        task_id = new_id("task")
        self.conn.execute(
            """
            INSERT INTO tasks
            (id, mandate_id, contour_id, message_id, title, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'open', ?, ?)
            """,
            (task_id, mandate_id, contour_id, message_id, title, now, now),
        )
        seq = self.conn.execute("SELECT seq FROM tasks WHERE id = ?", (task_id,)).fetchone()["seq"]
        self.conn.execute("UPDATE tasks SET public_no = ? WHERE id = ?", (task_public_no(seq), task_id))
        return self._required("SELECT * FROM tasks WHERE id = ?", (task_id,))

    def create_event(self, task_id: str, event_type: str, summary: str, now: str) -> str:
        event_id = new_id("event")
        self.conn.execute(
            """
            INSERT INTO task_events (id, task_id, event_type, summary, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_id, task_id, event_type, summary, now),
        )
        return event_id

    def attach_event_receipt(self, event_id: str, receipt_id: str) -> None:
        self.conn.execute("UPDATE task_events SET receipt_id = ? WHERE id = ?", (receipt_id, event_id))

    def insert_receipt(self, payload) -> sqlite3.Row:
        self.conn.execute(
            """
            INSERT INTO receipts
            (id, public_id, receipt_type, action_class, subject_type, subject_id,
             status, policy_result, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.id,
                payload.public_id,
                payload.receipt_type,
                payload.action_class,
                payload.subject_type,
                payload.subject_id,
                payload.status,
                payload.policy_result,
                payload.note,
                payload.created_at,
            ),
        )
        return self._required("SELECT * FROM receipts WHERE id = ?", (payload.id,))

    def insert_claim(self, claim_type: str, text: str, subject_type: str, subject_id: str, receipt_id: str, now: str) -> None:
        self.conn.execute(
            """
            INSERT INTO claims
            (id, claim_type, claim_text, subject_type, subject_id, receipt_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'verified_by_receipt', ?)
            """,
            (new_id("claim"), claim_type, text, subject_type, subject_id, receipt_id, now),
        )

    def insert_outbox_block(self, action_class: str, payload: str, receipt_id: str, now: str) -> None:
        self.conn.execute(
            """
            INSERT INTO outbox_items (id, action_class, payload, status, receipt_id, created_at)
            VALUES (?, ?, ?, 'blocked', ?, ?)
            """,
            (new_id("outbox"), action_class, payload, receipt_id, now),
        )

    def task_summaries(self) -> list[TaskSummary]:
        rows = self.conn.execute(
            """
            SELECT t.public_no, t.title, t.status, c.slug AS contour,
                   COUNT(r.id) AS receipt_count
            FROM tasks t
            JOIN contours c ON c.id = t.contour_id
            LEFT JOIN receipts r ON r.subject_type = 'task' AND r.subject_id = t.id
            GROUP BY t.id
            ORDER BY t.seq
            """
        ).fetchall()
        return [TaskSummary(**dict(row)) for row in rows]

    def task_detail(self, task_ref: str) -> sqlite3.Row:
        return self._required(
            """
            SELECT t.*, c.slug AS contour, m.public_id AS mandate_public_id
            FROM tasks t
            JOIN contours c ON c.id = t.contour_id
            JOIN mandates m ON m.id = t.mandate_id
            WHERE t.public_no = ? OR t.id = ?
            """,
            (task_ref, task_ref),
        )

    def task_receipts(self, task_id: str) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM receipts WHERE subject_type = 'task' AND subject_id = ? ORDER BY created_at",
            (task_id,),
        ).fetchall()

    def counts(self) -> dict[str, int]:
        names = ["persons", "contours", "mandates", "messages", "tasks", "task_events", "receipts", "claims"]
        return {name: self.conn.execute(f"SELECT COUNT(*) AS n FROM {name}").fetchone()["n"] for name in names}

    def _ensure_person(self, slug: str, name: str, now: str) -> str:
        return self._ensure_slug("persons", slug, {"display_name": name}, now)

    def _ensure_contour(self, slug: str, name: str, now: str) -> str:
        return self._ensure_slug("contours", slug, {"name": name}, now)

    def _ensure_mandate(self, person_id: str, contour_id: str, now: str) -> str:
        row = self.conn.execute("SELECT id FROM mandates WHERE contour_id = ? AND status = 'active'", (contour_id,)).fetchone()
        if row:
            return row["id"]
        mandate_id = new_id("mandate")
        self.conn.execute(
            """
            INSERT INTO mandates
            (id, public_id, principal_person_id, contour_id, title, scope, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
            """,
            (mandate_id, "MANDATE-FOUNDING-001", person_id, contour_id, "Manage Verace project work", "internal_project_work", now),
        )
        return mandate_id

    def _ensure_slug(self, table: str, slug: str, fields: dict[str, str], now: str) -> str:
        row = self.conn.execute(f"SELECT id FROM {table} WHERE slug = ?", (slug,)).fetchone()
        if row:
            return row["id"]
        item_id = new_id(table[:-1])
        columns = ["id", "slug", *fields.keys(), "created_at"]
        values = [item_id, slug, *fields.values(), now]
        marks = ", ".join("?" for _ in values)
        self.conn.execute(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({marks})", values)
        return item_id

    def _required(self, sql: str, params: tuple[str, ...]) -> sqlite3.Row:
        row = self.conn.execute(sql, params).fetchone()
        if row is None:
            raise RuntimeError("Required ledger row not found")
        return row
