from __future__ import annotations

from typing import Any

from src.geneva.computer_use_runtime import (
    ComputerUseAction,
    ComputerUseRuntime,
    result_to_dict,
)

from ..context import ToolContext
from ..errors import ToolInputError
from ..permission_handler import PermissionBehavior, PermissionResult
from ..protocol import ToolResult
from ..registry import ToolSpec


class ComputerUseTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="ComputerUse",
            description="Plan or execute computer-use actions through Geneva's policy-first action runtime.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["observe", "click", "type", "scroll", "wait", "screenshot", "extract_dom", "done"],
                    },
                    "target": {"type": "string"},
                    "text": {"type": "string"},
                    "url": {"type": "string"},
                    "amount": {"type": "integer"},
                    "confirm_sensitive": {"type": "boolean"},
                },
                "required": ["action"],
            },
            is_read_only=False,
            is_destructive=False,
            max_result_size_chars=50_000,
        )

    def check_permissions(
        self,
        tool_input: dict[str, Any],
        context: ToolContext,
    ) -> PermissionResult:
        action = self._action_from_input(tool_input)
        if ComputerUseRuntime.is_sensitive_action(action) and not action.confirm_sensitive:
            updated = dict(tool_input)
            updated["confirm_sensitive"] = True
            return PermissionResult(
                behavior=PermissionBehavior.ASK,
                message="Sensitive computer-use action requires explicit confirmation before Geneva can continue.",
                suggestion="Confirm only if the target action is intended and safe.",
                updated_input=updated,
            )
        return PermissionResult.allow()

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        action = self._action_from_input(tool_input)
        runtime = ComputerUseRuntime()
        try:
            result = runtime.execute(action)
        except ValueError as exc:
            raise ToolInputError(str(exc)) from exc
        return ToolResult(name="ComputerUse", output=result_to_dict(result))

    @staticmethod
    def _action_from_input(tool_input: dict[str, Any]) -> ComputerUseAction:
        action = tool_input.get("action")
        if not isinstance(action, str) or not action.strip():
            raise ToolInputError("action must be a non-empty string")
        amount = tool_input.get("amount")
        if amount is not None and not isinstance(amount, int):
            raise ToolInputError("amount must be an integer when provided")
        return ComputerUseAction(
            action=action,
            target=str(tool_input.get("target") or ""),
            text=str(tool_input.get("text") or ""),
            url=str(tool_input.get("url") or ""),
            amount=amount,
            confirm_sensitive=bool(tool_input.get("confirm_sensitive")),
        )
