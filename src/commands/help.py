from __future__ import annotations

from src.commands import COMMANDS, register


@register(name="help", description="List available slash commands.", aliases=["?"])
async def run(args: list[str]) -> str | None:
    del args
    seen = set()
    rows: list[str] = []
    for meta in sorted(COMMANDS.values(), key=lambda item: item.name):
        if meta.name in seen:
            continue
        seen.add(meta.name)
        alias_text = ",".join(meta.aliases) if meta.aliases else "-"
        rows.append(f"{meta.name} | {alias_text} | {meta.description}")
    return "\n".join(rows)
