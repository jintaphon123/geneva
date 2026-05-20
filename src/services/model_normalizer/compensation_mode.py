from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CompensationConfig:
    """Describes how Geneva should compensate for a model's limitations.

    strong tier:  no compensation, fast path
    medium tier:  cap turns, add JSON examples to tools
    weak tier:    aggressive cap, restrict destructive tools, JSON examples
    """

    max_turns_cap: int | None
    add_tool_json_examples: bool
    restrict_destructive: bool
    max_verify_cycles: int = 1  # 0=none, 1=one verify pass, 2=two passes


_STRONG = CompensationConfig(
    max_turns_cap=None,
    add_tool_json_examples=False,
    restrict_destructive=False,
    max_verify_cycles=0,
)
_MEDIUM = CompensationConfig(
    max_turns_cap=8,
    add_tool_json_examples=True,
    restrict_destructive=False,
    max_verify_cycles=1,
)
_WEAK = CompensationConfig(
    max_turns_cap=5,
    add_tool_json_examples=True,
    restrict_destructive=True,
    max_verify_cycles=2,
)


def get_compensation_config(tier: str) -> CompensationConfig:
    """Return compensation config for a model tier string."""
    if os.environ.get("GENEVA_DISABLE_MODEL_COMPENSATION") == "1":
        return _STRONG
    if tier == "strong":
        return _STRONG
    if tier == "medium":
        return _MEDIUM
    return _WEAK
