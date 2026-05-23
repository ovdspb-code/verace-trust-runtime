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


def test_cli_init_ingest_tasks_status_task_doctor(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"

    init = run_cli(db_path, "init")
    ingest = run_cli(
        db_path,
        "ingest-message",
        "--principal",
        "oleg",
        "--contour",
        "verace_project",
        "--text",
        "Подготовить тестовую задачу",
    )
    task_no = next(line.split(": ", 1)[1] for line in ingest.stdout.splitlines() if line.startswith("Task created:"))
    tasks = run_cli(db_path, "tasks")
    status = run_cli(db_path, "status")
    task = run_cli(db_path, "task", "--task", task_no)
    doctor = run_cli(db_path, "doctor")

    assert "Initialized ledger" in init.stdout
    assert "Receipt:" in ingest.stdout
    assert task_no in tasks.stdout
    assert "tasks=1" in status.stdout
    assert "Receipts: 1" in task.stdout
    assert "Doctor: OK" in doctor.stdout
