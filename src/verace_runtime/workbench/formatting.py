"""Human-readable workbench output formatting."""

from __future__ import annotations

from verace_runtime.ledger.models import ReviewSummary
from verace_runtime.rendering.models import RenderResult


def rendered_or_error(result: RenderResult) -> str:
    if not result.ok:
        raise RuntimeError(f"Cannot render {result.claim_class}: {result.reason}")
    return result.text


def format_brief(brief: dict[str, object]) -> str:
    counts = brief["counts"]
    schema = brief["schema"]
    lines = [
        "Verace session brief",
        "Doctor: OK" if brief["doctor"]["ok"] else "Doctor: FAIL",
        f"Schema: {schema['schema_name']} v{schema['schema_version']} current={schema['schema_current']}",
        f"Counts: tasks={counts['tasks']} reviews={counts['review_items']} decisions={counts['decisions']} receipts={counts['receipts']} claims={counts['claims']}",
        "Open reviews:",
    ]
    lines.extend(_review_lines(brief["reviews"]))
    lines.append("Tasks:")
    lines.extend(_task_lines(brief["tasks"]))
    lines.append("Latest decisions:")
    lines.extend(_decision_lines(brief["decisions"]))
    lines.append("Recent events:")
    lines.extend(_event_lines(brief["task_events"], "public_no"))
    lines.extend(_event_lines(brief["review_events"], "public_id"))
    return "\n".join(lines)


def format_reviews(items: list[ReviewSummary]) -> str:
    if not items:
        return "No review items."
    lines = ["Review queue"]
    for item in items:
        task = item.task_public_no or "-"
        lines.append(f"- {item.public_id} [{item.status}/{item.priority}/{item.review_type}] task={task} {item.title}")
    return "\n".join(lines)


def format_doctor(result: dict[str, object]) -> str:
    status = "OK" if result["ok"] else "FAIL"
    lines = [
        f"Doctor: {status}",
        f"Schema: {result['schema_name'] or 'unknown'} v{result['schema_version'] if result['schema_version'] is not None else 'unknown'} current={result['schema_current']}",
        f"Reason: {result['schema_reason']}",
        f"foreign_keys_ok={result['foreign_keys_ok']} seed_ok={result['seed_ok']}",
    ]
    counts = result["counts"]
    if counts:
        lines.append(f"tasks={counts.get('tasks', 0)} reviews={counts.get('review_items', 0)} receipts={counts.get('receipts', 0)} claims={counts.get('claims', 0)}")
    return "\n".join(lines)


def _review_lines(items: list[dict[str, object]]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item['public_id']} [{item['priority']}/{item['review_type']}] {item['title']}" for item in items]


def _task_lines(items: list[dict[str, object]]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item['public_no']} [{item['status']}] {item['title']}" for item in items]


def _decision_lines(items: list[dict[str, object]]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item['public_id']} [{item['status']}] {item['title']}" for item in items]


def _event_lines(items: list[dict[str, object]], id_key: str) -> list[str]:
    return [f"- {item[id_key]} {item['event_type']}: {item['summary']}" for item in items]

