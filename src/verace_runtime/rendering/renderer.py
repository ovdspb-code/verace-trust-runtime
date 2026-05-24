"""Deterministic system-action prose renderer."""

from __future__ import annotations

from verace_runtime.rendering.models import EvidenceView, RenderResult, SyntheticReceiptView


class ResponseClaimRenderer:
    current_claim_types = {
        "task_recorded": "task_recorded",
        "decision_recorded": "decision_recorded",
        "review_created": "review_item_created",
        "review_resolved": "review_item_resolved",
        "review_dismissed": "review_item_dismissed",
        "action_blocked": "action_blocked",
    }
    review_events = {
        "review_created": "review.item.created",
        "review_resolved": "review.item.resolved",
        "review_dismissed": "review.item.dismissed",
    }
    artifact_formats = frozenset({"pdf", "docx", "txt"})

    def render_current(self, claim_class: str, evidence: EvidenceView | None) -> RenderResult:
        if evidence is None:
            return self._fail(claim_class, "receipt-backed evidence not found")
        expected_claim = self.current_claim_types.get(claim_class)
        if expected_claim is None:
            return self._fail(claim_class, "unsupported claim class")
        if evidence.claim_class != claim_class:
            return self._fail(claim_class, "evidence claim class mismatch")
        if evidence.claim_type != expected_claim:
            return self._fail(claim_class, "claim type mismatch")
        expected_event = self.review_events.get(claim_class)
        if expected_event and evidence.event_type != expected_event:
            return self._fail(claim_class, "review lifecycle event mismatch")
        if claim_class == "action_blocked":
            if evidence.receipt_status != "blocked" or evidence.policy_result != "blocked":
                return self._fail(claim_class, "action block receipt is not blocked")
        elif evidence.receipt_status != "ok" or evidence.policy_result != "allowed":
            return self._fail(claim_class, "receipt is not an allowed ok receipt")
        if evidence.claim_status != "verified_by_receipt":
            return self._fail(claim_class, "claim is not verified by receipt")
        return RenderResult(True, self._text(claim_class, evidence), claim_class, evidence.receipt_public_id)

    def render_schema_healthy(self, doctor: dict[str, object]) -> RenderResult:
        if not doctor.get("ok") or not doctor.get("schema_current"):
            return self._fail("schema_healthy", "doctor/schema state is not healthy")
        name = doctor.get("schema_name") or "unknown"
        version = doctor.get("schema_version")
        text = f"Runtime schema is healthy: {name} v{version} is current."
        return RenderResult(True, text, "schema_healthy")

    def render_artifact_created(self, view: SyntheticReceiptView, proposed_format: str | None = None) -> RenderResult:
        fmt = (view.artifact_format or "").lower()
        if fmt not in self.artifact_formats:
            return self._fail(view.claim_class, "unknown artifact format")
        if view.receipt_status != "ok" or view.claim_type != "artifact_created":
            return self._fail(view.claim_class, "artifact receipt or claim is not sufficient")
        text = f"Artifact {view.subject} was prepared as {fmt.upper()}."
        return RenderResult(True, f"{text} Receipt: {view.receipt_public_id}.", view.claim_class, view.receipt_public_id)

    def render_external_send_completed(self, view: SyntheticReceiptView) -> RenderResult:
        if view.delivery_state != "sent":
            return self._fail(view.claim_class, "external-send receipt is not sent")
        return RenderResult(True, f"External send for {view.subject} completed. Receipt: {view.receipt_public_id}.", view.claim_class, view.receipt_public_id)

    def render_tests_passed(self, view: SyntheticReceiptView) -> RenderResult:
        if view.check_state != "passed":
            return self._fail(view.claim_class, "check receipt does not say passed")
        return RenderResult(True, f"Checks passed for {view.subject}. Receipt: {view.receipt_public_id}.", view.claim_class, view.receipt_public_id)

    def _text(self, claim_class: str, evidence: EvidenceView) -> str:
        phrases = {
            "task_recorded": f"Task {evidence.subject} was recorded in the ledger.",
            "decision_recorded": f"Decision {evidence.subject} was recorded in the ledger.",
            "review_created": f"Review {evidence.subject} was created.",
            "review_resolved": f"Review {evidence.subject} was resolved.",
            "review_dismissed": f"Review {evidence.subject} was dismissed.",
            "action_blocked": f"Action {evidence.subject} was blocked by policy.",
        }
        return f"{phrases[claim_class]} Receipt: {evidence.receipt_public_id}."

    def _fail(self, claim_class: str, reason: str) -> RenderResult:
        return RenderResult(False, "", claim_class, None, reason)
