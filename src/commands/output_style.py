from __future__ import annotations

from src.commands import register
from src.commands._shared import get_config, save_config


@register(name="output_style", description="Get or set the output theme.", aliases=["style"])
async def run(args: list[str]) -> str | None:
    subcommand = args[0] if args else "get"
    config = get_config()
    ui = config.setdefault("ui", {})
    if subcommand == "get":
        return str(ui.get("output_style", "minimal"))
    if subcommand == "set" and len(args) >= 2:
        theme = args[1]
        if theme not in {"dark", "light", "minimal"}:
            return "Theme must be one of: dark, light, minimal"
        ui["output_style"] = theme
        save_config(config)
        return f"Set output style to {theme}"
    return "Usage: /output_style get|set <dark|light|minimal>"
