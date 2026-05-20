"""Agent loop for multi-turn tool calling."""

from __future__ import annotations

import json
import os
import queue
import threading
import concurrent.futures
import time
from dataclasses import dataclass
from typing import Any, Callable

from .protocol import ToolCall, ToolResult
from .registry import ToolRegistry
from .context import ToolContext
if __package__ == "tool_system":
    from src.agent.conversation import Conversation, TextContentBlock, ToolUseContentBlock
    from src.context_system import build_context_prompt
    from src.outputStyles import resolve_output_style
    from src.providers.base import BaseProvider, ChatResponse
    from src.providers.anthropic_provider import AnthropicProvider
    from src.providers.minimax_provider import MinimaxProvider
    from src.services.model_normalizer import adapt_tool_schemas, get_compensation_config, record_outcome
    from src.services.model_router import classify_model_tier
    from src.token_estimation import count_tokens
else:
    from ..agent.conversation import Conversation, TextContentBlock, ToolUseContentBlock
    from ..context_system import build_context_prompt
    from ..outputStyles import resolve_output_style
    from ..providers.base import BaseProvider, ChatResponse
    from ..providers.anthropic_provider import AnthropicProvider
    from ..providers.minimax_provider import MinimaxProvider
    from ..services.model_normalizer import adapt_tool_schemas, get_compensation_config, record_outcome
    from ..services.model_router import classify_model_tier
    from ..token_estimation import count_tokens

MAX_TOOL_RESULT_HISTORY_TOKENS = 1_600
MAX_TOOL_RESULT_HISTORY_CHARS = 8_000
TOOL_RESULT_PREVIEW_CHARS = 4_000
TOOL_RESULT_FACT_LIMIT = 8
TOOL_RESULT_TEXT_PREVIEW_CHARS = 1_600
DEFAULT_TOOL_TIMEOUT_SECONDS = 90.0
_MAX_CONCURRENT_TOOLS: int = int(os.environ.get("GENEVA_MAX_TOOL_CONCURRENCY", "4"))
DEFAULT_RESPONSE_MAX_TOKENS = 4096
MIN_RESPONSE_MAX_TOKENS = 512
HARD_RESPONSE_MAX_TOKENS = 8192
RESPONSE_MAX_TOKENS_ENV = "GENEVA_MAX_OUTPUT_TOKENS"
DEFAULT_RESPONSE_CONTINUATION_LIMIT = 3
HARD_RESPONSE_CONTINUATION_LIMIT = 8
RESPONSE_CONTINUATION_LIMIT_ENV = "GENEVA_MAX_OUTPUT_CONTINUATIONS"
OUTPUT_CONTINUATION_PROMPT = (
    "Continue exactly from where the previous assistant message stopped. "
    "Do not repeat earlier text, do not summarize, and keep the same format."
)
OUTPUT_TRUNCATION_NOTICE = (
    "\n\n[Response paused after reaching Geneva's automatic continuation limit. "
    "Send \"continue\" to keep going.]"
)


def _is_anthropic_provider(provider: BaseProvider) -> bool:
    return isinstance(provider, (AnthropicProvider, MinimaxProvider))


def _build_openai_tool_result_content(result_output: Any) -> str:
    """Format tool result as string for OpenAI/GLM."""
    if isinstance(result_output, str):
        return result_output
    return json.dumps(result_output, ensure_ascii=False)


def compact_tool_result_for_history(name: str, output: Any) -> Any:
    """Keep huge tool outputs from becoming permanent context bloat."""
    serialized = _serialize_tool_result(output)
    token_count = count_tokens(serialized)
    if token_count <= MAX_TOOL_RESULT_HISTORY_TOKENS and len(serialized) <= MAX_TOOL_RESULT_HISTORY_CHARS:
        return output

    structured_summary = _tool_specific_compacted_summary(name, output)
    body = (
        f"Structured summary:\n{structured_summary}"
        if structured_summary
        else f"Preview:\n{serialized[:TOOL_RESULT_PREVIEW_CHARS].rstrip()}"
    )
    summary = summarize_tool_result(name, output)
    return (
        "[tool result compacted]\n"
        f"Tool: {name}\n"
        f"Summary: {summary}\n"
        f"Original estimate: {token_count:,} tokens, {len(serialized):,} chars.\n"
        "Reason: result exceeded the context history budget and was shortened before storage.\n"
        f"{body}"
    )


def _serialize_tool_result(output: Any) -> str:
    if isinstance(output, str):
        return output
    try:
        return json.dumps(output, ensure_ascii=False, sort_keys=True, default=str)
    except Exception:
        return str(output)


def _tool_specific_compacted_summary(name: str, output: Any) -> str | None:
    if not isinstance(output, dict):
        return None
    lowered = name.lower()
    if lowered == "websearch":
        return _compact_web_search_output(output)
    if lowered == "webfetch":
        return _compact_web_fetch_output(output)
    if lowered == "read":
        return _compact_read_output(output)
    if lowered == "bash":
        return _compact_bash_output(output)
    if lowered == "grep":
        return _compact_grep_output(output)
    if lowered == "glob":
        return _compact_glob_output(output)
    return _compact_dict_output(output)


def _compact_web_search_output(output: dict[str, Any]) -> str:
    results = output.get("results")
    lines = [f"Query: {_as_compact_text(output.get('query'), 220)}"]
    if isinstance(results, list):
        lines.append(f"Results kept: {min(len(results), TOOL_RESULT_FACT_LIMIT)} of {len(results)}")
        for idx, item in enumerate(results[:TOOL_RESULT_FACT_LIMIT], start=1):
            if not isinstance(item, dict):
                lines.append(f"{idx}. {_as_compact_text(item, 240)}")
                continue
            title = _as_compact_text(item.get("title"), 180)
            url = _as_compact_text(item.get("url"), 260)
            snippet = _as_compact_text(item.get("snippet"), 320)
            lines.append(f"{idx}. {title}\n   URL: {url}\n   Snippet: {snippet}")
    return "\n".join(lines)


def _compact_web_fetch_output(output: dict[str, Any]) -> str:
    content = _as_compact_text(output.get("content"), TOOL_RESULT_TEXT_PREVIEW_CHARS)
    return "\n".join(
        [
            f"URL: {_as_compact_text(output.get('url'), 320)}",
            f"Content-Type: {_as_compact_text(output.get('content_type'), 160)}",
            f"Content chars: {len(str(output.get('content') or ''))}",
            "Content preview:",
            content,
        ]
    )


def _compact_read_output(output: dict[str, Any]) -> str:
    file_payload = output.get("file")
    if not isinstance(file_payload, dict):
        return _compact_dict_output(output)
    read_type = output.get("type")
    path = file_payload.get("filePath") or file_payload.get("file_path")
    lines = [f"Type: {_as_compact_text(read_type, 80)}", f"Path: {_as_compact_text(path, 360)}"]
    if read_type == "text":
        start = file_payload.get("startLine")
        count = file_payload.get("numLines")
        total = file_payload.get("totalLines")
        lines.append(f"Lines: {start}-{(start or 1) + (count or 0) - 1}/{total}")
        lines.extend(["Content preview:", _as_compact_text(file_payload.get("content"), TOOL_RESULT_TEXT_PREVIEW_CHARS)])
        return "\n".join(lines)
    if read_type in {"image", "pdf"}:
        lines.append(f"Original bytes: {file_payload.get('originalSize')}")
        if read_type == "image":
            lines.append(f"Mime type: {_as_compact_text(file_payload.get('type'), 80)}")
        lines.append("Binary/base64 content omitted from history.")
        return "\n".join(lines)
    if read_type == "notebook":
        cells = file_payload.get("cells")
        cell_count = len(cells) if isinstance(cells, list) else 0
        lines.append(f"Notebook cells: {cell_count}")
        if isinstance(cells, list) and cells:
            first = cells[0] if isinstance(cells[0], dict) else {}
            lines.append(f"First cell: {_as_compact_text(first.get('cell_type'), 80)}")
            lines.append(_as_compact_text(first.get("source"), 600))
        return "\n".join(lines)
    return "\n".join(lines)


def _compact_bash_output(output: dict[str, Any]) -> str:
    stdout = str(output.get("stdout") or "")
    stderr = str(output.get("stderr") or "")
    return "\n".join(
        [
            f"CWD: {_as_compact_text(output.get('cwd'), 360)}",
            f"Exit code: {output.get('exit_code')}",
            f"stdout chars: {len(stdout)}",
            "stdout preview:",
            _as_compact_text(stdout, 900),
            f"stderr chars: {len(stderr)}",
            "stderr preview:",
            _as_compact_text(stderr, 900),
        ]
    )


def _compact_grep_output(output: dict[str, Any]) -> str:
    filenames = output.get("filenames")
    lines = [
        f"Mode: {_as_compact_text(output.get('mode'), 120)}",
        f"Files matched: {output.get('numFiles')}",
        f"Matches: {output.get('numMatches', 'n/a')}",
        f"Offset: {output.get('appliedOffset', 0)}",
    ]
    if isinstance(filenames, list):
        lines.append(_format_list("Files", filenames, limit=TOOL_RESULT_FACT_LIMIT))
    if output.get("content"):
        lines.extend(["Content preview:", _as_compact_text(output.get("content"), TOOL_RESULT_TEXT_PREVIEW_CHARS)])
    return "\n".join(lines)


def _compact_glob_output(output: dict[str, Any]) -> str:
    filenames = output.get("filenames")
    lines = [f"Files returned: {output.get('numFiles')}", f"Truncated: {bool(output.get('truncated'))}"]
    if isinstance(filenames, list):
        lines.append(_format_list("Files", filenames, limit=12))
    return "\n".join(lines)


def _compact_dict_output(output: dict[str, Any]) -> str:
    lines = [f"Keys: {', '.join(str(key) for key in list(output.keys())[:12])}"]
    for key, value in list(output.items())[:TOOL_RESULT_FACT_LIMIT]:
        lines.append(f"{key}: {_as_compact_text(value, 300)}")
    return "\n".join(lines)


def _format_list(label: str, values: list[Any], *, limit: int) -> str:
    kept = values[:limit]
    lines = [f"{label} kept: {len(kept)} of {len(values)}"]
    lines.extend(f"- {_as_compact_text(value, 360)}" for value in kept)
    return "\n".join(lines)


def _as_compact_text(value: Any, limit: int) -> str:
    if value is None:
        text = ""
    elif isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
        except Exception:
            text = str(value)
    text = text.replace("\x00", "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n... [compacted] ..."


def summarize_tool_result(name: str, output: Any) -> str:
    """Create a concise, single-line summary for tool result output."""
    if not isinstance(output, dict):
        return str(output)
    if name.lower() == "write":
        path = output.get("filePath") or output.get("file_path")
        op = output.get("type")
        return f"{name} · {path} · {op}"
    if name.lower() == "edit":
        path = output.get("filePath") or output.get("file_path")
        replace_all = output.get("replaceAll")
        return f"{name} · {path} · replaceAll={replace_all}"
    if name.lower() == "read":
        if output.get("type") == "text" and isinstance(output.get("file"), dict):
            f = output["file"]
            path = f.get("filePath")
            num = f.get("numLines")
            total = f.get("totalLines")
            start = f.get("startLine")
            return f"{name} · {path} · lines={start}-{(start or 1) + (num or 0) - 1}/{total}"
        if output.get("type") == "file_unchanged" and isinstance(output.get("file"), dict):
            return f"{name} · {output['file'].get('filePath')} · unchanged"
        if output.get("type") in {"image", "pdf", "notebook"} and isinstance(output.get("file"), dict):
            return f"{name} · {output['file'].get('filePath')} · {output.get('type')}"
        return f"{name}"
    if name.lower() == "glob":
        n = output.get("numFiles")
        return f"{name} · matches={n}"
    if name.lower() == "grep":
        n = output.get("numFiles")
        mode = output.get("mode")
        return f"{name} · mode={mode} · files={n}"
    if name.lower() == "bash":
        code = output.get("exit_code")
        return f"{name} · exit={code}"
    if name.lower() == "webfetch":
        url = output.get("url")
        ct = output.get("content_type")
        return f"{name} · {url} · {ct}"
    if name.lower() == "websearch":
        q = output.get("query")
        results = output.get("results")
        n = len(results) if isinstance(results, list) else None
        return f"{name} · \"{q}\" · results={n}"
    if name.lower() == "config":
        op = output.get("operation")
        setting = output.get("setting")
        return f"{name} · {op} · {setting}"
    if name.lower() == "taskstop":
        tid = output.get("task_id")
        stopped = output.get("stopped")
        return f"{name} · {tid} · stopped={stopped}"
    if name.lower() == "sendusermessage":
        n = 0
        atts = output.get("attachments")
        if isinstance(atts, list):
            n = len(atts)
        return f"{name} · attachments={n}"
    # default: truncate dict keys for brevity
    keys = ", ".join(list(output.keys())[:3])
    return f"{name} · {keys}"


@dataclass(frozen=True)
class ToolEvent:
    kind: str
    tool_name: str
    tool_input: dict[str, Any] | None = None
    tool_output: Any | None = None
    tool_use_id: str | None = None
    is_error: bool = False
    error: str | None = None
    status: str | None = None
    summary: str | None = None
    turn_index: int | None = None
    started_at: float | None = None
    completed_at: float | None = None
    duration_ms: int | None = None
    timeout_seconds: float | None = None


@dataclass(frozen=True)
class AgentLoopResult:
    """Result of running the agent loop."""
    response_text: str
    usage: dict[str, Any] | None = None  # {"input_tokens": int, "output_tokens": int}
    num_turns: int = 0
    cancelled: bool = False


ToolEventHandler = Callable[[ToolEvent], None]
TextChunkHandler = Callable[[str], None]


def _safe_call_handler(handler: ToolEventHandler | None, event: ToolEvent) -> None:
    if handler is None:
        return
    try:
        handler(event)
    except Exception:
        return


def _emit_text_chunks(handler: TextChunkHandler | None, text: str, *, chunk_size: int = 12) -> None:
    """Emit text in small chunks for user-visible streaming without changing loop semantics."""
    if handler is None or not text:
        return
    if chunk_size <= 0:
        chunk_size = len(text)
    for idx in range(0, len(text), chunk_size):
        try:
            handler(text[idx: idx + chunk_size])
        except Exception:
            return


def _bounded_timeout_seconds(value: Any) -> float:
    try:
        timeout = float(value)
    except (TypeError, ValueError):
        return DEFAULT_TOOL_TIMEOUT_SECONDS
    if timeout <= 0:
        return DEFAULT_TOOL_TIMEOUT_SECONDS
    return min(timeout, 300.0)


def _prompt_cache_enabled() -> bool:
    """Return True if GENEVA_PROMPT_CACHE=1 env is set (Anthropic only)."""
    return os.environ.get("GENEVA_PROMPT_CACHE", "0").strip().lower() in {"1", "true", "yes"}


def _bounded_response_max_tokens(value: Any = None) -> int:
    if value is None:
        value = os.environ.get(RESPONSE_MAX_TOKENS_ENV)
    try:
        tokens = int(value)
    except (TypeError, ValueError):
        tokens = DEFAULT_RESPONSE_MAX_TOKENS
    return min(max(tokens, MIN_RESPONSE_MAX_TOKENS), HARD_RESPONSE_MAX_TOKENS)


def _bounded_response_continuation_limit(value: Any = None) -> int:
    if value is None:
        value = os.environ.get(RESPONSE_CONTINUATION_LIMIT_ENV)
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = DEFAULT_RESPONSE_CONTINUATION_LIMIT
    return min(max(limit, 0), HARD_RESPONSE_CONTINUATION_LIMIT)


def _is_output_truncated_finish_reason(finish_reason: Any) -> bool:
    normalized = str(finish_reason or "").strip().lower()
    return normalized in {
        "length",
        "max_tokens",
        "max_output_tokens",
        "max_completion_tokens",
        "model_length",
        "token_limit",
    }


def _join_text_parts(parts: list[str]) -> str:
    return "".join(parts)


def _append_text_part(parts: list[str], next_part: str) -> list[str]:
    if not parts or not next_part:
        return [*parts, next_part] if next_part else parts

    existing = _join_text_parts(parts)
    max_overlap = min(len(existing), len(next_part), 800)
    for size in range(max_overlap, 19, -1):
        if existing.endswith(next_part[:size]):
            return [*parts, next_part[size:]]
    return [*parts, next_part]


def _messages_with_output_continuation(
    messages: list[dict[str, Any]],
    text_parts: list[str],
) -> list[dict[str, Any]]:
    if not text_parts:
        return messages
    return [
        *messages,
        {"role": "assistant", "content": _join_text_parts(text_parts)},
        {"role": "user", "content": OUTPUT_CONTINUATION_PROMPT},
    ]


def _dispatch_tool_with_timeout(
    *,
    tool_registry: ToolRegistry,
    call: ToolCall,
    tool_context: ToolContext,
    timeout_seconds: float,
) -> tuple[ToolResult, bool]:
    """Run a tool without letting one stuck call freeze the whole ReAct turn."""
    result_queue: queue.Queue[tuple[str, ToolResult | BaseException]] = queue.Queue(maxsize=1)

    def target() -> None:
        try:
            result_queue.put(("result", tool_registry.dispatch(call, tool_context)))
        except BaseException as exc:  # noqa: BLE001 - propagate to the agent loop safely.
            result_queue.put(("error", exc))

    worker = threading.Thread(target=target, name=f"tool:{call.name}", daemon=True)
    worker.start()
    worker.join(timeout_seconds)

    if worker.is_alive():
        return (
            ToolResult(
                name=call.name,
                output={
                    "error": f"Tool timed out after {timeout_seconds:.1f}s",
                    "tool_name": call.name,
                    "timeout_seconds": timeout_seconds,
                },
                is_error=True,
                tool_use_id=call.tool_use_id,
            ),
            True,
        )

    kind, payload = result_queue.get_nowait()
    if kind == "error":
        raise payload
    return payload, False


@dataclass
class _ToolExecOutcome:
    """All data from one tool call execution, ready for event-firing + conversation update."""
    tool_use: dict
    result: "ToolResult | None"
    timed_out: bool
    started_at: float
    completed_at: float
    exception: "Exception | None"


def _execute_one_tool(
    tool_use: dict,
    tool_registry: "ToolRegistry",
    tool_context: "ToolContext",
) -> _ToolExecOutcome:
    """Execute one tool call; return outcome with no side effects (no events, no conversation)."""
    tool_name = tool_use["name"]
    tool_id = tool_use["id"]
    tool_input = tool_use["input"]
    tool_spec = tool_registry.spec_for(tool_name)
    timeout_seconds = _bounded_timeout_seconds(
        getattr(tool_spec, "timeout_seconds", DEFAULT_TOOL_TIMEOUT_SECONDS)
    )
    started_at = time.time()
    try:
        call = ToolCall(name=tool_name, input=tool_input, tool_use_id=tool_id)
        result, timed_out = _dispatch_tool_with_timeout(
            tool_registry=tool_registry,
            call=call,
            tool_context=tool_context,
            timeout_seconds=timeout_seconds,
        )
        return _ToolExecOutcome(
            tool_use=tool_use,
            result=result,
            timed_out=timed_out,
            started_at=started_at,
            completed_at=time.time(),
            exception=None,
        )
    except Exception as exc:
        return _ToolExecOutcome(
            tool_use=tool_use,
            result=None,
            timed_out=False,
            started_at=started_at,
            completed_at=time.time(),
            exception=exc,
        )


def _partition_tool_uses(
    tool_uses: list[dict], tool_registry: "ToolRegistry"
) -> list[tuple[bool, list[dict]]]:
    """Group tool_uses into (is_concurrent_safe, [tool_use, ...]) batches.

    Consecutive is_concurrency_safe tools form one concurrent batch.
    Each non-safe tool is its own batch of one.
    """
    batches: list[tuple[bool, list[dict]]] = []
    for tu in tool_uses:
        spec = tool_registry.spec_for(tu["name"])
        is_safe = bool(spec and spec.is_concurrency_safe)
        if batches and batches[-1][0] and is_safe:
            batches[-1][1].append(tu)
        else:
            batches.append((is_safe, [tu]))
    return batches


def _call_provider_for_turn(
    *,
    provider: BaseProvider,
    api_messages: list[dict[str, Any]],
    call_kwargs: dict[str, Any],
    stream: bool,
    on_text_chunk: TextChunkHandler | None,
    on_tool_ready: Callable[[dict], None] | None = None,
    cancel_token: threading.Event | None = None,
) -> tuple[Any, bool]:
    """Call the provider, preferring structured streaming when available.

    Returns (response, streamed_live_text).
    """
    effective_chunk_handler = on_text_chunk
    if cancel_token is not None and on_text_chunk is not None:
        _orig = on_text_chunk
        _tok = cancel_token

        def _cancellable_chunk(chunk: str) -> None:
            if _tok.is_set():
                raise StopIteration("cancelled")
            _orig(chunk)

        effective_chunk_handler = _cancellable_chunk
    elif cancel_token is not None:
        _tok = cancel_token

        def _cancellable_chunk_noop(chunk: str) -> None:
            if _tok.is_set():
                raise StopIteration("cancelled")

        effective_chunk_handler = _cancellable_chunk_noop

    if stream:
        try:
            response = provider.chat_stream_response(
                api_messages,
                on_text_chunk=effective_chunk_handler,
                on_tool_ready=on_tool_ready,
                **call_kwargs,
            )
            if not isinstance(response, ChatResponse):
                raise TypeError("Structured streaming must return ChatResponse")
            return response, True
        except NotImplementedError:
            pass

    response = provider.chat(api_messages, **call_kwargs)
    return response, False


def _build_effective_system_prompt(style_prompt: str, tool_context: ToolContext) -> str:
    extra_system_prompt = getattr(tool_context, "extra_system_prompt", "")
    if isinstance(extra_system_prompt, str) and extra_system_prompt.strip():
        style_prompt = (
            f"{style_prompt}\n\n{extra_system_prompt}"
            if style_prompt.strip()
            else extra_system_prompt
        )
    try:
        context_prompt = build_context_prompt(
            tool_context.workspace_root,
            cwd=tool_context.cwd,
        )
    except Exception:
        context_prompt = ""
    if not context_prompt.strip():
        return style_prompt
    return f"{style_prompt}\n\n{context_prompt}"


def summarize_tool_use(name: str, tool_input: dict[str, Any]) -> str:
    lowered = name.lower()
    if lowered == "bash":
        cmd = tool_input.get("command")
        if isinstance(cmd, str):
            s = cmd.strip().replace("\n", " ")
            return s if len(s) <= 80 else s[:77] + "..."
        return ""
    if lowered in {"read", "write", "edit"}:
        p = tool_input.get("file_path") or tool_input.get("filePath") or tool_input.get("path")
        if isinstance(p, str):
            extra = ""
            if lowered == "read":
                off = tool_input.get("offset")
                lim = tool_input.get("limit")
                if isinstance(off, int) or isinstance(lim, int):
                    start = off if isinstance(off, int) else 1
                    if isinstance(lim, int):
                        extra = f" · lines {start}-{start + lim - 1}"
            return f"{p}{extra}"
        return ""
    if lowered == "glob":
        pat = tool_input.get("pattern")
        base = tool_input.get("path")
        if isinstance(pat, str) and isinstance(base, str):
            return f"{pat} · {base}"
        if isinstance(pat, str):
            return pat
        return ""
    if lowered == "grep":
        pat = tool_input.get("pattern")
        base = tool_input.get("path")
        if isinstance(pat, str) and isinstance(base, str):
            return f"{pat} · {base}"
        if isinstance(pat, str):
            return pat
        return ""
    if lowered == "webfetch":
        url = tool_input.get("url")
        return url if isinstance(url, str) else ""
    if lowered == "websearch":
        q = tool_input.get("query")
        return q if isinstance(q, str) else ""
    if lowered == "toolsearch":
        q = tool_input.get("query")
        return q if isinstance(q, str) else ""
    if lowered == "askuserquestion":
        qs = tool_input.get("questions")
        if isinstance(qs, list):
            return f"{len(qs)} question(s)"
        return ""
    if lowered == "sendusermessage":
        status = tool_input.get("status")
        return status if isinstance(status, str) else ""
    return ""



def run_agent_loop(
    conversation: Conversation,
    provider: BaseProvider,
    tool_registry: ToolRegistry,
    tool_context: ToolContext,
    max_turns: int = 20,
    stream: bool = False,
    verbose: bool = False,
    on_event: ToolEventHandler | None = None,
    on_text_chunk: TextChunkHandler | None = None,
    cancel_token: threading.Event | None = None,
    amendment_queue: "queue.Queue[str] | None" = None,
) -> AgentLoopResult:
    """Run agent loop: LLM -> tools -> LLM until no more tools or max turns.

    Args:
        conversation: Conversation with initial user message
        provider: LLM provider
        tool_registry: Tool registry to use
        tool_context: Tool context
        max_turns: Maximum tool turns before stopping
        stream: Whether to stream responses
        verbose: Whether to print tool calls/results
        on_event: Optional callback for tool events
        on_text_chunk: Optional callback for incremental user-visible text chunks

    Returns:
        AgentLoopResult with final text response, usage info, and turn count
    """
    # Phase 6D: apply weak-model compensation if needed
    _provider_model = getattr(provider, "model", None)
    if not isinstance(_provider_model, str):
        _provider_model = ""
    _model_tier = classify_model_tier(_provider_model) if _provider_model.strip() else "strong"
    _compensation = get_compensation_config(_model_tier)
    if _compensation.max_turns_cap is not None:
        max_turns = min(max_turns, _compensation.max_turns_cap)
    try:
        from src.geneva.structured_log import log_metric
        log_metric(
            "compensation_mode_active",
            model=_provider_model,
            tier=_model_tier,
            max_turns=max_turns,
            max_verify_cycles=_compensation.max_verify_cycles,
            add_tool_json_examples=_compensation.add_tool_json_examples,
        )
    except Exception:
        pass

    _early_futures: dict[str, Any] = {}
    _early_dispatch_pool = concurrent.futures.ThreadPoolExecutor(
        max_workers=min(4, _MAX_CONCURRENT_TOOLS),
        thread_name_prefix="geneva-early",
    )

    def _on_tool_ready(tool_use_dict: dict) -> None:
        if not stream:
            return
        try:
            name = tool_use_dict.get("name", "")
            tid = tool_use_dict.get("id", "")
            if not tid or tid in _early_futures:
                return
            spec = tool_registry.spec_for(name)
            if spec and spec.is_concurrency_safe and _compensation.restrict_destructive is False:
                future = _early_dispatch_pool.submit(
                    _execute_one_tool,
                    tool_use_dict,
                    tool_registry,
                    tool_context,
                )
                _early_futures[tid] = future
        except Exception:
            return

    def _cancel_early_futures() -> None:
        for future in _early_futures.values():
            future.cancel()
        _early_futures.clear()

    _early_dispatch_shutdown = False

    def _shutdown_early_dispatch_pool() -> None:
        nonlocal _early_dispatch_shutdown
        if _early_dispatch_shutdown:
            return
        _cancel_early_futures()
        _early_dispatch_pool.shutdown(wait=False)
        _early_dispatch_shutdown = True

    def _agent_loop_result(**kwargs: Any) -> AgentLoopResult:
        _shutdown_early_dispatch_pool()
        return AgentLoopResult(**kwargs)

    # Convert tools to schemas (Anthropic format)
    tool_schemas = []
    for spec in tool_registry.list_specs():
        tool_schemas.append({
            "name": spec.name,
            "description": spec.description,
            "input_schema": spec.input_schema,
        })
    effective_tool_schemas = adapt_tool_schemas(tool_schemas, _model_tier)

    # For OpenAI/GLM, keep separate message list in OpenAI format
    openai_messages: list[dict[str, Any]] = []
    last_user_visible_message: str | None = None
    style_name = getattr(tool_context, "output_style_name", None)
    style_dir = getattr(tool_context, "output_style_dir", None)
    style_prompt = resolve_output_style(style_name, style_dir).prompt
    effective_system_prompt = _build_effective_system_prompt(style_prompt, tool_context)

    # Seed OpenAI messages from initial conversation messages
    for msg in conversation.messages:
        if isinstance(msg.content, str):
            openai_messages.append({"role": msg.role, "content": msg.content})
        else:
            # If there are already block messages, we are probably Anthropic; leave as is
            pass

    # Track usage across all turns
    total_usage: dict[str, int] = {"input_tokens": 0, "output_tokens": 0}
    turn_count = 0
    response_text_parts: list[str] = []
    continuation_count = 0
    continuation_limit = _bounded_response_continuation_limit()
    _cancelled: bool = False
    _verify_cycles_used = 0

    def _emit_tool_use_event(tu: dict, turn_index: int) -> None:
        tu_name = tu["name"]
        tu_spec = tool_registry.spec_for(tu_name)
        tu_timeout = _bounded_timeout_seconds(
            getattr(tu_spec, "timeout_seconds", DEFAULT_TOOL_TIMEOUT_SECONDS)
        )
        _safe_call_handler(
            on_event,
            ToolEvent(
                kind="tool_use",
                tool_name=tu_name,
                tool_input=tu["input"],
                tool_use_id=tu["id"],
                status="queued",
                summary=summarize_tool_use(tu_name, tu["input"]),
                turn_index=turn_index,
                started_at=time.time(),
                timeout_seconds=tu_timeout,
            ),
        )

    def _process_tool_outcome(outcome: _ToolExecOutcome, turn_index: int) -> None:
        nonlocal last_user_visible_message

        tu = outcome.tool_use
        tool_id = tu["id"]
        tool_name = tu["name"]
        tool_input = tu["input"]
        tool_summary = summarize_tool_use(tool_name, tool_input)
        tool_spec = tool_registry.spec_for(tool_name)
        timeout_seconds = _bounded_timeout_seconds(
            getattr(tool_spec, "timeout_seconds", DEFAULT_TOOL_TIMEOUT_SECONDS)
        )
        started_at = outcome.started_at
        completed_at = outcome.completed_at
        duration_ms = int((completed_at - started_at) * 1000)

        if outcome.exception is not None:
            error_str = f"Error: {outcome.exception}"
            if _provider_model:
                record_outcome(_provider_model, False)
            if verbose:
                print(f"[Tool Error] {error_str}")
            _safe_call_handler(
                on_event,
                ToolEvent(
                    kind="tool_error",
                    tool_name=tool_name,
                    tool_input=tool_input,
                    tool_use_id=tool_id,
                    is_error=True,
                    error=error_str,
                    status="error",
                    summary=tool_summary,
                    turn_index=turn_index,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=duration_ms,
                    timeout_seconds=timeout_seconds,
                ),
            )
            if _is_anthropic_provider(provider):
                conversation.add_tool_result_message(tool_id, error_str, is_error=True)
            else:
                openai_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": error_str,
                })
            return

        result = outcome.result
        if result is None:
            result = ToolResult(
                name=tool_name,
                output={"error": "Tool returned no result"},
                is_error=True,
                tool_use_id=tool_id,
            )

        result_output = result.output
        history_output = compact_tool_result_for_history(tool_name, result_output)
        timed_out = outcome.timed_out

        if tool_name.lower() == "sendusermessage" and isinstance(result_output, dict):
            msg = result_output.get("message")
            if isinstance(msg, str):
                last_user_visible_message = msg
        if tool_name.lower() == "structuredoutput" and isinstance(result_output, dict):
            payload = result_output.get("structured_output")
            try:
                last_user_visible_message = json.dumps(payload, ensure_ascii=False, indent=2)
            except Exception:
                last_user_visible_message = str(payload)

        if verbose:
            use_summary = summarize_tool_use(tool_name, tool_input)
            if use_summary:
                print(f"{tool_name} · {use_summary}")
            print(f"{summarize_tool_result(tool_name, result_output)}")

        result_summary = summarize_tool_result(tool_name, result_output)
        if _provider_model:
            record_outcome(_provider_model, (not result.is_error) and (not timed_out))
        _safe_call_handler(
            on_event,
            ToolEvent(
                kind="tool_timeout" if timed_out else "tool_result",
                tool_name=tool_name,
                tool_output=history_output,
                tool_use_id=tool_id,
                is_error=result.is_error,
                error=result_output.get("error") if isinstance(result_output, dict) and result.is_error else None,
                status="timeout" if timed_out else ("error" if result.is_error else "complete"),
                summary=result_summary,
                turn_index=turn_index,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
                timeout_seconds=timeout_seconds,
            ),
        )
        if _is_anthropic_provider(provider):
            conversation.add_tool_result_message(tool_id, history_output)
        else:
            openai_messages.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "content": _build_openai_tool_result_content(history_output),
            })

    for turn in range(max_turns):
        if cancel_token is not None and cancel_token.is_set():
            _cancelled = True
            break
        # Drain amendments — inject before this turn
        if amendment_queue is not None:
            pending: list[str] = []
            while True:
                try:
                    pending.append(amendment_queue.get_nowait())
                except queue.Empty:
                    break
            if pending:
                combined = "\n\n".join(pending)
                conversation.add_user_message(f"[ผู้ใช้ส่งข้อความเพิ่มเติม]: {combined}")
                openai_messages.append({"role": "user", "content": f"[ผู้ใช้ส่งข้อความเพิ่มเติม]: {combined}"})

        turn_index = turn + 1
        _safe_call_handler(
            on_event,
            ToolEvent(
                kind="agent_turn_start",
                tool_name="AgentLoop",
                tool_input={"turn": turn_index, "max_turns": max_turns},
                status="running",
                summary=f"Agent turn {turn_index}/{max_turns}",
                turn_index=turn_index,
            ),
        )
        if _is_anthropic_provider(provider):
            api_messages = _messages_with_output_continuation(
                conversation.get_messages(),
                response_text_parts,
            )
        else:
            # Use OpenAI formatted messages for non-Anthropic
            api_messages = _messages_with_output_continuation(
                openai_messages,
                response_text_parts,
            )

        call_kwargs: dict[str, Any] = {"tools": effective_tool_schemas}
        call_kwargs["max_tokens"] = _bounded_response_max_tokens()
        if _is_anthropic_provider(provider):
            if _prompt_cache_enabled() and effective_system_prompt:
                call_kwargs["system"] = [
                    {
                        "type": "text",
                        "text": effective_system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
                call_kwargs["extra_headers"] = {"anthropic-beta": "prompt-caching-2024-07-31"}
            else:
                call_kwargs["system"] = effective_system_prompt
        else:
            api_messages = [{"role": "system", "content": effective_system_prompt}, *api_messages]
        try:
            response, streamed_live_text = _call_provider_for_turn(
                provider=provider,
                api_messages=api_messages,
                call_kwargs=call_kwargs,
                stream=stream,
                on_text_chunk=on_text_chunk,
                on_tool_ready=_on_tool_ready if stream else None,
                cancel_token=cancel_token,
            )
        except (StopIteration, Exception) as exc:
            if cancel_token is not None and cancel_token.is_set():
                _cancelled = True
                break
            _shutdown_early_dispatch_pool()
            raise
        if cancel_token is not None and cancel_token.is_set():
            _cancelled = True
            break
        turn_count += 1

        # Collect usage info
        if response.usage:
            total_usage["input_tokens"] += response.usage.get("input_tokens", 0)
            total_usage["output_tokens"] += response.usage.get("output_tokens", 0)

        # Build assistant content for Anthropic or just text for OpenAI
        final_assistant_content = response.content or ""
        tool_uses = response.tool_uses or []

        if not tool_uses:
            response_text_parts = _append_text_part(response_text_parts, final_assistant_content)

        output_truncated = _is_output_truncated_finish_reason(response.finish_reason)
        will_continue_output = (
            not tool_uses
            and bool(final_assistant_content)
            and output_truncated
            and continuation_count < continuation_limit
        )

        if tool_uses and _is_anthropic_provider(provider):
            response_text_parts = []
            assistant_blocks: list = []
            if response.content:
                assistant_blocks.append(TextContentBlock(type="text", text=response.content))

            for tool_use in tool_uses:
                assistant_blocks.append(ToolUseContentBlock(
                    type="tool_use",
                    id=tool_use["id"],
                    name=tool_use["name"],
                    input=tool_use["input"],
                ))

            conversation.add_assistant_message(assistant_blocks if assistant_blocks else "")
        elif tool_uses:
            response_text_parts = []
            # Persist assistant text for session history features like /render-last
            # and for subsequent non-Anthropic turns seeded from conversation.
            conversation.add_assistant_message(final_assistant_content)
            # Add assistant message to OpenAI messages (text only)
            openai_assistant_msg: dict[str, Any] = {"role": "assistant", "content": final_assistant_content}
            # If there are tool_uses, add them in OpenAI format
            if response.tool_uses:
                # Build OpenAI tool_calls
                tool_calls = []
                for tu in response.tool_uses:
                    tool_calls.append({
                        "id": tu["id"],
                        "type": "function",
                        "function": {
                            "name": tu["name"],
                            "arguments": json.dumps(tu["input"], ensure_ascii=False)
                        }
                    })
                openai_assistant_msg["tool_calls"] = tool_calls
            openai_messages.append(openai_assistant_msg)

        _safe_call_handler(
            on_event,
            ToolEvent(
                kind="agent_turn_complete",
                tool_name="AgentLoop",
                tool_output={
                    "finish_reason": response.finish_reason,
                    "tool_count": len(tool_uses),
                    "usage": response.usage or {},
                    "continuation_count": continuation_count,
                    "continuation_limit": continuation_limit,
                },
                status=(
                    "waiting_for_tools"
                    if tool_uses
                    else "continuing"
                    if will_continue_output
                    else "complete"
                ),
                summary=(
                    f"{len(tool_uses)} tool call(s)"
                    if tool_uses
                    else "Output token limit reached; continuing"
                    if will_continue_output
                    else "No tools requested"
                ),
                turn_index=turn_index,
            ),
        )

        if not tool_uses:
            if _early_futures:
                _cancel_early_futures()
            if will_continue_output:
                if stream and final_assistant_content and not streamed_live_text:
                    _emit_text_chunks(on_text_chunk, final_assistant_content)
                continuation_count += 1
                continue

            response_text = _join_text_parts(response_text_parts)
            if output_truncated and response_text:
                response_text += OUTPUT_TRUNCATION_NOTICE

            conversation.add_assistant_message(response_text)
            if not _is_anthropic_provider(provider):
                openai_messages.append({"role": "assistant", "content": response_text})

            # R6.2: mandatory verify pass for weak/medium models
            if (
                not tool_uses
                and _compensation.max_verify_cycles > 0
                and _verify_cycles_used < _compensation.max_verify_cycles
                and turn < max_turns - 1
            ):
                _verify_cycles_used += 1
                response_text_parts = []
                verify_message = "Please verify your answer is complete and correct before finalizing."
                conversation.add_user_message(verify_message)
                if not _is_anthropic_provider(provider):
                    openai_messages.append({"role": "user", "content": verify_message})
                try:
                    from src.geneva.structured_log import log_metric
                    log_metric("verify_cycle_triggered", model=_provider_model, cycle=_verify_cycles_used)
                except Exception:
                    pass
                continue

            if stream and response_text and not streamed_live_text:
                streamed_text = final_assistant_content if response_text_parts else response_text
                _emit_text_chunks(on_text_chunk, streamed_text)
                if output_truncated:
                    _emit_text_chunks(on_text_chunk, OUTPUT_TRUNCATION_NOTICE)
            elif stream and output_truncated:
                _emit_text_chunks(on_text_chunk, OUTPUT_TRUNCATION_NOTICE)
            # Check for pending amendments before exiting — if found, do another turn
            if amendment_queue is not None:
                _pending: list[str] = []
                while True:
                    try:
                        _pending.append(amendment_queue.get_nowait())
                    except queue.Empty:
                        break
                if _pending:
                    _combined = "\n\n".join(_pending)
                    conversation.add_user_message(f"[ผู้ใช้ส่งข้อความเพิ่มเติม]: {_combined}")
                    openai_messages.append({"role": "user", "content": f"[ผู้ใช้ส่งข้อความเพิ่มเติม]: {_combined}"})
                    continue
            if not response_text.strip() and last_user_visible_message is not None:
                return _agent_loop_result(
                    response_text=last_user_visible_message,
                    usage=total_usage if total_usage["input_tokens"] > 0 or total_usage["output_tokens"] > 0 else None,
                    num_turns=turn_count,
                )
            return _agent_loop_result(
                response_text=response_text,
                usage=total_usage if total_usage["input_tokens"] > 0 or total_usage["output_tokens"] > 0 else None,
                num_turns=turn_count,
            )

        tool_use_ids = {tu["id"] for tu in tool_uses}
        early_done = {
            tid: _early_futures.pop(tid)
            for tid in list(_early_futures)
            if tid in tool_use_ids
        }
        for tid in list(_early_futures):
            _early_futures.pop(tid).cancel()

        early_tool_uses_by_id = {
            tu["id"]: tu
            for tu in tool_uses
            if tu["id"] in early_done
        }
        remaining_tool_uses = [
            tu
            for tu in tool_uses
            if tu["id"] not in early_done
        ]

        for tu in tool_uses:
            if tu["id"] in early_done:
                _emit_tool_use_event(tu, turn_index)

        # Call tools — concurrent batches for consecutive read-only tools, serial otherwise
        batches = _partition_tool_uses(remaining_tool_uses, tool_registry)
        for is_concurrent, batch in batches:
            # Fire tool_use (queued) events for every tool in this batch before execution
            for tu in batch:
                _emit_tool_use_event(tu, turn_index)

            # Execute batch: parallel when safe + multiple tools, serial otherwise
            if is_concurrent and len(batch) > 1:
                import copy as _copy
                ctx_copies = []
                for _ in batch:
                    ctx_c = _copy.copy(tool_context)
                    ctx_c.read_file_fingerprints = dict(tool_context.read_file_fingerprints)
                    ctx_copies.append(ctx_c)
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=min(len(batch), _MAX_CONCURRENT_TOOLS),
                    thread_name_prefix="geneva-tool",
                ) as pool:
                    futures = [
                        pool.submit(_execute_one_tool, tu, tool_registry, ctx)
                        for tu, ctx in zip(batch, ctx_copies)
                    ]
                    outcomes = [f.result() for f in futures]  # preserves submission order
                for ctx_c in ctx_copies:
                    tool_context.read_file_fingerprints.update(ctx_c.read_file_fingerprints)
            else:
                outcomes = [_execute_one_tool(tu, tool_registry, tool_context) for tu in batch]

            # Process outcomes in original order: fire completion events + update conversation
            for outcome in outcomes:
                _process_tool_outcome(outcome, turn_index)

        for tool_id, future in early_done.items():
            tool_use = early_tool_uses_by_id[tool_id]
            try:
                outcome = future.result(timeout=5.0)
            except concurrent.futures.TimeoutError:
                now = time.time()
                outcome = _ToolExecOutcome(
                    tool_use=tool_use,
                    result=ToolResult(
                        name=tool_use["name"],
                        output={"error": "early dispatch timed out"},
                        is_error=True,
                        tool_use_id=tool_id,
                    ),
                    timed_out=True,
                    started_at=now,
                    completed_at=now,
                    exception=None,
                )
            except Exception as exc:
                now = time.time()
                outcome = _ToolExecOutcome(
                    tool_use=tool_use,
                    result=None,
                    timed_out=False,
                    started_at=now,
                    completed_at=now,
                    exception=exc,
                )
            _process_tool_outcome(outcome, turn_index)

    if _cancelled:
        return _agent_loop_result(
            response_text=_join_text_parts(response_text_parts),
            usage=total_usage if total_usage["input_tokens"] > 0 or total_usage["output_tokens"] > 0 else None,
            num_turns=turn_count,
            cancelled=True,
        )

    # Reached max turns
    _safe_call_handler(
        on_event,
        ToolEvent(
            kind="agent_loop_limit",
            tool_name="AgentLoop",
            tool_output={"max_turns": max_turns, "turns_completed": turn_count},
            is_error=True,
            error=f"Max tool turns reached after {turn_count} turn(s)",
            status="limit_reached",
            summary="Max tool turns reached",
            turn_index=turn_count,
        ),
    )
    return _agent_loop_result(
        response_text="[Max tool turns reached]",
        usage=total_usage if total_usage["input_tokens"] > 0 or total_usage["output_tokens"] > 0 else None,
        num_turns=turn_count,
    )
