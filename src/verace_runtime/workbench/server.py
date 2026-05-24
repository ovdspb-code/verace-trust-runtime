"""Local-only HTTP server for the Founder Workbench."""

from __future__ import annotations

import argparse
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from verace_runtime.app.service import FounderAssistantService
from verace_runtime.workbench.context import read_project_context
from verace_runtime.workbench.runtime_state import classify_runtime, reset_first_run_runtime
from verace_runtime.workbench.suggestions import find_suggestion
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
            state = classify_runtime(self.runtime_db)
            if path == "/":
                if state.first_run:
                    self._html(200, views.first_run_dashboard())
                elif state.unsafe:
                    self._html(*views.error_page(f"Unsafe runtime schema: {state.reason}", 200))
                else:
                    self._html(200, views.dashboard(service))
            elif path == "/plan":
                self._html(200, views.plan_page(service, dismissed=self.dismissed_suggestions, first_run=state.first_run))
            elif path == "/documents":
                self._html(200, views.documents_page())
            elif path == "/tasks/new":
                self._html(200, views.first_run_required_page() if state.first_run else views.task_form())
            elif path == "/decisions/new":
                self._html(200, views.first_run_required_page() if state.first_run else views.decision_form())
            elif path == "/reviews":
                self._html(200, views.first_run_required_page() if state.first_run else views.reviews(service))
            elif path == "/reviews/new":
                self._html(200, views.first_run_required_page() if state.first_run else views.review_form())
            elif path == "/suggestions/task":
                self._html(200, views.suggestion_task_form(_query_key(query)))
            elif path == "/suggestions/review":
                self._html(200, views.suggestion_review_form(_query_key(query)))
            elif path == "/suggestions/decision":
                self._html(200, views.suggestion_decision_form(_query_key(query)))
            elif path == "/suggestions/codex":
                self._html(200, views.codex_task_page(_query_key(query)))
            elif path == "/doctor":
                self._html(200, views.first_run_doctor_page() if state.first_run else views.doctor_page(service))
            else:
                self._html(*views.error_page("Page not found", 404))
        except (RuntimeError, sqlite3.Error) as exc:
            self._html(*views.error_page(str(exc), 400))

    def do_POST(self) -> None:
        try:
            path = urlparse(self.path).path
            form = self._form()
            service = FounderAssistantService(self.runtime_db)
            state = classify_runtime(self.runtime_db)
            if path == "/init":
                if state.unsafe:
                    self._html(*views.error_page(f"Unsafe runtime schema: {state.reason}", 400))
                    return
                if state.first_run:
                    reset_first_run_runtime(self.runtime_db)
                    service = FounderAssistantService(self.runtime_db)
                notice = actions.init_runtime(service)
                self._html(200, views.dashboard(service, notice))
            elif path == "/tasks":
                if _needs_ready(state):
                    return self._runtime_not_ready(state, service)
                notice = actions.create_task(service, form.get("text", ""))
                self._html(200, views.dashboard(service, notice))
            elif path == "/decisions":
                if _needs_ready(state):
                    return self._runtime_not_ready(state, service)
                notice = actions.record_decision(service, form.get("title", ""), form.get("text", ""))
                self._html(200, views.dashboard(service, notice))
            elif path == "/reviews":
                if _needs_ready(state):
                    return self._runtime_not_ready(state, service)
                notice = actions.create_review(service, form.get("title", ""), form.get("body", ""), form.get("review_type", ""), form.get("priority", ""), form.get("task"))
                self._html(200, views.reviews(service, notice))
            elif path.startswith("/reviews/") and path.endswith("/resolve"):
                if _needs_ready(state):
                    return self._runtime_not_ready(state, service)
                review = path.split("/")[2]
                notice = actions.resolve_review(service, review, form.get("resolution", ""), form.get("status", "resolved"))
                self._html(200, views.reviews(service, notice))
            elif path == "/suggestions/task":
                if _needs_ready(state):
                    return self._runtime_not_ready(state, service)
                key = _valid_suggestion_key(form)
                notice = actions.create_task(service, form.get("text", ""))
                self.dismissed_suggestions.add(key)
                self._html(200, views.plan_page(service, notice, self.dismissed_suggestions))
            elif path == "/suggestions/review":
                if _needs_ready(state):
                    return self._runtime_not_ready(state, service)
                key = _valid_suggestion_key(form)
                notice = actions.create_review(service, form.get("title", ""), form.get("body", ""), form.get("review_type", "risk"), form.get("priority", "high"), None)
                self.dismissed_suggestions.add(key)
                self._html(200, views.plan_page(service, notice, self.dismissed_suggestions))
            elif path == "/suggestions/decision":
                if _needs_ready(state):
                    return self._runtime_not_ready(state, service)
                key = _valid_suggestion_key(form)
                notice = actions.record_decision(service, form.get("title", ""), form.get("text", ""))
                self.dismissed_suggestions.add(key)
                self._html(200, views.plan_page(service, notice, self.dismissed_suggestions))
            elif path == "/suggestions/dismiss":
                self.dismissed_suggestions.add(_valid_suggestion_key(form))
                self._html(200, views.plan_page(service, "Предложение скрыто для этой сессии.", self.dismissed_suggestions))
            else:
                self._html(*views.error_page("Unsupported action", 404))
        except (RuntimeError, sqlite3.Error) as exc:
            if str(exc) == "Required ledger row not found":
                self._html(200, views.first_run_required_page())
                return
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

    def _runtime_not_ready(self, state, service: FounderAssistantService) -> None:
        if state.first_run:
            self._html(200, views.first_run_required_page("Сначала инициализируйте локальный ledger."))
            return
        self._html(*views.error_page(f"Unsafe runtime schema: {state.reason}", 400))


def _query_key(query: dict[str, list[str]]) -> str:
    values = query.get("key", [])
    if not values or not values[0]:
        raise RuntimeError("Suggestion key is required")
    return values[0]


def _valid_suggestion_key(form: dict[str, str]) -> str:
    key = form.get("key", "")
    if not key:
        raise RuntimeError("Suggestion key is required")
    find_suggestion(read_project_context(), key)
    return key


def _needs_ready(state) -> bool:
    return not state.ready


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
