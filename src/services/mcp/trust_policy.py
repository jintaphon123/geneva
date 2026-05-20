"""
MCP Server Approval Policy.
Tracks which MCP servers have been approved by the user.
Unapproved servers are denied connection by default.
"""
from __future__ import annotations

import json
from pathlib import Path

TRUST_PATH = Path.home() / ".geneva" / "mcp_trusted_servers.json"


def is_trusted(server_url: str) -> bool:
    """Return True if this server URL has been approved."""
    return server_url in _load()


def approve(server_url: str, label: str = "") -> None:
    """Mark a server as trusted. label is human-readable name."""
    data = _load()
    data[server_url] = {"approved": True, "label": label}
    _save(data)


def revoke(server_url: str) -> bool:
    """Remove trust for a server. Returns True if was trusted."""
    data = _load()
    if server_url not in data:
        return False
    del data[server_url]
    _save(data)
    return True


def list_trusted() -> list[dict]:
    """Return list of trusted server dicts: [{"url": ..., "label": ...}]"""
    return [{"url": url, **info} for url, info in _load().items()]


def require_trust(server_url: str) -> None:
    """Raise PermissionError if server is not trusted."""
    if not is_trusted(server_url):
        raise PermissionError(
            f"MCP server '{server_url}' has not been approved. "
            f"Call trust_policy.approve('{server_url}') first."
        )


def _load() -> dict:
    if not TRUST_PATH.exists():
        return {}
    try:
        return json.loads(TRUST_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict) -> None:
    import os

    TRUST_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = TRUST_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, TRUST_PATH)
