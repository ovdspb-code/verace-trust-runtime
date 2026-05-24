"""Local founder workbench CLI."""

from __future__ import annotations

import argparse
import sqlite3
import sys

from verace_runtime.workbench import commands


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="verace")
    parser.add_argument("--db", default=None, help="SQLite runtime DB path")
    sub = parser.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", default=argparse.SUPPRESS, help="SQLite runtime DB path")
    common.add_argument("--principal", default=commands.DEFAULT_PRINCIPAL)
    common.add_argument("--contour", default=commands.DEFAULT_CONTOUR)

    sub.add_parser("init", parents=[common])
    sub.add_parser("brief", parents=[common])
    add = sub.add_parser("add", parents=[common])
    add.add_argument("text")
    decision = sub.add_parser("decision", parents=[common])
    decision.add_argument("title")
    decision.add_argument("--text", required=True)

    review = sub.add_parser("review")
    review_sub = review.add_subparsers(dest="review_command", required=True)
    review_add = review_sub.add_parser("add", parents=[common])
    review_add.add_argument("title")
    review_add.add_argument("--body", required=True)
    review_add.add_argument("--type", dest="review_type", required=True)
    review_add.add_argument("--priority", required=True)
    review_add.add_argument("--task")
    review_list = review_sub.add_parser("list", parents=[common])
    review_list.add_argument("--status", default="open", choices=["open", "resolved", "dismissed", "all"])
    review_resolve = review_sub.add_parser("resolve", parents=[common])
    review_resolve.add_argument("review")
    review_resolve.add_argument("--resolution", required=True)
    review_resolve.add_argument("--status", default="resolved", choices=["resolved", "dismissed"])

    sub.add_parser("doctor", parents=[common])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        print(_dispatch(args))
        return 0
    except (RuntimeError, sqlite3.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _dispatch(args: argparse.Namespace) -> str:
    if args.command == "init":
        return commands.init(args)
    if args.command == "brief":
        return commands.brief(args)
    if args.command == "add":
        return commands.add(args)
    if args.command == "decision":
        return commands.decision(args)
    if args.command == "doctor":
        return commands.doctor(args)
    if args.command == "review" and args.review_command == "add":
        return commands.review_add(args)
    if args.command == "review" and args.review_command == "list":
        return commands.review_list(args)
    if args.command == "review" and args.review_command == "resolve":
        return commands.review_resolve(args)
    raise RuntimeError("Unsupported command")


if __name__ == "__main__":
    raise SystemExit(main())
