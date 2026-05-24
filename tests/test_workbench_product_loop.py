from __future__ import annotations

import os
import subprocess


def run_verace(db_path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["VERACE_RUNTIME_DB"] = str(db_path)
    return subprocess.run(["verace", *args], check=True, env=env, text=True, capture_output=True)


def test_full_founder_workbench_loop(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"

    run_verace(db_path, "init")
    task = run_verace(db_path, "add", "Подготовить тестовую задачу")
    decision = run_verace(db_path, "decision", "Workbench decision", "--text", "Synthetic decision.")
    review = run_verace(
        db_path,
        "review",
        "add",
        "Review workbench output",
        "--body",
        "Synthetic review item.",
        "--type",
        "architecture",
        "--priority",
        "high",
        "--task",
        "TR-000001",
    )
    listed = run_verace(db_path, "review", "list")
    resolved = run_verace(db_path, "review", "resolve", "REV-000001", "--resolution", "Synthetic resolution.")
    brief = run_verace(db_path, "brief")
    doctor = run_verace(db_path, "doctor")

    assert "Task TR-000001 was recorded in the ledger. Receipt: RCPT-" in task.stdout
    assert "Decision DEC-000001 was recorded in the ledger. Receipt: RCPT-" in decision.stdout
    assert "Review REV-000001 was created. Receipt: RCPT-" in review.stdout
    assert "REV-000001" in listed.stdout
    assert "Review REV-000001 was resolved. Receipt: RCPT-" in resolved.stdout
    assert "Verace session brief" in brief.stdout
    assert "Doctor: OK" in doctor.stdout

