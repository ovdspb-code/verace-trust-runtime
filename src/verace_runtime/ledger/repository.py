"""Raw-SQL repository for the runtime ledger."""

from __future__ import annotations

import sqlite3

from verace_runtime.ids import decision_public_no, new_id, new_public_id, task_public_no
from verace_runtime.ledger.models import DecisionSummary, TaskSummary


COUNT_TABLES = [
    "runtime_meta",
    "persons",
    "contours",
    "contour_memberships",
    "mandates",
    "messages",
    "decisions",
    "review_items",
    "tasks",
    "task_events",
    "review_events",
    "approvals",
    "receipts",
    "claims",
    "outbox_items",
    "capture_items",
    "capture_suggestions",
]


class LedgerRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def seed_founder(self, now: str) -> dict[str, str]:
        person_id = self.ensure_person("oleg", "Oleg Dolgikh", now)
        contour_id = self.ensure_contour("verace_project", "Verace Project", now)
        self.conn.execute(
            """
            INSERT OR IGNORE INTO contour_memberships
            (person_id, contour_id, role, created_at) VALUES (?, ?, 'principal', ?)
            """,
            (person_id, contour_id, now),
        )
        mandate_id = self.ensure_mandate(person_id, contour_id, now, "MANDATE-FOUNDING-001")
        return {"person_id": person_id, "contour_id": contour_id, "mandate_id": mandate_id}

    def find_person(self, slug: str) -> sqlite3.Row:
        return self._required("SELECT * FROM persons WHERE slug = ?", (slug,))

    def find_contour(self, slug: str) -> sqlite3.Row:
        return self._required("SELECT * FROM contours WHERE slug = ?", (slug,))

    def active_mandate(self, principal: str, contour: str) -> sqlite3.Row:
        return self._required(
            """
            SELECT m.* FROM mandates m
            JOIN persons p ON p.id = m.principal_person_id
            JOIN contours c ON c.id = m.contour_id
            WHERE p.slug = ? AND c.slug = ? AND m.status = 'active'
            ORDER BY m.created_at, m.public_id LIMIT 1
            """,
            (principal, contour),
        )

    def create_message(self, person_id: str, contour_id: str, text: str, now: str) -> sqlite3.Row:
        msg_id = new_id("message")
        self.conn.execute(
            """
            INSERT INTO messages
            (id, public_id, contour_id, principal_person_id, text, kind, created_at)
            VALUES (?, ?, ?, ?, ?, 'synthetic_inbound', ?)
            """,
            (msg_id, new_public_id("MSG"), contour_id, person_id, text, now),
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

    def create_decision(self, contour_id: str, mandate_id: str, message_id: str | None, title: str, text: str, now: str) -> sqlite3.Row:
        decision_id = new_id("decision")
        seq = self.conn.execute("SELECT COUNT(*) AS n FROM decisions").fetchone()["n"] + 1
        self.conn.execute(
            """
            INSERT INTO decisions
            (id, public_id, contour_id, mandate_id, message_id, title, decision_text, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
            """,
            (decision_id, decision_public_no(seq), contour_id, mandate_id, message_id, title, text, now),
        )
        return self._required("SELECT * FROM decisions WHERE id = ?", (decision_id,))

    def create_event(self, task_id: str, event_type: str, summary: str, receipt_id: str, now: str) -> str:
        event_id = new_id("event")
        self.conn.execute(
            """
            INSERT INTO task_events (id, task_id, event_type, summary, receipt_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_id, task_id, event_type, summary, receipt_id, now),
        )
        return event_id

    def update_task_status(self, task_id: str, status: str, now: str) -> None:
        self.conn.execute("UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?", (status, now, task_id))

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
            "INSERT INTO outbox_items (id, action_class, payload, status, receipt_id, created_at) VALUES (?, ?, ?, 'blocked', ?, ?)",
            (new_id("outbox"), action_class, payload, receipt_id, now),
        )

    def task_summaries(self) -> list[TaskSummary]:
        rows = self.conn.execute(
            """
            SELECT t.public_no, t.title, t.status, c.slug AS contour, COUNT(r.id) AS receipt_count
            FROM tasks t
            JOIN contours c ON c.id = t.contour_id
            LEFT JOIN receipts r ON r.subject_type = 'task' AND r.subject_id = t.id
            GROUP BY t.id ORDER BY t.seq
            """
        ).fetchall()
        return [TaskSummary(**dict(row)) for row in rows]

    def decision_summaries(self, limit: int | None = None) -> list[DecisionSummary]:
        sql = """
            SELECT d.public_id, d.title, d.status, c.slug AS contour, d.created_at
            FROM decisions d JOIN contours c ON c.id = d.contour_id
            ORDER BY d.rowid DESC
        """
        rows = self.conn.execute(sql + (" LIMIT ?" if limit else ""), (() if limit is None else (limit,))).fetchall()
        return [DecisionSummary(**dict(row)) for row in rows]

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
            "SELECT * FROM receipts WHERE subject_type = 'task' AND subject_id = ? ORDER BY created_at, public_id",
            (task_id,),
        ).fetchall()

    def brief_tasks(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT public_no, status, title FROM tasks
            WHERE status IN ('open', 'waiting', 'blocked')
            ORDER BY seq
            """
        ).fetchall()

    def recent_task_events(self, limit: int = 5) -> list[sqlite3.Row]:
        return self.conn.execute(
            """
            SELECT t.public_no, e.event_type, e.summary, e.created_at
            FROM task_events e JOIN tasks t ON t.id = e.task_id
            ORDER BY e.rowid DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()

    def counts(self) -> dict[str, int]:
        return {name: self.conn.execute(f"SELECT COUNT(*) AS n FROM {name}").fetchone()["n"] for name in COUNT_TABLES}

    def table_names(self) -> set[str]:
        return {row["name"] for row in self.conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}

    def seed_ok(self) -> bool:
        row = self.conn.execute(
            """
            SELECT COUNT(*) AS n FROM mandates m
            JOIN persons p ON p.id = m.principal_person_id
            JOIN contours c ON c.id = m.contour_id
            WHERE p.slug = 'oleg' AND c.slug = 'verace_project' AND m.status = 'active'
            """
        ).fetchone()
        return row["n"] == 1

    def invariant_counts(self) -> dict[str, int]:
        queries = {
            "claims_missing_receipt": "SELECT COUNT(*) AS n FROM claims c LEFT JOIN receipts r ON r.id = c.receipt_id WHERE c.receipt_id IS NULL OR r.id IS NULL",
            "task_events_missing_receipt": "SELECT COUNT(*) AS n FROM task_events e LEFT JOIN receipts r ON r.id = e.receipt_id WHERE e.receipt_id IS NULL OR r.id IS NULL",
            "outbox_missing_receipt": "SELECT COUNT(*) AS n FROM outbox_items o LEFT JOIN receipts r ON r.id = o.receipt_id WHERE o.status = 'blocked' AND (o.receipt_id IS NULL OR r.id IS NULL)",
            "decisions_missing_receipt": "SELECT COUNT(*) AS n FROM decisions d LEFT JOIN receipts r ON r.subject_type = 'decision' AND r.subject_id = d.id WHERE r.id IS NULL",
            "decisions_missing_claim": "SELECT COUNT(*) AS n FROM decisions d LEFT JOIN claims c ON c.subject_type = 'decision' AND c.subject_id = d.id WHERE c.id IS NULL",
            "review_items_missing_receipt": "SELECT COUNT(*) AS n FROM review_items i LEFT JOIN receipts r ON r.subject_type = 'review_item' AND r.subject_id = i.id AND r.action_class = 'internal.review.create' WHERE r.id IS NULL",
            "review_items_missing_claim": "SELECT COUNT(*) AS n FROM review_items i LEFT JOIN claims c ON c.subject_type = 'review_item' AND c.subject_id = i.id AND c.claim_type = 'review_item_created' WHERE c.id IS NULL",
            "review_events_missing_receipt": "SELECT COUNT(*) AS n FROM review_events e LEFT JOIN receipts r ON r.id = e.receipt_id WHERE e.receipt_id IS NULL OR r.id IS NULL",
            "review_resolutions_missing_text": "SELECT COUNT(*) AS n FROM review_items WHERE status IN ('resolved', 'dismissed') AND (resolution_text IS NULL OR trim(resolution_text) = '')",
            "review_items_invalid_status": "SELECT COUNT(*) AS n FROM review_items WHERE status NOT IN ('open', 'resolved', 'dismissed')",
            "review_items_missing_created_event": "SELECT COUNT(*) AS n FROM review_items i LEFT JOIN review_events e ON e.review_item_id = i.id AND e.event_type = 'review.item.created' WHERE e.id IS NULL",
            "review_resolutions_missing_event": "SELECT COUNT(*) AS n FROM review_items i LEFT JOIN review_events e ON e.review_item_id = i.id AND e.event_type = 'review.item.' || i.status WHERE i.status IN ('resolved', 'dismissed') AND e.id IS NULL",
            "review_resolutions_missing_claim": "SELECT COUNT(*) AS n FROM review_items i LEFT JOIN claims c ON c.subject_type = 'review_item' AND c.subject_id = i.id AND c.claim_type = 'review_item_' || i.status WHERE i.status IN ('resolved', 'dismissed') AND c.id IS NULL",
            "capture_items_missing_receipt": "SELECT COUNT(*) AS n FROM capture_items i LEFT JOIN receipts r ON r.id = i.receipt_id WHERE i.receipt_id IS NULL OR r.id IS NULL",
            "capture_items_invalid_status": "SELECT COUNT(*) AS n FROM capture_items WHERE status NOT IN ('captured', 'processed', 'archived')",
            "capture_suggestions_missing_capture": "SELECT COUNT(*) AS n FROM capture_suggestions s LEFT JOIN capture_items i ON i.id = s.capture_id WHERE i.id IS NULL",
            "capture_suggestions_invalid_status": "SELECT COUNT(*) AS n FROM capture_suggestions WHERE status NOT IN ('proposed', 'accepted', 'dismissed')",
            "accepted_capture_suggestions_incomplete": "SELECT COUNT(*) AS n FROM capture_suggestions s LEFT JOIN receipts r ON r.id = s.receipt_id WHERE s.status = 'accepted' AND (s.accepted_subject_type IS NULL OR s.accepted_subject_ref IS NULL OR s.receipt_id IS NULL OR r.id IS NULL)",
        }
        return {name: self.conn.execute(sql).fetchone()["n"] for name, sql in queries.items()}

    def ensure_person(self, slug: str, name: str, now: str) -> str:
        return self._ensure_slug("persons", slug, {"display_name": name}, now)

    def ensure_contour(self, slug: str, name: str, now: str) -> str:
        return self._ensure_slug("contours", slug, {"name": name}, now)

    def ensure_mandate(self, person_id: str, contour_id: str, now: str, public_id: str | None = None) -> str:
        row = self.conn.execute(
            "SELECT id FROM mandates WHERE principal_person_id = ? AND contour_id = ? AND status = 'active'",
            (person_id, contour_id),
        ).fetchone()
        if row:
            return row["id"]
        mandate_id = new_id("mandate")
        self.conn.execute(
            """
            INSERT INTO mandates
            (id, public_id, principal_person_id, contour_id, title, scope, status, created_at)
            VALUES (?, ?, ?, ?, 'Manage Verace project work', 'internal_project_work', 'active', ?)
            """,
            (mandate_id, public_id or new_public_id("MANDATE"), person_id, contour_id, now),
        )
        return mandate_id

    def _ensure_slug(self, table: str, slug: str, fields: dict[str, str], now: str) -> str:
        row = self.conn.execute(f"SELECT id FROM {table} WHERE slug = ?", (slug,)).fetchone()
        if row:
            return row["id"]
        item_id = new_id(table[:-1])
        columns = ["id", "slug", *fields.keys(), "created_at"]
        values = [item_id, slug, *fields.values(), now]
        self.conn.execute(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join('?' for _ in values)})", values)
        return item_id

    def _required(self, sql: str, params: tuple[str, ...]) -> sqlite3.Row:
        row = self.conn.execute(sql, params).fetchone()
        if row is None:
            raise RuntimeError("Required ledger row not found")
        return row
