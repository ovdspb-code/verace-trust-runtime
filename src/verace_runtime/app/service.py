"""Founder Assistant ledger seed service."""

from __future__ import annotations

from pathlib import Path

from verace_runtime.ledger.db import apply_schema, connect
from verace_runtime.ledger.models import IngestResult, InitResult, PolicyResult, TaskSummary
from verace_runtime.ledger.repository import LedgerRepository
from verace_runtime.policy.engine import PolicyEngine
from verace_runtime.receipts.factory import ReceiptFactory
from verace_runtime.time import utc_now_iso


class FounderAssistantService:
    def __init__(self, db_path: str | Path, policy: PolicyEngine | None = None) -> None:
        self.db_path = Path(db_path)
        self.policy = policy or PolicyEngine()
        self.receipts = ReceiptFactory()

    def init_runtime(self) -> InitResult:
        with connect(self.db_path) as conn:
            apply_schema(conn)
            repo = LedgerRepository(conn)
            now = utc_now_iso()
            decision = self.policy.evaluate("ledger.init")
            if not decision.allowed:
                receipt = self._policy_receipt(repo, decision, now)
                return InitResult("blocked", "blocked", "blocked", receipt["public_id"])
            repo.seed_founder(now)
            receipt = repo.insert_receipt(
                self.receipts.build(decision, "ledger.event", "runtime", "founder_seed", "Founder seed initialized")
            )
            repo.insert_claim("runtime_initialized", "Founder runtime seed is initialized", "runtime", "founder_seed", receipt["id"], now)
            mandate = repo.active_mandate("oleg", "verace_project")
            return InitResult("oleg", "verace_project", mandate["public_id"], receipt["public_id"])

    def ingest_message(self, principal: str, contour: str, text: str) -> IngestResult:
        clean_text = text.strip()
        if not clean_text:
            raise RuntimeError("Message text is empty")
        with connect(self.db_path) as conn:
            apply_schema(conn)
            repo = LedgerRepository(conn)
            now = utc_now_iso()
            person = repo.find_person(principal)
            contour_row = repo.find_contour(contour)
            mandate = repo.active_mandate(principal, contour)
            message_decision = self.policy.evaluate("internal.message.record")
            if not message_decision.allowed:
                receipt = self._policy_receipt(repo, message_decision, now)
                return IngestResult("", None, receipt["public_id"], "blocked")
            message = repo.create_message(person["id"], contour_row["id"], clean_text, now)
            message_receipt = self._receipt_message(repo, message, now)
            if self._is_note(clean_text):
                return IngestResult(message["public_id"], None, message_receipt["public_id"], "verified_by_receipt")
            task_decision = self.policy.evaluate("internal.task.create")
            if not task_decision.allowed:
                receipt = self._policy_receipt(repo, task_decision, now, "message", message["id"])
                return IngestResult(message["public_id"], None, receipt["public_id"], "blocked")
            task = repo.create_task(mandate["id"], contour_row["id"], message["id"], self._title(clean_text), now)
            receipt = repo.insert_receipt(
                self.receipts.build(task_decision, "ledger.event", "task", task["id"], f"Task {task['public_no']} created")
            )
            repo.create_event(task["id"], "task.created", "Task created from inbound message", receipt["id"], now)
            repo.insert_claim("task_recorded", f"Task {task['public_no']} was recorded in the ledger", "task", task["id"], receipt["id"], now)
            return IngestResult(message["public_id"], task["public_no"], receipt["public_id"], "verified_by_receipt")

    def request_action(self, action_class: str, payload: str = "{}") -> PolicyResult:
        with connect(self.db_path) as conn:
            apply_schema(conn)
            repo = LedgerRepository(conn)
            now = utc_now_iso()
            decision = self.policy.evaluate(action_class)
            if decision.allowed:
                receipt = repo.insert_receipt(
                    self.receipts.build(decision, "policy.allowed", "policy", action_class, decision.reason)
                )
                repo.insert_claim("action_allowed", f"Action {action_class} was allowed by policy", "policy", action_class, receipt["id"], now)
                return PolicyResult(action_class, True, receipt["public_id"], decision.reason)
            receipt = repo.insert_receipt(
                self.receipts.build(decision, "policy.blocked", "policy", action_class, decision.reason)
            )
            repo.insert_outbox_block(action_class, payload, receipt["id"], now)
            repo.insert_claim("action_blocked", f"Action {action_class} was blocked by policy", "policy", action_class, receipt["id"], now)
            return PolicyResult(action_class, False, receipt["public_id"], decision.reason)

    def list_tasks(self) -> list[TaskSummary]:
        with connect(self.db_path) as conn:
            apply_schema(conn)
            return LedgerRepository(conn).task_summaries()

    def task_detail(self, task_ref: str) -> dict[str, object]:
        with connect(self.db_path) as conn:
            apply_schema(conn)
            repo = LedgerRepository(conn)
            task = repo.task_detail(task_ref)
            receipts = repo.task_receipts(task["id"])
            return {"task": dict(task), "receipts": [dict(row) for row in receipts]}

    def status(self) -> dict[str, int]:
        with connect(self.db_path) as conn:
            apply_schema(conn)
            return LedgerRepository(conn).counts()

    def doctor(self) -> dict[str, object]:
        required = [
            "persons",
            "contours",
            "contour_memberships",
            "mandates",
            "messages",
            "tasks",
            "task_events",
            "approvals",
            "receipts",
            "claims",
            "outbox_items",
        ]
        with connect(self.db_path) as conn:
            repo = LedgerRepository(conn)
            schema_ok = set(required) <= repo.table_names()
            pragma_ok = conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
            integrity_ok = conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            foreign_keys_ok = len(conn.execute("PRAGMA foreign_key_check").fetchall()) == 0
            counts = repo.counts() if schema_ok else {}
            invariants = repo.invariant_counts() if schema_ok else {}
            seed_ok = repo.seed_ok() if schema_ok else False
        claim_receipt_ok = invariants.get("claims_missing_receipt", 1) == 0
        task_event_receipt_ok = invariants.get("task_events_missing_receipt", 1) == 0
        outbox_receipt_ok = invariants.get("outbox_missing_receipt", 1) == 0
        ok = all([schema_ok, pragma_ok, integrity_ok, foreign_keys_ok, seed_ok, claim_receipt_ok, task_event_receipt_ok, outbox_receipt_ok])
        return {
            "ok": ok,
            "schema_ok": schema_ok,
            "pragma_ok": pragma_ok,
            "integrity_ok": integrity_ok,
            "foreign_keys_ok": foreign_keys_ok,
            "seed_ok": seed_ok,
            "claim_receipt_ok": claim_receipt_ok,
            "task_event_receipt_ok": task_event_receipt_ok,
            "outbox_receipt_ok": outbox_receipt_ok,
            "required_tables": required,
            "counts": counts,
            "invariants": invariants,
        }

    def _receipt_message(self, repo: LedgerRepository, message, now: str):
        decision = self.policy.evaluate("internal.message.record")
        receipt = repo.insert_receipt(
            self.receipts.build(decision, "ledger.event", "message", message["id"], "Inbound message recorded")
        )
        repo.insert_claim("message_recorded", "Inbound message was recorded in the ledger", "message", message["id"], receipt["id"], now)
        return receipt

    def _policy_receipt(self, repo: LedgerRepository, decision, now: str, subject_type: str = "policy", subject_id: str | None = None):
        subject = subject_id or decision.action_class
        receipt = repo.insert_receipt(
            self.receipts.build(decision, "policy.blocked", subject_type, subject, decision.reason)
        )
        repo.insert_claim("action_blocked", f"Action {decision.action_class} was blocked by policy", subject_type, subject, receipt["id"], now)
        return receipt

    def _is_note(self, text: str) -> bool:
        return text.lower().startswith(("note:", "status:", "/status"))

    def _title(self, text: str) -> str:
        one_line = " ".join(text.split())
        return one_line[:100] if len(one_line) > 100 else one_line
