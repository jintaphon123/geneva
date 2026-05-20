from __future__ import annotations

from ._prompt_skill_utils import build_prompt_skill
from .model import PromptSkill
from src.services.mcp.types import McpToolDef


def build_skill_from_mcp_tool(tool_def: McpToolDef) -> PromptSkill:
    required = tool_def.input_schema.get("required", []) if isinstance(tool_def.input_schema, dict) else []
    properties = tool_def.input_schema.get("properties", {}) if isinstance(tool_def.input_schema, dict) else {}
    argument_lines = []
    for key, value in properties.items():
        if not isinstance(value, dict):
            continue
        arg_type = value.get("type", "any")
        desc = value.get("description", "")
        suffix = " (required)" if key in required else ""
        argument_lines.append(f"- `{key}` ({arg_type}){suffix}: {desc}")
    sections = [
        f"Use the MCP tool `{tool_def.name}`.",
        "",
        tool_def.description or "No additional description provided.",
        "",
        "Expected inputs:",
    ]
    sections.extend(argument_lines or ["- No structured inputs declared."])
    body = "\n".join(sections)
    markdown = f"---\nname: {tool_def.name}\ndescription: {tool_def.description or 'MCP tool wrapper'}\n---\n\n{body}\n"
    return build_prompt_skill(
        markdown,
        skill_name=tool_def.name,
        loaded_from="mcp",
        skill_root=None,
        description=tool_def.description or "MCP tool wrapper",
    )
