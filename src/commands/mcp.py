from __future__ import annotations

import time

from src.commands import register
from src.services.mcp.client import connect_to_server, disconnect
from src.services.mcp.config import McpServerConfig, add_server_config, get_configured_servers, remove_server_config


@register(name="mcp", description="Inspect and manage MCP server configuration.")
async def run(args: list[str]) -> str | None:
    subcommand = args[0] if args else "list"

    if subcommand == "list":
        servers = get_configured_servers()
        if not servers:
            return "No MCP servers configured."
        return "\n".join(
            f"{server.name} | {server.transport} | {server.url or ' '.join(server.command or [])}"
            for server in servers
        )

    if subcommand == "status":
        lines: list[str] = []
        for server in get_configured_servers():
            started = time.perf_counter()
            try:
                conn = await connect_to_server(server)
                await disconnect(conn)
                latency_ms = int((time.perf_counter() - started) * 1000)
                lines.append(f"{server.name} | ok | {latency_ms} ms")
            except Exception as exc:
                lines.append(f"{server.name} | error | {exc}")
        return "\n".join(lines) if lines else "No MCP servers configured."

    if subcommand == "add":
        if len(args) >= 4 and args[2] == "http":
            config = McpServerConfig(name=args[1], transport="http", command=None, url=args[3])
        elif len(args) >= 4 and args[2] == "stdio":
            config = McpServerConfig(name=args[1], transport="stdio", command=args[3:], url=None)
        else:
            name = input("Server name: ").strip()
            transport = input("Transport (stdio/http): ").strip() or "stdio"
            target = input("Command or URL: ").strip()
            config = (
                McpServerConfig(name=name, transport="http", command=None, url=target)
                if transport == "http"
                else McpServerConfig(name=name, transport="stdio", command=target.split(), url=None)
            )
        add_server_config(config)
        return f"Added MCP server {config.name}"

    if subcommand == "remove" and len(args) >= 2:
        remove_server_config(args[1])
        return f"Removed MCP server {args[1]}"

    return "Usage: /mcp list|status|add|remove"
