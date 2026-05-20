from __future__ import annotations

from src.commands import register
from src.commands._shared import get_config, get_nested, parse_jsonish, save_config, set_nested


@register(name="config", description="Get and set geneva config values.")
async def run(args: list[str]) -> str | None:
    subcommand = args[0] if args else "list"
    config = get_config()
    if subcommand == "list":
        return "\n".join(f"{key}={value}" for key, value in sorted(config.items()))
    if subcommand == "get" and len(args) >= 2:
        try:
            value = get_nested(config, args[1])
        except KeyError:
            return f"Missing config key: {args[1]}"
        return str(value)
    if subcommand == "set" and len(args) >= 3:
        set_nested(config, args[1], parse_jsonish(" ".join(args[2:])))
        save_config(config)
        return f"Updated {args[1]}"
    return "Usage: /config list|get <key>|set <key> <value>"
