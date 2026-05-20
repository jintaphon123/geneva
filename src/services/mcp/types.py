from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

try:  # pragma: no cover
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[assignment]

from .config import McpServerConfig


@dataclass
class McpToolDef:
    name: str
    description: str
    input_schema: dict


@dataclass
class McpToolResult:
    content: list[dict]
    is_error: bool


@dataclass
class McpServerConnection:
    config: McpServerConfig
    process: asyncio.subprocess.Process | None
    client: httpx.AsyncClient | None
    _request_id: int = 0
    _io_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _auth_token: str | None = None


__all__ = ["McpToolDef", "McpToolResult", "McpServerConnection"]
