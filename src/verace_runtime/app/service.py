"""Founder Assistant ledger seed service."""

from __future__ import annotations

from pathlib import Path

from verace_runtime.app.review_queue import add_review_item, list_review_items, resolve_review_item
from verace_runtime.app.session_brief import build_project_brief, build_session_brief
from verace_runtime.ledger.db import apply_schema, connect
from verace_runtime.ledger.models import DecisionResult, DecisionSummary, IngestResult, InitResult, PolicyResult, ReviewResult, ReviewSummary, TaskMutationResult, TaskSummary
from verace_runtime.ledger.migrations import doctor_schema_state
from verace_runtime.ledger.repository import COUNT_TABLES, LedgerRepository
from verace_runtime.policy.engine import PolicyEngine
from verace_runtime.receipts.factory import ReceiptFactory
from verace_runtime.rendering.models import RenderResult
from verace_runtime.rendering.receipt_views import RuntimeReceiptViews
from verace_runtime.rendering.renderer import ResponseClaimRenderer
from verace_runtime.time import utc_now_iso


class FounderAssistantService:
    allowed_statuses = frozenset({"open", "waiting", "blocked", "done", "canceled"})

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
            message_receipt = self._receipt_message(repo, message, message_decision, now)
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

    def record_decision(self, principal: str, contour: str, title: str, text: str) -> DecisionResult:
        clean_title = title.strip()
        clean_text = text.strip()
        if not clean_title or not clean_text:
            raise RuntimeError("Decision title and text are required")
        with connect(self.db_path) as conn:
            apply_schema(conn)
            repo = LedgerRepository(conn)
            now = utc_now_iso()
            contour_row = repo.find_contour(contour)
            mandate = repo.active_mandate(principal, contour)
            policy_decision = self.policy.evaluate("internal.decision.record")
            if not policy_decision.allowed:
                receipt = self._policy_receipt(repo, policy_decision, now)
                return DecisionResult("blocked", receipt["public_id"], "blocked")
            item = repo.create_decision(contour_row["id"], mandate["id"], None, clean_title, clean_text, now)
            receipt = repo.insert_receipt(
                self.receipts.build(policy_decision, "ledger.event", "decision", item["id"], f"Decision {item['public_id']} recorded")
            )
            repo.insert_claim("decision_recorded", f"Decision {item['public_id']} was recorded in the ledger", "decision", item["id"], receipt["id"], now)
            return DecisionResult(item["public_id"], receipt["public_id"], "verified_by_receipt")

    def list_decisions(self) -> list[DecisionSummary]:
        with connect(self.db_path) as conn:
            apply_schema(conn)
            return LedgerRepository(conn).decision_summaries()

    def set_task_status(self, task_ref: str, status: str, note: str) -> TaskMutationResult:
        clean_status = status.strip().lower()
        clean_note = note.strip() or f"Status changed to {clean_status}"
        if clean_status not in self.allowed_statuses:
            raise RuntimeError(f"Invalid task status: {status}")
        return self._mutate_task("internal.task.status_change", task_ref, clean_status, "task.status.changed", clean_note)

    def add_task_event(self, task_ref: str, event_type: str, summary: str) -> TaskMutationResult:
        clean_type = event_type.strip()
        clean_summary = summary.strip()
        if not clean_type or not clean_summary:
            raise RuntimeError("Event type and summary are required")
        return self._mutate_task("internal.task.event", task_ref, None, clean_type, clean_summary)

    def project_brief(self) -> dict[str, object]:
        return build_project_brief(self.db_path, self.policy, self.doctor)

    def add_review(self, principal: str, contour: str, title: str, body: str, review_type: str, priority: str, task_ref: str | None = None) -> ReviewResult:
        return add_review_item(self.db_path, self.policy, self.receipts, principal, contour, title, body, review_type, priority, task_ref)

    def list_reviews(self, status: str | None = "open") -> list[ReviewSummary]:
        return list_review_items(self.db_path, self.policy, status)

    def resolve_review(self, review_ref: str, resolution: str, status: str = "resolved") -> ReviewResult:
        return resolve_review_item(self.db_path, self.policy, self.receipts, review_ref, resolution, status)

    def session_brief(self) -> dict[str, object]:
        return build_session_brief(self.db_path, self.policy, self.doctor)

    def render_claim(self, claim_class: str, subject: str | None = None) -> RenderResult:
        renderer = ResponseClaimRenderer()
        if claim_class == "schema_healthy":
            return renderer.render_schema_healthy(self.doctor())
        if not subject:
            return RenderResult(False, "", claim_class, "refusal", None, "subject is required")
        with connect(self.db_path) as conn:
            apply_schema(conn)
            views = RuntimeReceiptViews(conn)
            if claim_class == "task_recorded":
                evidence = views.task_recorded(subject)
            elif claim_class == "decision_recorded":
                evidence = views.decision_recorded(subject)
            elif claim_class in {"review_created", "review_resolved", "review_dismissed"}:
                event = ResponseClaimRenderer.review_events[claim_class]
                claim = ResponseClaimRenderer.current_claim_types[claim_class]
                evidence = views.review_lifecycle(subject, claim_class, event, claim)
            elif claim_class == "action_blocked":
                evidence = views.action_blocked(subject)
            else:
                return RenderResult(False, "", claim_class, "refusal", None, "unsupported claim class")
        return renderer.render_current(claim_class, evidence)

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

    def schema_status(self) -> dict[str, object]:
        with connect(self.db_path) as conn:
            return doctor_schema_state(conn)

    def doctor(self) -> dict[str, object]:
        required = COUNT_TABLES
        with connect(self.db_path) as conn:
            schema_state = doctor_schema_state(conn)
            repo = LedgerRepository(conn)
            pragma_ok = conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
            integrity_ok = conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            foreign_keys_ok = len(conn.execute("PRAGMA foreign_key_check").fetchall()) == 0
            schema_current = bool(schema_state["schema_current"])
            schema_ok = schema_current and set(required) <= repo.table_names()
            counts = repo.counts() if schema_ok else {}
            invariants = repo.invariant_counts() if schema_ok else {}
            seed_ok = repo.seed_ok() if schema_ok else False
        checks = {
            "claim_receipt_ok": invariants.get("claims_missing_receipt", 1) == 0,
            "task_event_receipt_ok": invariants.get("task_events_missing_receipt", 1) == 0,
            "outbox_receipt_ok": invariants.get("outbox_missing_receipt", 1) == 0,
            "decision_receipt_ok": invariants.get("decisions_missing_receipt", 1) == 0,
            "decision_claim_ok": invariants.get("decisions_missing_claim", 1) == 0,
            "review_item_receipt_ok": invariants.get("review_items_missing_receipt", 1) == 0,
            "review_item_claim_ok": invariants.get("review_items_missing_claim", 1) == 0,
            "review_event_receipt_ok": invariants.get("review_events_missing_receipt", 1) == 0,
            "review_resolution_ok": invariants.get("review_resolutions_missing_text", 1) == 0,
            "review_status_ok": invariants.get("review_items_invalid_status", 1) == 0,
            "review_created_event_ok": invariants.get("review_items_missing_created_event", 1) == 0,
            "review_resolution_event_ok": invariants.get("review_resolutions_missing_event", 1) == 0,
            "review_resolution_claim_ok": invariants.get("review_resolutions_missing_claim", 1) == 0,
            "capture_item_receipt_ok": invariants.get("capture_items_missing_receipt", 1) == 0,
            "capture_item_status_ok": invariants.get("capture_items_invalid_status", 1) == 0,
            "capture_suggestion_capture_ok": invariants.get("capture_suggestions_missing_capture", 1) == 0,
            "capture_suggestion_status_ok": invariants.get("capture_suggestions_invalid_status", 1) == 0,
            "capture_suggestion_accept_ok": invariants.get("accepted_capture_suggestions_incomplete", 1) == 0,
        }
        ok = all([schema_ok, pragma_ok, integrity_ok, foreign_keys_ok, schema_state["schema_current"], seed_ok, *checks.values()])
        return {
            "ok": ok,
            **schema_state,
            "schema_ok": schema_ok,
            "pragma_ok": pragma_ok,
            "integrity_ok": integrity_ok,
            "foreign_keys_ok": foreign_keys_ok,
            "seed_ok": seed_ok,
            **checks,
            "required_tables": required,
            "counts": counts,
            "invariants": invariants,
        }

    def _receipt_message(self, repo: LedgerRepository, message, decision, now: str):
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

    def _mutate_task(self, action_class: str, task_ref: str, status: str | None, event_type: str, summary: str) -> TaskMutationResult:
        with connect(self.db_path) as conn:
            apply_schema(conn)
            repo = LedgerRepository(conn)
            now = utc_now_iso()
            task = repo.task_detail(task_ref)
            decision = self.policy.evaluate(action_class)
            if not decision.allowed:
                receipt = self._policy_receipt(repo, decision, now, "task", task["id"])
                return TaskMutationResult(task["public_no"], task["status"], receipt["public_id"], "blocked")
            note = f"Task {task['public_no']} {event_type}"
            receipt = repo.insert_receipt(self.receipts.build(decision, "ledger.event", "task", task["id"], note))
            if status is not None:
                repo.update_task_status(task["id"], status, now)
            repo.create_event(task["id"], event_type, summary, receipt["id"], now)
            claim_text = f"Task {task['public_no']} recorded event {event_type}"
            repo.insert_claim(event_type.replace(".", "_"), claim_text, "task", task["id"], receipt["id"], now)
            return TaskMutationResult(task["public_no"], status or task["status"], receipt["public_id"], "verified_by_receipt")

    def _is_note(self, text: str) -> bool:
        return text.lower().startswith(("note:", "status:", "/status"))

    def _title(self, text: str) -> str:
        one_line = " ".join(text.split())
        return one_line[:100] if len(one_line) > 100 else one_line
