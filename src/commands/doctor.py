from __future__ import annotations

import os
import sys

from src.commands import register
from src.commands._shared import format_table, git_status, package_status, provider_config, provider_ping, shell_status
from src.services.mcp.config import load_mcp_config


@register(name="doctor", description="Run environment and dependency checks.")
async def run(args: list[str]) -> str | None:
    del args
    rows: list[tuple[str, str]] = []
    rows.append(("python", "pass" if sys.version_info >= (3, 11) else f"fail ({sys.version.split()[0]})"))
    for package_name in ("anthropic", "httpx", "pydantic", "watchdog", "nbformat"):
        rows.append((f"pkg:{package_name}", package_status(package_name)))
    rows.append(("ANTHROPIC_API_KEY", "present" if os.getenv("ANTHROPIC_API_KEY") else "missing"))
    rows.append(("OPENAI_API_KEY", "present" if os.getenv("OPENAI_API_KEY") else "missing"))
    rows.append(("git", git_status()))
    rows.append(("shell", shell_status()))
    try:
        rows.append(("mcp_config", f"pass ({len(load_mcp_config())} servers)"))
    except Exception as exc:
        rows.append(("mcp_config", f"fail ({exc})"))

    anthropic_cfg = provider_config("anthropic")
    if anthropic_cfg.get("api_key"):
        rows.append(
            (
                "provider_ping",
                provider_ping(
                    "anthropic",
                    str(anthropic_cfg.get("api_key")),
                    anthropic_cfg.get("base_url"),
                    anthropic_cfg.get("default_model"),
                ),
            )
        )
    else:
        rows.append(("provider_ping", "skipped (no api key)"))
    return format_table(rows)
