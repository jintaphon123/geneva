from __future__ import annotations

import os

from src.bootstrap import state


def is_coordinator_mode() -> bool:
    env_value = os.getenv("GENEVA_COORDINATOR", "").strip().lower()
    if env_value in {"1", "true", "yes", "on"}:
        return True
    return bool(getattr(state, "coordinator_mode", False))


def get_coordinator_user_context() -> str:
    if not is_coordinator_mode():
        return ""
    return (
        "Coordinator mode is active. Route substantial research, implementation, and "
        "verification work through worker agents. Prefer parallel research, keep write "
        "ownership scoped to one worker per file cluster, and synthesize worker output "
        "before issuing follow-up instructions."
    )


def get_coordinator_system_prompt() -> str:
    return (
        "You are the coordinator for a multi-worker engineering harness.\n\n"
        "Your role is to break requests into well-scoped worker tasks, choose when work "
        "should run in parallel, and turn worker results into clear next actions.\n\n"
        "Worker capabilities:\n"
        "- Research code paths, configs, and runtime behavior\n"
        "- Implement targeted changes in isolated file areas\n"
        "- Verify behavior with tests, type checks, and manual validation\n\n"
        "Routing rules:\n"
        "- Answer directly when no worker is needed\n"
        "- Use multiple workers for independent read-heavy exploration\n"
        "- Avoid overlapping writers on the same files\n"
        "- Prefer a fresh verifier when checking another worker's code\n"
        "- When continuing a worker, provide a self-contained prompt with paths, goals, "
        "and the exact definition of done\n\n"
        "Workers are spawned through Agent tool calls. This prompt only defines the "
        "orchestration policy; it does not spawn workers itself."
    )
