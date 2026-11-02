"""Stable Home Assistant container launcher.
Runs bundled bot or verified /data release; restores last known working version.
Never accesses Home Assistant Supervisor permissions or configuration secrets.
"""
import os
from pathlib import Path
import subprocess
import sys
import time

from updater_core import (
    ROOT, LAST_GOOD, BUILTIN_VERSION, ACTIVE, installed, release_dir,
    atomic_json, read_json, rollback,
)

PYTHON = sys.executable
BUNDLED = Path("/app")
READY = ROOT / "worker_ready.json"
READY_TIMEOUT = 90
RESTART_CODE = 42


def good_version():
    payload = read_json(LAST_GOOD, {})
    version = payload.get("version") if isinstance(payload, dict) else None
    return version if version else BUILTIN_VERSION


def start_worker(version):
    origin = BUNDLED if version == BUILTIN_VERSION else release_dir(version)
    script = origin / "bot.py"
    if not script.is_file():
        raise RuntimeError("Bot-Version fehlt: " + version)
    READY.unlink(missing_ok=True)
    env = os.environ.copy()
    # Repository release takes priority over packaged modules.
    env["PYTHONPATH"] = str(origin) + os.pathsep + str(BUNDLED)
    env["CORPSEGRINDER_READY_FILE"] = str(READY)
    env["CORPSEGRINDER_WORKER_VERSION"] = version
    print("[Launcher] Starte Bot-Code " + version, flush=True)
    return subprocess.Popen([PYTHON, "-u", str(script)], env=env)


def ready_from(process, version):
    if not READY.is_file():
        return False
    state = read_json(READY, {})
    return state.get("pid") == process.pid and state.get("version") == version


def stop_worker(process):
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def serve():
    ROOT.mkdir(parents=True, exist_ok=True)
    repeat_failures = 0
    while True:
        version = installed()
        try:
            child = start_worker(version)
        except (OSError, RuntimeError) as exc:
            print("[Launcher] Start fehlgeschlagen: " + str(exc), flush=True)
            if version != good_version():
                rollback("Startdatei fehlt")
            time.sleep(5)
            continue
        successful = False
        deadline = time.monotonic() + READY_TIMEOUT
        try:
            while time.monotonic() < deadline:
                if ready_from(child, version):
                    successful = True
                    break
                if child.poll() is not None:
                    break
                time.sleep(1)
            if successful:
                atomic_json(LAST_GOOD, {"version": version})
                repeat_failures = 0
                print("[Launcher] Discord verbunden: " + version, flush=True)
                exit_code = child.wait()
                if exit_code == RESTART_CODE:
                    print("[Launcher] Update angefordert; Bot wird neu gestartet.", flush=True)
                    continue
                print("[Launcher] Bot beendet (Code " + str(exit_code) + ").", flush=True)
                time.sleep(5)
            else:
                print("[Launcher] Keine erfolgreiche Discord-Anmeldung für Version " + version, flush=True)
                stop_worker(child)
                if version != good_version():
                    previous = rollback("Discord nicht verbunden oder Prozess abgestürzt")
                    print("[Launcher] Rollback auf " + previous, flush=True)
                else:
                    repeat_failures += 1
                    time.sleep(min(5 * repeat_failures, 30))
        except KeyboardInterrupt:
            stop_worker(child)
            raise


if __name__ == "__main__":
    try:
        serve()
    except KeyboardInterrupt:
        sys.exit(0)
