from __future__ import annotations

import os
import sqlite3
import subprocess
import sys


def run_cli(db_path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    return subprocess.run(
        [sys.executable, "-m", "verace_runtime.cli", *args, "--db", str(db_path)],
        check=check,
        cwd=os.getcwd(),
        env=env,
        text=True,
        capture_output=True,
    )


def test_schema_status_cli_reports_healthy_db(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    run_cli(db_path, "init")

    result = run_cli(db_path, "schema-status")

    assert "Schema: verace_runtime" in result.stdout
    assert "Version: 1" in result.stdout
    assert "Known: True" in result.stdout
    assert "Current: True" in result.stdout
    assert "Migration required: False" in result.stdout


def test_doctor_cli_includes_schema_state(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    run_cli(db_path, "init")

    result = run_cli(db_path, "doctor")

    assert "Doctor: OK" in result.stdout
    assert "Schema: verace_runtime" in result.stdout
    assert "Version: 1" in result.stdout


def test_schema_status_cli_reports_unsafe_db(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE orphan_state(id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO orphan_state(id) VALUES ('x')")

    status = run_cli(db_path, "schema-status")
    doctor = run_cli(db_path, "doctor")

    assert "Schema: unknown" in status.stdout
    assert "Current: False" in status.stdout
    assert "Migration required: True" in status.stdout
    assert "Doctor: FAIL" in doctor.stdout
