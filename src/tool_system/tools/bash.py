from __future__ import annotations

import re as _re
import shlex
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from ..context import ToolContext
from ..errors import ToolInputError
from ..permission_handler import PermissionResult
from ..profiles import is_dangerous_command
from ..protocol import ToolResult
from ..registry import ToolSpec


def _truncate(s: str, limit: int = 20000) -> str:
    if len(s) <= limit:
        return s
    return s[:limit] + "\n\n... [truncated] ..."


def _try_extract_cd(command: str) -> Path | None:
    stripped = command.strip()
    if not stripped.startswith("cd "):
        return None
    try:
        parts = shlex.split(stripped, posix=True)
    except ValueError:
        return None
    if len(parts) >= 2 and parts[0] == "cd":
        return Path(parts[1])
    return None


_SENSITIVE_PATTERNS: list[tuple[_re.Pattern[str], str]] = [
    # File deletion
    (_re.compile(r"\brm\b\s+(?!.*-rf\s*/)", _re.IGNORECASE), "file deletion (rm)"),
    (_re.compile(r"\brmdir\b", _re.IGNORECASE), "directory removal (rmdir)"),
    (_re.compile(r"\bunlink\b", _re.IGNORECASE), "file removal (unlink)"),
    # Write to sensitive dirs
    (_re.compile(r"[>|]\s*(~/)?\.ssh/", _re.IGNORECASE), "write to ~/.ssh"),
    (_re.compile(r"[>|]\s*(~/)?\.geneva/", _re.IGNORECASE), "write to ~/.geneva"),
    (_re.compile(r"[>|]\s*(~/)?\.config/", _re.IGNORECASE), "write to ~/.config"),
    (_re.compile(r"[>|]\s*/etc/", _re.IGNORECASE), "write to /etc"),
    # Background process
    (_re.compile(r"\bnohup\b", _re.IGNORECASE), "background process (nohup)"),
    (_re.compile(r"&\s*$"), "background process (&)"),
    # Network mutations
    (_re.compile(r"\bcurl\b.+(-X\s*(POST|PUT|DELETE|PATCH))", _re.IGNORECASE), "network mutation (curl)"),
    (_re.compile(r"\bwget\b.+--post", _re.IGNORECASE), "network POST (wget)"),
    (_re.compile(r"\bnc\b", _re.IGNORECASE), "network connection (nc)"),
]

_SSH_OPTIONS_WITH_ARGS = {
    "-B",
    "-b",
    "-c",
    "-D",
    "-E",
    "-e",
    "-F",
    "-I",
    "-i",
    "-J",
    "-L",
    "-l",
    "-m",
    "-O",
    "-o",
    "-p",
    "-Q",
    "-R",
    "-S",
    "-W",
    "-w",
}


def _ssh_has_remote_command(command: str) -> bool:
    try:
        parts = shlex.split(command, posix=True)
    except ValueError:
        return False

    for index, part in enumerate(parts):
        if Path(part).name != "ssh":
            continue
        cursor = index + 1
        while cursor < len(parts) and parts[cursor].startswith("-"):
            option = parts[cursor]
            if option == "--":
                cursor += 1
                break
            option_key = option[:2]
            if option in _SSH_OPTIONS_WITH_ARGS or option_key in _SSH_OPTIONS_WITH_ARGS:
                cursor += 2 if option == option_key else 1
            else:
                cursor += 1
        if cursor < len(parts) and cursor + 1 < len(parts):
            return True
    return False


def _is_sensitive_command(command: str) -> tuple[bool, str]:
    """Return (is_sensitive, reason). Checks only after is_dangerous_command passes."""
    for pattern, reason in _SENSITIVE_PATTERNS:
        if pattern.search(command):
            return True, reason
    if _ssh_has_remote_command(command):
        return True, "remote command execution (ssh)"
    return False, ""


class BashTool:
    def check_permissions(self, tool_input: dict, context: Any) -> PermissionResult:
        command = tool_input.get("command", "")
        if is_dangerous_command(command):
            return PermissionResult.ask(
                f"Potentially dangerous command: {command[:120]}",
                suggestion="Review the command carefully before allowing execution",
            )
        sensitive, reason = _is_sensitive_command(command)
        if sensitive:
            return PermissionResult.ask(
                f"Sensitive command ({reason}): {command[:120]}",
                suggestion=f"This command performs {reason}. Confirm before running.",
            )
        return PermissionResult.allow()

    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="Bash",
            description="Execute a shell command.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "command": {"type": "string"},
                    "cwd": {"type": "string"},
                    "timeout_s": {"type": "integer"},
                    "idempotency_key": {"type": "string"},
                    "run_in_background": {"type": "boolean"},
                },
                "required": ["command"],
            },
            is_destructive=True,
            max_result_size_chars=50_000,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        command = tool_input["command"]
        if not isinstance(command, str) or not command.strip():
            raise ToolInputError("command must be a non-empty string")
        if "\x00" in command:
            raise ToolInputError("command contains NUL byte")
        if is_dangerous_command(command):
            raise PermissionError(f"Dangerous command blocked: {command[:120]}")

        idempotency_key = tool_input.get("idempotency_key")
        if idempotency_key:
            cached = context.idempotency_cache.get(idempotency_key)
            if cached is not None:
                return ToolResult(name="Bash", output=cached)

        if tool_input.get("run_in_background"):
            task_id = uuid.uuid4().hex[:8]
            started_at = time.time()

            def _bg_run() -> None:
                try:
                    explicit_cwd_bg = tool_input.get("cwd")
                    if explicit_cwd_bg is not None:
                        bg_cwd = context.ensure_allowed_path(explicit_cwd_bg)
                    else:
                        bg_cwd = context.cwd or context.workspace_root
                    timeout_s_bg = tool_input.get("timeout_s", 60)
                    if not isinstance(timeout_s_bg, int) or timeout_s_bg < 1 or timeout_s_bg > 600:
                        timeout_s_bg = 60
                    completed = subprocess.run(
                        ["bash", "-lc", command],
                        cwd=str(bg_cwd),
                        capture_output=True,
                        text=True,
                        timeout=timeout_s_bg,
                    )
                    result = {
                        "task_id": task_id,
                        "command": command,
                        "cwd": str(bg_cwd),
                        "exit_code": completed.returncode,
                        "stdout": _truncate(completed.stdout or ""),
                        "stderr": _truncate(completed.stderr or ""),
                        "started_at": started_at,
                        "completed_at": time.time(),
                    }
                except subprocess.TimeoutExpired:
                    result = {
                        "task_id": task_id,
                        "command": command,
                        "exit_code": -1,
                        "stdout": "",
                        "stderr": "Background task timed out",
                        "started_at": started_at,
                        "completed_at": time.time(),
                    }
                except Exception as exc:
                    result = {
                        "task_id": task_id,
                        "command": command,
                        "exit_code": -1,
                        "stdout": "",
                        "stderr": str(exc),
                        "started_at": started_at,
                        "completed_at": time.time(),
                    }
                if context.bg_task_notify is not None:
                    context.bg_task_notify(task_id, command, result)

            t = threading.Thread(target=_bg_run, daemon=True, name=f"bg-bash-{task_id}")
            t.start()
            return ToolResult(
                name="Bash",
                output={
                    "status": "running",
                    "task_id": task_id,
                    "message": f"Command started in background (task_id={task_id}). You will be notified when it completes.",
                },
            )

        explicit_cwd = tool_input.get("cwd")
        if explicit_cwd is not None:
            if not isinstance(explicit_cwd, str) or not explicit_cwd.startswith("/"):
                raise ToolInputError("cwd must be an absolute path when provided")
            cwd = context.ensure_allowed_path(explicit_cwd)
        else:
            cwd = context.cwd or context.workspace_root

        cd_target = _try_extract_cd(command)
        if cd_target is not None and command.strip().startswith("cd ") and len(command.strip().splitlines()) == 1:
            next_dir = (cwd / cd_target).expanduser().resolve() if not cd_target.is_absolute() else cd_target.expanduser().resolve()
            next_dir = context.ensure_allowed_path(next_dir)
            if not next_dir.exists() or not next_dir.is_dir():
                return ToolResult(name="Bash", output={"error": f"directory does not exist: {next_dir}"}, is_error=True)
            context.cwd = next_dir
            return ToolResult(name="Bash", output={"cwd": str(context.cwd), "stdout": "", "stderr": ""})

        timeout_s = tool_input.get("timeout_s", 60)
        if not isinstance(timeout_s, int) or timeout_s < 1 or timeout_s > 600:
            raise ToolInputError("timeout_s must be an integer between 1 and 600")

        completed = subprocess.run(
            ["bash", "-lc", command],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )

        stdout = _truncate(completed.stdout or "")
        stderr = _truncate(completed.stderr or "")
        output: dict[str, Any] = {
            "cwd": str(cwd),
            "exit_code": completed.returncode,
            "stdout": stdout,
            "stderr": stderr,
        }
        if idempotency_key:
            context.idempotency_cache[idempotency_key] = output
        return ToolResult(name="Bash", output=output, is_error=completed.returncode != 0)
