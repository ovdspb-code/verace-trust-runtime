"""Server-rendered pages for the founder workbench."""

from __future__ import annotations

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.workbench.html import esc, items, page


def dashboard(service: FounderAssistantService, notice: str | None = None) -> str:
    doctor = service.doctor()
    if not doctor["ok"]:
        return page("Verace brief", _doctor_block(doctor) + _init_form(), notice)
    brief = service.session_brief()
    body = _doctor_block(brief["doctor"]) + "<div class='grid'>"
    body += _panel("Open tasks", _task_rows(brief["tasks"]))
    body += _panel("Open reviews", _review_rows(brief["reviews"]))
    body += _panel("Latest decisions", _decision_rows(brief["decisions"]))
    body += _panel("Recent events", _event_rows(brief["task_events"], "public_no") + _event_rows(brief["review_events"], "public_id"))
    counts = brief["counts"]
    body += _panel("Counts", [f"tasks={counts['tasks']} reviews={counts['review_items']} decisions={counts['decisions']}", f"receipts={counts['receipts']} claims={counts['claims']}"])
    body += "</div>"
    return page("Verace brief", body, notice)


def task_form() -> str:
    return page("Add task", "<section><h2>Add task</h2><form method='post' action='/tasks'><label>Task</label><textarea name='text' required rows='4'></textarea><button>Add task</button></form></section>")


def decision_form() -> str:
    return page("Record decision", "<section><h2>Record decision</h2><form method='post' action='/decisions'><label>Title</label><input name='title' required><label>Decision text</label><textarea name='text' required rows='5'></textarea><button>Record decision</button></form></section>")


def reviews(service: FounderAssistantService, notice: str | None = None) -> str:
    open_items = service.list_reviews("open")
    rows = []
    for item in open_items:
        task = item.task_public_no or "-"
        rows.append(
            f"<strong>{esc(item.public_id)}</strong> [{esc(item.priority)}/{esc(item.review_type)}] task={esc(task)} {esc(item.title)}"
            f"<form class='inline' method='post' action='/reviews/{esc(item.public_id)}/resolve'>"
            "<input name='resolution' placeholder='Resolution' required><select name='status'><option>resolved</option><option>dismissed</option></select><button>Close</button></form>"
        )
    body = "<section><h2>Open reviews</h2>" + items(rows) + "<p><a class='button' href='/reviews/new'>Add review</a></p></section>"
    return page("Reviews", body, notice)


def review_form() -> str:
    body = """
    <section><h2>Add review</h2><form method="post" action="/reviews">
    <label>Title</label><input name="title" required>
    <label>Body</label><textarea name="body" required rows="5"></textarea>
    <label>Type</label><select name="review_type"><option>architecture</option><option>decision</option><option>risk</option><option>clarification</option><option>evidence</option><option>approval_request</option></select>
    <label>Priority</label><select name="priority"><option>normal</option><option>high</option><option>critical</option><option>low</option></select>
    <label>Task public ID</label><input name="task" placeholder="TR-000001">
    <button>Add review</button></form></section>
    """
    return page("Add review", body)


def doctor_page(service: FounderAssistantService) -> str:
    return page("Doctor", _doctor_block(service.doctor()))


def error_page(message: str, status: int = 400) -> tuple[int, str]:
    return status, page("Error", "", error=message)


def _doctor_block(doctor: dict[str, object]) -> str:
    status = "OK" if doctor["ok"] else "FAIL"
    css = "ok" if doctor["ok"] else "fail"
    return (
        f"<section><h2>Doctor: <span class='{css}'>{status}</span></h2>"
        f"<p>Schema: {esc(doctor['schema_name'] or 'unknown')} v{esc(doctor['schema_version'] if doctor['schema_version'] is not None else 'unknown')} "
        f"current={esc(doctor['schema_current'])}</p><p>Reason: {esc(doctor['schema_reason'])}</p></section>"
    )


def _init_form() -> str:
    return "<section><h2>Initialize runtime</h2><form method='post' action='/init'><button>Initialize</button></form></section>"


def _panel(title: str, rows: list[str]) -> str:
    return f"<section><h2>{esc(title)}</h2>{items(rows)}</section>"


def _task_rows(rows: list[dict[str, object]]) -> list[str]:
    return [f"<strong>{esc(row['public_no'])}</strong> [{esc(row['status'])}] {esc(row['title'])}" for row in rows]


def _review_rows(rows: list[dict[str, object]]) -> list[str]:
    return [f"<strong>{esc(row['public_id'])}</strong> [{esc(row['priority'])}/{esc(row['review_type'])}] {esc(row['title'])}" for row in rows]


def _decision_rows(rows: list[dict[str, object]]) -> list[str]:
    return [f"<strong>{esc(row['public_id'])}</strong> [{esc(row['status'])}] {esc(row['title'])}" for row in rows]


def _event_rows(rows: list[dict[str, object]], id_key: str) -> list[str]:
    return [f"{esc(row[id_key])} {esc(row['event_type'])}: {esc(row['summary'])}" for row in rows]

