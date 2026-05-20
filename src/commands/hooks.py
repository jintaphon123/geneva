from __future__ import annotations

import os

from src.commands import register
from src.hooks.post_sampling_hooks import get_registered_hooks


def _hook_status(name: str) -> str:
    env_key = f"GENEVA_HOOK_{name.upper()}"
    value = os.getenv(env_key)
    return "enabled" if value in {None, "", "1", "true", "on"} else "disabled"


@register(name="hooks", description="Show and toggle post-sampling hooks.")
async def run(args: list[str]) -> str | None:
    subcommand = args[0] if args else "list"
    if subcommand == "list":
        hooks = ["observation_masking", *[hook.__name__ for hook in get_registered_hooks()]]
        lines = []
        for hook_name in dict.fromkeys(hooks):
            lines.append(f"{hook_name} | {_hook_status(hook_name)}")
        return "\n".join(lines)
    if subcommand in {"enable", "disable"} and len(args) >= 2:
        hook_name = args[1].upper().replace("-", "_")
        os.environ[f"GENEVA_HOOK_{hook_name}"] = "1" if subcommand == "enable" else "0"
        if hook_name == "OBSERVATION_MASKING":
            os.environ["GENEVA_DISABLE_OBSERVATION_MASKING"] = "0" if subcommand == "enable" else "1"
        return f"{subcommand}d hook {args[1]}"
    return "Usage: /hooks list|enable <hook>|disable <hook>"
