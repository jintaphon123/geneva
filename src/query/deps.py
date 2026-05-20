from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.cost_tracker import CostTracker
from src.permissions import ToolPermissionContext


@dataclass
class QueryDeps:
    cost_tracker: CostTracker
    session_store: Any
    permission_ctx: ToolPermissionContext | None
