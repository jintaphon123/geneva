"""OpenRouter provider implementation."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable, Generator, Optional

from src.services.model_normalizer import repair_tool_call_json as _repair_tool_json

from .base import ChatResponse, MessageInput, TextChunkCallback
from .openai_compatible import OpenAICompatibleProvider
from .openai_compatible import _convert_to_openai_tool_schema


OPENROUTER_MODELS = [
    "deepseek/deepseek-v4-flash",
    "openrouter/free",
]
OPENROUTER_TIMEOUT_SECONDS = 60 * 60
OPENROUTER_DEFAULT_MAX_TOKENS = 4096
OPENROUTER_HARD_MAX_TOKENS = 8192
OPENROUTER_MAX_TOKENS_ENV = "GENEVA_OPENROUTER_MAX_TOKENS"
OPENROUTER_FREE_FALLBACK_MODEL = "openrouter/free"
OPENROUTER_FREE_FALLBACK_ENV = "GENEVA_OPENROUTER_FREE_FALLBACK"


class OpenRouterProvider(OpenAICompatibleProvider):
    """OpenRouter — unified gateway to 100+ models."""

    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "deepseek/deepseek-v4-flash"

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        super().__init__(api_key, base_url or self.DEFAULT_BASE_URL, model or self.DEFAULT_MODEL)

    def _create_client(self) -> Any:
        return None

    def chat(
        self,
        messages: list[MessageInput],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        payload = self._build_payload(messages, tools, stream=False, kwargs=kwargs)
        data = self._post_json(payload)
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        return ChatResponse(
            content=str(message.get("content") or ""),
            model=str(data.get("model") or payload["model"]),
            usage=self._usage_from_dict(data.get("usage")),
            finish_reason=str(choice.get("finish_reason") or "stop"),
            reasoning_content=_optional_string(message.get("reasoning_content")),
            tool_uses=self._tool_uses_from_message(message) or None,
        )

    def chat_stream(
        self,
        messages: list[MessageInput],
        tools: Optional[list[dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        payload = self._build_payload(messages, tools, stream=True, kwargs=kwargs)
        for event in self._stream_events(payload):
            choices = event.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            content = delta.get("content")
            if content:
                yield str(content)

    def chat_stream_response(
        self,
        messages: list[MessageInput],
        tools: Optional[list[dict[str, Any]]] = None,
        on_text_chunk: TextChunkCallback | None = None,
        on_tool_ready: Callable[[dict], None] | None = None,
        **kwargs: Any,
    ) -> ChatResponse:
        payload = self._build_payload(messages, tools, stream=True, kwargs=kwargs)
        content_parts: list[str] = []
        reasoning_parts: list[str] = []
        response_model = str(payload["model"])
        finish_reason = "stop"
        usage: dict[str, Any] = {}
        tool_calls_by_index: dict[int, dict[str, str]] = {}

        for event in self._stream_events(payload):
            response_model = str(event.get("model") or response_model)
            if isinstance(event.get("usage"), dict):
                usage = self._usage_from_dict(event["usage"])

            choices = event.get("choices") or []
            if not choices:
                continue
            choice = choices[0]
            if choice.get("finish_reason"):
                finish_reason = str(choice["finish_reason"])

            delta = choice.get("delta") or {}
            content = delta.get("content")
            if content:
                piece = str(content)
                content_parts.append(piece)
                if on_text_chunk is not None:
                    on_text_chunk(piece)

            reasoning = delta.get("reasoning_content")
            if reasoning:
                reasoning_parts.append(str(reasoning))

            for tool_call in delta.get("tool_calls") or []:
                index = int(tool_call.get("index") or 0)
                entry = tool_calls_by_index.setdefault(
                    index,
                    {"id": "", "name": "", "arguments": ""},
                )
                if tool_call.get("id"):
                    entry["id"] = str(tool_call["id"])
                function = tool_call.get("function") or {}
                if function.get("name"):
                    entry["name"] += str(function["name"])
                if function.get("arguments"):
                    entry["arguments"] += str(function["arguments"])

        return ChatResponse(
            content="".join(content_parts),
            model=response_model,
            usage=usage,
            finish_reason=finish_reason,
            reasoning_content="".join(reasoning_parts) if reasoning_parts else None,
            tool_uses=self._tool_uses_from_deltas(tool_calls_by_index) or None,
        )

    def get_available_models(self) -> list[str]:
        return OPENROUTER_MODELS

    def _build_payload(
        self,
        messages: list[MessageInput],
        tools: Optional[list[dict[str, Any]]],
        *,
        stream: bool,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        bounded_kwargs = dict(kwargs)
        bounded_kwargs["max_tokens"] = _bounded_openrouter_max_tokens(kwargs.get("max_tokens"))
        payload: dict[str, Any] = {
            "model": self._get_model(**kwargs),
            "messages": self._prepare_messages(messages),
            "stream": stream,
        }
        if tools:
            converted = [_convert_to_openai_tool_schema(tool) for tool in tools]
            payload["tools"] = [tool for tool in converted if tool is not None]
        for key, value in bounded_kwargs.items():
            if key not in {"model", "tools"}:
                payload[key] = value
        return payload

    def _post_json(self, payload: dict[str, Any], *, allow_free_fallback: bool = True) -> dict[str, Any]:
        request = urllib.request.Request(
            self._chat_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=OPENROUTER_TIMEOUT_SECONDS) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if allow_free_fallback and _should_retry_with_free_model(payload, exc.code, detail):
                return self._post_json(_free_fallback_payload(payload), allow_free_fallback=False)
            raise RuntimeError(f"OpenRouter request failed ({exc.code}): {detail}") from exc

    def _stream_events(
        self,
        payload: dict[str, Any],
        *,
        allow_free_fallback: bool = True,
    ) -> Generator[dict[str, Any], None, None]:
        request = urllib.request.Request(
            self._chat_url(),
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=OPENROUTER_TIMEOUT_SECONDS) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if not data or data == "[DONE]":
                        continue
                    yield json.loads(data)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if allow_free_fallback and _should_retry_with_free_model(payload, exc.code, detail):
                yield from self._stream_events(_free_fallback_payload(payload), allow_free_fallback=False)
                return
            raise RuntimeError(f"OpenRouter stream failed ({exc.code}): {detail}") from exc

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://secondbrain.local",
            "X-Title": "Geneva",
        }

    def _chat_url(self) -> str:
        base_url = (self.base_url or self.DEFAULT_BASE_URL).rstrip("/")
        return f"{base_url}/chat/completions"

    def _usage_from_dict(self, usage: Any) -> dict[str, Any]:
        if not isinstance(usage, dict):
            return {}
        return {
            "input_tokens": int(usage.get("prompt_tokens") or 0),
            "output_tokens": int(usage.get("completion_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
        }

    def _tool_uses_from_message(self, message: dict[str, Any]) -> list[dict[str, Any]]:
        tool_uses: list[dict[str, Any]] = []
        for tool_call in message.get("tool_calls") or []:
            function = tool_call.get("function") or {}
            tool_uses.append(
                {
                    "id": str(tool_call.get("id") or ""),
                    "name": str(function.get("name") or ""),
                    "input": _json_object(function.get("arguments")),
                }
            )
        return [tool_use for tool_use in tool_uses if tool_use["name"]]

    def _tool_uses_from_deltas(self, deltas: dict[int, dict[str, str]]) -> list[dict[str, Any]]:
        tool_uses: list[dict[str, Any]] = []
        for index in sorted(deltas):
            item = deltas[index]
            if not item["name"]:
                continue
            tool_uses.append(
                {
                    "id": item["id"] or f"tool_call_{index}",
                    "name": item["name"],
                    "input": _json_object(item["arguments"]),
                }
            )
        return tool_uses


def _json_object(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    return _repair_tool_json(str(raw)) or {}


def _optional_string(value: Any) -> str | None:
    return str(value) if value else None


def _free_fallback_enabled() -> bool:
    return os.environ.get(OPENROUTER_FREE_FALLBACK_ENV, "1").strip().lower() not in {"0", "false", "no"}


def _should_retry_with_free_model(payload: dict[str, Any], status_code: int, detail: str) -> bool:
    if not _free_fallback_enabled():
        return False
    if status_code != 402:
        return False
    if str(payload.get("model") or "") == OPENROUTER_FREE_FALLBACK_MODEL:
        return False
    lowered = detail.lower()
    return _contains_any(
        lowered,
        (
            "insufficient credits",
            "never purchased credits",
            "requires more credits",
            "can only afford",
            "or fewer max_tokens",
        ),
    )


def _free_fallback_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, "model": OPENROUTER_FREE_FALLBACK_MODEL}


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _bounded_openrouter_max_tokens(value: Any = None) -> int:
    if value is None:
        value = os.environ.get(OPENROUTER_MAX_TOKENS_ENV)
    try:
        tokens = int(value)
    except (TypeError, ValueError):
        tokens = OPENROUTER_DEFAULT_MAX_TOKENS
    return min(max(tokens, 512), OPENROUTER_HARD_MAX_TOKENS)
