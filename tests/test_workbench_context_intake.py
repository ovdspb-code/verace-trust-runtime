from __future__ import annotations

from pathlib import Path

from verace_runtime.workbench.context import read_project_context


def test_context_intake_extracts_project_state_and_next_work():
    context = read_project_context(Path.cwd())

    assert context.project_name == "Verace - Trust Runtime"
    assert context.current_phase == "Phase 1 - Founder Assistant Seed"
    assert context.current_product_surface == "Persona Front Door over Browser Founder Workbench"
    assert context.next_work


def test_context_intake_reads_open_risks_and_decisions():
    context = read_project_context(Path.cwd())

    assert any(risk.status == "Open" for risk in context.open_risks)
    assert context.decision_count >= 1
    assert context.latest_decisions


def test_context_intake_lists_documentation_map():
    context = read_project_context(Path.cwd())
    paths = {doc.path for doc in context.documents}

    assert "README.md" in paths
    assert "docs/ops/PROJECT_STATE.md" in paths
    assert any(path.startswith("docs/adr/ADR-TR") for path in paths)
    assert any(path.startswith("docs/briefs/BRIEF-TR") for path in paths)
    assert any(path.startswith("docs/plans/PLAN-TR") for path in paths)
