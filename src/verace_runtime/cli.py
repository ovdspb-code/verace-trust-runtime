"""Command line entrypoint for the Ledger Seed MVP."""

from __future__ import annotations

import argparse
import sqlite3
import sys

from verace_runtime.app.service import FounderAssistantService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="verace-runtime")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", default=".runtime/verace.sqlite3", help="SQLite runtime DB path")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", parents=[common])
    ingest = sub.add_parser("ingest-message", parents=[common])
    ingest.add_argument("--principal", required=True)
    ingest.add_argument("--contour", required=True)
    ingest.add_argument("--text", required=True)
    sub.add_parser("status", parents=[common])
    sub.add_parser("tasks", parents=[common])
    task = sub.add_parser("task", parents=[common])
    task.add_argument("--task", required=True)
    decision = sub.add_parser("record-decision", parents=[common])
    decision.add_argument("--principal", required=True)
    decision.add_argument("--contour", required=True)
    decision.add_argument("--title", required=True)
    decision.add_argument("--text", required=True)
    sub.add_parser("decisions", parents=[common])
    status = sub.add_parser("set-task-status", parents=[common])
    status.add_argument("--task", required=True)
    status.add_argument("--status", required=True)
    status.add_argument("--note", required=True)
    event = sub.add_parser("add-task-event", parents=[common])
    event.add_argument("--task", required=True)
    event.add_argument("--event-type", required=True)
    event.add_argument("--summary", required=True)
    sub.add_parser("project-brief", parents=[common])
    sub.add_parser("doctor", parents=[common])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = FounderAssistantService(args.db)
    try:
        if args.command == "init":
            result = service.init_runtime()
            print(f"Initialized ledger: {args.db}")
            print(f"Principal: {result.principal}")
            print(f"Contour: {result.contour}")
            print(f"Mandate: {result.mandate_public_id}")
            print(f"Receipt: {result.receipt_public_id}")
        elif args.command == "ingest-message":
            result = service.ingest_message(args.principal, args.contour, args.text)
            print(f"Message recorded: {result.message_public_id}")
            if result.task_public_no:
                print(f"Task created: {result.task_public_no}")
            else:
                print("Task created: none")
            print(f"Claim: {result.claim_status}")
            print(f"Receipt: {result.receipt_public_id}")
        elif args.command == "tasks":
            _print_tasks(service)
        elif args.command == "status":
            _print_status(service)
        elif args.command == "task":
            _print_task(service, args.task)
        elif args.command == "doctor":
            _print_doctor(service)
        elif args.command == "record-decision":
            result = service.record_decision(args.principal, args.contour, args.title, args.text)
            print(f"Decision recorded: {result.public_id}")
            print(f"Claim: {result.claim_status}")
            print(f"Receipt: {result.receipt_public_id}")
        elif args.command == "decisions":
            _print_decisions(service)
        elif args.command == "set-task-status":
            result = service.set_task_status(args.task, args.status, args.note)
            print(f"Task updated: {result.task_public_no}")
            print(f"Status: {result.status}")
            print(f"Claim: {result.claim_status}")
            print(f"Receipt: {result.receipt_public_id}")
        elif args.command == "add-task-event":
            result = service.add_task_event(args.task, args.event_type, args.summary)
            print(f"Task event recorded: {result.task_public_no}")
            print(f"Status: {result.status}")
            print(f"Claim: {result.claim_status}")
            print(f"Receipt: {result.receipt_public_id}")
        elif args.command == "project-brief":
            _print_project_brief(service)
        return 0
    except (RuntimeError, sqlite3.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _print_tasks(service: FounderAssistantService) -> None:
    tasks = service.list_tasks()
    if not tasks:
        print("No tasks.")
        return
    for task in tasks:
        print(f"{task.public_no} | {task.status} | {task.contour} | receipts={task.receipt_count} | {task.title}")


def _print_status(service: FounderAssistantService) -> None:
    counts = service.status()
    print("Verace Runtime status")
    print(f"persons={counts['persons']} contours={counts['contours']} mandates={counts['mandates']}")
    print(f"tasks={counts['tasks']} events={counts['task_events']} receipts={counts['receipts']} claims={counts['claims']}")


def _print_task(service: FounderAssistantService, task_ref: str) -> None:
    detail = service.task_detail(task_ref)
    task = detail["task"]
    print(f"Task: {task['public_no']}")
    print(f"Status: {task['status']}")
    print(f"Contour: {task['contour']}")
    print(f"Mandate: {task['mandate_public_id']}")
    print(f"Title: {task['title']}")
    print(f"Receipts: {len(detail['receipts'])}")
    for receipt in detail["receipts"]:
        print(f"- {receipt['public_id']} {receipt['receipt_type']} {receipt['status']}")


def _print_decisions(service: FounderAssistantService) -> None:
    decisions = service.list_decisions()
    if not decisions:
        print("No decisions.")
        return
    for decision in decisions:
        print(f"{decision.public_id} | {decision.status} | {decision.contour} | {decision.created_at} | {decision.title}")


def _print_project_brief(service: FounderAssistantService) -> None:
    brief = service.project_brief()
    counts = brief["counts"]
    print("Project brief")
    print("Doctor: OK" if brief["doctor"]["ok"] else "Doctor: FAIL")
    print(f"tasks={counts['tasks']} decisions={counts['decisions']} receipts={counts['receipts']} claims={counts['claims']}")
    print("Tasks:")
    for task in brief["tasks"]:
        print(f"- {task['public_no']} [{task['status']}] {task['title']}")
    print("Latest decisions:")
    for decision in brief["decisions"]:
        print(f"- {decision['public_id']} [{decision['status']}] {decision['title']}")
    print("Recent events:")
    for event in brief["events"]:
        print(f"- {event['public_no']} {event['event_type']}: {event['summary']}")


def _print_doctor(service: FounderAssistantService) -> None:
    result = service.doctor()
    print("Doctor: OK" if result["ok"] else "Doctor: FAIL")
    counts = result["counts"]
    print(f"schema_ok={result['schema_ok']} pragma_ok={result['pragma_ok']} integrity_ok={result['integrity_ok']}")
    print(f"foreign_keys_ok={result['foreign_keys_ok']} seed_ok={result['seed_ok']}")
    print(f"claim_receipt_ok={result['claim_receipt_ok']} task_event_receipt_ok={result['task_event_receipt_ok']} outbox_receipt_ok={result['outbox_receipt_ok']}")
    print(f"decision_receipt_ok={result['decision_receipt_ok']} decision_claim_ok={result['decision_claim_ok']}")
    print(f"tables={len(result['required_tables'])} tasks={counts.get('tasks', 0)} receipts={counts.get('receipts', 0)}")


if __name__ == "__main__":
    raise SystemExit(main())
