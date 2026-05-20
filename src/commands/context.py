from __future__ import annotations

from src.commands import register
from src.commands._shared import get_model_and_provider, load_latest_or_requested_session, session_messages_as_api
from src.context_system.context_analyzer import analyze_context
from src.tool_system.defaults import build_default_registry


@register(name="context", description="Show current context usage.")
async def run(args: list[str]) -> str | None:
    del args
    session = load_latest_or_requested_session()
    model, _provider = get_model_and_provider()
    registry = build_default_registry(include_user_tools=False)
    tool_schemas = [
        {
            "name": spec.name,
            "description": spec.description,
            "input_schema": dict(spec.input_schema),
        }
        for spec in registry.list_specs()
    ]
    data = analyze_context(
        conversation_api_messages=session_messages_as_api(session),
        model=model,
        system_prompt="",
        tool_schemas=tool_schemas,
        claude_md_content="",
    )
    lines = [
        f"used_tokens={data.total_tokens}",
        f"max_tokens={data.max_tokens}",
        f"percent_used={data.percentage}",
        f"context_files_loaded={len(data.memory_files)}",
    ]
    if data.percentage > 80:
        lines.append("warning=context window above 80%")
    return "\n".join(lines)
