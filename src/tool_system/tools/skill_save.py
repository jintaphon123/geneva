from __future__ import annotations

import re
from typing import Any

from ..context import ToolContext
from ..errors import ToolInputError
from ..protocol import ToolResult
from ..registry import ToolSpec


class SkillSaveTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="SkillSave",
            description=(
                "Save a new custom skill (or overwrite an existing one). "
                "Creates the SKILL.md file in ~/.geneva/skills/{name}/ and registers it immediately. "
                "Use this after collecting all information from the user to finalize their skill. "
                "The skill will appear in My Skills right away."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Skill name: lowercase, letters/digits/hyphens only (e.g. 'agent-harness', 'my-skill')",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full SKILL.md content including YAML frontmatter (---\\nname: ...\\ndescription: ...\\n---\\n\\n# ...)",
                    },
                },
                "required": ["name", "content"],
            },
            is_read_only=False,
            max_result_size_chars=4_000,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        name = str(tool_input.get("name") or "").strip()
        content = str(tool_input.get("content") or "").strip()

        if not name:
            raise ToolInputError("name is required")
        if not re.match(r"^[a-z0-9][a-z0-9\-]*$", name):
            raise ToolInputError("name must be lowercase letters/digits/hyphens (e.g. 'my-skill')")
        if not content:
            raise ToolInputError("content is required")
        if "---" not in content:
            raise ToolInputError("content must include YAML frontmatter (---\\nname: ...\\n---)")

        try:
            from src.geneva.web_runtime import get_engine  # lazy import to avoid circular deps
        except ImportError:
            raise ToolInputError("SkillSave is only available in the Geneva web context")

        engine = get_engine()
        result = engine.create_skill_record(name, content, status="active", source="manual")
        if result is None:
            raise ToolInputError(f"Failed to create skill '{name}' — name may be invalid")

        return ToolResult(
            name="SkillSave",
            output={
                "ok": True,
                "name": result.get("name", name),
                "message": f"Skill '{name}' saved successfully. It now appears in My Skills.",
            },
            content_type="json",
        )
