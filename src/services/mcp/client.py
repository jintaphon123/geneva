from __future__ import annotations

import asyncio
import json
from typing import Any

try:  # pragma: no cover - import guard for lightweight validation environments
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[assignment]

from .config import McpServerConfig
from .types import McpServerConnection, McpToolDef, McpToolResult


_SESSION_AUTH_TOKENS: dict[str, str] = {}


async def connect_to_server(config: McpServerConfig) -> McpServerConnection:
    if config.transport == "stdio":
        if not config.command:
            raise ValueError(f"Stdio MCP server '{config.name}' requires a command")
        env = None
        if config.env:
            env = {**config.env}
        process = await asyncio.create_subprocess_exec(
            *config.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        conn = McpServerConnection(config=config, process=process, client=None)
    else:
        if httpx is None:
            raise RuntimeError("httpx is required for HTTP MCP transports")
        if not config.url:
            raise ValueError(f"HTTP MCP server '{config.name}' requires a URL")
        conn = McpServerConnection(
            config=config,
            process=None,
            client=httpx.AsyncClient(timeout=60.0),
        )

    await _initialize(conn)
    return conn


async def disconnect(conn: McpServerConnection) -> None:
    if conn.client is not None:
        await conn.client.aclose()
    if conn.process is not None:
        if conn.process.returncode is None:
            conn.process.terminate()
            try:
                await asyncio.wait_for(conn.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                conn.process.kill()
                await conn.process.wait()


async def list_tools(conn: McpServerConnection) -> list[McpToolDef]:
    result = await _rpc_request(conn, "tools/list", {})
    tools = result.get("tools", [])
    return [
        McpToolDef(
            name=str(tool.get("name", "")),
            description=str(tool.get("description", "")),
            input_schema=dict(tool.get("inputSchema", {})),
        )
        for tool in tools
        if isinstance(tool, dict)
    ]


async def call_tool(conn: McpServerConnection, name: str, args: dict) -> McpToolResult:
    result = await _rpc_request(conn, "tools/call", {"name": name, "arguments": args})
    return McpToolResult(
        content=list(result.get("content", [])),
        is_error=bool(result.get("isError", result.get("is_error", False))),
    )


async def list_resources(conn: McpServerConnection) -> list[dict]:
    result = await _rpc_request(conn, "resources/list", {})
    return [resource for resource in result.get("resources", []) if isinstance(resource, dict)]


async def read_resource(conn: McpServerConnection, uri: str) -> dict:
    result = await _rpc_request(conn, "resources/read", {"uri": uri})
    if not isinstance(result, dict):
        raise RuntimeError("Invalid MCP resource response")
    return result


async def _initialize(conn: McpServerConnection) -> None:
    await _rpc_request(
        conn,
        "initialize",
        {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "geneva", "version": "0.1.0"},
        },
    )
    await _rpc_notify(conn, "notifications/initialized", {})


async def _rpc_request(conn: McpServerConnection, method: str, params: dict[str, Any]) -> dict[str, Any]:
    async with conn._io_lock:
        conn._request_id += 1
        request_id = conn._request_id
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }
        if conn.process is not None:
            await _write_stdio_message(conn.process, payload)
            while True:
                message = await _read_stdio_message(conn.process)
                if "id" not in message or message["id"] != request_id:
                    continue
                return _extract_result(message)
        return await _post_http_message(conn, payload)


async def _rpc_notify(conn: McpServerConnection, method: str, params: dict[str, Any]) -> None:
    payload = {"jsonrpc": "2.0", "method": method, "params": params}
    if conn.process is not None:
        async with conn._io_lock:
            await _write_stdio_message(conn.process, payload)
        return
    await _post_http_message(conn, payload, expect_response=False)


async def _post_http_message(
    conn: McpServerConnection,
    payload: dict[str, Any],
    *,
    expect_response: bool = True,
) -> dict[str, Any]:
    if conn.client is None or not conn.config.url:
        raise RuntimeError("HTTP MCP connection is not initialized")
    headers = {"Content-Type": "application/json"}
    token = await _get_auth_token(conn, prompt=False)
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = await conn.client.post(conn.config.url, json=payload, headers=headers)
    if response.status_code in {401, 403}:
        token = await _get_auth_token(conn, prompt=True)
        if not token:
            raise RuntimeError(f"MCP server '{conn.config.name}' requires authentication")
        headers["Authorization"] = f"Bearer {token}"
        response = await conn.client.post(conn.config.url, json=payload, headers=headers)

    response.raise_for_status()
    if not expect_response or not response.content:
        return {}
    return _extract_result(response.json())


async def _get_auth_token(conn: McpServerConnection, *, prompt: bool) -> str | None:
    if conn._auth_token:
        return conn._auth_token
    cached = _SESSION_AUTH_TOKENS.get(conn.config.name)
    if cached:
        conn._auth_token = cached
        return cached
    if not prompt:
        return None
    token = await asyncio.to_thread(
        input,
        f"Enter auth token for MCP server '{conn.config.name}' (leave blank to cancel): ",
    )
    token = token.strip()
    if not token:
        return None
    conn._auth_token = token
    _SESSION_AUTH_TOKENS[conn.config.name] = token
    return token


async def _write_stdio_message(
    process: asyncio.subprocess.Process,
    payload: dict[str, Any],
) -> None:
    if process.stdin is None:
        raise RuntimeError("MCP stdio server has no stdin")
    body = json.dumps(payload).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    process.stdin.write(header + body)
    await process.stdin.drain()


async def _read_stdio_message(process: asyncio.subprocess.Process) -> dict[str, Any]:
    if process.stdout is None:
        raise RuntimeError("MCP stdio server has no stdout")

    content_length = 0
    while True:
        line = await process.stdout.readline()
        if not line:
            raise RuntimeError("MCP stdio server closed the connection")
        stripped = line.decode("utf-8").strip()
        if not stripped:
            break
        key, _, value = stripped.partition(":")
        if key.lower() == "content-length":
            content_length = int(value.strip())

    if content_length <= 0:
        raise RuntimeError("Invalid MCP stdio message framing")
    body = await process.stdout.readexactly(content_length)
    message = json.loads(body.decode("utf-8"))
    if not isinstance(message, dict):
        raise RuntimeError("MCP stdio response must be a JSON object")
    return message


def _extract_result(message: dict[str, Any]) -> dict[str, Any]:
    if "error" in message:
        error = message["error"] or {}
        if isinstance(error, dict):
            code = error.get("code", "unknown")
            detail = error.get("message", "Unknown MCP error")
            raise RuntimeError(f"MCP error {code}: {detail}")
        raise RuntimeError(f"MCP error: {error}")
    result = message.get("result", message)
    if not isinstance(result, dict):
        raise RuntimeError("MCP result payload must be an object")
    return result
