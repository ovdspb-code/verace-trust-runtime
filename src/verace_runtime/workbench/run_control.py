"""Internal run-control for the local Founder Workbench server."""

from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_RUNTIME_DIR = ".runtime"
PLAN_PATH = "/plan"


@dataclass(frozen=True)
class ControlConfig:
    host: str
    port: int
    runtime_dir: Path
    db_path: Path
    pid_file: Path
    log_file: Path

    @property
    def plan_url(self) -> str:
        return f"http://{self.host}:{self.port}{PLAN_PATH}"


def build_config(host: str, port: int, runtime_dir: str | None, db_path: str | None) -> ControlConfig:
    if host != DEFAULT_HOST:
        raise RuntimeError("Founder Workbench control only supports 127.0.0.1")
    runtime = Path(runtime_dir or os.environ.get("VERACE_WORKBENCH_RUNTIME_DIR") or DEFAULT_RUNTIME_DIR)
    db = Path(db_path or os.environ.get("VERACE_RUNTIME_DB") or runtime / "verace.sqlite3")
    return ControlConfig(
        host=host,
        port=port,
        runtime_dir=runtime,
        db_path=db,
        pid_file=runtime / "workbench.pid",
        log_file=runtime / "workbench.log",
    )


def status(config: ControlConfig) -> int:
    state, detail = _server_state(config, clean_stale=True)
    print(f"{state}: {detail}")
    return 0 if state in {"running", "running_external"} else 1


def start(config: ControlConfig) -> int:
    config.runtime_dir.mkdir(parents=True, exist_ok=True)
    state, detail = _server_state(config, clean_stale=True)
    if state == "running":
        print(f"running: {detail}")
        return 0
    if state == "running_external":
        print(f"running: existing workbench responds at {config.plan_url}")
        return 0
    if state == "port_conflict":
        print(f"port conflict: {detail}")
        return 1
    if state == "dead":
        print(f"dead: {detail}")
        return 1

    env = os.environ.copy()
    env["VERACE_RUNTIME_DB"] = str(config.db_path)
    with config.log_file.open("ab", buffering=0) as log:
        process = subprocess.Popen(
            [sys.executable, "-m", "verace_runtime.workbench.server", "--host", config.host, "--port", str(config.port)],
            stdout=log,
            stderr=log,
            env=env,
            start_new_session=True,
        )
    config.pid_file.write_text(str(process.pid))
    if _wait_for_health(config):
        print(f"started: {config.plan_url}")
        return 0
    print(f"health check failed: see {config.log_file}")
    return 1


def open_workbench(config: ControlConfig) -> int:
    started = start(config)
    if started != 0:
        return started
    if not _health_ok(config):
        print(f"health check failed: {config.plan_url}")
        return 1
    if not webbrowser.open(config.plan_url):
        print(f"open failed: {config.plan_url}")
        return 1
    print(f"opened: {config.plan_url}")
    return 0


def stop(config: ControlConfig) -> int:
    pid = _read_pid(config.pid_file)
    if pid is None:
        _remove_pid(config.pid_file)
        print("not running: no valid pid")
        return 1
    if not _pid_alive(pid):
        _remove_pid(config.pid_file)
        print("stale: removed stale pid")
        return 1
    if not _pid_owned_workbench(pid):
        _remove_pid(config.pid_file)
        print("unowned pid: removed pid file without stopping process")
        return 1
    _signal_process(pid, signal.SIGTERM)
    for _ in range(30):
        _reap_pid(pid)
        if not _pid_alive(pid) or not _port_open(config.host, config.port):
            _remove_pid(config.pid_file)
            print("stopped")
            return 0
        time.sleep(0.1)
    _signal_process(pid, signal.SIGKILL)
    for _ in range(10):
        _reap_pid(pid)
        if not _pid_alive(pid) or not _port_open(config.host, config.port):
            _remove_pid(config.pid_file)
            print("stopped")
            return 0
        time.sleep(0.1)
    print("stop failed: process did not exit")
    return 1


def restart(config: ControlConfig) -> int:
    stop(config)
    return start(config)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="verace-workbench-control")
    parser.add_argument("command", choices=("start", "open", "status", "stop", "restart"))
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--runtime-dir", default=None)
    parser.add_argument("--db", default=None)
    args = parser.parse_args(argv)
    try:
        config = build_config(args.host, args.port, args.runtime_dir, args.db)
        commands = {
            "start": start,
            "open": open_workbench,
            "status": status,
            "stop": stop,
            "restart": restart,
        }
        return commands[args.command](config)
    except (OSError, RuntimeError, URLError) as exc:
        print(f"error: {exc}")
        return 1


def _server_state(config: ControlConfig, clean_stale: bool) -> tuple[str, str]:
    pid = _read_pid(config.pid_file)
    if pid is not None:
        if _pid_alive(pid):
            if not _pid_owned_workbench(pid):
                if clean_stale:
                    _remove_pid(config.pid_file)
                if _port_open(config.host, config.port):
                    return _port_state_without_pid(config)
                return "unowned", "removed unowned pid" if clean_stale else "pid is not a workbench server"
            if _health_ok(config):
                return "running", f"pid {pid} responds at {config.plan_url}"
            return "dead", f"pid {pid} is alive but {PLAN_PATH} health check failed"
        if clean_stale:
            _remove_pid(config.pid_file)
        if _port_open(config.host, config.port):
            return _port_state_without_pid(config)
        return "stale", "removed stale pid" if clean_stale else "pid is stale"
    if _port_open(config.host, config.port):
        return _port_state_without_pid(config)
    return "not_running", "no workbench server is running"


def _port_state_without_pid(config: ControlConfig) -> tuple[str, str]:
    if _health_ok(config):
        return "running_external", f"workbench responds without pid file at {config.plan_url}"
    return "port_conflict", f"{config.host}:{config.port} is occupied by an unknown process"


def _wait_for_health(config: ControlConfig, attempts: int = 40) -> bool:
    for _ in range(attempts):
        if _health_ok(config):
            return True
        time.sleep(0.1)
    return False


def _health_ok(config: ControlConfig) -> bool:
    try:
        with urlopen(config.plan_url, timeout=0.5) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status == 200 and "План проекта" in body and "Traceback" not in body
    except Exception:
        return False


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except OSError:
        return False


def _read_pid(path: Path) -> int | None:
    try:
        text = path.read_text().strip()
        return int(text) if text else None
    except (FileNotFoundError, ValueError):
        return None


def _remove_pid(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _pid_command(pid: int) -> str:
    proc_cmdline = Path(f"/proc/{pid}/cmdline")
    try:
        raw = proc_cmdline.read_bytes()
        if raw:
            return " ".join(part.decode("utf-8", errors="replace") for part in raw.split(b"\0") if part)
    except OSError:
        pass
    try:
        result = subprocess.run(
            ["ps", "-ww", "-p", str(pid), "-o", "command="],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _pid_owned_workbench(pid: int) -> bool:
    return "verace_runtime.workbench.server" in _pid_command(pid)


def _signal_process(pid: int, sig: int) -> None:
    try:
        os.killpg(pid, sig)
    except OSError:
        try:
            os.kill(pid, sig)
        except OSError:
            pass


def _reap_pid(pid: int) -> None:
    try:
        os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        pass
    except OSError:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
