"""SeekDB CI helper to start/stop a local instance."""

from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree

import pymysql
import rpmfile


def log(message: str) -> None:
    print(message, flush=True)


def die(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr, flush=True)
    sys.exit(1)


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    rpm_url: str
    cache_dir: Path
    rpm_path: Path
    extract_dir: Path
    data_dir: Path

    host: str
    port: int
    user: str
    password: str

    memory_limit: str
    cpu_count: int
    datafile_size: str
    datafile_next: str
    datafile_maxsize: str
    log_disk_size: str
    startup_timeout_seconds: int


def load_settings() -> Settings:
    base_dir = Path(os.getenv("SEEKDB_CI_DIR", Path.cwd() / ".seekdb-ci")).resolve()
    rpm_url = os.getenv(
        "SEEKDB_RPM_URL",
        "https://mirrors.oceanbase.com/community/stable/el/9/x86_64/seekdb-1.0.1.0-100000392025122619.el9.x86_64.rpm",
    )
    cache_dir = base_dir / "cache"
    rpm_path = cache_dir / "seekdb.rpm"
    extract_dir = base_dir / "seekdb-root"
    data_dir = base_dir / "data"

    host = os.getenv("SEEKDB_HOST", "127.0.0.1")
    port = int(os.getenv("SEEKDB_PORT", "2881"))
    user = os.getenv("SEEKDB_USER", "root")
    password = os.getenv("SEEKDB_PASSWORD", "")

    return Settings(
        base_dir=base_dir,
        rpm_url=rpm_url,
        cache_dir=cache_dir,
        rpm_path=rpm_path,
        extract_dir=extract_dir,
        data_dir=data_dir,
        host=host,
        port=port,
        user=user,
        password=password,
        memory_limit=os.getenv("SEEKDB_MEMORY_LIMIT", "2G"),
        cpu_count=int(os.getenv("SEEKDB_CPU_COUNT", "2")),
        datafile_size=os.getenv("SEEKDB_DATAFILE_SIZE", "2G"),
        datafile_next=os.getenv("SEEKDB_DATAFILE_NEXT", "2G"),
        datafile_maxsize=os.getenv("SEEKDB_DATAFILE_MAXSIZE", "10G"),
        log_disk_size=os.getenv("SEEKDB_LOG_DISK_SIZE", "2G"),
        startup_timeout_seconds=int(os.getenv("SEEKDB_STARTUP_TIMEOUT", "60")),
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def observer_bin(settings: Settings) -> Path:
    return settings.extract_dir / "usr" / "bin" / "observer"


def pid_file(settings: Settings) -> Path:
    return settings.data_dir / "observer.pid"


def log_file(settings: Settings) -> Path:
    return settings.data_dir / "observer.log"


def port_open(settings: Settings) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.5)
        try:
            sock.connect((settings.host, settings.port))
        except OSError:
            return False
        else:
            return True


def wait_for_port(settings: Settings) -> None:
    deadline = time.time() + settings.startup_timeout_seconds
    while time.time() < deadline:
        if port_open(settings):
            return
        time.sleep(1)
    die("seekdb did not open the port in time")


def wait_for_select_one(settings: Settings) -> None:
    deadline = time.time() + settings.startup_timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            conn = pymysql.connect(
                host=settings.host,
                port=settings.port,
                user=settings.user,
                password=settings.password,
                connect_timeout=2,
            )
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            conn.close()
        except pymysql.MySQLError as exc:
            last_error = exc
            time.sleep(1)
        else:
            log("SELECT 1 OK")
            return
    die(f"SELECT 1 failed: {last_error}")


def download_rpm(settings: Settings) -> None:
    if settings.rpm_path.exists():
        log(f"RPM already exists: {settings.rpm_path}")
        return

    ensure_dir(settings.cache_dir)
    log("Downloading seekdb RPM...")
    urllib.request.urlretrieve(settings.rpm_url, settings.rpm_path)  # noqa: S310
    log(f"Downloaded: {settings.rpm_path}")


def extract_rpm(settings: Settings) -> None:
    if settings.extract_dir.exists():
        rmtree(settings.extract_dir)
    ensure_dir(settings.extract_dir)

    log("Extracting RPM...")
    with rpmfile.open(settings.rpm_path) as rpm:
        for member in rpm.getmembers():
            target_path = settings.extract_dir / member.name.lstrip("/")
            if member.isdir:
                target_path.mkdir(parents=True, exist_ok=True)
                continue
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with rpm.extractfile(member) as src, target_path.open("wb") as dst:
                dst.write(src.read())

    observer = observer_bin(settings)
    observer.chmod(0o755)
    log(f"Extracted to: {settings.extract_dir}")


def ensure_extracted(settings: Settings) -> None:
    if observer_bin(settings).exists():
        return
    download_rpm(settings)
    extract_rpm(settings)


def resolve_libaio_dir() -> str:
    candidates = [
        "/usr/lib/x86_64-linux-gnu",
        "/usr/lib64",
        "/usr/lib",
    ]
    for path in candidates:
        if Path(path, "libaio.so.1").exists():
            return path
    return ""


def start_observer(settings: Settings) -> None:
    ensure_extracted(settings)

    if port_open(settings):
        if pid_file(settings).exists():
            log("seekdb already running")
            return
        die(f"port {settings.port} already in use")

    ensure_dir(settings.data_dir / "store" / "redo")
    ensure_dir(settings.data_dir / "log")

    ld_path = resolve_libaio_dir()
    if not ld_path:
        die("libaio.so.1 not found; install libaio1")

    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = f"{ld_path}:{env['LD_LIBRARY_PATH']}" if env.get("LD_LIBRARY_PATH") else ld_path

    cmd = [
        str(observer_bin(settings)),
        "--nodaemon",
        "--port",
        str(settings.port),
        "--base-dir",
        str(settings.data_dir),
        "--data-dir",
        str(settings.data_dir / "store"),
        "--redo-dir",
        str(settings.data_dir / "store" / "redo"),
        "--parameter",
        f"datafile_size={settings.datafile_size}",
        "--parameter",
        f"datafile_next={settings.datafile_next}",
        "--parameter",
        f"datafile_maxsize={settings.datafile_maxsize}",
        "--parameter",
        f"log_disk_size={settings.log_disk_size}",
        "--parameter",
        f"memory_limit={settings.memory_limit}",
        "--parameter",
        f"cpu_count={settings.cpu_count}",
    ]

    with log_file(settings).open("ab") as log_fp:
        proc = subprocess.Popen(  # noqa: S603
            cmd,
            cwd=str(settings.data_dir),
            env=env,
            stdout=log_fp,
            stderr=log_fp,
            start_new_session=True,
        )

    pid_file(settings).write_text(str(proc.pid))
    log(f"Started seekdb (pid={proc.pid}) on {settings.host}:{settings.port}")

    wait_for_port(settings)
    wait_for_select_one(settings)


def stop_observer(settings: Settings) -> None:
    if not pid_file(settings).exists():
        log("No pid file found")
        return

    pid_text = pid_file(settings).read_text().strip()
    if not pid_text:
        log("Empty pid file")
        pid_file(settings).unlink(missing_ok=True)
        return

    pid = int(pid_text)
    try:
        os.kill(pid, 0)
    except OSError:
        log("seekdb is not running")
        pid_file(settings).unlink(missing_ok=True)
        return

    log(f"Stopping seekdb (pid={pid})")
    os.kill(pid, signal.SIGTERM)

    for _ in range(30):
        time.sleep(1)
        try:
            os.kill(pid, 0)
        except OSError:
            pid_file(settings).unlink(missing_ok=True)
            log("Stopped")
            return

    die("seekdb did not stop gracefully")


def status_observer(settings: Settings) -> None:
    if pid_file(settings).exists():
        pid_text = pid_file(settings).read_text().strip()
        if pid_text:
            pid = int(pid_text)
            try:
                os.kill(pid, 0)
                log(f"seekdb process: running (pid={pid})")
            except OSError:
                log("seekdb process: stale pid file")
        else:
            log("seekdb process: empty pid file")
    else:
        log("seekdb process: not running")

    log(f"port {settings.port}: {'open' if port_open(settings) else 'closed'}")
    log(f"log file: {log_file(settings)}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="seekdb-ci")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("start", help="Start seekdb and run SELECT 1")
    sub.add_parser("stop", help="Stop seekdb")
    sub.add_parser("status", help="Show process and port status")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    settings = load_settings()

    if args.command == "start":
        start_observer(settings)
        return
    if args.command == "stop":
        stop_observer(settings)
        return
    if args.command == "status":
        status_observer(settings)
        return

    die("Unknown command")


if __name__ == "__main__":
    main()
