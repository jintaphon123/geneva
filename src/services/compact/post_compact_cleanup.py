from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PostCompactCleanup:
    def cleanup(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen_tool_use_ids: set[str] = set()
        cleaned: list[dict[str, Any]] = []
        for message in messages:
            content = message.get("content")
            if isinstance(content, list):
                kept_blocks: list[dict[str, Any]] = []
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") == "tool_use" and block.get("id"):
                        seen_tool_use_ids.add(str(block["id"]))
                        kept_blocks.append(block)
                    elif block.get("type") == "tool_result":
                        tool_use_id = str(block.get("tool_use_id", ""))
                        if tool_use_id and tool_use_id in seen_tool_use_ids:
                            kept_blocks.append(block)
                    else:
                        kept_blocks.append(block)
                if kept_blocks:
                    cleaned.append({**message, "content": kept_blocks})
            else:
                cleaned.append(message)
        return cleaned
