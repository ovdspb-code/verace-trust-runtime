from __future__ import annotations

import os
import subprocess
import sys


def run_cli(db_path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    return subprocess.run(
        [sys.executable, "-m", "verace_runtime.cli", *args, "--db", str(db_path)],
        check=True,
        cwd=os.getcwd(),
        env=env,
        text=True,
        capture_output=True,
    )


def test_cli_project_memory_commands(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    run_cli(db_path, "init")
    ingest = run_cli(db_path, "ingest-message", "--principal", "oleg", "--contour", "verace_project", "--text", "Synthetic task")
    task_no = next(line.split(": ", 1)[1] for line in ingest.stdout.splitlines() if line.startswith("Task created:"))

    decision = run_cli(db_path, "record-decision", "--principal", "oleg", "--contour", "verace_project", "--title", "Test decision", "--text", "Synthetic decision.")
    decisions = run_cli(db_path, "decisions")
    status = run_cli(db_path, "set-task-status", "--task", task_no, "--status", "waiting", "--note", "Synthetic waiting")
    event = run_cli(db_path, "add-task-event", "--task", task_no, "--event-type", "review.note", "--summary", "Synthetic event")
    brief = run_cli(db_path, "project-brief")

    assert "Decision recorded: DEC-" in decision.stdout
    assert "Test decision" in decisions.stdout
    assert "Status: waiting" in status.stdout
    assert "Task event recorded" in event.stdout
    assert "Project brief" in brief.stdout
    assert task_no in brief.stdout
