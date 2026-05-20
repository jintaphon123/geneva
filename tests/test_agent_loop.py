"""Test agent loop with mocked provider to verify tool invocation."""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile
import time

from src.agent.conversation import Conversation
from src.providers.base import ChatResponse
from src.tool_system.context import ToolContext
from src.tool_system.agent_loop import compact_tool_result_for_history, run_agent_loop, AgentLoopResult
from src.tool_system.protocol import ToolResult
from src.tool_system.registry import ToolRegistry, ToolSpec


class TestWriteTool:
    """Small test-only file writer so agent-loop coverage is registry-agnostic."""

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="Write",
            description="Write a file for agent loop tests.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "file_path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["file_path", "content"],
            },
        )

    def run(self, tool_input: dict[str, str], context: ToolContext) -> ToolResult:
        path = context.ensure_allowed_path(tool_input["file_path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(tool_input["content"], encoding="utf-8")
        return ToolResult(
            name="Write",
            output={"file_path": str(path), "written": True},
        )


class TestLargeResultTool:
    """Returns a deliberately oversized payload for context-bloat tests."""

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="BigSearch",
            description="Return a large search result.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        )

    def run(self, tool_input: dict[str, str], context: ToolContext) -> ToolResult:
        return ToolResult(
            name="BigSearch",
            output={"query": tool_input["query"], "results": ["x " * 5000 for _ in range(4)]},
        )


class TestSlowTool:
    """Sleeps longer than its declared timeout."""

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="SlowTool",
            description="Sleep for timeout coverage.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {},
            },
            timeout_seconds=0.01,
        )

    def run(self, tool_input: dict[str, str], context: ToolContext) -> ToolResult:
        time.sleep(0.05)
        return ToolResult(name="SlowTool", output={"ok": True})


class TestAgentLoop(unittest.TestCase):
    """Test agent loop logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.registry = ToolRegistry([TestWriteTool()])
        self.context = ToolContext(workspace_root=self.workspace)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_agent_loop_calls_tool(self):
        """Test agent loop correctly dispatches a tool call from mocked LLM."""
        conversation = Conversation()
        conversation.add_user_message("Create a file hello.py with content print('hello world')")

        # Mock provider
        mock_provider = MagicMock()
        mock_provider.chat_stream_response.side_effect = NotImplementedError()

        # First response: tool use Write
        mock_tool_use = {
            "id": "toolu_123",
            "name": "Write",
            "input": {
                "file_path": str(self.workspace / "hello.py"),
                "content": "print('hello world')"
            }
        }
        mock_response1 = ChatResponse(
            content="I will create the file.",
            model="test-model",
            usage={"input_tokens": 10, "output_tokens": 20},
            finish_reason="tool_use",
            tool_uses=[mock_tool_use],
        )

        # Second response: final text after tool result
        mock_response2 = ChatResponse(
            content="File created successfully!",
            model="test-model",
            usage={"input_tokens": 30, "output_tokens": 10},
            finish_reason="stop",
            tool_uses=None,
        )

        mock_provider.chat.side_effect = [mock_response1, mock_response2]

        result = run_agent_loop(
            conversation=conversation,
            provider=mock_provider,
            tool_registry=self.registry,
            tool_context=self.context,
            verbose=False,
        )

        # Verify final response
        self.assertIsInstance(result, AgentLoopResult)
        self.assertEqual(result.response_text, "File created successfully!")

        # Verify provider was called twice
        self.assertEqual(mock_provider.chat.call_count, 2)

        # Verify file was created
        hello_py = self.workspace / "hello.py"
        self.assertTrue(hello_py.exists())
        self.assertEqual(hello_py.read_text(), "print('hello world')")

    def test_agent_loop_creates_hello_world(self):
        """Test agent loop creates hello.py and writes print('hello world')."""
        conversation = Conversation()
        conversation.add_user_message("Create a file hello.py with content print('hello world')")

        mock_provider = MagicMock()
        mock_provider.chat_stream_response.side_effect = NotImplementedError()

        # First response: tool use Write
        hello_path = self.workspace / "hello.py"
        mock_tool_write = {
            "id": "toolu_123",
            "name": "Write",
            "input": {
                "file_path": str(hello_path),
                "content": "print('hello world')"
            }
        }
        mock_response1 = ChatResponse(
            content="I will create the file.",
            model="test-model",
            usage={"input_tokens": 10, "output_tokens": 20},
            finish_reason="tool_use",
            tool_uses=[mock_tool_write],
        )

        # Second response: final
        mock_response2 = ChatResponse(
            content="File created successfully!",
            model="test-model",
            usage={"input_tokens": 30, "output_tokens": 10},
            finish_reason="stop",
            tool_uses=None,
        )

        mock_provider.chat.side_effect = [mock_response1, mock_response2]

        result = run_agent_loop(
            conversation=conversation,
            provider=mock_provider,
            tool_registry=self.registry,
            tool_context=self.context,
            verbose=False,
        )

        self.assertIsInstance(result, AgentLoopResult)
        self.assertEqual(result.response_text, "File created successfully!")
        self.assertTrue(hello_path.exists())
        self.assertEqual(hello_path.read_text(), "print('hello world')")

    def test_agent_loop_stream_emits_final_text_chunks(self):
        """Streaming mode emits final response chunks without changing the result."""
        conversation = Conversation()
        conversation.add_user_message("Say hello")

        mock_provider = MagicMock()
        mock_provider.chat_stream_response.side_effect = NotImplementedError()
        mock_provider.chat.return_value = ChatResponse(
            content="Hello from Geneva!",
            model="test-model",
            usage={"input_tokens": 3, "output_tokens": 4},
            finish_reason="stop",
            tool_uses=None,
        )

        chunks: list[str] = []
        result = run_agent_loop(
            conversation=conversation,
            provider=mock_provider,
            tool_registry=self.registry,
            tool_context=self.context,
            stream=True,
            verbose=False,
            on_text_chunk=chunks.append,
        )

        self.assertEqual("".join(chunks), "Hello from Geneva!")
        self.assertEqual(result.response_text, "Hello from Geneva!")
        self.assertEqual(mock_provider.chat.call_count, 1)
        self.assertEqual(len(conversation.messages), 2)
        self.assertEqual(conversation.messages[-1].role, "assistant")
        self.assertEqual(conversation.messages[-1].content, "Hello from Geneva!")

    def test_agent_loop_stream_only_emits_final_turn_text(self):
        """Streaming mode skips interim tool-planning text and emits the final answer only."""
        conversation = Conversation()
        conversation.add_user_message("Create a file hello.py with content print('hello world')")

        mock_provider = MagicMock()
        mock_provider.chat_stream_response.side_effect = NotImplementedError()
        hello_path = self.workspace / "hello.py"
        mock_response1 = ChatResponse(
            content="I will create the file.",
            model="test-model",
            usage={"input_tokens": 10, "output_tokens": 20},
            finish_reason="tool_use",
            tool_uses=[{
                "id": "toolu_123",
                "name": "Write",
                "input": {
                    "file_path": str(hello_path),
                    "content": "print('hello world')",
                },
            }],
        )
        mock_response2 = ChatResponse(
            content="File created successfully!",
            model="test-model",
            usage={"input_tokens": 30, "output_tokens": 10},
            finish_reason="stop",
            tool_uses=None,
        )
        mock_provider.chat.side_effect = [mock_response1, mock_response2]

        chunks: list[str] = []
        result = run_agent_loop(
            conversation=conversation,
            provider=mock_provider,
            tool_registry=self.registry,
            tool_context=self.context,
            stream=True,
            verbose=False,
            on_text_chunk=chunks.append,
        )

        self.assertEqual("".join(chunks), "File created successfully!")
        self.assertEqual(result.response_text, "File created successfully!")
        self.assertTrue(hello_path.exists())

    def test_agent_loop_stream_uses_structured_provider_streaming_for_tool_turns(self):
        """Structured provider streaming can emit pre-tool text and final text across turns."""
        conversation = Conversation()
        conversation.add_user_message("Create hello.py")

        provider = MagicMock()
        hello_path = self.workspace / "hello.py"

        stream_responses = [
            ChatResponse(
                content="I will create the file.",
                model="test-model",
                usage={"input_tokens": 10, "output_tokens": 20},
                finish_reason="tool_use",
                tool_uses=[{
                    "id": "toolu_123",
                    "name": "Write",
                    "input": {
                        "file_path": str(hello_path),
                        "content": "print('hello world')",
                    },
                }],
            ),
            ChatResponse(
                content="File created successfully!",
                model="test-model",
                usage={"input_tokens": 30, "output_tokens": 10},
                finish_reason="stop",
                tool_uses=None,
            ),
        ]

        def stream_side_effect(messages, tools=None, on_text_chunk=None, **kwargs):
            response = stream_responses.pop(0)
            if on_text_chunk is not None and response.content:
                on_text_chunk(response.content)
            return response

        provider.chat_stream_response.side_effect = stream_side_effect
        provider.chat.side_effect = AssertionError("chat() should not be used when structured streaming is available")

        chunks: list[str] = []
        result = run_agent_loop(
            conversation=conversation,
            provider=provider,
            tool_registry=self.registry,
            tool_context=self.context,
            stream=True,
            verbose=False,
            on_text_chunk=chunks.append,
        )

        self.assertEqual("".join(chunks), "I will create the file.File created successfully!")
        self.assertEqual(result.response_text, "File created successfully!")
        self.assertEqual(provider.chat_stream_response.call_count, 2)
        self.assertTrue(hello_path.exists())

    def test_agent_loop_stream_falls_back_when_structured_streaming_is_unavailable(self):
        """If the provider lacks structured streaming, the stable synchronous path still works."""
        conversation = Conversation()
        conversation.add_user_message("Say hello")

        provider = MagicMock()
        provider.chat_stream_response.side_effect = NotImplementedError()
        provider.chat.return_value = ChatResponse(
            content="Hello from fallback!",
            model="test-model",
            usage={"input_tokens": 2, "output_tokens": 3},
            finish_reason="stop",
            tool_uses=None,
        )

        chunks: list[str] = []
        result = run_agent_loop(
            conversation=conversation,
            provider=provider,
            tool_registry=self.registry,
            tool_context=self.context,
            stream=True,
            verbose=False,
            on_text_chunk=chunks.append,
        )

        self.assertEqual("".join(chunks), "Hello from fallback!")
        self.assertEqual(result.response_text, "Hello from fallback!")
        provider.chat.assert_called_once()

    def test_agent_loop_sets_default_output_token_firewall(self):
        """Provider calls must never inherit an expensive provider default output cap."""
        conversation = Conversation()
        conversation.add_user_message("Say hello")
        provider = MagicMock()
        provider.chat_stream_response.side_effect = NotImplementedError()
        provider.chat.return_value = ChatResponse(
            content="Hello",
            model="test-model",
            usage={"input_tokens": 2, "output_tokens": 3},
            finish_reason="stop",
            tool_uses=None,
        )

        run_agent_loop(
            conversation=conversation,
            provider=provider,
            tool_registry=self.registry,
            tool_context=self.context,
            verbose=False,
        )

        self.assertEqual(provider.chat.call_args.kwargs["max_tokens"], 4096)

    def test_agent_loop_caps_configured_output_tokens(self):
        conversation = Conversation()
        conversation.add_user_message("Say hello")
        provider = MagicMock()
        provider.chat_stream_response.side_effect = NotImplementedError()
        provider.chat.return_value = ChatResponse(
            content="Hello",
            model="test-model",
            usage={"input_tokens": 2, "output_tokens": 3},
            finish_reason="stop",
            tool_uses=None,
        )

        with patch.dict("os.environ", {"GENEVA_MAX_OUTPUT_TOKENS": "65536"}):
            run_agent_loop(
                conversation=conversation,
                provider=provider,
                tool_registry=self.registry,
                tool_context=self.context,
                verbose=False,
            )

        self.assertEqual(provider.chat.call_args.kwargs["max_tokens"], 8192)

    def test_agent_loop_auto_continues_output_token_limit(self):
        conversation = Conversation()
        conversation.add_user_message("Write the full implementation")
        provider = MagicMock()
        provider.chat_stream_response.side_effect = NotImplementedError()
        provider.chat.side_effect = [
            ChatResponse(
                content="first half ",
                model="test-model",
                usage={"input_tokens": 2, "output_tokens": 4096},
                finish_reason="length",
                tool_uses=None,
            ),
            ChatResponse(
                content="second half",
                model="test-model",
                usage={"input_tokens": 2, "output_tokens": 20},
                finish_reason="stop",
                tool_uses=None,
            ),
        ]
        chunks: list[str] = []

        result = run_agent_loop(
            conversation=conversation,
            provider=provider,
            tool_registry=self.registry,
            tool_context=self.context,
            stream=True,
            verbose=False,
            on_text_chunk=chunks.append,
        )

        self.assertEqual(result.response_text, "first half second half")
        self.assertEqual("".join(chunks), "first half second half")
        self.assertEqual(provider.chat.call_count, 2)
        second_call_messages = provider.chat.call_args_list[1].args[0]
        self.assertEqual(second_call_messages[-2], {"role": "assistant", "content": "first half "})
        self.assertEqual(second_call_messages[-1]["role"], "user")
        self.assertIn("Continue exactly", second_call_messages[-1]["content"])
        self.assertEqual([message.role for message in conversation.messages], ["user", "assistant"])
        self.assertEqual(conversation.messages[-1].content, "first half second half")

    def test_agent_loop_reports_when_continuation_limit_is_exhausted(self):
        conversation = Conversation()
        conversation.add_user_message("Write a very long answer")
        provider = MagicMock()
        provider.chat_stream_response.side_effect = NotImplementedError()
        provider.chat.side_effect = [
            ChatResponse(
                content="part one ",
                model="test-model",
                usage={"input_tokens": 2, "output_tokens": 4096},
                finish_reason="length",
                tool_uses=None,
            ),
            ChatResponse(
                content="part two",
                model="test-model",
                usage={"input_tokens": 2, "output_tokens": 4096},
                finish_reason="length",
                tool_uses=None,
            ),
        ]

        with patch.dict("os.environ", {"GENEVA_MAX_OUTPUT_CONTINUATIONS": "1"}):
            result = run_agent_loop(
                conversation=conversation,
                provider=provider,
                tool_registry=self.registry,
                tool_context=self.context,
                verbose=False,
            )

        self.assertEqual(provider.chat.call_count, 2)
        self.assertIn("part one part two", result.response_text)
        self.assertIn("automatic continuation limit", result.response_text)
        self.assertEqual(conversation.messages[-1].content, result.response_text)

    def test_agent_loop_does_not_fallback_after_provider_stream_error(self):
        """A real provider failure should surface once, not trigger a duplicate non-stream request."""
        conversation = Conversation()
        conversation.add_user_message("Say hello")
        provider = MagicMock()
        provider.chat_stream_response.side_effect = RuntimeError(
            "OpenRouter stream failed (402): {\"error\":{\"message\":\"requires more credits\"}}"
        )

        with self.assertRaises(RuntimeError):
            run_agent_loop(
                conversation=conversation,
                provider=provider,
                tool_registry=self.registry,
                tool_context=self.context,
                stream=True,
                verbose=False,
            )

        provider.chat.assert_not_called()

    def test_tool_timeout_returns_error_result_and_emits_trace(self):
        """A stuck tool must not freeze the ReAct loop."""
        conversation = Conversation()
        conversation.add_user_message("Run the slow tool")
        registry = ToolRegistry([TestSlowTool()])
        provider = MagicMock()
        provider.chat_stream_response.side_effect = NotImplementedError()
        provider.chat.side_effect = [
            ChatResponse(
                content="Running slow tool.",
                model="test-model",
                usage={"input_tokens": 1, "output_tokens": 1},
                finish_reason="tool_use",
                tool_uses=[{"id": "toolu_slow", "name": "SlowTool", "input": {}}],
            ),
            ChatResponse(
                content="Handled timeout.",
                model="test-model",
                usage={"input_tokens": 1, "output_tokens": 1},
                finish_reason="stop",
                tool_uses=None,
            ),
        ]
        events = []

        result = run_agent_loop(
            conversation=conversation,
            provider=provider,
            tool_registry=registry,
            tool_context=self.context,
            verbose=False,
            on_event=events.append,
        )

        self.assertEqual(result.response_text, "Handled timeout.")
        timeout_event = next(event for event in events if event.kind == "tool_timeout")
        self.assertEqual(timeout_event.tool_name, "SlowTool")
        self.assertEqual(timeout_event.status, "timeout")
        self.assertTrue(timeout_event.is_error)
        self.assertIsNotNone(timeout_event.duration_ms)
        second_call_messages = provider.chat.call_args_list[1].args[0]
        tool_message = next(message for message in second_call_messages if message["role"] == "tool")
        self.assertIn("timed out", tool_message["content"])

    def test_agent_loop_emits_turn_telemetry_events(self):
        conversation = Conversation()
        conversation.add_user_message("Say hello")
        provider = MagicMock()
        provider.chat_stream_response.side_effect = NotImplementedError()
        provider.chat.return_value = ChatResponse(
            content="Hello",
            model="test-model",
            usage={"input_tokens": 2, "output_tokens": 3},
            finish_reason="stop",
            tool_uses=None,
        )
        events = []

        run_agent_loop(
            conversation=conversation,
            provider=provider,
            tool_registry=self.registry,
            tool_context=self.context,
            verbose=False,
            on_event=events.append,
        )

        self.assertEqual(events[0].kind, "agent_turn_start")
        self.assertEqual(events[1].kind, "agent_turn_complete")
        self.assertEqual(events[1].status, "complete")

    def test_large_tool_result_is_compacted_before_reentering_history(self):
        """Huge tool output is shortened before being sent back to the model."""
        conversation = Conversation()
        conversation.add_user_message("Search a lot")
        registry = ToolRegistry([TestLargeResultTool()])
        provider = MagicMock()
        provider.chat_stream_response.side_effect = NotImplementedError()
        provider.chat.side_effect = [
            ChatResponse(
                content="Searching.",
                model="test-model",
                usage={"input_tokens": 10, "output_tokens": 5},
                finish_reason="tool_use",
                tool_uses=[{
                    "id": "toolu_big",
                    "name": "BigSearch",
                    "input": {"query": "oversized"},
                }],
            ),
            ChatResponse(
                content="Compacted result handled.",
                model="test-model",
                usage={"input_tokens": 20, "output_tokens": 5},
                finish_reason="stop",
                tool_uses=None,
            ),
        ]

        result = run_agent_loop(
            conversation=conversation,
            provider=provider,
            tool_registry=registry,
            tool_context=self.context,
            verbose=False,
        )
        second_call_messages = provider.chat.call_args_list[1].args[0]
        tool_message = next(message for message in second_call_messages if message["role"] == "tool")

        self.assertEqual(result.response_text, "Compacted result handled.")
        self.assertIn("[tool result compacted]", tool_message["content"])
        self.assertLess(len(tool_message["content"]), 5000)

    def test_small_tool_result_is_left_intact(self):
        payload = {"ok": True, "message": "short"}

        self.assertEqual(compact_tool_result_for_history("SmallTool", payload), payload)

    def test_web_search_compaction_preserves_titles_urls_without_full_blob(self):
        huge_snippet = "useful summary " + ("noise " * 4000) + "TAIL_MARKER"
        payload = {
            "query": "geneva memory systems",
            "results": [
                {
                    "title": "Memory architecture reference",
                    "url": "https://example.com/memory",
                    "snippet": huge_snippet,
                }
                for _ in range(4)
            ],
        }

        compacted = compact_tool_result_for_history("WebSearch", payload)

        self.assertIsInstance(compacted, str)
        self.assertIn("[tool result compacted]", compacted)
        self.assertIn("Memory architecture reference", compacted)
        self.assertIn("https://example.com/memory", compacted)
        self.assertNotIn("TAIL_MARKER", compacted)
        self.assertLess(len(compacted), 5000)

    def test_web_fetch_compaction_preserves_url_and_preview(self):
        payload = {
            "url": "https://example.com/deep-context",
            "content_type": "text/html",
            "content": "Important thesis. " + ("body " * 5000) + "TAIL_MARKER",
        }

        compacted = compact_tool_result_for_history("WebFetch", payload)

        self.assertIsInstance(compacted, str)
        self.assertIn("https://example.com/deep-context", compacted)
        self.assertIn("Content preview:", compacted)
        self.assertNotIn("TAIL_MARKER", compacted)
        self.assertLess(len(compacted), 5000)

    def test_read_binary_compaction_omits_base64_payload(self):
        payload = {
            "type": "image",
            "file": {
                "filePath": "/tmp/mock.png",
                "type": "image/png",
                "originalSize": 12000,
                "base64": "A" * 12000,
            },
        }

        compacted = compact_tool_result_for_history("Read", payload)

        self.assertIsInstance(compacted, str)
        self.assertIn("Binary/base64 content omitted from history.", compacted)
        self.assertNotIn("A" * 200, compacted)

    def test_bash_compaction_preserves_exit_and_output_previews(self):
        payload = {
            "cwd": "/workspace",
            "exit_code": 2,
            "stdout": "first line\n" + ("stdout noise " * 1200),
            "stderr": "fatal error\n" + ("stderr noise " * 1200),
        }

        compacted = compact_tool_result_for_history("Bash", payload)

        self.assertIsInstance(compacted, str)
        self.assertIn("Exit code: 2", compacted)
        self.assertIn("stdout preview:", compacted)
        self.assertIn("fatal error", compacted)
        self.assertLess(len(compacted), 5000)


if __name__ == "__main__":
    unittest.main()
