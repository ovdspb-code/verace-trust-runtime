"""Local-only HTTP server for the Founder Workbench."""

from __future__ import annotations

import argparse
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.workbench import actions, views


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_DB = ".runtime/verace.sqlite3"


def make_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, db_path: str | Path | None = None) -> ThreadingHTTPServer:
    if host != DEFAULT_HOST:
        raise RuntimeError("Founder Workbench must bind to 127.0.0.1")
    db = Path(db_path or os.environ.get("VERACE_RUNTIME_DB") or DEFAULT_DB)

    class Handler(WorkbenchHandler):
        runtime_db = db
        dismissed_suggestions: set[str] = set()

    return ThreadingHTTPServer((host, port), Handler)


class WorkbenchHandler(BaseHTTPRequestHandler):
    runtime_db: Path

    def do_GET(self) -> None:
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            query = parse_qs(parsed.query, keep_blank_values=True)
            service = FounderAssistantService(self.runtime_db)
            if path == "/":
                self._html(200, views.dashboard(service))
            elif path == "/plan":
                self._html(200, views.plan_page(service, dismissed=self.dismissed_suggestions))
            elif path == "/documents":
                self._html(200, views.documents_page())
            elif path == "/tasks/new":
                self._html(200, views.task_form())
            elif path == "/decisions/new":
                self._html(200, views.decision_form())
            elif path == "/reviews":
                self._html(200, views.reviews(service))
            elif path == "/reviews/new":
                self._html(200, views.review_form())
            elif path == "/suggestions/task":
                self._html(200, views.suggestion_task_form(_query_key(query)))
            elif path == "/suggestions/review":
                self._html(200, views.suggestion_review_form(_query_key(query)))
            elif path == "/suggestions/decision":
                self._html(200, views.suggestion_decision_form(_query_key(query)))
            elif path == "/suggestions/codex":
                self._html(200, views.codex_task_page(_query_key(query)))
            elif path == "/doctor":
                self._html(200, views.doctor_page(service))
            else:
                self._html(*views.error_page("Page not found", 404))
        except (RuntimeError, sqlite3.Error) as exc:
            self._html(*views.error_page(str(exc), 400))

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path
            form = self._form()
            service = FounderAssistantService(self.runtime_db)
            if path == "/init":
                notice = actions.init_runtime(service)
                self._html(200, views.dashboard(service, notice))
            elif path == "/tasks":
                notice = actions.create_task(service, form.get("text", ""))
                self._html(200, views.dashboard(service, notice))
            elif path == "/decisions":
                notice = actions.record_decision(service, form.get("title", ""), form.get("text", ""))
                self._html(200, views.dashboard(service, notice))
            elif path == "/reviews":
                notice = actions.create_review(service, form.get("title", ""), form.get("body", ""), form.get("review_type", ""), form.get("priority", ""), form.get("task"))
                self._html(200, views.reviews(service, notice))
            elif path.startswith("/reviews/") and path.endswith("/resolve"):
                review = path.split("/")[2]
                notice = actions.resolve_review(service, review, form.get("resolution", ""), form.get("status", "resolved"))
                self._html(200, views.reviews(service, notice))
            elif path == "/suggestions/task":
                notice = actions.create_task(service, form.get("text", ""))
                self._html(200, views.plan_page(service, notice, self.dismissed_suggestions))
            elif path == "/suggestions/review":
                notice = actions.create_review(service, form.get("title", ""), form.get("body", ""), form.get("review_type", "risk"), form.get("priority", "high"), None)
                self._html(200, views.plan_page(service, notice, self.dismissed_suggestions))
            elif path == "/suggestions/decision":
                notice = actions.record_decision(service, form.get("title", ""), form.get("text", ""))
                self._html(200, views.plan_page(service, notice, self.dismissed_suggestions))
            elif path == "/suggestions/dismiss":
                self.dismissed_suggestions.add(form.get("key", ""))
                self._html(200, views.plan_page(service, "Предложение скрыто для этой сессии.", self.dismissed_suggestions))
            else:
                self._html(*views.error_page("Unsupported action", 404))
        except (RuntimeError, sqlite3.Error) as exc:
            self._html(*views.error_page(str(exc), 400))

    def log_message(self, format: str, *args: object) -> None:
        return

    def _form(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        parsed = parse_qs(raw, keep_blank_values=True)
        return {key: values[0].strip() for key, values in parsed.items()}

    def _html(self, status: int, body: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def _query_key(query: dict[str, list[str]]) -> str:
    values = query.get("key", [])
    if not values or not values[0]:
        raise RuntimeError("Suggestion key is required")
    return values[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="verace-workbench")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--db", default=None)
    args = parser.parse_args(argv)
    server = make_server(args.host, args.port, args.db)
    print(f"Verace Founder Workbench: http://{args.host}:{args.port}/")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
