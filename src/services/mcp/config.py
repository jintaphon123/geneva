from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class McpServerConfig:
    name: str
    transport: Literal["stdio", "http"]
    command: list[str] | None
    url: str | None
    env: dict[str, str] = field(default_factory=dict)


_SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def load_mcp_config() -> list[McpServerConfig]:
    settings = _read_settings()
    raw_servers = settings.get("mcp_servers", {})
    if isinstance(raw_servers, list):
        return [_normalize_server(f"server-{index}", entry) for index, entry in enumerate(raw_servers)]
    if not isinstance(raw_servers, dict):
        return []
    return [_normalize_server(name, entry) for name, entry in raw_servers.items()]


def get_configured_servers() -> list[McpServerConfig]:
    return load_mcp_config()


def add_server_config(config: McpServerConfig) -> None:
    settings = _read_settings()
    servers = settings.setdefault("mcp_servers", {})
    if not isinstance(servers, dict):
        servers = {}
        settings["mcp_servers"] = servers
    payload = asdict(config)
    payload.pop("name", None)
    servers[config.name] = payload
    _write_settings(settings)


def remove_server_config(name: str) -> None:
    settings = _read_settings()
    servers = settings.get("mcp_servers", {})
    if isinstance(servers, dict) and name in servers:
        del servers[name]
        _write_settings(settings)


def _normalize_server(name: str, entry: object) -> McpServerConfig:
    if not isinstance(entry, dict):
        raise ValueError(f"Invalid MCP config for server '{name}'")

    url = entry.get("url")
    transport = entry.get("transport")
    if transport not in {"stdio", "http"}:
        transport = "http" if url else "stdio"

    command = entry.get("command")
    if isinstance(command, str):
        args = entry.get("args") or []
        if not isinstance(args, list):
            raise ValueError(f"Invalid args for MCP server '{name}'")
        command = [command, *[str(arg) for arg in args]]
    elif isinstance(command, list):
        command = [str(part) for part in command]
    else:
        command = None

    env = entry.get("env") or {}
    if not isinstance(env, dict):
        raise ValueError(f"Invalid env for MCP server '{name}'")

    return McpServerConfig(
        name=name,
        transport=transport,
        command=command,
        url=str(url) if url else None,
        env={str(key): str(value) for key, value in env.items()},
    )


def _read_settings() -> dict:
    if not _SETTINGS_PATH.exists():
        return {}
    try:
        data = json.loads(_SETTINGS_PATH.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {_SETTINGS_PATH}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected object at {_SETTINGS_PATH}")
    return data


def _write_settings(settings: dict) -> None:
    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SETTINGS_PATH.write_text(json.dumps(settings, indent=2, sort_keys=True))
