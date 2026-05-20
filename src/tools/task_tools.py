from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from src.tool_system.context import ToolContext
from src.tool_system.errors import ToolInputError
from src.tool_system.protocol import ToolResult
from src.tool_system.registry import ToolSpec


@dataclass
class Task:
    id: str
    name: str
    status: Literal["running", "completed", "failed", "stopped"]
    output: list[str]
    created_at: str


_TASKS: dict[str, Task] = {}


def _new_task_id() -> str:
    return uuid4().hex[:12]


def create_task(name: str) -> Task:
    task = Task(
        id=_new_task_id(),
        name=name,
        status="running",
        output=[],
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _TASKS[task.id] = task
    return task


def get_task(task_id: str) -> Task | None:
    return _TASKS.get(task_id)


def list_tasks() -> list[Task]:
    return sorted(_TASKS.values(), key=lambda task: task.created_at)


def stop_task(task_id: str) -> bool:
    task = _TASKS.get(task_id)
    if task is None:
        return False
    task.status = "stopped"
    return True


def _store_in_context(task: Task, context: ToolContext) -> None:
    context.tasks[task.id] = {
        "id": task.id,
        "subject": task.name,
        "description": task.name,
        "status": task.status,
        "output": "\n".join(task.output),
        "created_at": task.created_at,
    }


def _task_payload(task: Task) -> dict[str, Any]:
    payload = asdict(task)
    payload["subject"] = task.name
    payload["description"] = task.name
    return payload


class TaskCreateTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="TaskCreate",
            description="Create a lightweight in-memory task.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {"type": "string"},
                    "subject": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
            is_read_only=True,
            strict=True,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        name = tool_input.get("name") or tool_input.get("subject") or tool_input.get("description")
        if not isinstance(name, str) or not name.strip():
            raise ToolInputError("name must be a non-empty string")
        task = create_task(name.strip())
        _store_in_context(task, context)
        return ToolResult(name="TaskCreate", output={"task_id": task.id, "task": {"id": task.id, "subject": task.name}})


class TaskGetTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="TaskGet",
            description="Get a task by ID.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "taskId": {"type": "string"},
                    "task_id": {"type": "string"},
                },
            },
            is_read_only=True,
            strict=True,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        del context
        task_id = tool_input.get("taskId") or tool_input.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ToolInputError("task id must be a non-empty string")
        task = get_task(task_id)
        return ToolResult(name="TaskGet", output={"task": _task_payload(task) if task else None})


class TaskListTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="TaskList",
            description="List all in-memory tasks.",
            input_schema={"type": "object", "additionalProperties": False, "properties": {}},
            is_read_only=True,
            strict=True,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        del tool_input, context
        return ToolResult(name="TaskList", output={"tasks": [_task_payload(task) for task in list_tasks()]})


class TaskOutputTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="TaskOutput",
            description="Read output lines for a task.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "task_id": {"type": "string"},
                    "taskId": {"type": "string"},
                },
            },
            is_read_only=True,
            strict=True,
            aliases=("AgentOutputTool", "BashOutputTool"),
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        del context
        task_id = tool_input.get("task_id") or tool_input.get("taskId")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ToolInputError("task id must be a non-empty string")
        task = get_task(task_id)
        if task is None:
            return ToolResult(name="TaskOutput", output={"retrieval_status": "success", "task": None})
        return ToolResult(
            name="TaskOutput",
            output={
                "retrieval_status": "success" if task.output else "not_ready",
                "task": {
                    "task_id": task.id,
                    "task_type": "task_list",
                    "status": task.status,
                    "description": task.name,
                    "output": "\n".join(task.output),
                },
            },
        )


class TaskUpdateTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="TaskUpdate",
            description="Update task status or append task output.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "taskId": {"type": "string"},
                    "task_id": {"type": "string"},
                    "status": {"type": "string"},
                    "output_line": {"type": "string"},
                    "outputLine": {"type": "string"},
                    "name": {"type": "string"},
                    "subject": {"type": "string"},
                },
            },
            is_read_only=True,
            strict=True,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        task_id = tool_input.get("taskId") or tool_input.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ToolInputError("task id must be a non-empty string")
        task = get_task(task_id)
        if task is None:
            return ToolResult(name="TaskUpdate", output={"success": False, "taskId": task_id, "updatedFields": [], "error": "Task not found"})

        updated_fields: list[str] = []
        status = tool_input.get("status")
        if status is not None:
            if status == "pending":
                status = "running"
            if status == "in_progress":
                status = "running"
            if status not in {"running", "completed", "failed", "stopped"}:
                raise ToolInputError("status must be running|completed|failed|stopped")
            task.status = status
            updated_fields.append("status")

        name = tool_input.get("name") or tool_input.get("subject")
        if name is not None:
            if not isinstance(name, str):
                raise ToolInputError("name must be a string")
            task.name = name
            updated_fields.append("name")

        output_line = tool_input.get("output_line") or tool_input.get("outputLine")
        if output_line is not None:
            if not isinstance(output_line, str):
                raise ToolInputError("output_line must be a string")
            task.output.append(output_line)
            updated_fields.append("output")

        _store_in_context(task, context)
        return ToolResult(name="TaskUpdate", output={"success": True, "taskId": task.id, "updatedFields": updated_fields})
