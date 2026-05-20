from __future__ import annotations

import shutil
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

from src.commands import register

_GENEVA_DIR = Path.home() / ".geneva"
_BACKUP_DIR = _GENEVA_DIR / "backups"


@register(name="backup", description="Backup or restore ~/.geneva data.")
async def run(args: list[str]) -> str | None:
    sub = args[0] if args else "create"
    try:
        if sub == "create":
            return _create()
        if sub == "list":
            return _list()
        if sub == "restore":
            if len(args) < 2:
                return "Usage: /backup restore <backup-path>"
            return _restore(args[1])
        return f"Unknown subcommand: {sub}. Use: create | list | restore <path>"
    except Exception as exc:
        return f"Backup error: {exc}"


def _create() -> str:
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = _BACKUP_DIR / f"geneva-backup-{ts}.tar.gz"
    with tarfile.open(out_path, "w:gz") as tar:
        for item in _GENEVA_DIR.iterdir():
            if item.name in {"backups", ".consolidate-lock"}:
                continue
            tar.add(item, arcname=item.name)
    size_mb = out_path.stat().st_size / 1_048_576
    return f"Backup created: {out_path} ({size_mb:.1f} MB)"


def _list() -> str:
    if not _BACKUP_DIR.exists():
        return "No backups found."
    files = sorted(_BACKUP_DIR.glob("*.tar.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return "No backups found."
    lines = []
    for i, f in enumerate(files[:10], 1):
        st = f.stat()
        size_mb = st.st_size / 1_048_576
        mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
        lines.append(f"{i}. {f.name}  {size_mb:.1f} MB  {mtime}")
    return "\n".join(lines)


def _restore(backup_path: str) -> str:
    src = Path(backup_path).expanduser()
    if not src.exists():
        return f"Backup not found: {src}"
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(src, "r:gz") as tar:
            tar.extractall(tmp)
        for item in Path(tmp).iterdir():
            dest = _GENEVA_DIR / item.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            shutil.move(str(item), str(dest))
    return f"Restore complete from {src}"
