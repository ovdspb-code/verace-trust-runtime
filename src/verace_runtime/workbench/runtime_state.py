"""Workbench-only runtime state classification."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.ledger.migrations import inspect_schema_state
from verace_runtime.ledger.repository import COUNT_TABLES


@dataclass(frozen=True)
class WorkbenchRuntimeState:
    kind: str
    reason: str

    @property
    def first_run(self) -> bool:
        return self.kind == "first_run"

    @property
    def ready(self) -> bool:
        return self.kind == "ready"

    @property
    def unsafe(self) -> bool:
        return self.kind == "unsafe"


def classify_runtime(db_path: str | Path) -> WorkbenchRuntimeState:
    path = Path(db_path)
    if not path.exists() or path.stat().st_size == 0:
        return WorkbenchRuntimeState("first_run", "missing or empty runtime database")
    try:
        with sqlite3.connect(path) as conn:
            conn.row_factory = sqlite3.Row
            state = inspect_schema_state(conn)
            if state.empty:
                return WorkbenchRuntimeState("first_run", state.reason)
            if not state.schema_current:
                return _non_current_state(conn, state.reason)
        doctor = FounderAssistantService(path).doctor()
    except sqlite3.Error as exc:
        return WorkbenchRuntimeState("unsafe", f"sqlite error: {exc}")
    except RuntimeError as exc:
        if str(exc) == "Required ledger row not found":
            return WorkbenchRuntimeState("first_run", "required seed rows are absent")
        return WorkbenchRuntimeState("unsafe", str(exc))
    if doctor["ok"]:
        return WorkbenchRuntimeState("ready", "ready")
    if not doctor.get("seed_ok", False):
        return WorkbenchRuntimeState("first_run", "required seed rows are absent")
    return WorkbenchRuntimeState("unsafe", str(doctor.get("schema_reason") or "runtime checks failed"))


def reset_first_run_runtime(db_path: str | Path) -> None:
    path = Path(db_path)
    for candidate in (path, path.with_name(path.name + "-wal"), path.with_name(path.name + "-shm")):
        try:
            candidate.unlink()
        except FileNotFoundError:
            pass


def _non_current_state(conn: sqlite3.Connection, reason: str) -> WorkbenchRuntimeState:
    if _has_only_empty_runtime_tables(conn):
        return WorkbenchRuntimeState("first_run", reason)
    return WorkbenchRuntimeState("unsafe", reason)


def _has_only_empty_runtime_tables(conn: sqlite3.Connection) -> bool:
    tables = _table_names(conn)
    if not tables:
        return True
    for table in tables:
        if table.startswith("sqlite_"):
            continue
        if table not in COUNT_TABLES:
            return False
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if count:
            return False
    return True


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {row["name"] for row in rows}
