"""
Tests for the compact service.
"""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Union
from unittest.mock import AsyncMock, MagicMock, patch

from src.agent.conversation import (
    Conversation,
    Message,
    TextContentBlock,
    ToolResultContentBlock,
    ToolUseContentBlock,
)
from src.providers.base import ChatResponse


class MockConversation:
    """Mock conversation for testing (simple list-based)."""

    def __init__(self, messages=None):
        self.messages = messages or []

    def get_messages(self):
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]

    def clear(self):
        self.messages.clear()


class TestCompactBoundaryMessages(unittest.TestCase):
    """Tests for compact boundary message creation."""

    def test_creates_boundary_message(self):
        """Boundary message is created with correct properties."""
        from src.compact_service.messages import create_compact_boundary_message, is_compact_boundary_message
        msg = create_compact_boundary_message(
            trigger="manual",
            pre_compact_token_count=5000,
            messages_summarized=10,
        )
        self.assertTrue(is_compact_boundary_message(msg))
        self.assertEqual(msg.role, "system")
        self.assertTrue(getattr(msg, "_is_internal", False))

    def test_non_boundary_is_not_boundary(self):
        """Regular messages are not boundary messages."""
        from src.compact_service.messages import is_compact_boundary_message
        msg = Message(role="user", content="Hello")
        self.assertFalse(is_compact_boundary_message(msg))

    def test_get_messages_after_boundary_with_no_boundary(self):
        """Returns all messages when no boundary exists."""
        from src.compact_service.messages import get_messages_after_boundary
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi"),
        ]
        result = get_messages_after_boundary(messages)
        self.assertEqual(len(result), 2)

    def test_get_messages_after_boundary_with_boundary(self):
        """Returns only messages after last boundary."""
        from src.compact_service.messages import create_compact_boundary_message, get_messages_after_boundary
        messages = [
            Message(role="user", content="Old"),
            Message(role="assistant", content="Old response"),
        ]
        boundary = create_compact_boundary_message(trigger="manual")
        messages.append(boundary)
        messages.append(Message(role="user", content="New"))
        messages.append(Message(role="assistant", content="New response"))

        result = get_messages_after_boundary(messages)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].content, "New")
        self.assertEqual(result[1].content, "New response")

    def test_summary_message_format(self):
        """Summary message has correct role and content."""
        from src.compact_service.messages import create_compact_summary_message
        msg = create_compact_summary_message(
            "The user was working on a Python project. "
            "They asked about implementing a feature."
        )
        self.assertEqual(msg.role, "user")
        # msg.content is a list of ContentBlock, not a single TextContentBlock
        self.assertIn("continued from a previous conversation", msg.content[0].text)


class TestCompactConversation(unittest.TestCase):
    """Tests for compact_conversation()."""

    def setUp(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tmpdir.cleanup()

    def _make_conversation(self, messages):
        """Create a Conversation with given messages."""
        conv = Conversation()
        conv.messages = messages
        return conv

    def test_not_enough_messages_raises(self):
        """Less than 2 messages raises ValueError."""
        from src.compact_service.service import compact_conversation
        conv = self._make_conversation([
            Message(role="user", content="Hello"),
        ])

        mock_provider = MagicMock()
        mock_provider.chat_async = AsyncMock(
            return_value=ChatResponse(content="Summary", model="test", usage={}, finish_reason="stop")
        )

        with self.assertRaises(ValueError) as ctx:
            asyncio.run(compact_conversation(conv, mock_provider, "claude-sonnet-4-6"))
        self.assertIn("Not enough messages", str(ctx.exception))

    def test_sync_fallback_on_llm_failure(self):
        """Falls back to sync extraction on LLM failure."""
        from src.compact_service.service import compact_conversation
        conv = self._make_conversation([
            Message(role="user", content="Hello world " * 50),
            Message(role="assistant", content="Hi there! " * 50),
            Message(role="user", content="What about the code? " * 50),
        ])

        mock_provider = MagicMock()
        mock_provider.chat_async = AsyncMock(side_effect=Exception("LLM failed"))
        mock_provider.chat = MagicMock(side_effect=Exception("Sync LLM failed"))

        result = asyncio.run(compact_conversation(conv, mock_provider, "claude-sonnet-4-6"))
        self.assertEqual(result.trigger, "manual")
        self.assertIn("Conversation had", result.summary_text)

    def test_boundary_and_summary_inserted(self):
        """Boundary and summary messages are inserted into conversation."""
        from src.compact_service.service import compact_conversation
        conv = self._make_conversation([
            Message(role="user", content="Hello world " * 50),
            Message(role="assistant", content="Hi there! " * 50),
            Message(role="user", content="What about the code? " * 50),
            Message(role="assistant", content="Here's the code... " * 50),
        ])
        mock_provider = MagicMock()
        mock_provider.chat_async = AsyncMock(
            return_value=ChatResponse(
                content="User worked on Python code. Assistant helped with implementation.",
                model="test",
                usage={},
                finish_reason="stop"
            )
        )

        result = asyncio.run(compact_conversation(conv, mock_provider, "claude-sonnet-4-6"))

        self.assertEqual(len(conv.messages), result.post_compact_count)

        # Check that internal boundary is present
        boundary = next(
            (m for m in conv.messages if getattr(m, "_is_internal", False)),
            None
        )
        self.assertIsNotNone(boundary)
        # Recent tail is preserved verbatim so the active task does not disappear.
        self.assertEqual(conv.messages[-1].content, "Here's the code... " * 50)

    def test_compact_preserves_fresh_tail(self):
        """Compaction summarizes old messages but keeps recent task state."""
        from src.compact_service.service import compact_conversation

        conv = self._make_conversation([
            Message(role="user", content=f"Old request {idx} " * 20)
            if idx % 2 == 0
            else Message(role="assistant", content=f"Old answer {idx} " * 20)
            for idx in range(10)
        ])
        tail_before = [msg.content for msg in conv.messages[-4:]]

        mock_provider = MagicMock()
        mock_provider.chat_async = AsyncMock(
            return_value=ChatResponse(
                content="Older work was summarized with decisions and files.",
                model="test",
                usage={},
                finish_reason="stop",
            )
        )

        result = asyncio.run(
            compact_conversation(
                conv,
                mock_provider,
                "claude-sonnet-4-6",
                fresh_tail_messages=4,
            )
        )

        self.assertEqual([msg.content for msg in conv.messages[-4:]], tail_before)
        self.assertLess(result.post_compact_count, 10)
        self.assertIn("Older work was summarized", result.summary_text)

    def test_compact_writes_context_ledger(self):
        """Compaction records what was summarized and what stayed raw."""
        from src.compact_service.service import compact_conversation
        from src.services.compact.context_ledger import list_context_ledger_records

        conv = self._make_conversation([
            Message(role="user", content=f"Request {idx} " * 30)
            if idx % 2 == 0
            else Message(role="assistant", content=f"Answer {idx} " * 30)
            for idx in range(8)
        ])

        mock_provider = MagicMock()
        mock_provider.chat_async = AsyncMock(
            return_value=ChatResponse(
                content="Compact summary with files, decisions, and next steps.",
                model="test",
                usage={},
                finish_reason="stop",
            )
        )

        result = asyncio.run(
            compact_conversation(
                conv,
                mock_provider,
                "claude-sonnet-4-6",
                fresh_tail_messages=2,
                session_id="compact-session",
                ledger_dir=Path(self.tmpdir.name) / "ledger",
            )
        )
        records = list_context_ledger_records(
            "compact-session",
            ledger_dir=Path(self.tmpdir.name) / "ledger",
        )

        self.assertIsNotNone(result.ledger_record)
        self.assertEqual(records[0]["event"], "compact")
        actions = {entry["action"] for entry in records[0]["entries"]}
        self.assertIn("compacted", actions)
        self.assertIn("preserved", actions)
        self.assertEqual(records[0]["metadata"]["fresh_tail_count"], 2)

    def test_custom_instructions_passed_to_llm(self):
        """Custom instructions are included in the prompt."""
        from src.compact_service.service import compact_conversation
        conv = self._make_conversation([
            Message(role="user", content="Hello " * 20),
            Message(role="assistant", content="Hi " * 20),
        ])

        captured_messages = []

        def capture_messages(*args, **kwargs):
            captured_messages.append(kwargs.get("messages", args[1] if len(args) > 1 else []))
            return ChatResponse(content="Summary", model="test", usage={}, finish_reason="stop")

        mock_provider = MagicMock()
        mock_provider.chat_async = AsyncMock(side_effect=capture_messages)

        asyncio.run(compact_conversation(
            conv, mock_provider, "claude-sonnet-4-6",
            custom_instructions="Focus on the Python code"
        ))

        # Custom instruction should appear in the last message
        self.assertGreater(len(captured_messages), 0)
        last_msg = captured_messages[0][-1] if captured_messages else {}
        self.assertIn("Focus on the Python code", last_msg.get("content", ""))


class TestCompactIntegration(unittest.TestCase):
    """Integration tests for compact with mock REPL flow."""

    def test_compact_preserves_boundary_marker_in_serialization(self):
        """Boundary markers are preserved when conversation is serialized."""
        from src.compact_service.messages import create_compact_boundary_message
        conv = Conversation()
        conv.messages.append(Message(role="user", content="Hello"))
        conv.messages.append(Message(role="assistant", content="Hi"))
        boundary = create_compact_boundary_message(trigger="manual", pre_compact_token_count=1000)
        conv.messages.append(boundary)

        # Serialize
        data = conv.to_dict()
        self.assertEqual(len(data["messages"]), 3)

        # Boundary should have _is_internal=True in serialized form
        boundary_data = data["messages"][2]
        self.assertTrue(boundary_data.get("_is_internal", False))

        # Deserialize
        restored = Conversation.from_dict(data)
        self.assertEqual(len(restored.messages), 3)

        # Boundary should still be internal
        self.assertTrue(getattr(restored.messages[2], "_is_internal", False))

        # get_messages() should skip internal messages
        api_messages = restored.get_messages()
        self.assertEqual(len(api_messages), 2)  # Only user + assistant

    def test_compact_result_dataclass(self):
        """CompactionResult dataclass has expected fields."""
        from src.command_system.types import CompactionResult
        result = CompactionResult(
            pre_compact_count=10,
            post_compact_count=2,
            tokens_saved=5000,
            trigger="manual",
            summary_preview="User worked on...",
        )
        self.assertEqual(result.pre_compact_count, 10)
        self.assertEqual(result.post_compact_count, 2)
        self.assertEqual(result.tokens_saved, 5000)
        self.assertEqual(result.trigger, "manual")
        self.assertIn("User worked on", result.summary_preview)


if __name__ == "__main__":
    unittest.main()
