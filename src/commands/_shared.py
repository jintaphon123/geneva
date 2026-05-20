from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from src import config as app_config
from src.bootstrap import state
from src.permissions import ToolPermissionContext
from src.providers import get_provider_class
from src.session_store import DEFAULT_SESSION_DIR, StoredSession, load_session


def mask_secret(value: str | None) -> str:
    if not value:
        return "missing"
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def format_table(rows: list[tuple[str, str]]) -> str:
    if not rows:
        return ""
    width = max(len(left) for left, _ in rows)
    return "\n".join(f"{left.ljust(width)} | {right}" for left, right in rows)


def get_config() -> dict[str, Any]:
    return app_config.load_config()


def save_config(config: dict[str, Any]) -> None:
    app_config.save_config(config)


def get_nested(config: dict[str, Any], dotted_key: str) -> Any:
    current: Any = config
    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_key)
        current = current[part]
    return current


def set_nested(config: dict[str, Any], dotted_key: str, value: Any) -> None:
    parts = dotted_key.split(".")
    current = config
    for part in parts[:-1]:
        next_value = current.get(part)
        if not isinstance(next_value, dict):
            next_value = {}
            current[part] = next_value
        current = next_value
    current[parts[-1]] = value


def current_session_id() -> str:
    return state.get_session_id()


def latest_session_id() -> str | None:
    if not DEFAULT_SESSION_DIR.exists():
        return None
    candidates = sorted(DEFAULT_SESSION_DIR.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        return None
    return candidates[0].stem


def load_latest_or_requested_session(session_id: str | None = None) -> StoredSession | None:
    resolved = session_id or latest_session_id()
    if not resolved:
        return None
    try:
        return load_session(resolved)
    except FileNotFoundError:
        return None


def save_session_to_state(session: StoredSession) -> None:
    state.session_id = session.session_id
    setattr(state, "current_session", session)


def session_messages_as_api(session: StoredSession | None) -> list[dict[str, str]]:
    if session is None:
        return []
    return [{"role": "user", "content": message} for message in session.messages]


def get_model_and_provider() -> tuple[str, str]:
    config = get_config()
    provider = os.getenv("MODEL_PROVIDER") or config.get("default_provider", "anthropic")
    provider_cfg = config.get("providers", {}).get(provider, {})
    model = os.getenv("MODEL_ID") or provider_cfg.get("default_model", "unknown")
    return str(model), str(provider)


def set_model_and_provider(model: str, provider: str | None = None) -> tuple[str, str]:
    config = get_config()
    resolved_provider = provider or os.getenv("MODEL_PROVIDER") or config.get("default_provider", "anthropic")
    config["default_provider"] = resolved_provider
    provider_cfg = config.setdefault("providers", {}).setdefault(resolved_provider, {})
    provider_cfg["default_model"] = model
    save_config(config)
    os.environ["MODEL_ID"] = model
    os.environ["MODEL_PROVIDER"] = resolved_provider
    return model, resolved_provider


def get_permission_context() -> ToolPermissionContext:
    current = getattr(state, "permission_context", None)
    if isinstance(current, ToolPermissionContext):
        return current
    current = ToolPermissionContext()
    setattr(state, "permission_context", current)
    return current


def set_permission_context(ctx: ToolPermissionContext) -> None:
    setattr(state, "permission_context", ctx)


def provider_ping(provider_name: str, api_key: str, base_url: str | None, model: str | None) -> str:
    started = time.perf_counter()
    try:
        provider_class = get_provider_class(provider_name)
        provider = provider_class(api_key=api_key, base_url=base_url, model=model)
        provider.chat(
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=8,
        )
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return f"ok ({elapsed_ms} ms)"
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return f"error ({elapsed_ms} ms): {exc}"


def package_status(module_name: str) -> str:
    return "pass" if importlib.util.find_spec(module_name) else "fail"


def shell_status() -> str:
    shell = os.getenv("SHELL") or shutil.which("sh")
    return shell or "missing"


def git_status() -> str:
    return shutil.which("git") or "missing"


def list_feature_env() -> list[tuple[str, str]]:
    items = []
    for key in sorted(os.environ):
        if key.startswith("GENEVA_FEATURE_"):
            items.append((key, os.environ[key]))
    return items


def git_modified_files(cwd: Path | None = None) -> list[str]:
    root = cwd or Path.cwd()
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def parse_jsonish(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered == "null":
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass
    try:
        return json.loads(value)
    except Exception:
        return value


def provider_config(provider_name: str) -> dict[str, Any]:
    config = get_config()
    return dict(config.get("providers", {}).get(provider_name, {}))


def ensure_home_config() -> Path:
    return app_config.get_config_path()
