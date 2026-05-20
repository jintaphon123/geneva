from __future__ import annotations

import os

from src.commands import register
from src.commands._shared import list_feature_env, mask_secret


@register(name="env", description="Show the environment variables used by geneva.")
async def run(args: list[str]) -> str | None:
    del args
    rows = [
        ("ANTHROPIC_API_KEY", mask_secret(os.getenv("ANTHROPIC_API_KEY"))),
        ("OPENAI_API_KEY", mask_secret(os.getenv("OPENAI_API_KEY"))),
        ("MODEL_ID", os.getenv("MODEL_ID", "missing")),
        ("MODEL_PROVIDER", os.getenv("MODEL_PROVIDER", "missing")),
        ("GENEVA_AUTO_DREAM", os.getenv("GENEVA_AUTO_DREAM", "missing")),
        ("GENEVA_COORDINATOR", os.getenv("GENEVA_COORDINATOR", "missing")),
    ]
    rows.extend(list_feature_env())
    return "\n".join(f"{key}={value}" for key, value in rows)
