from __future__ import annotations

from src.bootstrap.state import per_model_tokens
from src.commands import register
from src.commands._shared import current_session_id
from src.cost_tracker import CostTracker


@register(name="cost", description="Show cost and token usage.")
async def run(args: list[str]) -> str | None:
    del args
    tracker = CostTracker()
    tracker.restore_from_disk(current_session_id())
    lines = [tracker.format_cost_summary(), "", "per_model:"]
    for model, usage in sorted(per_model_tokens.items()):
        lines.append(
            f"{model} | input={usage.input} | output={usage.output} | cost={tracker.get_per_model_breakdown().get(model, 0.0):.4f}"
        )
    lines.append(f"total | ${tracker.get_total_cost_usd():.4f}")
    return "\n".join(lines)
