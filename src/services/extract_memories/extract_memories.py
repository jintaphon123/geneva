from __future__ import annotations

import inspect
import re
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from ...geneva.memory_write_review import record_memory_write_event
from ...memdir.brain_engine import remember
from ...memdir.memory_scan import format_memory_manifest, scan_memory_files
from ...memdir.paths import get_auto_mem_path
from .prompts import build_extract_auto_only_prompt, build_extract_combined_prompt


def _transcript_from_context(context: dict) -> list[dict]:
    transcript: list[dict] = []
    for message in context.get("messages", []):
        if isinstance(message, dict):
            role = str(message.get("role") or message.get("type") or "unknown")
            content = message.get("content")
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(str(part.get("text", "")))
                content = "\n".join(text_parts)
            transcript.append({"role": role, "content": str(content or "")})
    return transcript


def _infer_type(text: str, scoped: bool = False) -> str:
    lowered = text.lower()
    if scoped and any(
        token in lowered
        for token in (
            "goal",
            "next action",
            "reflection",
            "source",
            "todo",
            "เป้าหมาย",
            "สิ่งที่ต้องทำ",
            "สะท้อน",
            "แหล่งข้อมูล",
        )
    ):
        return "project"
    if any(token in lowered for token in ("prefer", "always", "never", "working style", "i like", "ชอบ", "ไม่ชอบ", "สไตล์การทำงาน")):
        return "user"
    if any(token in lowered for token in ("feedback", "please don't", "correction", "confirm", "แก้", "ข้อเสนอแนะ")):
        return "feedback"
    if any(
        token in lowered
        for token in (
            "decision",
            "deadline",
            "project",
            "architecture",
            "ship",
            "release",
            "ตัดสินใจ",
            "เดดไลน์",
            "กำหนดส่ง",
            "โปรเจกต์",
            "โครงการ",
            "สถาปัตยกรรม",
        )
    ):
        return "project"
    return "reference"


_IDENTITY_PATTERNS = [
    re.compile(r"(?:ฉัน|ผม|เรา|ดิฉัน)\s*ชื่อ\s*([^\s,.\n!?]+(?:\s+[^\s,.\n!?]+)?)"),
    re.compile(r"\bmy name is\s+([A-Za-z][A-Za-z0-9 ._'’-]{1,80})", re.IGNORECASE),
    re.compile(r"\bcall me\s+([A-Za-z][A-Za-z0-9 ._'’-]{1,80})", re.IGNORECASE),
]


def _identity_memory(content: str) -> dict[str, Any] | None:
    for pattern in _IDENTITY_PATTERNS:
        match = pattern.search(content)
        if not match:
            continue
        name = re.sub(r"\s+", " ", match.group(1)).strip(" .,!?:;")
        if not name:
            continue
        return {
            "type": "user",
            "content": f"User identity: name is {name}.",
            "memory_kind": "identity",
            "source_type": "user_direct",
            "evidence_quote": content[:160],
            "sensitivity": "private",
        }
    return None


def _heuristic_extract(transcript: list[dict], scoped: bool = False) -> list[dict[str, Any]]:
    extracted: list[dict[str, Any]] = []
    for turn in transcript:
        if turn["role"] != "user":
            continue
        content = turn["content"].strip()
        identity = _identity_memory(content)
        if identity is not None:
            extracted.append(identity)
            continue
        if len(content) < 20:
            continue
        lowered = content.lower()
        should_extract = (
            "remember" in lowered
            or "จำ" in lowered
            or "prefer" in lowered
            or "ชอบ" in lowered
            or "always" in lowered
            or "never" in lowered
            or "ห้าม" in lowered
            or "deadline" in lowered
            or "เดดไลน์" in lowered
            or "กำหนดส่ง" in lowered
            or "ตัดสินใจ" in lowered
            or (scoped and "goal" in lowered)
            or (scoped and "next action" in lowered)
            or (scoped and "reflection" in lowered)
            or (scoped and "todo" in lowered)
            or (scoped and "เป้าหมาย" in lowered)
            or (scoped and "สิ่งที่ต้องทำ" in lowered)
            or re.search(r"\bdecision\b", lowered) is not None
        )
        if should_extract:
            memory_type = _infer_type(content, scoped=scoped)
            extracted.append(
                {
                    "type": memory_type,
                    "content": content,
                    "memory_kind": "preference" if memory_type == "user" else None,
                    "source_type": "user_direct",
                    "evidence_quote": content[:160],
                    "sensitivity": "private",
                }
            )
    return extracted


async def _maybe_await(result: object) -> object:
    if inspect.isawaitable(result):
        return await result  # type: ignore[no-any-return]
    return result


def _parse_llm_memory_json(text: object) -> list[dict] | None:
    """Parse LLM response into normalized memory dicts. Returns None if unparseable."""
    if not text:
        return None
    raw = str(text)
    # Try to find JSON array in response (possibly wrapped in ```json...```)
    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", raw, re.DOTALL)
    if match:
        raw = match.group(1)
    else:
        bracket_start = raw.find("[")
        bracket_end = raw.rfind("]")
        if bracket_start != -1 and bracket_end > bracket_start:
            raw = raw[bracket_start : bracket_end + 1]
    try:
        import json as _json
        items = _json.loads(raw)
        if isinstance(items, dict) and isinstance(items.get("memories"), list):
            items = items["memories"]
        if not isinstance(items, list):
            return None
        result = []
        valid_types = {"user", "project", "feedback", "reference"}
        valid_kinds = {"identity", "preference", "project", "decision", "reflection", "reference", "episode", "skill", "feedback"}
        valid_sensitivity = {"public", "private", "restricted"}
        for item in items:
            if not isinstance(item, dict):
                continue
            content = str(item.get("content", "")).strip()
            mem_type = str(item.get("type", "reference")).strip().lower()
            if not content or len(content) < 10:
                continue
            if mem_type not in valid_types:
                mem_type = "reference"
            memory_kind = str(item.get("memory_kind") or item.get("kind") or "").strip().lower().replace("-", "_")
            sensitivity = str(item.get("sensitivity") or "").strip().lower()
            validity_window_days = item.get("validity_window_days")
            try:
                validity_window_days = int(validity_window_days) if validity_window_days is not None else None
            except (TypeError, ValueError):
                validity_window_days = None
            result.append(
                {
                    "type": mem_type,
                    "content": content,
                    "memory_kind": memory_kind if memory_kind in valid_kinds else None,
                    "evidence_quote": str(item.get("evidence_quote") or item.get("evidence") or content[:100]).strip()[:240],
                    "sensitivity": sensitivity if sensitivity in valid_sensitivity else "private",
                    "validity_window_days": validity_window_days,
                }
            )
        return result if result else None
    except Exception:
        return None


def init_extract_memories(
    memory_dir: Path | None = None,
    agent_caller: Callable | None = None,
) -> Callable[[dict], Awaitable[None]]:
    async def runner(context: dict) -> None:
        await run_extraction(context, memory_dir=memory_dir, agent_caller=agent_caller)

    return runner


async def run_extraction(
    context: dict,
    memory_dir: Path | None = None,
    agent_caller: Callable | None = None,
) -> None:
    transcript = _transcript_from_context(context)
    if not transcript:
        return

    target_memory_dir = (memory_dir or get_auto_mem_path(Path.cwd())).expanduser()
    scope = context.get("scope")
    memory_scope = str(scope).strip() if scope is not None and str(scope).strip() else None
    session_id = context.get("session_id")
    source_session_id = str(session_id).strip() if session_id is not None and str(session_id).strip() else None
    turn_id = context.get("turn_id")
    source_turn_id = str(turn_id).strip() if turn_id is not None and str(turn_id).strip() else None
    existing_manifest = format_memory_manifest(scan_memory_files(target_memory_dir))
    explicit_request = context.get("user_request")
    if explicit_request:
        prompt = build_extract_combined_prompt(transcript, existing_manifest, str(explicit_request))
    else:
        prompt = build_extract_auto_only_prompt(transcript, existing_manifest)

    if agent_caller is not None:
        try:
            raw_response = await _maybe_await(agent_caller(prompt))
            parsed = _parse_llm_memory_json(raw_response)
            if parsed:
                for item in parsed:
                    try:
                        result = await remember(
                            item["content"],
                            item["type"],
                            source_type="llm_extracted",
                            scope=memory_scope,
                            source_session_id=source_session_id,
                            memory_kind=item.get("memory_kind"),
                            evidence_quote=item.get("evidence_quote") or (item["content"][:100] if isinstance(item["content"], str) else None),
                            sensitivity=item.get("sensitivity"),
                            validity_window_days=item.get("validity_window_days"),
                        )
                        if result.memory_id and result.operation not in {"noop", "conflict"}:
                            record_memory_write_event(
                                memory_id=result.memory_id,
                                session_id=source_session_id,
                                turn_id=source_turn_id,
                                project_id=memory_scope,
                                write_type="auto_saved",
                                confidence=0.76,
                                sensitivity=str(item.get("sensitivity") or "private"),
                                user_visible_text=str(item["content"]),
                                source_excerpt=str(item["content"])[:240],
                            )
                    except Exception:
                        continue
                return
        except Exception:
            pass

    for item in _heuristic_extract(transcript, scoped=memory_scope is not None):
        try:
            result = await remember(
                item["content"],
                item["type"],
                source_type=item.get("source_type") or "user_direct",
                scope=memory_scope,
                source_session_id=source_session_id,
                memory_kind=item.get("memory_kind"),
                evidence_quote=item.get("evidence_quote") or (item["content"][:100] if isinstance(item["content"], str) else None),
                sensitivity=item.get("sensitivity"),
                validity_window_days=item.get("validity_window_days"),
            )
            if result.memory_id and result.operation not in {"noop", "conflict"}:
                record_memory_write_event(
                    memory_id=result.memory_id,
                    session_id=source_session_id,
                    turn_id=source_turn_id,
                    project_id=memory_scope,
                    write_type="auto_saved",
                    confidence=0.74,
                    sensitivity=str(item.get("sensitivity") or "private"),
                    user_visible_text=str(item["content"]),
                    source_excerpt=str(item["content"])[:240],
                )
        except Exception:
            continue
