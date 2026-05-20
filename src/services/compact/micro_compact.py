from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.token_estimation import count_tokens


@dataclass
class MicroCompact:
    max_tokens: int = 200

    def compress_message(self, message: dict[str, Any]) -> dict[str, Any]:
        content = message.get("content")
        if isinstance(content, str) and count_tokens(content) > self.max_tokens:
            return {**message, "content": self._summarize_text(content)}
        if isinstance(content, list):
            compressed_blocks: list[dict[str, Any]] = []
            for block in content:
                if not isinstance(block, dict):
                    compressed_blocks.append({"type": "text", "text": str(block)})
                    continue
                block_content = block.get("content")
                if isinstance(block_content, str) and count_tokens(block_content) > self.max_tokens:
                    compressed_blocks.append({**block, "content": self._summarize_text(block_content)})
                else:
                    compressed_blocks.append(block)
            return {**message, "content": compressed_blocks}
        return dict(message)

    def _summarize_text(self, text: str) -> str:
        words = text.split()
        preview = " ".join(words[: min(len(words), 64)])
        return f"[micro-compacted] {preview}"
