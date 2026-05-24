"""SQLite connection and schema utilities."""

from __future__ import annotations

import sqlite3
from importlib import resources
from pathlib import Path

from verace_runtime.ledger.migrations import ensure_schema_current


def connect(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    schema = resources.files("verace_runtime.ledger").joinpath("schema.sql").read_text()
    ensure_schema_current(conn, schema)
