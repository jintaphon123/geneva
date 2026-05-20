"""Anthropic provider implementation."""

from __future__ import annotations

from typing import Callable, Generator, Optional, Any

try:
    import anthropic  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    class _MissingAnthropic:
        class Anthropic:  # type: ignore[no-redef]
            def __init__(self, *args, **kwargs):
                raise ModuleNotFoundError(
                    "anthropic package is not installed. Install optional dependencies to use AnthropicProvider."
                )

    anthropic = _MissingAnthropic()

from src.services.model_normalizer import repair_tool_call_json as _repair_tool_json

from .base import BaseProvider, ChatResponse, MessageInput, TextChunkCallback


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider."""

    def __init__(
        self, api_key: str, base_url: Optional[str] = None, model: Optional[str] = None
    ):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            base_url: Base URL (optional)
            model: Default model (default: claude-sonnet-4-6)
        """
        super().__init__(api_key, base_url, model or "claude-sonnet-4-6")

        self._client_kwargs = {"api_key": api_key}
        if base_url:
            self._client_kwargs["base_url"] = base_url
        self.client = None

    def _ensure_client(self):
        if self.client is not None:
            return self.client
        self.client = anthropic.Anthropic(**self._client_kwargs)
        return self.client

    def _build_chat_response(self, response: Any) -> ChatResponse:
        """Convert Anthropic SDK response into the shared ChatResponse shape."""
        content_text = ""
        tool_uses: list[dict[str, Any]] = []

        for block in response.content:
            block_type = getattr(block, "type", "text")
            if block_type == "text":
                text_val = getattr(block, "text", "")
                if text_val is not None:
                    content_text += str(text_val)
            elif block_type == "tool_use":
                tool_uses.append({
                    "id": str(getattr(block, "id", "")),
                    "name": str(getattr(block, "name", "")),
                    "input": dict(getattr(block, "input", {})),
                })

        usage = getattr(response, "usage", None)
        return ChatResponse(
            content=content_text,
            model=getattr(response, "model", self.model or ""),
            usage={
                "input_tokens": getattr(usage, "input_tokens", 0),
                "output_tokens": getattr(usage, "output_tokens", 0),
            },
            finish_reason=str(getattr(response, "stop_reason", "stop")),
            tool_uses=tool_uses if tool_uses else None,
        )

    def chat(
        self,
        messages: list[MessageInput],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs
    ) -> ChatResponse:
        """Synchronous chat completion.

        Args:
            messages: List of chat messages
            tools: Optional list of tool schemas
            **kwargs: Additional parameters (model, max_tokens, temperature, etc.)

        Returns:
            Chat response
        """
        model = self._get_model(**kwargs)
        max_tokens = kwargs.get("max_tokens", 4096)

        system = kwargs.pop("system", None)

        # Convert messages to Anthropic format
        anthropic_messages = self._prepare_messages(messages)

        # Make API call
        client = self._ensure_client()
        extra_kwargs: dict[str, Any] = {}
        if tools:
            extra_kwargs["tools"] = tools

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=anthropic_messages,
            **({"system": system} if system else {}),
            **extra_kwargs,
            **{k: v for k, v in kwargs.items() if k not in ["model", "max_tokens", "tools"]},
        )

        return self._build_chat_response(response)

    def chat_stream(
        self,
        messages: list[MessageInput],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """Streaming chat completion.

        Args:
            messages: List of chat messages
            tools: Optional list of tool schemas
            **kwargs: Additional parameters

        Yields:
            Chunks of response content
        """
        model = self._get_model(**kwargs)
        max_tokens = kwargs.get("max_tokens", 4096)

        # Convert messages
        anthropic_messages = self._prepare_messages(messages)

        # Stream API call
        client = self._ensure_client()
        extra_kwargs: dict[str, Any] = {}
        if tools:
            extra_kwargs["tools"] = tools

        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            messages=anthropic_messages,
            **extra_kwargs,
            **{k: v for k, v in kwargs.items() if k not in ["model", "max_tokens", "tools"]},
        ) as stream:
            for text in stream.text_stream:
                yield text

    def chat_stream_response(
        self,
        messages: list[MessageInput],
        tools: Optional[list[dict[str, Any]]] = None,
        on_text_chunk: TextChunkCallback | None = None,
        on_tool_ready: Callable[[dict], None] | None = None,
        **kwargs
    ) -> ChatResponse:
        """Stream Anthropic events and return the final structured response."""
        model = self._get_model(**kwargs)
        max_tokens = kwargs.get("max_tokens", 4096)
        system = kwargs.pop("system", None)
        anthropic_messages = self._prepare_messages(messages)

        client = self._ensure_client()
        extra_kwargs: dict[str, Any] = {}
        if tools:
            extra_kwargs["tools"] = tools

        streamed_text = ""
        current_tool_id: str | None = None
        current_tool_name: str | None = None
        current_tool_json = ""
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            messages=anthropic_messages,
            **({"system": system} if system else {}),
            **extra_kwargs,
            **{k: v for k, v in kwargs.items() if k not in ["model", "max_tokens", "tools"]},
        ) as stream:
            for event in stream:
                event_type = str(getattr(event, "type", ""))
                event_class = event.__class__.__name__
                is_block_start = (
                    event_type == "content_block_start"
                    or "ContentBlockStart" in event_class
                )
                is_block_stop = (
                    event_type == "content_block_stop"
                    or "ContentBlockStop" in event_class
                )

                block = getattr(event, "content_block", None)
                if block is None:
                    block = getattr(event, "block", None)
                if is_block_start and getattr(block, "type", None) == "tool_use":
                    current_tool_id = str(getattr(block, "id", "") or "")
                    current_tool_name = str(getattr(block, "name", "") or "")
                    current_tool_json = ""

                delta = getattr(event, "delta", None)
                delta_type = getattr(delta, "type", None) if delta is not None else None
                if delta is not None and (
                    delta_type == "input_json_delta"
                    or hasattr(delta, "partial_json")
                ):
                    partial_json = getattr(delta, "partial_json", "")
                    if partial_json:
                        current_tool_json += str(partial_json)
                    continue

                text = None
                if delta_type == "text_delta":
                    text = getattr(delta, "text", None)
                elif delta is not None and hasattr(delta, "text"):
                    text = getattr(delta, "text", None)
                elif hasattr(event, "text"):
                    text = getattr(event, "text", None)

                if text:
                    text_piece = str(text)
                    streamed_text += text_piece
                    if on_text_chunk is not None:
                        on_text_chunk(text_piece)

                if is_block_stop and current_tool_id:
                    try:
                        if on_tool_ready is not None:
                            on_tool_ready({
                                "id": current_tool_id,
                                "name": current_tool_name or "",
                                "input": _repair_tool_json(current_tool_json) or {},
                            })
                    except Exception:
                        pass
                    finally:
                        current_tool_id = None
                        current_tool_name = None
                        current_tool_json = ""
            try:
                final_message = stream.get_final_message()
            except Exception:
                final_message = None

        if final_message is not None:
            response = self._build_chat_response(final_message)
            if on_text_chunk is not None and not streamed_text and response.content:
                on_text_chunk(response.content)
            return response

        return ChatResponse(
            content=streamed_text,
            model=model,
            usage={},
            finish_reason="stop",
            tool_uses=None,
        )

    def get_available_models(self) -> list[str]:
        """Get list of available Anthropic models.

        Returns:
            List of model names
        """
        return [
            # Claude 4 series (latest)
            "claude-sonnet-4-6",
            "claude-sonnet-4-5",
            "claude-sonnet-4-5-20250929",
            "claude-sonnet-4-0",
            "claude-sonnet-4-20250514",
            "claude-opus-4-6",
            "claude-opus-4-5",
            "claude-opus-4-5-20251101",
            "claude-opus-4-1",
            "claude-opus-4-1-20250805",
            "claude-opus-4-0",
            "claude-opus-4-20250514",
            "claude-haiku-4-5",
            "claude-haiku-4-5-20251001",
            # Legacy
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]
