"""Secure, pinned Github bot-code updater. Bundled in HA app; no Supervisor privileges."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.error
import urllib.request

REPO = "drunkenmo/corpsegrinder-wow-bot"
MANIFEST_URL = "https://raw.githubusercontent.com/" + REPO + "/main/bot_releases/latest.json"
RAW_COMMIT_URL = "https://raw.githubusercontent.com/" + REPO + "/{commit}/corpsegrinder_wow_bot/{file}"
ROOT = Path(os.environ.get("CORPSEGRINDER_DATA_DIR", "/data")) / "bot_updates"
RELEASES = ROOT / "releases"
ACTIVE = ROOT / "active.json"
LAST_GOOD = ROOT / "last_good.json"
BUILTIN_VERSION = "1.0.6"
MAX_DOWNLOAD = 500_000
REQUIRED = ("bot.py", "community_features.py")
SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
COMMIT = re.compile(r"^[a-f0-9]{40}$")


class UpdateError(RuntimeError):
    pass


def version_tuple(value):
    if not isinstance(value, str) or not SEMVER.fullmatch(value):
        raise UpdateError("Ungültige Bot-Versionsnummer.")
    return tuple(int(item) for item in value.split("."))


def request_bytes(url, max_size=MAX_DOWNLOAD):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Corpsegrinder-Bot-Updater/1.0",
        "Cache-Control": "no-cache",
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = response.read(max_size + 1)
    except (OSError, urllib.error.URLError) as exc:
        raise UpdateError("GitHub nicht erreichbar oder Datei fehlt.") from exc
    if len(data) > max_size:
        raise UpdateError("Update-Datei überschreitet die Größenbegrenzung.")
    return data


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                     dir=path.parent, delete=False) as f:
        tmp = Path(f.name)
        json.dump(data, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def installed():
    data = read_json(ACTIVE, {"version": BUILTIN_VERSION})
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        return BUILTIN_VERSION
    if version != BUILTIN_VERSION and not release_dir(version).is_dir():
        return BUILTIN_VERSION
    return version


def release_dir(version):
    version_tuple(version)
    return RELEASES / version


def validate_manifest(manifest):
    if not isinstance(manifest, dict):
        raise UpdateError("Ungültiges Update-Manifest.")
    version = manifest.get("version")
    version_tuple(version)
    commit = manifest.get("commit")
    if not isinstance(commit, str) or not COMMIT.fullmatch(commit):
        raise UpdateError("GitHub-Commit im Manifest ungültig.")
    files = manifest.get("files")
    if not isinstance(files, dict) or set(files.keys()) != set(REQUIRED):
        raise UpdateError("Unerwartete Dateien im Update-Manifest.")
    for filename in REQUIRED:
        checksum = files[filename]
        if not isinstance(checksum, str) or not SHA256.fullmatch(checksum):
            raise UpdateError("Ungültige SHA-256-Prüfsumme für " + filename)
    minimum = manifest.get("min_bootstrap", BUILTIN_VERSION)
    if version_tuple(minimum) > version_tuple(BUILTIN_VERSION):
        raise UpdateError("Dieses Update benötigt eine neuere Home-Assistant-App.")
    return manifest


def remote_manifest():
    import time
    # Separate requests to main may be cached by CDN; query busting is harmless.
    url = MANIFEST_URL + "?t=" + str(int(time.time()))
    try:
        manifest = json.loads(request_bytes(url, 20_000).decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise UpdateError("GitHub hat kein gültiges Update-Manifest geliefert.") from exc
    return validate_manifest(manifest)


def check_update():
    manifest = remote_manifest()
    current = installed()
    return manifest, version_tuple(manifest["version"]) > version_tuple(current)


def install_update(manifest):
    """Downloads only two explicitly named files at a pinned Git commit.
    Does not touch Discord token, character DB, or HA Supervisor API.
    """
    validate_manifest(manifest)
    version = manifest["version"]
    if version_tuple(version) <= version_tuple(installed()):
        raise UpdateError("Keine neuere Bot-Version verfügbar.")
    RELEASES.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=RELEASES))
    try:
        for filename in REQUIRED:
            url = RAW_COMMIT_URL.format(commit=manifest["commit"], file=filename)
            payload = request_bytes(url)
            digest = hashlib.sha256(payload).hexdigest()
            if digest != manifest["files"][filename]:
                raise UpdateError("Prüfsumme stimmt nicht: " + filename)
            try:
                compile(payload, filename, "exec")
            except (SyntaxError, ValueError) as exc:
                raise UpdateError("Python-Syntaxfehler in " + filename) from exc
            (staging / filename).write_bytes(payload)
        destination = release_dir(version)
        if destination.exists():
            # A verified release is immutable. Reuse only after checking it.
            for filename in REQUIRED:
                stored = (destination / filename)
                if not stored.exists() or hashlib.sha256(stored.read_bytes()).hexdigest() != manifest["files"][filename]:
                    raise UpdateError("Eine vorhandene Version stimmt nicht mit GitHub überein.")
        else:
            os.rename(staging, destination)
            staging = None
        atomic_json(ACTIVE, {"version": version, "commit": manifest["commit"]})
        return version
    finally:
        if staging is not None and staging.exists():
            import shutil
            shutil.rmtree(staging)


def rollback(reason):
    good = read_json(LAST_GOOD, {})
    value = good.get("version", BUILTIN_VERSION) if isinstance(good, dict) else BUILTIN_VERSION
    if value != BUILTIN_VERSION and not release_dir(value).is_dir():
        value = BUILTIN_VERSION
    atomic_json(ACTIVE, {"version": value, "rollback_reason": str(reason)[:300]})
    return value


def mark_ready():
    marker = os.environ.get("CORPSEGRINDER_READY_FILE")
    if marker:
        path = Path(marker)
        atomic_json(path, {"pid": os.getpid(), "version": os.environ.get("CORPSEGRINDER_WORKER_VERSION")})


if __name__ == "__main__":
    print("Installiert:", installed())
    manifest, available = check_update()
    print("GitHub:", manifest["version"], "Update verfügbar:", available)
