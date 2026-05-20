from __future__ import annotations
from enum import Enum


class TurnState(Enum):
    IDLE = "idle"
    RECEIVED = "received"
    CONTEXT_BUILT = "context_built"
    MODEL_STARTED = "model_started"
    TOOL_PENDING = "tool_pending"
    ASSISTANT_DONE = "assistant_done"
    PERSISTED = "persisted"
    CANCELLED = "cancelled"
