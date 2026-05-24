from __future__ import annotations

import os
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


def test_cli_render_claim_supported_classes(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    run_cli(db_path, "init")
    run_cli(db_path, "ingest-message", "--principal", "oleg", "--contour", "verace_project", "--text", "Synthetic task")
    decision = run_cli(
        db_path,
        "record-decision",
        "--principal",
        "oleg",
        "--contour",
        "verace_project",
        "--title",
        "Renderer decision",
        "--text",
        "Synthetic decision.",
    )
    decision_id = next(line.split(": ", 1)[1] for line in decision.stdout.splitlines() if line.startswith("Decision recorded:"))
    review = run_cli(db_path, "add-review", "--principal", "oleg", "--contour", "verace_project", "--title", "Review", "--body", "Body.", "--review-type", "risk", "--priority", "high")
    review_id = next(line.split(": ", 1)[1] for line in review.stdout.splitlines() if line.startswith("Review recorded:"))
    run_cli(db_path, "resolve-review", "--review", review_id, "--resolution", "Synthetic resolution.")

    task = run_cli(db_path, "render-claim", "--claim-class", "task_recorded", "--subject", "TR-000001")
    decision_render = run_cli(db_path, "render-claim", "--claim-class", "decision_recorded", "--subject", decision_id)
    review_render = run_cli(db_path, "render-claim", "--claim-class", "review_resolved", "--subject", review_id)
    schema = run_cli(db_path, "render-claim", "--claim-class", "schema_healthy")

    assert "Task TR-000001 was recorded" in task.stdout
    assert f"Decision {decision_id} was recorded" in decision_render.stdout
    assert f"Review {review_id} was resolved" in review_render.stdout
    assert "Runtime schema is healthy" in schema.stdout


def test_cli_render_claim_fails_cleanly_for_unsupported_class(tmp_path):
    db_path = tmp_path / "runtime.sqlite3"
    run_cli(db_path, "init")

    result = run_cli(db_path, "render-claim", "--claim-class", "made_up", "--subject", "x", check=False)

    assert result.returncode == 2
    assert "cannot render made_up" in result.stderr
    assert "Traceback" not in result.stderr

