from __future__ import annotations

import os
import subprocess


def run_verace(db_path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["VERACE_RUNTIME_DB"] = str(db_path)
    return subprocess.run(["verace", *args], check=check, env=env, text=True, capture_output=True)


def test_workbench_init_brief_and_doctor(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"

    init = run_verace(db_path, "init")
    brief = run_verace(db_path, "brief")
    doctor = run_verace(db_path, "doctor")

    assert "Runtime receipt: RCPT-" in init.stdout
    assert "Verace session brief" in brief.stdout
    assert "Doctor: OK" in brief.stdout
    assert "Doctor: OK" in doctor.stdout


def test_workbench_unsupported_db_fails_without_traceback(tmp_path):
    db_path = tmp_path / "missing" / "runtime.sqlite3"

    result = run_verace(db_path, "add", "Task before init", check=False)

    assert result.returncode == 2
    assert "error:" in result.stderr
    assert "Traceback" not in result.stderr

