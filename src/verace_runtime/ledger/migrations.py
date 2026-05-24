"""Schema inspection and lightweight migration discipline."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from verace_runtime.time import utc_now_iso


CURRENT_SCHEMA_NAME = "verace_runtime"
CURRENT_SCHEMA_VERSION = 3


class SchemaError(RuntimeError):
    """Raised when a DB schema is unsafe for normal runtime use."""


@dataclass(frozen=True)
class SchemaState:
    schema_name: str | None
    schema_version: int | None
    schema_version_raw: str | None
    schema_known: bool
    schema_current: bool
    migration_required: bool
    empty: bool
    reason: str


@dataclass(frozen=True)
class Migration:
    target_version: int
    description: str
    apply: Callable[[sqlite3.Connection], None]
    destructive: bool = False


PRODUCTION_MIGRATIONS: tuple[Migration, ...] = (
    Migration(2, "add review queue tables", lambda conn: conn.executescript(_REVIEW_QUEUE_SQL)),
    Migration(3, "add capture inbox tables", lambda conn: conn.executescript(_CAPTURE_INBOX_SQL)),
)


_REVIEW_QUEUE_SQL = """
CREATE TABLE IF NOT EXISTS review_items (
  id TEXT PRIMARY KEY,
  public_id TEXT NOT NULL UNIQUE,
  contour_id TEXT NOT NULL REFERENCES contours(id),
  mandate_id TEXT NOT NULL REFERENCES mandates(id),
  task_id TEXT REFERENCES tasks(id),
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  review_type TEXT NOT NULL,
  priority TEXT NOT NULL,
  status TEXT NOT NULL,
  resolution_text TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_events (
  id TEXT PRIMARY KEY,
  review_item_id TEXT NOT NULL REFERENCES review_items(id),
  event_type TEXT NOT NULL,
  summary TEXT NOT NULL,
  receipt_id TEXT NOT NULL REFERENCES receipts(id),
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_review_items_status ON review_items(status, created_at, public_id);
CREATE INDEX IF NOT EXISTS idx_review_events_created_at ON review_events(created_at, id);
"""


_CAPTURE_INBOX_SQL = """
CREATE TABLE IF NOT EXISTS capture_items (
  id TEXT PRIMARY KEY,
  public_id TEXT NOT NULL UNIQUE,
  source_type TEXT NOT NULL,
  source_label TEXT,
  raw_text TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  receipt_id TEXT NOT NULL REFERENCES receipts(id)
);

CREATE TABLE IF NOT EXISTS capture_suggestions (
  id TEXT PRIMARY KEY,
  public_id TEXT NOT NULL UNIQUE,
  capture_id TEXT NOT NULL REFERENCES capture_items(id),
  kind TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  reason TEXT NOT NULL,
  source_span TEXT,
  status TEXT NOT NULL,
  accepted_subject_type TEXT,
  accepted_subject_ref TEXT,
  receipt_id TEXT REFERENCES receipts(id),
  created_at TEXT NOT NULL,
  updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_capture_items_status ON capture_items(status, created_at, public_id);
CREATE INDEX IF NOT EXISTS idx_capture_suggestions_capture ON capture_suggestions(capture_id, status, public_id);
"""


def inspect_schema_state(conn: sqlite3.Connection, target_version: int = CURRENT_SCHEMA_VERSION) -> SchemaState:
    tables = _table_names(conn)
    if not tables:
        return SchemaState(None, None, None, True, False, False, True, "empty database")
    if "runtime_meta" not in tables:
        return SchemaState(None, None, None, False, False, True, False, "missing runtime_meta")
    meta = _read_meta(conn)
    name = meta.get("schema_name")
    raw_version = meta.get("schema_version")
    if {"schema_name", "schema_version", "created_at", "last_migrated_at"} - set(meta):
        return SchemaState(name, None, raw_version, False, False, True, False, "missing runtime_meta keys")
    if name != CURRENT_SCHEMA_NAME:
        return SchemaState(name, None, raw_version, False, False, True, False, "unknown schema_name")
    try:
        version = int(raw_version or "")
    except ValueError:
        return SchemaState(name, None, raw_version, False, False, True, False, "malformed schema_version")
    if version == target_version:
        return SchemaState(name, version, raw_version, True, True, False, False, "current")
    if version > target_version:
        return SchemaState(name, version, raw_version, False, False, True, False, "newer schema_version")
    return SchemaState(name, version, raw_version, True, False, True, False, "migration required")


def ensure_schema_current(conn: sqlite3.Connection, schema_sql: str) -> SchemaState:
    state = inspect_schema_state(conn)
    if state.empty:
        conn.executescript(schema_sql)
        write_current_metadata(conn, created_at=utc_now_iso())
        return inspect_schema_state(conn)
    if state.schema_current:
        return state
    if not state.schema_known or state.schema_version is None:
        raise SchemaError(f"Unsafe runtime schema: {state.reason}")
    migrated = run_migrations(conn, state, CURRENT_SCHEMA_VERSION, PRODUCTION_MIGRATIONS)
    if not migrated.schema_current:
        raise SchemaError(f"Unsafe runtime schema: {migrated.reason}")
    return migrated


def run_migrations(
    conn: sqlite3.Connection,
    state: SchemaState,
    target_version: int,
    migrations: Sequence[Migration],
) -> SchemaState:
    if state.schema_version is None:
        raise SchemaError("Cannot migrate unknown schema version")
    if state.schema_version > target_version:
        raise SchemaError("Cannot downgrade runtime schema")
    by_version = {item.target_version: item for item in migrations}
    version = state.schema_version
    while version < target_version:
        next_version = version + 1
        migration = by_version.get(next_version)
        if migration is None:
            raise SchemaError(f"Missing migration to schema version {next_version}")
        if migration.destructive:
            raise SchemaError(f"Destructive migration blocked: {migration.description}")
        migration.apply(conn)
        write_meta(conn, {"schema_version": str(next_version), "last_migrated_at": utc_now_iso()})
        version = next_version
    return inspect_schema_state(conn, target_version=target_version)


def write_current_metadata(conn: sqlite3.Connection, created_at: str) -> None:
    write_meta(
        conn,
        {
            "schema_name": CURRENT_SCHEMA_NAME,
            "schema_version": str(CURRENT_SCHEMA_VERSION),
            "created_at": created_at,
            "last_migrated_at": created_at,
        },
    )


def write_meta(conn: sqlite3.Connection, values: dict[str, str]) -> None:
    now = utc_now_iso()
    for key, value in values.items():
        conn.execute(
            """
            INSERT INTO runtime_meta (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, value, now),
        )


def doctor_schema_state(conn: sqlite3.Connection) -> dict[str, object]:
    try:
        state = inspect_schema_state(conn)
    except sqlite3.Error as exc:
        return {
            "schema_name": None,
            "schema_version": None,
            "schema_known": False,
            "schema_current": False,
            "migration_required": True,
            "schema_reason": f"sqlite error: {exc}",
        }
    return {
        "schema_name": state.schema_name,
        "schema_version": state.schema_version,
        "schema_known": state.schema_known,
        "schema_current": state.schema_current,
        "migration_required": state.migration_required,
        "schema_reason": state.reason,
    }


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {row["name"] if isinstance(row, sqlite3.Row) else row[0] for row in rows}


def _read_meta(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute("SELECT key, value FROM runtime_meta").fetchall()
    meta = {}
    for row in rows:
        key = row["key"] if isinstance(row, sqlite3.Row) else row[0]
        value = row["value"] if isinstance(row, sqlite3.Row) else row[1]
        meta[key] = value
    return meta
