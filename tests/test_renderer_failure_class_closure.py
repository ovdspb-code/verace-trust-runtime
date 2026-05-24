from __future__ import annotations

from verace_runtime.rendering.models import EvidenceView, SyntheticReceiptView
from verace_runtime.rendering.renderer import ResponseClaimRenderer


def test_artifact_format_mismatch_repairs_to_receipt_format():
    renderer = ResponseClaimRenderer()
    view = SyntheticReceiptView("artifact_created", "A-1", "RCPT-1", claim_type="artifact_created", artifact_format="docx")

    result = renderer.render_artifact_created(view, proposed_format="pdf")

    assert result.ok is True
    assert result.source == "synthetic_receipt_view"
    assert "DOCX" in result.text
    assert "PDF" not in result.text


def test_unknown_artifact_format_fails_closed():
    renderer = ResponseClaimRenderer()
    view = SyntheticReceiptView("artifact_created", "A-1", "RCPT-1", claim_type="artifact_created", artifact_format="unknown")

    result = renderer.render_artifact_created(view)

    assert result.ok is False
    assert result.source == "refusal"
    assert result.reason == "unknown artifact format"


def test_draft_external_send_cannot_render_as_sent():
    renderer = ResponseClaimRenderer()
    view = SyntheticReceiptView("external_send_sent", "send-1", "RCPT-1", delivery_state="draft")

    result = renderer.render_external_send_completed(view)

    assert result.ok is False
    assert result.reason == "external-send receipt is not sent"


def test_tests_passed_requires_passed_check_receipt():
    renderer = ResponseClaimRenderer()
    view = SyntheticReceiptView("tests_passed", "check-1", "RCPT-1", check_state=None)

    result = renderer.render_tests_passed(view)

    assert result.ok is False
    assert result.reason == "check receipt does not say passed"


def test_wrong_subject_claim_class_fails_closed():
    renderer = ResponseClaimRenderer()
    evidence = EvidenceView(
        claim_class="decision_recorded",
        subject="TR-000001",
        subject_type="task",
        receipt_public_id="RCPT-1",
        receipt_type="ledger.event",
        action_class="internal.task.create",
        receipt_status="ok",
        policy_result="allowed",
        claim_type="task_recorded",
        claim_status="verified_by_receipt",
    )

    result = renderer.render_current("task_recorded", evidence)

    assert result.ok is False
    assert result.reason == "evidence claim class mismatch"


def test_wrong_claim_type_fails_closed():
    renderer = ResponseClaimRenderer()
    evidence = EvidenceView(
        claim_class="task_recorded",
        subject="TR-000001",
        subject_type="task",
        receipt_public_id="RCPT-1",
        receipt_type="ledger.event",
        action_class="internal.task.create",
        receipt_status="ok",
        policy_result="allowed",
        claim_type="decision_recorded",
        claim_status="verified_by_receipt",
    )

    result = renderer.render_current("task_recorded", evidence)

    assert result.ok is False
    assert result.reason == "claim type mismatch"
