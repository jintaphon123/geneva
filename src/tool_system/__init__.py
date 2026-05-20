from __future__ import annotations

import sys
from pathlib import Path

if __package__ == "tool_system":
    _repo_root = Path(__file__).resolve().parents[2]
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))

from .context import ToolContext
from .errors import ToolError, ToolInputError, ToolPermissionError
from .loader import load_tools_from_dir
from .permission_handler import PermissionResult
from .protocol import ToolCall, ToolResult
from .registry import Tool, ToolRegistry, ToolSpec

__all__ = [
    "PermissionResult",
    "Tool",
    "ToolCall",
    "ToolContext",
    "ToolError",
    "ToolInputError",
    "ToolPermissionError",
    "ToolRegistry",
    "ToolResult",
    "ToolSpec",
    "load_tools_from_dir",
]
