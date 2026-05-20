from __future__ import annotations

from pathlib import Path

from src.bootstrap import state
from src.commands import register
from src.commands._shared import current_session_id, get_model_and_provider, load_latest_or_requested_session
from src.coordinator.coordinator_mode import is_coordinator_mode
from src.cost_tracker import CostTracker
from src.memdir.paths import get_auto_mem_path

try:
    from src.memdir.memory_scan import scan_memory_files

    HAS_MEM_SCAN = True
except ImportError:
    HAS_MEM_SCAN = False


@register(name="status", description="Show session and runtime status.")
async def run(args: list[str]) -> str | None:
    del args
    model, provider = get_model_and_provider()
    tracker = CostTracker()
    tracker.restore_from_disk(current_session_id())
    session = load_latest_or_requested_session(current_session_id())
    memory_count = len(scan_memory_files(get_auto_mem_path(Path.cwd()))) if HAS_MEM_SCAN else 0
    return "\n".join(
        [
            f"session_id={current_session_id()}",
            f"model={model}",
            f"provider={provider}",
            f"cost_usd={tracker.get_total_cost_usd():.4f}",
            f"turns={len(session.messages) if session else 0}",
            f"plan_mode={'on' if state.plan_mode else 'off'}",
            f"coordinator_mode={'on' if is_coordinator_mode() else 'off'}",
            f"memory_files={memory_count}",
        ]
    )
