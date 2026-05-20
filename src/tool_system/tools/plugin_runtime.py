from __future__ import annotations

from pathlib import Path
from typing import Any

from src.geneva.plugin_runtime import PluginRuntime

from ..context import ToolContext
from ..errors import ToolInputError
from ..protocol import ToolResult
from ..registry import ToolSpec


class PluginListTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="PluginList",
            description="List Geneva plugin manifests, including first-class built-in capability plugins.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "include_builtin": {"type": "boolean"},
                    "plugin_dir": {"type": "string"},
                },
            },
            is_read_only=True,
            max_result_size_chars=100_000,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        include_builtin = bool(tool_input.get("include_builtin", True))
        plugin_dir_value = tool_input.get("plugin_dir")
        plugin_dir: Path | None = None
        if plugin_dir_value is not None:
            if not isinstance(plugin_dir_value, str) or not plugin_dir_value.strip():
                raise ToolInputError("plugin_dir must be a non-empty string when provided")
            plugin_dir = context.ensure_allowed_path(plugin_dir_value)
        runtime = PluginRuntime(plugin_dir=plugin_dir)
        return ToolResult(
            name="PluginList",
            output={
                "plugin_dir": str(runtime.plugin_dir),
                "manifests": runtime.list_manifest_dicts(include_builtin=include_builtin),
            },
        )
