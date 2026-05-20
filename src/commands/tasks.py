from __future__ import annotations

from src.commands import register
from src.tools.task_tools import create_task, get_task, list_tasks, stop_task


@register(name="tasks", description="Inspect and manage background tasks.")
async def run(args: list[str]) -> str | None:
    subcommand = args[0] if args else "list"

    if subcommand == "list":
        tasks = list_tasks()
        if not tasks:
            return "No tasks."
        return "\n".join(f"{task.id} | {task.status} | {task.name}" for task in tasks)

    if subcommand == "create" and len(args) >= 2:
        task = create_task(" ".join(args[1:]))
        return f"Created task {task.id}"

    if subcommand == "stop" and len(args) >= 2:
        stopped = stop_task(args[1])
        return f"Stopped task {args[1]}" if stopped else f"Task not found: {args[1]}"

    if subcommand == "output" and len(args) >= 2:
        task = get_task(args[1])
        if task is None:
            return f"Task not found: {args[1]}"
        return "\n".join(task.output) if task.output else "(no output)"

    return "Usage: /tasks list|create <name>|stop <id>|output <id>"
