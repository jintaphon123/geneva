from __future__ import annotations

import logging
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.geneva.skill_control_plane import (
    SkillControlError,
    SkillEvalStatus,
    SkillControlPlane,
    SkillRecord,
    SkillStatus,
    normalize_skill_name,
)

logger = logging.getLogger(__name__)

SKILLS_DIR = Path.home() / ".geneva" / "skills"
SKILLS_DIR_ENV = "GENEVA_SKILLS_DIR"
DEFAULT_SKILLS_DIR = Path(__file__).resolve().parent / "default_skills"
DEFAULT_SKILL_NAMES: frozenset[str] = (
    frozenset(p.parent.name for p in DEFAULT_SKILLS_DIR.glob("*/SKILL.md"))
    if DEFAULT_SKILLS_DIR.exists()
    else frozenset()
)


@dataclass
class SkillMeta:
    name: str
    description: str
    triggers: list[str]
    command: str
    path: Path
    enabled: bool = True
    status: str = "active"
    source: str = "disk"
    safety_status: str = "passed"
    safety_findings: list[str] | None = None
    usage_count: int = 0
    last_used_at: str | None = None
    checksum: str = ""
    generated_from: str | None = None
    source_session_id: str | None = None
    review_notes: list[str] | None = None


@dataclass
class Skill(SkillMeta):
    system_prompt: str = ""


class SkillEngine:
    """Loads, caches, and injects skill system prompts."""

    def __init__(self, skills_dir: Path | None = None) -> None:
        self._dir = skills_dir or _resolve_skills_dir()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._control = SkillControlPlane(self._dir)
        self._skills: dict[str, Skill] = {}
        self._records: dict[str, SkillRecord] = {}
        self._install_default_skills()
        self.reload()

    def _install_default_skills(self) -> None:
        if not DEFAULT_SKILLS_DIR.exists():
            return
        for source_skill in DEFAULT_SKILLS_DIR.glob("*/SKILL.md"):
            target_dir = self._dir / source_skill.parent.name
            target_file = target_dir / "SKILL.md"
            if target_file.exists():
                continue
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_skill, target_file)
                try:
                    self._control.set_source(source_skill.parent.name, 'builtin')
                except Exception:
                    pass
            except Exception as exc:
                logger.warning("Failed to install default skill %s: %s", source_skill, exc)

    def reload(self) -> int:
        """Scan skills directory and reload all skills. Returns count."""
        loaded: dict[str, Skill] = {}
        records = {record.name: record for record in self._control.refresh()}

        for record in records.values():
            if record.status != "active" or record.safety.status == "blocked":
                continue
            skill_path = (self._dir / record.path).resolve()
            try:
                raw = skill_path.read_text(encoding="utf-8", errors="replace")
                frontmatter, body = _parse_skill_frontmatter(raw)
                name = _normalize_skill_name(
                    str(frontmatter.get("name") or _default_skill_name(skill_path))
                )
                if not name:
                    continue
                description = _frontmatter_description(raw, frontmatter)
                triggers = _build_triggers(name, description)

                loaded[name] = Skill(
                    name=name,
                    description=description[:200],
                    triggers=triggers,
                    command=f"/{name}",
                    path=skill_path,
                    enabled=record.status == "active",
                    status=record.status,
                    source=record.source,
                    safety_status=record.safety.status,
                    safety_findings=record.safety.findings,
                    usage_count=record.usage_count,
                    last_used_at=record.last_used_at,
                    checksum=record.checksum,
                    generated_from=record.generated_from,
                    source_session_id=record.source_session_id,
                    review_notes=record.review_notes,
                    system_prompt=body.strip(),
                )
            except Exception as exc:
                logger.warning("Failed to load skill %s: %s", skill_path, exc)

        self._skills = loaded
        self._records = records
        logger.info("SkillEngine: loaded %d skills from %s", len(loaded), self._dir)
        return len(loaded)

    def list_skills(self, *, active_only: bool = False) -> list[dict[str, Any]]:
        if not self._records:
            self.reload()
        records = self._records.values()
        if active_only:
            records = [
                record
                for record in records
                if record.status == "active" and record.safety.status != "blocked"
            ]
        return [
            self._record_payload(record)
            for record in records
            if record.status != "archived"
        ]

    def get(self, name: str) -> Skill | None:
        normalized = _normalize_skill_name(name.removeprefix("/"))
        return self._skills.get(normalized)

    def detect_trigger(self, user_input: str) -> str | None:
        """Return skill name if user_input triggers a skill, else None."""
        text = user_input.strip().lower()

        if text.startswith("/"):
            parts = text[1:].split()
            command = parts[0] if parts else ""
            if command in self._skills:
                return command

        if len(text) < 20:
            return None
        for name, skill in self._skills.items():
            for trigger in skill.triggers[1:]:
                if len(trigger) > 5 and re.search(r"\b" + re.escape(trigger) + r"\b", text):
                    return name
        return None

    def create_skill(self, name: str, content: str) -> Skill | None:
        """Write a new skill SKILL.md file and reload."""
        try:
            self.create_skill_record(name, content, status="active", source="manual")
        except SkillControlError:
            return None
        normalized = _normalize_skill_name(name)
        return self._skills.get(normalized)

    def create_skill_record(
        self,
        name: str,
        content: str,
        *,
        status: SkillStatus = "active",
        source: str = "manual",
        generated_from: str | None = None,
        source_session_id: str | None = None,
    ) -> dict[str, Any] | None:
        safe_name = _normalize_skill_name(name)
        if not safe_name:
            return None
        record = self._control.write_skill(
            safe_name,
            content,
            status=status,
            source=source,
            generated_from=generated_from,
            source_session_id=source_session_id,
        )
        self.reload()
        return self._record_payload(record, include_prompt=True)

    def update_skill(self, name: str, content: str) -> bool:
        record = self._control.get(name)
        if record is None:
            return False
        try:
            self._control.write_skill(
                record.name,
                content,
                status=record.status,
                source=record.source,
                generated_from=record.generated_from,
                source_session_id=record.source_session_id,
            )
        except SkillControlError:
            raise
        self.reload()
        return True

    def delete_skill(self, name: str) -> bool:
        ok = self._control.delete_skill(name)
        if not ok:
            return False
        self.reload()
        return True

    def set_status(self, name: str, status: SkillStatus, note: str | None = None) -> dict[str, Any] | None:
        record = self._control.set_status(name, status, note)
        self.reload()
        return self._record_payload(record, include_prompt=True)

    def add_eval_case(
        self,
        name: str,
        *,
        input_text: str,
        expected: str,
        status: SkillEvalStatus = "pending",
        actual: str = "",
        notes: str = "",
    ) -> dict[str, Any] | None:
        record = self._control.add_eval_case(
            name,
            input_text=input_text,
            expected=expected,
            status=status,
            actual=actual,
            notes=notes,
        )
        self.reload()
        return self._record_payload(record, include_prompt=True)

    def update_eval_case(
        self,
        name: str,
        eval_id: str,
        *,
        status: SkillEvalStatus,
        actual: str = "",
        notes: str = "",
    ) -> dict[str, Any] | None:
        record = self._control.update_eval_case(
            name,
            eval_id,
            status=status,
            actual=actual,
            notes=notes,
        )
        self.reload()
        return self._record_payload(record, include_prompt=True)

    def rollback(self, name: str, revision_id: str) -> dict[str, Any] | None:
        record = self._control.rollback(name, revision_id)
        self.reload()
        return self._record_payload(record, include_prompt=True)

    def submit_feedback(
        self,
        name: str,
        *,
        score: int,
        outcome: str,
        note: str = "",
        suggested_change: str = "",
        source_session_id: str | None = None,
    ) -> dict[str, Any] | None:
        record = self._control.submit_feedback(
            name,
            score=score,
            outcome=outcome,
            note=note,
            suggested_change=suggested_change,
            source_session_id=source_session_id,
        )
        self.reload()
        return self._record_payload(record, include_prompt=True)

    def describe_skill(self, name: str, *, include_prompt: bool = False) -> dict[str, Any] | None:
        record = self._control.get(name)
        if record is None:
            return None
        return self._record_payload(record, include_prompt=include_prompt)

    def record_invocation(self, name: str) -> None:
        self._control.record_invocation(name)
        self.reload()

    def detect_create_intent(self, user_input: str) -> bool:
        """R10.6: Return True if user wants to create a new skill (Thai or English)."""
        u = user_input.lower()
        triggers = [
            "สร้าง skill", "ทำ skill", "เพิ่ม skill", "สร้างสกิล", "ทำสกิล",
            "create skill", "build skill", "make skill", "add skill",
            "create a skill", "build a skill", "make a skill", "add a skill",
        ]
        return any(t in u for t in triggers)

    def get_autopilot_spec(self, user_input: str) -> dict | None:
        """R10.6: Extract skill spec dict from user message if present.

        Returns {"name": str, "description": str} or None if not enough info.
        """
        import re
        patterns = [
            r"skill\s+(?:ชื่อ|named?|for|to\s+help)\s+(.+?)(?:\s*$|\s+(?:ครับ|ค่ะ|นะ))",
            r"skill\s+สำหรับ\s+(.+?)(?:\s*$)",
            r"skill\s+to\s+(.+?)(?:\s*$|\.)",
        ]
        for pat in patterns:
            m = re.search(pat, user_input, re.IGNORECASE)
            if m:
                desc = m.group(1).strip()[:80]
                slug = re.sub(r"[^\w฀-๿]+", "_", desc[:20]).strip("_").lower()
                return {"name": slug or "new_skill", "description": desc}
        return None

    def count(self, *, active_only: bool = False) -> int:
        return len(self.list_skills(active_only=active_only))

    def _record_payload(self, record: SkillRecord, *, include_prompt: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": record.name,
            "description": record.description,
            "command": record.command or f"/{record.name}",
            "triggers": record.triggers,
            "enabled": record.status == "active" and record.safety.status != "blocked",
            "status": record.status,
            "source": "builtin" if record.name in DEFAULT_SKILL_NAMES else record.source,
            "safety_status": record.safety.status,
            "safety_findings": record.safety.findings,
            "usage_count": record.usage_count,
            "last_used_at": record.last_used_at,
            "checksum": record.checksum,
            "generated_from": record.generated_from,
            "source_session_id": record.source_session_id,
            "review_notes": record.review_notes,
            "path": record.path,
            "eval_cases": [item.__dict__ for item in record.eval_cases],
            "revisions": [
                {
                    "id": revision.id,
                    "checksum": revision.checksum,
                    "source": revision.source,
                    "note": revision.note,
                    "created_at": revision.created_at,
                    "content_preview": revision.content[:500],
                }
                for revision in record.revisions
            ],
            "feedback": [item.__dict__ for item in record.feedback],
            "feedback_summary": _feedback_summary(record),
        }
        if include_prompt:
            payload["system_prompt"] = (self._control.read_markdown(record.name) or "")[:6_000]
        return payload


_engine: SkillEngine | None = None


def get_engine() -> SkillEngine:
    global _engine
    if _engine is None:
        _engine = SkillEngine()
    return _engine


def reset_engine() -> None:
    global _engine
    _engine = None


def _resolve_skills_dir() -> Path:
    override = os.environ.get(SKILLS_DIR_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return SKILLS_DIR


def _parse_skill_frontmatter(raw: str) -> tuple[dict[str, Any], str]:
    from src.skills.frontmatter import parse_frontmatter

    parsed = parse_frontmatter(raw)
    if isinstance(parsed, tuple):
        frontmatter, body = parsed
        return dict(frontmatter), str(body)
    frontmatter = getattr(parsed, "frontmatter", {})
    body = getattr(parsed, "body", raw)
    return dict(frontmatter), str(body)


def _frontmatter_description(raw: str, frontmatter: dict[str, Any]) -> str:
    raw_description = frontmatter.get("description") or ""
    if isinstance(raw_description, list):
        description = ", ".join(str(item).strip() for item in raw_description if str(item).strip())
    else:
        description = str(raw_description).strip()
    if description and description not in {">", "|", ">-", "|-"}:
        return description
    block_description = _extract_block_scalar_description(raw)
    return block_description or description


def _extract_block_scalar_description(raw: str) -> str:
    lines = raw.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return ""
    try:
        end_idx = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return ""

    fm_lines = lines[1:end_idx]
    for index, line in enumerate(fm_lines):
        stripped = line.strip()
        if not stripped.startswith("description:"):
            continue
        value = stripped.split(":", 1)[1].strip()
        if value and value not in {">", "|", ">-", "|-"}:
            return value
        collected: list[str] = []
        for continuation in fm_lines[index + 1 :]:
            if not continuation.startswith((" ", "\t")):
                break
            collected.append(continuation.strip())
        return " ".join(part for part in collected if part).strip()
    return ""


def _build_triggers(name: str, description: str) -> list[str]:
    triggers = [name]
    if description:
        words = re.findall(r"\b[\w-]{4,}\b", description.lower())
        triggers.extend(word for word in words[:8] if word not in triggers)
    return triggers


def _feedback_summary(record: SkillRecord) -> dict[str, Any]:
    total = len(record.feedback)
    if total == 0:
        return {"count": 0, "average_score": None, "positive": 0, "negative": 0}
    scores = [item.score for item in record.feedback]
    return {
        "count": total,
        "average_score": round(sum(scores) / total, 2),
        "positive": sum(1 for score in scores if score >= 4),
        "negative": sum(1 for score in scores if score <= 2),
    }


def _default_skill_name(skill_path: Path) -> str:
    return skill_path.parent.name if skill_path.name == "SKILL.md" else skill_path.stem


def _normalize_skill_name(name: str) -> str:
    return normalize_skill_name(name)
