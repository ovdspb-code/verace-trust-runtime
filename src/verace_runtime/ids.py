"""Small ID helpers for the runtime ledger."""

from __future__ import annotations

from uuid import uuid4


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:16]}"


def new_public_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8].upper()}"


def task_public_no(seq: int) -> str:
    return f"TR-{seq:06d}"


def decision_public_no(seq: int) -> str:
    return f"DEC-{seq:06d}"


def review_public_no(seq: int) -> str:
    return f"REV-{seq:06d}"
