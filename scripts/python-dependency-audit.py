from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = APP_ROOT / "requirements.txt"
AUDIT_CACHE = APP_ROOT / ".qa-cache" / "pip-audit"
PIP_AUDIT_VERSION = "pip-audit>=2.7.3"


def main() -> int:
    if not REQUIREMENTS.exists():
        print(f"requirements file not found: {REQUIREMENTS}", file=sys.stderr)
        return 1

    env = ensure_pip_audit_env()
    command = [
        sys.executable,
        "-m",
        "pip_audit",
        "-r",
        str(REQUIREMENTS),
        "--progress-spinner",
        "off",
        "--strict",
    ]
    return subprocess.call(command, cwd=APP_ROOT, env=env)


def ensure_pip_audit_env() -> dict[str, str]:
    env = dict(os.environ)
    if module_available("pip_audit"):
        return env

    AUDIT_CACHE.mkdir(parents=True, exist_ok=True)
    if not module_available("pip_audit", AUDIT_CACHE):
        print(f"Installing {PIP_AUDIT_VERSION} into {AUDIT_CACHE}", flush=True)
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--quiet",
                "--target",
                str(AUDIT_CACHE),
                PIP_AUDIT_VERSION,
            ],
            cwd=APP_ROOT,
        )

    env["PYTHONPATH"] = prepend_pythonpath(AUDIT_CACHE, env.get("PYTHONPATH"))
    return env


def module_available(module: str, path: Path | None = None) -> bool:
    if path is None:
        return importlib.util.find_spec(module) is not None

    path_text = str(path)
    sys.path.insert(0, path_text)
    try:
        return importlib.util.find_spec(module) is not None
    finally:
        try:
            sys.path.remove(path_text)
        except ValueError:
            pass


def prepend_pythonpath(path: Path, current: str | None) -> str:
    parts = [str(path)]
    if current:
        parts.append(current)
    return os.pathsep.join(parts)


if __name__ == "__main__":
    raise SystemExit(main())
