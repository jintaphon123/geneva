from __future__ import annotations

from src.commands import register
from src.commands._shared import get_permission_context, set_permission_context
from src.permissions import ToolPermissionContext


@register(name="permissions", description="Show and update blocked tools.", aliases=["perms"])
async def run(args: list[str]) -> str | None:
    ctx = get_permission_context()
    subcommand = args[0] if args else "show"

    if subcommand == "show":
        return (
            f"deny_names={sorted(ctx.deny_names)}\n"
            f"deny_prefixes={list(ctx.deny_prefixes)}"
        )

    if subcommand == "deny" and len(args) >= 2:
        updated = ToolPermissionContext.from_iterables(
            deny_names=sorted(set(ctx.deny_names) | {args[1].lower()}),
            deny_prefixes=list(ctx.deny_prefixes),
        )
        set_permission_context(updated)
        return f"Denied tool {args[1]}"

    if subcommand == "allow" and len(args) >= 2:
        updated_names = sorted(name for name in ctx.deny_names if name != args[1].lower())
        updated = ToolPermissionContext.from_iterables(
            deny_names=updated_names,
            deny_prefixes=list(ctx.deny_prefixes),
        )
        set_permission_context(updated)
        return f"Allowed tool {args[1]}"

    if subcommand == "deny-prefix" and len(args) >= 2:
        updated = ToolPermissionContext.from_iterables(
            deny_names=sorted(ctx.deny_names),
            deny_prefixes=list(dict.fromkeys([*ctx.deny_prefixes, args[1].lower()])),
        )
        set_permission_context(updated)
        return f"Denied prefix {args[1]}"

    return "Usage: /permissions show|deny <tool>|allow <tool>|deny-prefix <prefix>"
