from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QueryConfig:
    model: str
    max_tokens: int
    temperature: float
    system_prompt: str
    provider: str
    session_id: str
