"""
Compact service for /compact command.

Handles the full compaction flow:
1. Pre-process messages (microcompact, strip images)
2. Call LLM to generate summary
3. Return boundary marker + summary messages
4. Update conversation in place
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from ..agent.conversation import Conversation, Message
from ..context_system.microcompact import microcompact_messages, strip_images_from_messages
from ..services.compact.context_ledger import (
    append_context_ledger_record,
    build_compact_context_ledger,
    new_context_ledger_id,
)
from ..providers.base import BaseProvider
from .messages import (
    create_compact_boundary_message,
    create_compact_summary_message,
    get_messages_after_boundary,
    is_compact_boundary_message,
)

logger = logging.getLogger(__name__)

# Maximum output tokens for the summary model
COMPACT_MAX_OUTPUT_TOKENS = 4096

# No-tools preamble prepended to the summary prompt
NO_TOOLS_PREAMBLE = """CRITICAL: Respond with TEXT ONLY. Do NOT call any tools.
Do NOT use Read, Bash, Grep, or any other tool. Your entire response must be plain text.
"""

SUMMARY_PROMPT_TEMPLATE = NO_TOOLS_PREAMBLE + """
Your task is to create a detailed summary of the conversation so far.

Include:
1. Primary Request and Intent: What the user asked for
2. Key Technical Concepts: Technologies, frameworks, patterns discussed
3. Files and Code Sections: Files examined, modified, or created (with snippets)
4. Errors and Fixes: Problems encountered and how they were resolved
5. Problem Solving: What was accomplished
6. All User Messages: All non-tool-result user messages
7. Pending Tasks: Tasks explicitly requested but not yet done
8. Current Work: What was being worked on immediately before this summary
9. Optional Next Step: Next step in line with recent requests

Respond ONLY with plain text. No tools. No XML tags.
"""


@dataclass
class CompactResult:
    """Result of a compaction operation."""
    boundary_message: Message
    summary_message: Message
    tokens_saved: int
    pre_compact_count: int
    post_compact_count: int
    summary_text: str
    trigger: str = "manual"
    user_display_message: Optional[str] = None
    ledger_record: dict[str, Any] | None = None


async def compact_conversation(
    conversation: Conversation,
    provider: BaseProvider,
    model: str,
    custom_instructions: Optional[str] = None,
    trigger: str = "manual",
    fresh_tail_messages: int = 6,
    session_id: str | None = None,
    ledger_dir: Path | None = None,
) -> CompactResult:
    """
    Compact a conversation by summarizing older messages.

    This is the Python equivalent of the TypeScript compactConversation().
    It is NOT a 1:1 port — it omits features unavailable in a Python CLI:
    - Forked agent with cache sharing (no subprocess isolation in Python REPL)
    - Session memory (no disk-backed session memory extraction)
    - Reactive compact (no background compaction agent)
    - Hook system (no pre/post compact hooks in Geneva)

    Args:
        conversation: The live Conversation object (mutated in place)
        provider: The LLM provider for generating the summary
        model: Model name for the summary call
        custom_instructions: Optional user instructions for the summarizer
        trigger: "manual" or "auto"

    Returns:
        CompactResult with boundary, summary, and metadata
    """
    # Step 1: Get messages after the last boundary (skip already-summarized)
    messages = get_messages_after_boundary(conversation.messages)

    if len(messages) < 2:
        raise ValueError("Not enough messages to compact.")

    tail_count = min(max(0, fresh_tail_messages), max(0, len(messages) - 2))
    messages_to_summarize = messages[:-tail_count] if tail_count else messages
    fresh_tail = messages[-tail_count:] if tail_count else []

    if len(messages_to_summarize) < 2:
        raise ValueError("Not enough older messages to compact while preserving the fresh tail.")

    # Step 2: Count pre-compact tokens
    from ..token_estimation import count_messages_tokens
    api_messages = _messages_to_api(messages_to_summarize)
    pre_compact_tokens = count_messages_tokens(api_messages)
    pre_compact_count = len(conversation.messages)

    # Step 3: Microcompact — strip images and clear old tool results
    api_messages_stripped = strip_images_from_messages(api_messages)
    compacted_api, tokens_saved = microcompact_messages(api_messages_stripped)

    # Step 4: Build summary prompt
    prompt = SUMMARY_PROMPT_TEMPLATE
    if custom_instructions:
        prompt += f"\n\nAdditional instructions: {custom_instructions}"

    # Build messages for the summary API call
    # System prompt + recent messages + summary request
    summary_request_messages: list[dict[str, Any]] = []

    # Add the messages being replaced, not the protected fresh tail.
    context_messages = compacted_api[-20:] if len(compacted_api) > 20 else compacted_api
    for msg in context_messages:
        summary_request_messages.append(msg)

    # Add the summary request as the last user message
    summary_request_messages.append({
        "role": "user",
        "content": prompt,
    })

    # Step 5: Call the LLM to generate summary
    summary_text = ""
    try:
        response = await provider.chat_async(
            messages=summary_request_messages,
            tools=None,  # No tools during compaction
            model=model,
            max_tokens=COMPACT_MAX_OUTPUT_TOKENS,
        )
        summary_text = response.content.strip()
    except Exception as e:
        # Try sync fallback
        try:
            response = provider.chat(
                messages=summary_request_messages,
                tools=None,
                model=model,
                max_tokens=COMPACT_MAX_OUTPUT_TOKENS,
            )
            summary_text = response.content.strip()
        except Exception as e2:
            logger.warning(f"Compact LLM call failed: {e}, sync fallback: {e2}, using text extraction")
            summary_text = _fallback_summary(messages)

    if not summary_text:
        summary_text = _fallback_summary(messages)

    ledger_id = new_context_ledger_id("compact")

    # Step 6: Create boundary marker
    last_msg_uuid = None
    if messages_to_summarize:
        last_msg = messages_to_summarize[-1]
        if hasattr(last_msg, 'uuid'):
            last_msg_uuid = getattr(last_msg, 'uuid', None)
        elif isinstance(last_msg, dict):
            last_msg_uuid = last_msg.get("uuid")

    boundary_msg = create_compact_boundary_message(
        trigger=trigger,
        pre_compact_token_count=pre_compact_tokens,
        last_message_uuid=last_msg_uuid,
        messages_summarized=len(messages_to_summarize),
        context_ledger_id=ledger_id,
    )

    # Step 7: Create summary message
    summary_msg = create_compact_summary_message(
        summary_text,
        summarize_metadata={"context_ledger_id": ledger_id},
    )

    # Step 8: Insert boundary + summary into conversation
    # Find position after the last boundary marker
    boundary_indices = [
        i for i, m in enumerate(conversation.messages)
        if is_compact_boundary_message(m)
    ]

    if boundary_indices:
        insert_pos = max(boundary_indices) + 1
    else:
        insert_pos = 0

    # Remove only the older messages being summarized. Keep the fresh tail verbatim
    # so the model keeps immediate task state, recent user intent, and tool results.
    if insert_pos == 0:
        conversation.messages.clear()
        conversation.messages.append(boundary_msg)
        conversation.messages.append(summary_msg)
        conversation.messages.extend(fresh_tail)
    else:
        conversation.messages = list(conversation.messages[:insert_pos])
        conversation.messages.append(boundary_msg)
        conversation.messages.append(summary_msg)
        conversation.messages.extend(fresh_tail)

    post_compact_count = len(conversation.messages)
    post_compact_tokens = count_messages_tokens(conversation.get_messages())
    total_tokens_saved = max(0, pre_compact_tokens - post_compact_tokens)
    fresh_tail_tokens = count_messages_tokens(_messages_to_api(fresh_tail)) if fresh_tail else 0
    ledger_record = build_compact_context_ledger(
        record_id=ledger_id,
        session_id=session_id or "unknown",
        model=model,
        trigger=trigger,
        pre_compact_tokens=pre_compact_tokens,
        post_compact_tokens=post_compact_tokens,
        messages_summarized=len(messages_to_summarize),
        fresh_tail_count=len(fresh_tail),
        fresh_tail_tokens=fresh_tail_tokens,
        summary_text=summary_text,
        microcompact_tokens_saved=tokens_saved,
        total_tokens_saved=max(tokens_saved, total_tokens_saved),
        summary_request_message_count=len(context_messages),
    )
    if session_id:
        try:
            append_context_ledger_record(ledger_record, ledger_dir=ledger_dir)
        except Exception:
            logger.exception("Failed to write compact context ledger")

    # Step 9: Build user display message
    saved_str = f"~{tokens_saved:,}" if tokens_saved > 0 else "some"
    user_display = (
        f"Compacted conversation ({saved_str} tokens saved). "
        f"Pre-compact: {pre_compact_tokens:,} tokens. "
        f"Press Ctrl+O to see full summary."
    )

    return CompactResult(
        boundary_message=boundary_msg,
        summary_message=summary_msg,
        tokens_saved=max(tokens_saved, total_tokens_saved),
        pre_compact_count=pre_compact_count,
        post_compact_count=post_compact_count,
        summary_text=summary_text,
        trigger=trigger,
        user_display_message=user_display,
        ledger_record=ledger_record.to_dict(),
    )


def _messages_to_api(messages: list[Message]) -> list[dict[str, Any]]:
    conversation = Conversation()
    conversation.messages = list(messages)
    return conversation.get_messages()


def _fallback_summary(messages: list[Message]) -> str:
    """
    Generate a simple text fallback summary when the LLM call fails.
    """
    user_msgs: list[str] = []
    assistant_msgs: list[str] = []

    for msg in messages:
        role = getattr(msg, 'role', None)
        if role is None and isinstance(msg, dict):
            role = msg.get("role")

        content = getattr(msg, 'content', '')
        if content is None and isinstance(msg, dict):
            content = msg.get("content", "")

        if role == "user":
            if isinstance(content, str):
                user_msgs.append(content[:200])
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        user_msgs.append(block.get("text", "")[:200])
        elif role == "assistant":
            if isinstance(content, str):
                assistant_msgs.append(content[:200])
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        assistant_msgs.append(block.get("text", "")[:200])

    summary_parts = [f"Conversation had {len(messages)} messages."]

    # Extract tool use info
    tool_uses = []
    for msg in messages:
        content = getattr(msg, 'content', [])
        if isinstance(msg, dict):
            content = msg.get("content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_uses.append(block.get("name", ""))

    if tool_uses:
        summary_parts.append(f"Tools used: {', '.join(tool_uses[:10])}")

    if user_msgs:
        summary_parts.append(f"Last user message: {user_msgs[-1][:150]}")
    if assistant_msgs:
        summary_parts.append(f"Last assistant message: {assistant_msgs[-1][:150]}")

    return "\n".join(summary_parts)
