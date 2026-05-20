from __future__ import annotations

from dataclasses import dataclass, field

from src.query.config import QueryConfig


@dataclass
class DirectConnectSession:
    session_id: str
    created_at: str
    config: QueryConfig
    transcript: list[dict] = field(default_factory=list)
