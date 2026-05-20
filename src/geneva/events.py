from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


StreamEventType = Literal[
    "memory_load_start",
    "memory_load_complete",
    "agent_turn_start",
    "agent_turn_complete",
    "agent_loop_limit",
    "text_delta",
    "tool_call_start",
    "tool_input_delta",
    "tool_executing",
    "tool_permission_request",
    "tool_permission_resolved",
    "tool_complete",
    "tool_error",
    "tool_timeout",
    "memory_update",
    "heartbeat",
    "turn_complete",
    "background_task_done",
    "error",
]

ErrorCode = Literal[
    "auth_error",
    "quota_error",
    "rate_limit",
    "timeout",
    "token_budget_error",
    "tool_error",
    "memory_error",
    "network_error",
    "validation_error",
    "internal_error",
]

MemoryAction = Literal["ADD", "UPDATE", "NOOP", "SUPERSEDE", "ARCHIVE", "EXPIRE"]


@dataclass(frozen=True)
class ErrorInfo:
    code: ErrorCode
    message: str
    recoverable: bool
    suggestion: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def public_error_info(exc: BaseException | str) -> ErrorInfo:
    """Convert raw provider/runtime failures into user-safe stream errors."""
    text = str(exc)
    lowered = text.lower()

    if _contains_any(lowered, ("api key", "unauthorized", "unauthorised", "401", "403", "auth")):
        return ErrorInfo(
            code="auth_error",
            message="I could not reach the selected model because provider access is not ready.",
            recoverable=False,
            suggestion="Check Settings for the active provider key and model access, then try again.",
        )
    if _contains_any(lowered, ("context length", "maximum context", "too many tokens", "requested up to", "max_tokens")):
        return ErrorInfo(
            code="token_budget_error",
            message="This turn is too large for the current model budget.",
            recoverable=True,
            suggestion="Use /compact, shorten the request, lower output tokens, or switch to a model with a larger usable context window.",
        )
    if _contains_any(lowered, ("never purchased credits", "insufficient credits")):
        return ErrorInfo(
            code="quota_error",
            message="The selected paid model requires provider credits before it can start.",
            recoverable=True,
            suggestion="Add provider credits or use a free router/model.",
        )
    if _contains_any(lowered, ("402", "requires more credits", "can only afford", "insufficient_quota", "credit")):
        return ErrorInfo(
            code="quota_error",
            message="The selected model could not start because the provider account does not have enough credits for this request.",
            recoverable=True,
            suggestion="Add provider credits, switch to a cheaper model, or retry after compacting the conversation.",
        )
    if _contains_any(lowered, ("429", "rate limit", "rate_limit", "too many requests")):
        return ErrorInfo(
            code="rate_limit",
            message="The model provider is rate-limiting this request.",
            recoverable=True,
            suggestion="Wait a moment, then retry the turn.",
        )
    if _contains_any(lowered, ("timeout", "timed out")):
        return ErrorInfo(
            code="timeout",
            message="The model provider took too long to respond.",
            recoverable=True,
            suggestion="Retry with a narrower request, or try a faster model.",
        )
    if _contains_any(lowered, ("network", "connection", "dns", "ssl", "urlopen", "fetch")):
        return ErrorInfo(
            code="network_error",
            message="Geneva lost the connection to the model provider.",
            recoverable=True,
            suggestion="Check the network/provider status, then retry.",
        )
    return ErrorInfo(
        code="internal_error",
        message="Geneva hit an unexpected problem while answering.",
        recoverable=True,
        suggestion="Retry the turn. If it repeats, check provider settings and the server log.",
    )


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


@dataclass(frozen=True)
class TurnStreamEvent:
    turn_id: str
    event_seq: int
    type: StreamEventType
    data: dict[str, Any]
    timestamp: float
    tool_call_id: str | None = None
    error: ErrorInfo | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.error is not None:
            payload["error"] = self.error.to_dict()
        return payload


@dataclass(frozen=True)
class MemoryActivity:
    session_id: str
    timestamp: float
    action: MemoryAction
    title: str
    memory_id: str | None = None
    content: str = ""
    confidence: float | None = None
    write_event: dict[str, Any] | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
