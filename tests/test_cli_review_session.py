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


def test_cli_review_and_session_commands(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    run_cli(db_path, "init")
    ingest = run_cli(db_path, "ingest-message", "--principal", "oleg", "--contour", "verace_project", "--text", "Synthetic task")
    task_no = next(line.split(": ", 1)[1] for line in ingest.stdout.splitlines() if line.startswith("Task created:"))
    review = run_cli(
        db_path,
        "add-review",
        "--principal",
        "oleg",
        "--contour",
        "verace_project",
        "--title",
        "CLI review",
        "--body",
        "Synthetic body.",
        "--review-type",
        "architecture",
        "--priority",
        "high",
        "--task",
        task_no,
    )
    review_id = next(line.split(": ", 1)[1] for line in review.stdout.splitlines() if line.startswith("Review recorded:"))

    reviews = run_cli(db_path, "reviews")
    resolved = run_cli(db_path, "resolve-review", "--review", review_id, "--resolution", "Synthetic resolution.")
    brief = run_cli(db_path, "session-brief")
    doctor = run_cli(db_path, "doctor")

    assert "Review recorded: REV-" in review.stdout
    assert review_id in reviews.stdout
    assert "Status: resolved" in resolved.stdout
    assert "Session brief" in brief.stdout
    assert "Doctor: OK" in doctor.stdout
