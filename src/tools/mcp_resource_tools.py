from __future__ import annotations

import os
from typing import Any

from src.services.mcp import client as mcp_client
from src.services.mcp.client import connect_to_server, disconnect, list_resources as async_list_resources, read_resource as async_read_resource
from src.services.mcp.config import get_configured_servers
from src.tool_system.context import ToolContext
from src.tool_system.errors import ToolInputError
from src.tool_system.protocol import ToolResult
from src.tool_system.registry import ToolSpec
from src.utils.asyncio_tools import run_awaitable_sync

_MCP_CONNECTIONS: dict[str, Any] = {}


def _find_config(server_name: str):
    for server in get_configured_servers():
        if server.name == server_name:
            return server
    return None


def _get_or_connect(server_name: str):
    if server_name in _MCP_CONNECTIONS:
        return _MCP_CONNECTIONS[server_name]
    config = _find_config(server_name)
    if config is None:
        raise KeyError(server_name)
    conn = run_awaitable_sync(connect_to_server(config))
    _MCP_CONNECTIONS[server_name] = conn
    return conn


class ListMcpResourcesTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="ListMcpResourcesTool",
            description="List resources from connected or configured MCP servers.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {"server": {"type": "string"}},
            },
            is_read_only=True,
            max_result_size_chars=100_000,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        server = tool_input.get("server")
        if server is not None and (not isinstance(server, str) or not server.strip()):
            raise ToolInputError("server must be a non-empty string when provided")
        if isinstance(server, str) and server in context.mcp_clients:
            client = context.mcp_clients[server]
            items = client.list_resources()
            return ToolResult(name="ListMcpResourcesTool", output=items)
        if not server:
            return ToolResult(
                name="ListMcpResourcesTool",
                output=[{"server": item.name, "transport": item.transport} for item in get_configured_servers()],
            )
        try:
            conn = _get_or_connect(server)
            items = run_awaitable_sync(async_list_resources(conn))
            return ToolResult(name="ListMcpResourcesTool", output=items)
        except KeyError:
            return ToolResult(name="ListMcpResourcesTool", output={"error": f"mcp server not configured: {server}"}, is_error=True)
        except Exception as exc:
            return ToolResult(name="ListMcpResourcesTool", output={"error": str(exc)}, is_error=True)


class ReadMcpResourceTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="ReadMcpResourceTool",
            description="Read a resource from an MCP server.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {"server": {"type": "string"}, "uri": {"type": "string"}},
                "required": ["server", "uri"],
            },
            is_read_only=True,
            max_result_size_chars=100_000,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        server = tool_input.get("server")
        uri = tool_input.get("uri")
        if not isinstance(server, str) or not server.strip():
            raise ToolInputError("server must be a non-empty string")
        if not isinstance(uri, str) or not uri.strip():
            raise ToolInputError("uri must be a non-empty string")
        if server in context.mcp_clients:
            out = context.mcp_clients[server].read_resource(uri)
            return ToolResult(name="ReadMcpResourceTool", output=out)
        try:
            conn = _get_or_connect(server)
            out = run_awaitable_sync(async_read_resource(conn, uri))
            return ToolResult(name="ReadMcpResourceTool", output=out)
        except KeyError:
            return ToolResult(name="ReadMcpResourceTool", output={"error": f"mcp server not configured: {server}"}, is_error=True)
        except Exception as exc:
            return ToolResult(name="ReadMcpResourceTool", output={"error": str(exc)}, is_error=True)


class McpAuthTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="McpAuthTool",
            description="Store an auth token for a configured MCP server.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "server_name": {"type": "string"},
                    "token": {"type": "string"},
                },
                "required": ["server_name"],
            },
            max_result_size_chars=10_000,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        del context
        server_name = tool_input.get("server_name")
        token = tool_input.get("token")
        if not isinstance(server_name, str) or not server_name.strip():
            raise ToolInputError("server_name must be a non-empty string")
        if token is None:
            token = input(f"Enter auth token for {server_name}: ").strip()
        if not isinstance(token, str) or not token:
            return ToolResult(name="McpAuthTool", output={"success": False, "reason": "no token provided"}, is_error=True)
        env_key = f"MCP_AUTH_{server_name.upper()}"
        os.environ[env_key] = token
        if hasattr(mcp_client, "_SESSION_AUTH_TOKENS"):
            mcp_client._SESSION_AUTH_TOKENS[server_name] = token  # type: ignore[attr-defined]
        return ToolResult(name="McpAuthTool", output={"success": True, "server_name": server_name})
