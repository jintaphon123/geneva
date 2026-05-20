"""Conversation management for Geneva."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union
from datetime import datetime


@dataclass
class TextContentBlock:
    """A text content block."""
    type: str = "text"
    text: str = ""


@dataclass
class ToolUseContentBlock:
    """A tool use content block."""
    type: str = "tool_use"
    id: str = ""
    name: str = ""
    input: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResultContentBlock:
    """A tool result content block."""
    type: str = "tool_result"
    tool_use_id: str = ""
    content: Union[str, list[dict[str, Any]]] = ""
    is_error: bool = False


ContentBlock = Union[TextContentBlock, ToolUseContentBlock, ToolResultContentBlock]
MessageContent = Union[str, list[ContentBlock], list[dict[str, Any]]]


def _is_raw_content_list(content: object) -> bool:
    return isinstance(content, list) and bool(content) and isinstance(content[0], dict)


def _is_multimodal_content_list(content: object) -> bool:
    return _is_raw_content_list(content) and any(
        isinstance(block, dict) and block.get("type") == "image"
        for block in content
    )


def _text_from_content(content: MessageContent) -> str:
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content:
        if isinstance(block, TextContentBlock):
            parts.append(block.text)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text") or ""))
    return " ".join(part for part in parts if part)


@dataclass
class Message:
    """Conversation message."""
    role: str  # "user", "assistant", "system"
    content: MessageContent
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    # Internal marker for messages that should be filtered from API (e.g., compact boundary)
    _is_internal: bool = field(default=False, repr=False)


@dataclass
class Conversation:
    """Conversation manager."""
    messages: list[Message] = field(default_factory=list)
    max_history: int = 100

    def add_message(self, role: str, content: MessageContent):
        """Add a message to conversation."""
        if len(self.messages) >= self.max_history:
            self.messages.pop(0)

        self.messages.append(Message(role=role, content=content))

    def add_user_message(self, text: str):
        """Add a plain user text message."""
        self.add_message("user", text)

    def add_user_message_with_images(self, text: str, images: list[dict[str, str]]) -> None:
        """Add a user message with text and image content blocks."""
        content: list[dict[str, Any]] = [{"type": "text", "text": text}]
        for img in images:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": img.get("media_type", "image/jpeg"),
                    "data": img["data"],
                },
            })
        self.add_message("user", content)

    def add_assistant_message(self, content: MessageContent):
        """Add an assistant message (text or tool use)."""
        self.add_message("assistant", content)

    def add_tool_result_message(self, tool_use_id: str, content: Union[str, list[dict]], is_error: bool = False):
        """Add a tool result message."""
        block = ToolResultContentBlock(
            type="tool_result",
            tool_use_id=tool_use_id,
            content=content,
            is_error=is_error
        )
        self.add_message("user", [block])

    def get_messages(self) -> list[dict]:
        """Get messages in API format (Anthropic style)."""
        api_messages = []
        for msg in self.messages:
            # Skip internal messages (e.g., compact boundary markers)
            if getattr(msg, "_is_internal", False):
                continue
            if isinstance(msg.content, str):
                api_messages.append({"role": msg.role, "content": msg.content})
            elif _is_raw_content_list(msg.content):
                api_messages.append({"role": msg.role, "content": msg.content})
            else:
                content_blocks = []
                for block in msg.content:
                    if isinstance(block, TextContentBlock):
                        content_blocks.append({"type": "text", "text": block.text})
                    elif isinstance(block, ToolUseContentBlock):
                        content_blocks.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input
                        })
                    elif isinstance(block, ToolResultContentBlock):
                        content_blocks.append({
                            "type": "tool_result",
                            "tool_use_id": block.tool_use_id,
                            "content": block.content,
                            "is_error": block.is_error
                        })
                api_messages.append({"role": msg.role, "content": content_blocks})
        return api_messages

    def get_display_messages(self) -> list[dict]:
        """Get messages for frontend display — includes timestamp and stable id.

        Do NOT use this for AI provider calls. Use get_messages() for that.
        """
        display_messages = []
        idx = 0
        for msg in self.messages:
            if getattr(msg, "_is_internal", False):
                continue
            if isinstance(msg.content, str):
                content_out: str | list = msg.content
            elif _is_raw_content_list(msg.content):
                content_out = msg.content
            else:
                content_out = []
                for block in msg.content:
                    if isinstance(block, TextContentBlock):
                        content_out.append({"type": "text", "text": block.text})
                    elif isinstance(block, ToolUseContentBlock):
                        content_out.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input,
                        })
                    elif isinstance(block, ToolResultContentBlock):
                        content_out.append({
                            "type": "tool_result",
                            "tool_use_id": block.tool_use_id,
                            "content": block.content,
                            "is_error": block.is_error,
                        })
            display_messages.append({
                "id": f"msg-{idx}",
                "role": msg.role,
                "content": content_out,
                "timestamp": msg.timestamp,
            })
            idx += 1
        return display_messages

    def truncate_at_display_index(self, display_idx: int) -> str | None:
        """Remove message at display_idx and everything after it.

        Returns the text of the removed message, or None if out of range.
        display_idx matches the 'id' field from get_display_messages() (e.g. "msg-3" → 3).
        """
        display_count = 0
        for actual_idx, msg in enumerate(self.messages):
            if getattr(msg, "_is_internal", False):
                continue
            if display_count == display_idx:
                removed = self.messages[actual_idx]
                self.messages = self.messages[:actual_idx]
                return _text_from_content(removed.content)
            display_count += 1
        return None

    def remove_last_assistant(self) -> str | None:
        """Remove last assistant message and return the last user message (for retry), or None.

        Returns the text of the last user message remaining after truncation, or None if no
        assistant message exists to remove.
        """
        last_assistant_idx: int | None = None
        for idx, msg in enumerate(self.messages):
            if getattr(msg, "_is_internal", False):
                continue
            if msg.role == "assistant":
                last_assistant_idx = idx

        if last_assistant_idx is None:
            return None

        # Find the user message immediately before the last assistant
        last_user_idx: int | None = None
        last_user_text: str | None = None
        for idx in range(last_assistant_idx - 1, -1, -1):
            msg = self.messages[idx]
            if getattr(msg, "_is_internal", False):
                continue
            if msg.role == "user":
                last_user_idx = idx
                last_user_text = _text_from_content(msg.content)
                break

        # Cut from the user message onwards so sendTurn can re-add it cleanly
        cut_at = last_user_idx if last_user_idx is not None else last_assistant_idx
        self.messages = self.messages[:cut_at]
        return last_user_text

    def clear(self):
        """Clear conversation."""
        self.messages.clear()

    def to_dict(self) -> dict:
        """Serialize conversation."""
        messages_data = []
        for msg in self.messages:
            if isinstance(msg.content, str):
                content_data = msg.content
            elif _is_raw_content_list(msg.content):
                content_data = msg.content
            else:
                content_data = []
                for block in msg.content:
                    if isinstance(block, TextContentBlock):
                        content_data.append({"type": "text", "text": block.text})
                    elif isinstance(block, ToolUseContentBlock):
                        content_data.append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input
                        })
                    elif isinstance(block, ToolResultContentBlock):
                        content_data.append({
                            "type": "tool_result",
                            "tool_use_id": block.tool_use_id,
                            "content": block.content,
                            "is_error": block.is_error
                        })
            messages_data.append({
                "role": msg.role,
                "content": content_data,
                "timestamp": msg.timestamp,
                "_is_internal": getattr(msg, "_is_internal", False),
            })
        return {
            "messages": messages_data,
            "max_history": self.max_history
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Conversation':
        """Deserialize conversation."""
        conv = cls(max_history=data.get("max_history", 100))
        for msg_data in data.get("messages", []):
            content = msg_data["content"]
            if isinstance(content, str):
                msg_content = content
            elif _is_multimodal_content_list(content):
                msg_content = content
            else:
                msg_content = []
                for block_data in content:
                    block_type = block_data.get("type")
                    if block_type == "text":
                        msg_content.append(TextContentBlock(type="text", text=block_data.get("text", "")))
                    elif block_type == "tool_use":
                        msg_content.append(ToolUseContentBlock(
                            type="tool_use",
                            id=block_data.get("id", ""),
                            name=block_data.get("name", ""),
                            input=block_data.get("input", {})
                        ))
                    elif block_type == "tool_result":
                        msg_content.append(ToolResultContentBlock(
                            type="tool_result",
                            tool_use_id=block_data.get("tool_use_id", ""),
                            content=block_data.get("content", ""),
                            is_error=block_data.get("is_error", False)
                        ))
            conv.messages.append(Message(
                role=msg_data["role"],
                content=msg_content,
                timestamp=msg_data.get("timestamp", ""),
                _is_internal=msg_data.get("_is_internal", False),
            ))
        return conv
