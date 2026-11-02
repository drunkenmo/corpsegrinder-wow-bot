"""Build an immutable, sha256-pinned release manifest for the stable bot updater."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "corpsegrinder_wow_bot"
OUT = ROOT / "bot_releases" / "latest.json"
FILES = ("bot.py", "community_features.py")
VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")

source = ast.parse((APP / "community_features.py").read_text(encoding="utf-8"))
version = None
for node in source.body:
    if (isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "VERSION"
            for target in node.targets) and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)):
        version = node.value.value

if not version or not VERSION_PATTERN.fullmatch(version):
    raise RuntimeError("VERSION in community_features.py fehlt oder ist ungültig.")

old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else None
if old:
    before = tuple(map(int, old["version"].split(".")))
    after = tuple(map(int, version.split(".")))
    same_files = old.get("files") == {
        filename: hashlib.sha256((APP / filename).read_bytes()).hexdigest()
        for filename in FILES
    }
    if after == before and same_files:
        print("Release bereits aktuell:", version)
        raise SystemExit(0)
    if after <= before:
        raise RuntimeError("Bot-Version muss für jede geänderte Veröffentlichung steigen.")

commit = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
manifest = {
    "version": version,
    "min_bootstrap": "1.0.6",
    "commit": commit,
    "files": {
        filename: hashlib.sha256((APP / filename).read_bytes()).hexdigest()
        for filename in FILES
    },
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("Bot-Update veröffentlicht:", version, "aus Commit", commit)
