from __future__ import annotations

import socket
from pathlib import Path
from urllib.request import urlopen

from verace_runtime.workbench import run_control


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _config(tmp_path: Path, port: int | None = None) -> run_control.ControlConfig:
    runtime = tmp_path / "runtime"
    return run_control.build_config("127.0.0.1", port or _free_port(), str(runtime), str(runtime / "verace.sqlite3"))


def _body(config: run_control.ControlConfig, path: str = "/plan") -> str:
    with urlopen(f"http://{config.host}:{config.port}{path}", timeout=5) as response:
        assert response.status == 200
        return response.read().decode("utf-8")


def test_stale_pid_is_removed_and_status_reports_not_running(tmp_path, capsys):
    config = _config(tmp_path)
    config.runtime_dir.mkdir(parents=True)
    config.pid_file.write_text("999999999")

    assert run_control.status(config) == 1

    assert not config.pid_file.exists()
    assert "stale" in capsys.readouterr().out


def test_start_creates_pid_and_server_answers_plan(tmp_path):
    config = _config(tmp_path)
    try:
        assert run_control.start(config) == 0
        assert config.pid_file.exists()
        body = _body(config)
        assert "План проекта" in body
        assert "Traceback" not in body
    finally:
        run_control.stop(config)


def test_second_start_reuses_existing_server(tmp_path):
    config = _config(tmp_path)
    try:
        assert run_control.start(config) == 0
        first_pid = config.pid_file.read_text().strip()
        assert run_control.start(config) == 0
        second_pid = config.pid_file.read_text().strip()
    finally:
        run_control.stop(config)

    assert first_pid == second_pid


def test_open_calls_browser_after_health_ok(tmp_path, monkeypatch):
    config = _config(tmp_path)
    opened: list[str] = []
    monkeypatch.setattr(run_control.webbrowser, "open", lambda url: opened.append(url) or True)
    try:
        assert run_control.open_workbench(config) == 0
    finally:
        run_control.stop(config)

    assert opened == [config.plan_url]


def test_stop_terminates_own_process_and_removes_pid(tmp_path):
    config = _config(tmp_path)

    assert run_control.start(config) == 0
    pid = int(config.pid_file.read_text())
    assert run_control._pid_alive(pid)
    assert run_control.stop(config) == 0

    assert not config.pid_file.exists()
    assert not run_control._pid_alive(pid)


def test_unknown_port_conflict_fails_explicitly(tmp_path, capsys):
    port = _free_port()
    config = _config(tmp_path, port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", port))
        sock.listen(1)

        assert run_control.start(config) == 1

    assert "port conflict" in capsys.readouterr().out
    assert not config.pid_file.exists()


def test_control_refuses_non_localhost_host(tmp_path, capsys):
    rc = run_control.main(["status", "--host", "0.0.0.0", "--runtime-dir", str(tmp_path)])

    assert rc == 1
    assert "127.0.0.1" in capsys.readouterr().out
