"""Deterministic local documentation intake for the workbench."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocumentItem:
    category: str
    title: str
    path: str
    status: str
    purpose: str


@dataclass(frozen=True)
class RiskItem:
    title: str
    status: str
    mitigation: str
    source_file: str


@dataclass(frozen=True)
class ProjectContext:
    project_name: str
    current_phase: str
    current_product_surface: str
    current_work: str
    recent_work: str
    next_work: str
    accepted_adrs: list[str]
    merged_briefs: list[str]
    open_risks: list[RiskItem]
    recent_worklog: list[str]
    decision_count: int
    latest_decisions: list[str]
    documents: list[DocumentItem]


def project_root() -> Path:
    return Path(os.environ.get("VERACE_PROJECT_ROOT", Path(__file__).resolve().parents[3]))


def read_project_context(root: Path | None = None) -> ProjectContext:
    base = root or project_root()
    project_state = _read(base / "docs/ops/PROJECT_STATE.md")
    risk_register = _read(base / "docs/ops/RISK_REGISTER.md")
    decisions = _read(base / "docs/ops/DECISIONS.md")
    worklog = _read(base / "docs/ops/WORKLOG.md")
    return ProjectContext(
        project_name=_field(project_state, "**Project:**") or "Verace",
        current_phase=_field(project_state, "**Current phase:**") or "unknown",
        current_product_surface=_current_product_surface(project_state),
        current_work=_current_work(project_state),
        recent_work=_recent_work(project_state),
        next_work=_first_bullet(project_state, "## Next Intended Work"),
        accepted_adrs=_bullets(project_state, "## Accepted ADRs"),
        merged_briefs=[line[2:].strip() for line in _bullets(project_state, "## Active Implementation Brief") if "merged in PR" in line],
        open_risks=_open_risks(risk_register),
        recent_worklog=_headings(worklog, "## ", 5),
        decision_count=len(_decision_rows(decisions)),
        latest_decisions=_decision_rows(decisions)[-3:],
        documents=_document_map(base),
    )


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _field(text: str, prefix: str) -> str:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip().strip("* ")
    return ""


def _section(text: str, title: str) -> list[str]:
    lines = text.splitlines()
    in_section = False
    out: list[str] = []
    for line in lines:
        if line.strip() == title:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            out.append(line)
    return out


def _bullets(text: str, title: str) -> list[str]:
    return [line.strip() for line in _section(text, title) if line.strip().startswith("- ")]


def _first_bullet(text: str, title: str) -> str:
    items = _bullets(text, title)
    return items[0][2:].strip().rstrip(".") if items else ""


def _current_product_surface(text: str) -> str:
    for line in _bullets(text, "## Current Work"):
        if "Current product surface:" in line:
            return line.split("Current product surface:", 1)[1].strip().rstrip(".")
    return ""


def _current_work(text: str) -> str:
    for line in _bullets(text, "## Current Work"):
        if "Current work:" in line:
            return line.split("Current work:", 1)[1].strip().rstrip(".")
    return ""


def _recent_work(text: str) -> str:
    for line in _bullets(text, "## Current Work"):
        if "Recent work:" in line:
            return line.split("Recent work:", 1)[1].strip().rstrip(".")
    return ""


def _open_risks(text: str) -> list[RiskItem]:
    risks: list[RiskItem] = []
    for line in text.splitlines():
        if not line.startswith("| ") or line.startswith("| Risk") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 3 and cells[1] == "Open":
            risks.append(RiskItem(cells[0], cells[1], cells[2], "docs/ops/RISK_REGISTER.md"))
    return risks


def _decision_rows(text: str) -> list[str]:
    rows: list[str] = []
    for line in text.splitlines():
        if line.startswith("| D-"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) >= 2:
                rows.append(f"{cells[0]}: {cells[1]}")
    return rows


def _headings(text: str, prefix: str, limit: int) -> list[str]:
    return [line.removeprefix(prefix).strip() for line in text.splitlines() if line.startswith(prefix)][:limit]


def _document_map(base: Path) -> list[DocumentItem]:
    specs = [("README", "README.md"), ("Operations", "docs/ops/*.md"), ("ADRs", "docs/adr/*.md"), ("Briefs", "docs/briefs/*.md"), ("Plans", "docs/plans/*.md")]
    docs: list[DocumentItem] = []
    for category, pattern in specs:
        paths = [base / pattern] if "*" not in pattern else sorted(base.glob(pattern))
        for path in paths:
            if path.exists() and path.is_file():
                docs.append(_document_item(base, category, path))
    return docs


def _document_item(base: Path, category: str, path: Path) -> DocumentItem:
    text = _read(path)
    title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")), path.name)
    status = "Accepted v1.0" if "Accepted v1.0" in text else "Proposed v1.0" if "Proposed v1.0" in text else "merged" if "merged in PR" in text else ""
    purpose = next((line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#") and not line.startswith("|")), "")
    return DocumentItem(category, title, str(path.relative_to(base)), status, purpose[:160])
