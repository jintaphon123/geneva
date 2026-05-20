from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
FASTAPI_CACHE = APP_ROOT / ".qa-cache" / "fastapi-contracts"
TEST_PACKAGES = [
    "fastapi>=0.115.0",
    "uvicorn>=0.30.0",
    "httpx>=0.27.0",
]


def main() -> int:
    env = ensure_fastapi_env()
    command = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_geneva_web.py",
        "-q",
        "-rs",
    ]
    completed = subprocess.run(command, cwd=APP_ROOT, env=env, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if completed.returncode != 0:
        return completed.returncode
    combined = f"{completed.stdout}\n{completed.stderr}".lower()
    if "skipped" in combined:
        print("FastAPI contract gate failed: web tests still skipped TestClient coverage.", file=sys.stderr)
        return 1
    return 0


def ensure_fastapi_env() -> dict[str, str]:
    env = dict(os.environ)
    if modules_available(["fastapi", "httpx"]):
        return env_with_pythonpath(env, APP_ROOT)

    FASTAPI_CACHE.mkdir(parents=True, exist_ok=True)
    if not modules_available(["fastapi", "httpx"], FASTAPI_CACHE):
        print(f"Installing FastAPI TestClient dependencies into {FASTAPI_CACHE}", flush=True)
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--quiet",
                "--target",
                str(FASTAPI_CACHE),
                *TEST_PACKAGES,
            ],
            cwd=APP_ROOT,
        )

    return env_with_pythonpath(env, FASTAPI_CACHE, APP_ROOT)


def modules_available(modules: list[str], path: Path | None = None) -> bool:
    if path is None:
        return all(importlib.util.find_spec(module) is not None for module in modules)

    path_text = str(path)
    sys.path.insert(0, path_text)
    try:
        return all(importlib.util.find_spec(module) is not None for module in modules)
    finally:
        try:
            sys.path.remove(path_text)
        except ValueError:
            pass


def env_with_pythonpath(env: dict[str, str], *paths: Path) -> dict[str, str]:
    existing = env.get("PYTHONPATH")
    parts = [str(path) for path in paths]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


if __name__ == "__main__":
    raise SystemExit(main())
