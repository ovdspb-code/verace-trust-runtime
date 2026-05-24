from __future__ import annotations

import os
import subprocess


def run_verace(db_path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["VERACE_RUNTIME_DB"] = str(db_path)
    return subprocess.run(["verace", *args], check=True, env=env, text=True, capture_output=True)


def test_workbench_state_changes_use_receipt_rendered_output(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    run_verace(db_path, "init")

    task = run_verace(db_path, "add", "Synthetic task")
    decision = run_verace(db_path, "decision", "Rendered decision", "--text", "Synthetic decision.")
    review = run_verace(db_path, "review", "add", "Rendered review", "--body", "Body.", "--type", "risk", "--priority", "normal")
    dismissed = run_verace(db_path, "review", "resolve", "REV-000001", "--resolution", "Not needed.", "--status", "dismissed")

    for output in (task.stdout, decision.stdout, review.stdout, dismissed.stdout):
        assert "Receipt: RCPT-" in output
    assert "Task TR-000001 was recorded in the ledger." in task.stdout
    assert "Decision DEC-000001 was recorded in the ledger." in decision.stdout
    assert "Review REV-000001 was created." in review.stdout
    assert "Review REV-000001 was dismissed." in dismissed.stdout


def test_workbench_db_flag_overrides_env(tmp_path):
    env_db = tmp_path / "env.sqlite3"
    flag_db = tmp_path / "flag.sqlite3"
    env = os.environ.copy()
    env["VERACE_RUNTIME_DB"] = str(env_db)

    result = subprocess.run(["verace", "--db", str(flag_db), "init"], check=True, env=env, text=True, capture_output=True)

    assert f"Runtime DB: {flag_db}" in result.stdout
    assert flag_db.exists()
    assert not env_db.exists()

