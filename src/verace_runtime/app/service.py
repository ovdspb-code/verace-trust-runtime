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
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.policy = PolicyEngine()
        self.receipts = ReceiptFactory()

    def init_runtime(self) -> InitResult:
        with connect(self.db_path) as conn:
            apply_schema(conn)
            repo = LedgerRepository(conn)
            now = utc_now_iso()
            ids = repo.seed_founder(now)
            decision = self.policy.evaluate("ledger.init")
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
            message = repo.create_message(person["id"], contour_row["id"], clean_text, now)
            message_receipt = self._receipt_message(repo, message, now)
            if self._is_note(clean_text):
                return IngestResult(message["public_id"], None, message_receipt["public_id"], "verified_by_receipt")
            task = repo.create_task(mandate["id"], contour_row["id"], message["id"], self._title(clean_text), now)
            event_id = repo.create_event(task["id"], "task.created", "Task created from inbound message", now)
            decision = self.policy.evaluate("internal.task.create")
            receipt = repo.insert_receipt(
                self.receipts.build(decision, "ledger.event", "task", task["id"], f"Task {task['public_no']} created")
            )
            repo.attach_event_receipt(event_id, receipt["id"])
            repo.insert_claim("task_recorded", f"Task {task['public_no']} was recorded in the ledger", "task", task["id"], receipt["id"], now)
            return IngestResult(message["public_id"], task["public_no"], receipt["public_id"], "verified_by_receipt")

    def request_action(self, action_class: str, payload: str = "{}") -> PolicyResult:
        with connect(self.db_path) as conn:
            apply_schema(conn)
            repo = LedgerRepository(conn)
            now = utc_now_iso()
            decision = self.policy.evaluate(action_class)
            if decision.allowed:
                return PolicyResult(action_class, True, None, decision.reason)
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
        counts = self.status()
        required = ["persons", "contours", "mandates", "tasks", "receipts", "claims"]
        ok = counts["persons"] >= 1 and counts["contours"] >= 1 and counts["mandates"] >= 1
        return {"ok": ok, "required_tables": required, "counts": counts}

    def _receipt_message(self, repo: LedgerRepository, message, now: str):
        decision = self.policy.evaluate("internal.message.record")
        receipt = repo.insert_receipt(
            self.receipts.build(decision, "ledger.event", "message", message["id"], "Inbound message recorded")
        )
        repo.insert_claim("message_recorded", "Inbound message was recorded in the ledger", "message", message["id"], receipt["id"], now)
        return receipt

    def _is_note(self, text: str) -> bool:
        return text.lower().startswith(("note:", "status:", "/status"))

    def _title(self, text: str) -> str:
        one_line = " ".join(text.split())
        return one_line[:100] if len(one_line) > 100 else one_line
