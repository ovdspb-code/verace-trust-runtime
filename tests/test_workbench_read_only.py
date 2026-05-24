from __future__ import annotations

import os
import subprocess

from verace_runtime.app.service import FounderAssistantService


def run_verace(db_path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["VERACE_RUNTIME_DB"] = str(db_path)
    return subprocess.run(["verace", *args], check=True, env=env, text=True, capture_output=True)


def test_workbench_read_only_commands_do_not_mutate_status_counts(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    run_verace(db_path, "init")
    run_verace(db_path, "add", "Synthetic task")
    run_verace(db_path, "review", "add", "Review", "--body", "Body.", "--type", "architecture", "--priority", "high")
    service = FounderAssistantService(db_path)

    before = service.status()
    run_verace(db_path, "brief")
    run_verace(db_path, "review", "list")
    run_verace(db_path, "doctor")
    after = service.status()

    assert after == before

