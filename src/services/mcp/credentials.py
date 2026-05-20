"""
MCP Connector credential storage.
Stores per-connector credentials in ~/.geneva/mcp_credentials.json
with simple obfuscation (NOT crypto-grade - upgrade to keychain for Layer 1).
"""
from __future__ import annotations

import base64
import json
from pathlib import Path

CREDS_PATH = Path.home() / ".geneva" / "mcp_credentials.json"
_OBFUSCATION_KEY = b"geneva_creds_v1"


def _obfuscate(plaintext: str) -> str:
    """XOR obfuscation - not security, just not plaintext on disk."""
    data = plaintext.encode("utf-8")
    key = _OBFUSCATION_KEY
    result = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return base64.b64encode(result).decode("ascii")


def _deobfuscate(encoded: str) -> str:
    data = base64.b64decode(encoded.encode("ascii"))
    key = _OBFUSCATION_KEY
    result = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
    return result.decode("utf-8")


def save_credential(connector_name: str, key: str, value: str) -> None:
    """Store a credential. connector_name e.g. 'google', 'notion', 'github'."""
    creds = _load_all()
    if connector_name not in creds:
        creds[connector_name] = {}
    creds[connector_name][key] = _obfuscate(value)
    _save_all(creds)


def get_credential(connector_name: str, key: str) -> str | None:
    """Retrieve a credential. Returns None if not found."""
    creds = _load_all()
    raw = creds.get(connector_name, {}).get(key)
    if raw is None:
        return None
    try:
        return _deobfuscate(raw)
    except Exception:
        return None


def delete_credential(connector_name: str, key: str | None = None) -> bool:
    """Delete one key or all keys for a connector."""
    creds = _load_all()
    if connector_name not in creds:
        return False
    if key is None:
        del creds[connector_name]
    else:
        creds[connector_name].pop(key, None)
    _save_all(creds)
    return True


def list_connectors() -> list[str]:
    """Return connector names that have stored credentials."""
    return list(_load_all().keys())


def _load_all() -> dict:
    if not CREDS_PATH.exists():
        return {}
    try:
        return json.loads(CREDS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_all(creds: dict) -> None:
    import os

    CREDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CREDS_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(creds, indent=2), encoding="utf-8")
    os.replace(tmp, CREDS_PATH)
