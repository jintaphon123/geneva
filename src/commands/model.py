from __future__ import annotations

from src.commands import register
from src.commands._shared import get_model_and_provider, set_model_and_provider


@register(name="model", description="Get or set the active model.")
async def run(args: list[str]) -> str | None:
    subcommand = args[0] if args else "get"
    if subcommand == "get":
        model, provider = get_model_and_provider()
        return f"MODEL_ID={model}\nMODEL_PROVIDER={provider}"
    if subcommand == "set" and len(args) >= 2:
        provider = None
        if "--provider" in args:
            idx = args.index("--provider")
            if idx + 1 < len(args):
                provider = args[idx + 1]
        model, resolved_provider = set_model_and_provider(args[1], provider)
        return f"Set model to {model} (provider={resolved_provider})"
    return "Usage: /model get|set <model_id> [--provider <name>]"
