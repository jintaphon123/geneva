from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol

from src.permissions import ToolPermissionContext as RootToolPermissionContext
from src.tool_system.profiles import get_manifest_entry

from .context import ToolContext
from .errors import ToolPermissionError
from .permission_handler import PermissionResult
from .protocol import ToolCall, ToolResult
from .schema_validation import validate_json_schema


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: Mapping[str, Any]
    aliases: tuple[str, ...] = ()
    is_read_only: bool = False
    is_destructive: bool = False
    strict: bool = False
    max_result_size_chars: int = 20_000
    timeout_seconds: float = 90.0
    is_concurrency_safe: bool = False


class Tool(Protocol):
    def spec(self) -> ToolSpec: ...

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult: ...

    def check_permissions(
        self, tool_input: dict[str, Any], context: ToolContext
    ) -> PermissionResult:
        """Check if this tool has permission to run.

        Args:
            tool_input: The input arguments for the tool.
            context: The tool execution context.

        Returns:
            PermissionResult indicating allow, deny, or ask.
        """
        return PermissionResult.allow()


class ToolRegistry:
    def __init__(self, tools: Iterable[Tool] | None = None) -> None:
        self._tools: list[Tool] = []
        self._by_name: dict[str, Tool] = {}
        if tools:
            for tool in tools:
                self.register(tool)

    def register(self, tool: Tool) -> None:
        spec = tool.spec()
        key = spec.name.lower()
        if key in self._by_name:
            raise ValueError(f"duplicate tool name: {spec.name}")
        self._tools.append(tool)
        self._by_name[key] = tool
        for alias in spec.aliases:
            alias_key = alias.lower()
            if alias_key in self._by_name:
                raise ValueError(f"duplicate tool alias: {alias}")
            self._by_name[alias_key] = tool

    def list_specs(self) -> list[ToolSpec]:
        return [tool.spec() for tool in self._tools]

    def get(self, name: str) -> Tool | None:
        return self._by_name.get(name.lower())

    def spec_for(self, name: str) -> ToolSpec | None:
        tool = self.get(name)
        return tool.spec() if tool is not None else None

    def dispatch(
        self,
        call: ToolCall,
        context: ToolContext,
        permission_ctx: RootToolPermissionContext | None = None,
    ) -> ToolResult:
        tool = self.get(call.name)
        if tool is None:
            try:
                from src.geneva.audit_log import append_audit_entry

                append_audit_entry(
                    tool_name=call.name,
                    scope="unregistered",
                    args=call.input,
                    outcome="deny",
                    reason="unknown tool (deny-by-default)",
                    session_id=getattr(context, "session_id", None),
                    turn_id=getattr(context, "turn_id", None),
                )
            except Exception:
                pass
            return ToolResult(
                name=call.name,
                output={"error": f"unknown tool: {call.name}", "policy": "deny-by-default"},
                is_error=True,
                tool_use_id=call.tool_use_id,
            )
        spec = tool.spec()
        # R4.3 deny-by-default: tool must be in permission manifest
        _manifest = get_manifest_entry(spec.name)
        if _manifest is None:
            try:
                from src.geneva.audit_log import append_audit_entry

                append_audit_entry(
                    tool_name=spec.name,
                    scope="unregistered",
                    args=call.input,
                    outcome="deny",
                    reason="tool not in permission manifest (deny-by-default)",
                    session_id=getattr(context, "session_id", None),
                    turn_id=getattr(context, "turn_id", None),
                )
            except Exception:
                pass
            return ToolResult(
                name=call.name,
                output={"error": f"tool '{call.name}' is not registered in the permission manifest", "policy": "deny-by-default"},
                is_error=True,
                tool_use_id=call.tool_use_id,
            )
        context.ensure_tool_allowed(spec.name)
        if permission_ctx and permission_ctx.blocks(spec.name):
            raise ToolPermissionError(
                f"Tool '{spec.name}' is blocked by permission policy"
            )
        validate_json_schema(call.input, spec.input_schema, root_name=spec.name)

        # Check permissions before running
        permission_result = tool.check_permissions(call.input, context) if hasattr(tool, 'check_permissions') else PermissionResult.allow()
        if permission_result.behavior.value == "deny":
            return ToolResult(
                name=spec.name,
                output={"error": permission_result.message or "permission denied"},
                is_error=True,
                tool_use_id=call.tool_use_id,
            )
        if permission_result.behavior.value == "ask":
            # Need user interaction
            if context.permission_handler is None:
                # No handler available, deny by default
                return ToolResult(
                    name=spec.name,
                    output={"error": permission_result.message or "permission required but no handler available"},
                    is_error=True,
                    tool_use_id=call.tool_use_id,
                )
            # Call the permission handler
            allowed, _ = context.permission_handler(
                spec.name,
                permission_result.message or f"Tool '{spec.name}' requires permission",
                permission_result.suggestion,
            )
            if not allowed:
                return ToolResult(
                    name=spec.name,
                    output={
                        "error": f"permission denied: {permission_result.message or 'user approval required'}",
                        "permission_required": True,
                        "suggestion": permission_result.suggestion,
                    },
                    is_error=True,
                    tool_use_id=call.tool_use_id,
                )
            # User allowed - proceed with potentially updated input
            if permission_result.updated_input:
                call = ToolCall(
                    name=call.name,
                    input=permission_result.updated_input,
                    tool_use_id=call.tool_use_id,
                )

        _m = get_manifest_entry(spec.name)
        try:
            from src.geneva.audit_log import append_audit_entry

            append_audit_entry(
                tool_name=spec.name,
                scope=_m.category if _m else "unknown",
                args=call.input,
                outcome="start",
                session_id=getattr(context, "session_id", None),
                turn_id=getattr(context, "turn_id", None),
            )
        except Exception:
            pass
        try:
            result = tool.run(call.input, context)
        except Exception:
            try:
                from src.geneva.audit_log import append_audit_entry

                append_audit_entry(
                    tool_name=spec.name,
                    scope=_m.category if _m else "unknown",
                    args=call.input,
                    outcome="error",
                    reason="tool raised before returning ToolResult",
                    session_id=getattr(context, "session_id", None),
                    turn_id=getattr(context, "turn_id", None),
                )
            except Exception:
                pass
            raise
        try:
            from src.geneva.audit_log import append_audit_entry

            append_audit_entry(
                tool_name=spec.name,
                scope=_m.category if _m else "unknown",
                args=call.input,
                outcome="error" if result.is_error else "allow",
                session_id=getattr(context, "session_id", None),
                turn_id=getattr(context, "turn_id", None),
            )
        except Exception:
            pass
        if result.tool_use_id is None and call.tool_use_id is not None:
            return ToolResult(
                name=result.name,
                output=result.output,
                is_error=result.is_error,
                tool_use_id=call.tool_use_id,
                content_type=result.content_type,
            )
        return result
