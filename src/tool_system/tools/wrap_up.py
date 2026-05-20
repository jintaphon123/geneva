from __future__ import annotations

from typing import Any

from ...memdir.brain_engine import remember
from ...memdir.transcript_store import get_session_transcript
from ...utils.asyncio_tools import run_awaitable_sync
from ..context import ToolContext
from ..errors import ToolInputError
from ..protocol import ToolResult
from ..registry import ToolSpec


class WrapUpTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="WrapUp",
            description=(
                "Save a structured session wrap-up: write memory entries to the knowledge base "
                "and return a transcript summary. Call at end of session with key facts, decisions, "
                "and a brief summary."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "session_id": {"type": "string", "description": "Current session ID"},
                    "summary": {"type": "string", "description": "Brief summary of this session (1-3 sentences)"},
                    "memories": {
                        "type": "array",
                        "description": "Key facts, decisions, and preferences to remember",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "enum": ["user", "project", "feedback", "reference"],
                                },
                                "content": {"type": "string"},
                            },
                            "required": ["type", "content"],
                        },
                    },
                },
                "required": ["session_id", "summary"],
            },
            is_read_only=False,
            max_result_size_chars=10_000,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        session_id = tool_input.get("session_id", "")
        summary = tool_input.get("summary", "")
        memories_input = tool_input.get("memories") or []

        if not isinstance(session_id, str) or not session_id.strip():
            raise ToolInputError("session_id must be a non-empty string")
        if not isinstance(summary, str) or not summary.strip():
            raise ToolInputError("summary must be a non-empty string")

        memories_written = 0
        errors = []
        for item in memories_input:
            if not isinstance(item, dict):
                continue
            content = str(item.get("content", "")).strip()
            mem_type = str(item.get("type", "reference")).strip()
            if not content or len(content) < 5:
                continue
            try:
                result = run_awaitable_sync(
                    remember(content, mem_type, source_type="wrap_up", source_session_id=session_id)
                )
                if result and result.success:
                    memories_written += 1
            except Exception as exc:
                errors.append(str(exc)[:100])

        transcript = get_session_transcript(session_id)
        transcript_turns = len(transcript)

        return ToolResult(
            name="WrapUp",
            output={
                "status": "saved",
                "summary": summary,
                "memories_written": memories_written,
                "transcript_turns": transcript_turns,
                "errors": errors[:5] if errors else [],
            },
        )
