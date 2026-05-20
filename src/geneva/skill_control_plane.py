from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from src.skills.frontmatter import parse_frontmatter

SkillStatus = Literal["review", "active", "disabled", "archived"]
SafetyStatus = Literal["passed", "warning", "blocked"]
SkillEvalStatus = Literal["pending", "passed", "failed"]

CONTROL_PLANE_FILE = ".skill-control-plane.json"
CONTROL_PLANE_VERSION = 1
MAX_SKILL_BYTES = 80_000


class SkillControlError(ValueError):
    pass


@dataclass
class SkillSafety:
    status: SafetyStatus = "passed"
    findings: list[str] = field(default_factory=list)


@dataclass
class SkillEvalCase:
    id: str
    input: str
    expected: str
    status: SkillEvalStatus = "pending"
    actual: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SkillEvalCase":
        now = _now_iso()
        return cls(
            id=str(payload.get("id") or _short_id("eval")),
            input=str(payload.get("input") or ""),
            expected=str(payload.get("expected") or ""),
            status=_coerce_eval_status(payload.get("status")),
            actual=str(payload.get("actual") or ""),
            notes=str(payload.get("notes") or ""),
            created_at=str(payload.get("created_at") or now),
            updated_at=str(payload.get("updated_at") or now),
        )


@dataclass
class SkillRevision:
    id: str
    checksum: str
    content: str
    source: str
    note: str = ""
    created_at: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SkillRevision":
        return cls(
            id=str(payload.get("id") or _short_id("rev")),
            checksum=str(payload.get("checksum") or ""),
            content=str(payload.get("content") or ""),
            source=str(payload.get("source") or "unknown"),
            note=str(payload.get("note") or ""),
            created_at=str(payload.get("created_at") or _now_iso()),
        )


@dataclass
class SkillFeedback:
    id: str
    score: int
    outcome: str
    note: str = ""
    suggested_change: str = ""
    source_session_id: str | None = None
    created_at: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SkillFeedback":
        return cls(
            id=str(payload.get("id") or _short_id("fb")),
            score=_bounded_int(payload.get("score"), minimum=1, maximum=5, default=3),
            outcome=str(payload.get("outcome") or "unknown"),
            note=str(payload.get("note") or ""),
            suggested_change=str(payload.get("suggested_change") or ""),
            source_session_id=_optional_text(payload.get("source_session_id")),
            created_at=str(payload.get("created_at") or _now_iso()),
        )


@dataclass
class SkillRecord:
    name: str
    path: str
    status: SkillStatus
    source: str
    description: str = ""
    command: str = ""
    triggers: list[str] = field(default_factory=list)
    checksum: str = ""
    safety: SkillSafety = field(default_factory=SkillSafety)
    generated_from: str | None = None
    source_session_id: str | None = None
    created_at: str = ""
    updated_at: str = ""
    activated_at: str | None = None
    disabled_at: str | None = None
    archived_at: str | None = None
    usage_count: int = 0
    last_used_at: str | None = None
    review_notes: list[str] = field(default_factory=list)
    eval_cases: list[SkillEvalCase] = field(default_factory=list)
    revisions: list[SkillRevision] = field(default_factory=list)
    feedback: list[SkillFeedback] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SkillRecord":
        safety_payload = payload.get("safety")
        safety = (
            SkillSafety(
                status=str(safety_payload.get("status") or "passed"),  # type: ignore[arg-type]
                findings=[str(item) for item in safety_payload.get("findings") or []],
            )
            if isinstance(safety_payload, dict)
            else SkillSafety()
        )
        return cls(
            name=str(payload.get("name") or ""),
            path=str(payload.get("path") or ""),
            status=_coerce_status(payload.get("status")),
            source=str(payload.get("source") or "disk"),
            description=str(payload.get("description") or ""),
            command=str(payload.get("command") or ""),
            triggers=[str(item) for item in payload.get("triggers") or []],
            checksum=str(payload.get("checksum") or ""),
            safety=safety,
            generated_from=_optional_text(payload.get("generated_from")),
            source_session_id=_optional_text(payload.get("source_session_id")),
            created_at=str(payload.get("created_at") or _now_iso()),
            updated_at=str(payload.get("updated_at") or _now_iso()),
            activated_at=_optional_text(payload.get("activated_at")),
            disabled_at=_optional_text(payload.get("disabled_at")),
            archived_at=_optional_text(payload.get("archived_at")),
            usage_count=int(payload.get("usage_count") or 0),
            last_used_at=_optional_text(payload.get("last_used_at")),
            review_notes=[str(item) for item in payload.get("review_notes") or []],
            eval_cases=[
                SkillEvalCase.from_dict(item)
                for item in payload.get("eval_cases") or []
                if isinstance(item, dict)
            ],
            revisions=[
                SkillRevision.from_dict(item)
                for item in payload.get("revisions") or []
                if isinstance(item, dict)
            ],
            feedback=[
                SkillFeedback.from_dict(item)
                for item in payload.get("feedback") or []
                if isinstance(item, dict)
            ],
        )


class SkillControlPlane:
    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir.expanduser().resolve()
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.skills_dir / CONTROL_PLANE_FILE

    def set_source(self, name: str, source: str) -> None:
        records = self._load_records()
        if name in records:
            records[name].source = source
            self._save_records(records)

    def refresh(self) -> list[SkillRecord]:
        records = self._load_records()
        seen: set[str] = set()

        for skill_path in self._skill_files():
            content = skill_path.read_text(encoding="utf-8", errors="replace")
            name, description, triggers = inspect_skill_markdown(content, fallback_name=_default_skill_name(skill_path))
            if not name:
                continue
            seen.add(name)
            safety = scan_skill_safety(content)
            checksum = _checksum(content)
            rel_path = str(skill_path.relative_to(self.skills_dir))
            existing = records.get(name)
            now = _now_iso()
            if existing is None:
                status: SkillStatus = "review" if safety.status == "blocked" else "active"
                existing = SkillRecord(
                    name=name,
                    path=rel_path,
                    status=status,
                    source="disk",
                    created_at=now,
                )
            previous_checksum = existing.checksum
            existing.path = rel_path
            existing.description = description[:300]
            existing.command = f"/{name}"
            existing.triggers = triggers
            existing.checksum = checksum
            existing.safety = safety
            existing.updated_at = now if previous_checksum != checksum else existing.updated_at
            records[name] = existing

        records = {
            name: record
            for name, record in records.items()
            if name in seen or record.status == "archived"
        }
        self._save_records(records)
        return sorted(records.values(), key=lambda record: (record.status != "review", record.name))

    def get(self, name: str) -> SkillRecord | None:
        return self._load_records().get(normalize_skill_name(name))

    def read_markdown(self, name: str) -> str | None:
        record = self.get(name)
        if record is None:
            return None
        path = self._record_path(record)
        if not path.exists() or not path.is_file():
            return None
        return path.read_text(encoding="utf-8", errors="replace")

    def write_skill(
        self,
        name: str,
        content: str,
        *,
        status: SkillStatus = "active",
        source: str = "manual",
        generated_from: str | None = None,
        source_session_id: str | None = None,
        revision_note: str = "",
    ) -> SkillRecord:
        safe_name = normalize_skill_name(name)
        if not safe_name:
            raise SkillControlError("Skill name is required")
        content = content.strip()
        if not content:
            raise SkillControlError("Skill content is required")
        safety = scan_skill_safety(content)
        if status == "active" and safety.status == "blocked":
            raise SkillControlError("Blocked skill cannot be activated before review")

        skill_dir = self._safe_skill_dir(safe_name)
        skill_dir.mkdir(parents=True, exist_ok=True)
        records = self._load_records()
        now = _now_iso()
        skill_path = skill_dir / "SKILL.md"
        old_record = records.get(safe_name)
        old_content = skill_path.read_text(encoding="utf-8", errors="replace") if skill_path.exists() else ""
        parsed_name, description, triggers = inspect_skill_markdown(content, fallback_name=safe_name)
        final_name = parsed_name or safe_name
        record = records.get(final_name) or SkillRecord(
            name=final_name,
            path=str(skill_path.relative_to(self.skills_dir)),
            status=status,
            source=source,
            created_at=now,
        )
        if old_content:
            _append_revision(record, old_content, source="before-write", note=revision_note or "Snapshot before write")

        self._atomic_write(skill_path, content + "\n")
        record.path = str(skill_path.relative_to(self.skills_dir))
        record.status = status
        record.source = source or record.source
        record.description = description[:300]
        record.command = f"/{final_name}"
        record.triggers = triggers
        record.checksum = _checksum(content)
        record.safety = safety
        record.generated_from = generated_from or record.generated_from
        record.source_session_id = source_session_id or record.source_session_id
        record.updated_at = now
        if status == "active":
            record.activated_at = now
        _append_revision(record, content, source=source, note=revision_note or "Current content")
        if old_record is not None and old_record.name != final_name:
            records.pop(old_record.name, None)
        records[final_name] = record
        self._save_records(records)
        return record

    def set_status(self, name: str, status: SkillStatus, note: str | None = None) -> SkillRecord:
        records = self._load_records()
        normalized = normalize_skill_name(name)
        record = records.get(normalized)
        if record is None:
            raise SkillControlError("Skill not found")
        markdown = self.read_markdown(normalized)
        if markdown is None:
            raise SkillControlError("Skill file not found")
        safety = scan_skill_safety(markdown)
        if status == "active" and safety.status == "blocked":
            raise SkillControlError("Blocked skill cannot be activated before review")
        if status == "active" and _requires_eval_before_activation(record) and not _has_passing_eval(record):
            raise SkillControlError("Generated skill requires one passed evaluation before activation")

        now = _now_iso()
        record.status = status
        record.safety = safety
        record.updated_at = now
        if status == "active":
            record.activated_at = now
        elif status == "disabled":
            record.disabled_at = now
        elif status == "archived":
            record.archived_at = now
        if note:
            record.review_notes.append(note[:500])
        records[normalized] = record
        self._save_records(records)
        return record

    def add_eval_case(
        self,
        name: str,
        *,
        input_text: str,
        expected: str,
        status: SkillEvalStatus = "pending",
        actual: str = "",
        notes: str = "",
    ) -> SkillRecord:
        records = self._load_records()
        normalized = normalize_skill_name(name)
        record = records.get(normalized)
        if record is None:
            raise SkillControlError("Skill not found")
        if not input_text.strip() or not expected.strip():
            raise SkillControlError("Evaluation input and expected behavior are required")
        now = _now_iso()
        record.eval_cases.append(
            SkillEvalCase(
                id=_short_id("eval"),
                input=input_text.strip()[:2_000],
                expected=expected.strip()[:2_000],
                status=status,
                actual=actual.strip()[:4_000],
                notes=notes.strip()[:1_000],
                created_at=now,
                updated_at=now,
            )
        )
        record.updated_at = now
        records[normalized] = record
        self._save_records(records)
        return record

    def update_eval_case(
        self,
        name: str,
        eval_id: str,
        *,
        status: SkillEvalStatus,
        actual: str = "",
        notes: str = "",
    ) -> SkillRecord:
        records = self._load_records()
        normalized = normalize_skill_name(name)
        record = records.get(normalized)
        if record is None:
            raise SkillControlError("Skill not found")
        case = next((item for item in record.eval_cases if item.id == eval_id), None)
        if case is None:
            raise SkillControlError("Evaluation case not found")
        case.status = status
        case.actual = actual.strip()[:4_000]
        case.notes = notes.strip()[:1_000]
        case.updated_at = _now_iso()
        record.updated_at = case.updated_at
        records[normalized] = record
        self._save_records(records)
        return record

    def rollback(self, name: str, revision_id: str) -> SkillRecord:
        record = self.get(name)
        if record is None:
            raise SkillControlError("Skill not found")
        revision = next((item for item in record.revisions if item.id == revision_id), None)
        if revision is None or not revision.content.strip():
            raise SkillControlError("Revision not found")
        return self.write_skill(
            record.name,
            revision.content,
            status=record.status,
            source="rollback",
            generated_from=record.generated_from,
            source_session_id=record.source_session_id,
            revision_note=f"Rollback to {revision.id}",
        )

    def submit_feedback(
        self,
        name: str,
        *,
        score: int,
        outcome: str,
        note: str = "",
        suggested_change: str = "",
        source_session_id: str | None = None,
    ) -> SkillRecord:
        records = self._load_records()
        normalized = normalize_skill_name(name)
        record = records.get(normalized)
        if record is None:
            raise SkillControlError("Skill not found")
        feedback = SkillFeedback(
            id=_short_id("fb"),
            score=_bounded_int(score, minimum=1, maximum=5, default=3),
            outcome=outcome.strip()[:200] or "unknown",
            note=note.strip()[:1_000],
            suggested_change=suggested_change.strip()[:2_000],
            source_session_id=source_session_id,
            created_at=_now_iso(),
        )
        record.feedback.append(feedback)
        record.feedback = record.feedback[-50:]
        if feedback.score <= 2 or feedback.outcome.lower() in {"failed", "bad", "poor"}:
            record.status = "review"
            record.review_notes.append(f"Feedback {feedback.id}: {feedback.outcome}")
        records[normalized] = record
        self._save_records(records)

        if feedback.suggested_change:
            markdown = self.read_markdown(normalized) or ""
            adjusted = _append_feedback_backlog(markdown, feedback)
            return self.write_skill(
                normalized,
                adjusted,
                status="review",
                source="feedback",
                generated_from=record.generated_from,
                source_session_id=source_session_id or record.source_session_id,
                revision_note=f"Feedback adjustment {feedback.id}",
            )
        return record

    def delete_skill(self, name: str) -> bool:
        records = self._load_records()
        normalized = normalize_skill_name(name)
        record = records.pop(normalized, None)
        if record is None:
            return False
        path = self._record_path(record)
        if path.name == "SKILL.md" and path.parent.parent == self.skills_dir:
            shutil.rmtree(path.parent, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
        self._save_records(records)
        return True

    def record_invocation(self, name: str) -> None:
        records = self._load_records()
        normalized = normalize_skill_name(name)
        record = records.get(normalized)
        if record is None:
            return
        record.usage_count += 1
        record.last_used_at = _now_iso()
        records[normalized] = record
        self._save_records(records)

    def _load_records(self) -> dict[str, SkillRecord]:
        if not self.registry_path.exists():
            return {}
        try:
            raw = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        skills = raw.get("skills") if isinstance(raw, dict) else {}
        if not isinstance(skills, dict):
            return {}
        return {
            normalize_skill_name(name): SkillRecord.from_dict(payload)
            for name, payload in skills.items()
            if isinstance(payload, dict) and normalize_skill_name(name)
        }

    def _save_records(self, records: dict[str, SkillRecord]) -> None:
        payload = {
            "version": CONTROL_PLANE_VERSION,
            "updated_at": _now_iso(),
            "skills": {name: _record_to_dict(record) for name, record in sorted(records.items())},
        }
        self._atomic_write(self.registry_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    def _skill_files(self) -> list[Path]:
        candidates: list[Path] = []
        candidates.extend(self.skills_dir.glob("*/SKILL.md"))
        candidates.extend(path for path in self.skills_dir.glob("*.md") if path.name != CONTROL_PLANE_FILE)
        return sorted(candidates)

    def _record_path(self, record: SkillRecord) -> Path:
        target = (self.skills_dir / record.path).resolve()
        try:
            target.relative_to(self.skills_dir)
        except ValueError as exc:
            raise SkillControlError("Skill path escapes skills directory") from exc
        return target

    def _safe_skill_dir(self, name: str) -> Path:
        target = (self.skills_dir / name).resolve()
        try:
            target.relative_to(self.skills_dir)
        except ValueError as exc:
            raise SkillControlError("Skill path escapes skills directory") from exc
        return target

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent), text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        finally:
            try:
                Path(tmp_name).unlink(missing_ok=True)
            except OSError:
                pass


def inspect_skill_markdown(content: str, *, fallback_name: str) -> tuple[str, str, list[str]]:
    parsed = parse_frontmatter(content)
    frontmatter = parsed.frontmatter
    name = normalize_skill_name(str(frontmatter.get("name") or fallback_name))
    description = _description_from_frontmatter(content, frontmatter)
    return name, description, _build_triggers(name, description)


def scan_skill_safety(content: str) -> SkillSafety:
    findings: list[str] = []
    status: SafetyStatus = "passed"
    encoded_size = len(content.encode("utf-8"))
    parsed = parse_frontmatter(content)
    frontmatter = parsed.frontmatter

    if not frontmatter.get("name"):
        findings.append("missing name frontmatter")
        status = "blocked"
    if not frontmatter.get("description"):
        findings.append("missing description frontmatter")
        status = "blocked"
    if encoded_size > MAX_SKILL_BYTES:
        findings.append(f"skill exceeds {MAX_SKILL_BYTES} bytes")
        status = "blocked"
    if re.search(r"sk-(?:ant|proj|live|test)-[A-Za-z0-9_-]{12,}", content):
        findings.append("possible API key embedded in skill")
        status = "blocked"
    if re.search(r"\b(?:password|api_key|secret|token)\s*[:=]\s*['\"][^'\"]{8,}", content, re.IGNORECASE):
        findings.append("possible secret assignment embedded in skill")
        status = "blocked"
    if re.search(r"\b(?:curl|wget)\b[^\n|;]*\|\s*(?:sh|bash|zsh)", content, re.IGNORECASE):
        findings.append("pipe-to-shell install command requires manual review")
        status = _max_safety(status, "warning")
    if re.search(r"\brm\s+-rf\s+(?:/|~|\$HOME)", content):
        findings.append("destructive shell command requires manual review")
        status = _max_safety(status, "warning")
    if re.search(r"ignore (?:all )?(?:previous|system|developer) instructions", content, re.IGNORECASE):
        findings.append("prompt-injection language requires manual review")
        status = _max_safety(status, "warning")

    allowed_tools = frontmatter.get("allowed-tools")
    if isinstance(allowed_tools, str):
        allowed = [part.strip() for part in allowed_tools.split(",")]
    elif isinstance(allowed_tools, list):
        allowed = [str(part).strip() for part in allowed_tools]
    else:
        allowed = []
    broad_tools = {"Bash", "Write", "Edit", "MultiEdit"}
    if any(tool in broad_tools for tool in allowed):
        findings.append("skill requests high-impact tools")
        status = _max_safety(status, "warning")
    return SkillSafety(status=status, findings=findings)


def normalize_skill_name(name: str) -> str:
    normalized = name.lower().strip().removeprefix("/")
    normalized = normalized.replace(" ", "-")
    normalized = re.sub(r"[^\w-]", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized)
    return normalized.strip("-")


def _record_to_dict(record: SkillRecord) -> dict[str, Any]:
    data = asdict(record)
    data["safety"] = asdict(record.safety)
    data["eval_cases"] = [asdict(item) for item in record.eval_cases[-30:]]
    data["revisions"] = [asdict(item) for item in record.revisions[-20:]]
    data["feedback"] = [asdict(item) for item in record.feedback[-50:]]
    return data


def _append_revision(record: SkillRecord, content: str, *, source: str, note: str) -> None:
    checksum = _checksum(content)
    if record.revisions and record.revisions[-1].checksum == checksum:
        return
    record.revisions.append(
        SkillRevision(
            id=_short_id("rev"),
            checksum=checksum,
            content=content,
            source=source,
            note=note[:500],
            created_at=_now_iso(),
        )
    )
    record.revisions = record.revisions[-20:]


def _requires_eval_before_activation(record: SkillRecord) -> bool:
    return record.source in {"generated", "feedback"}


def _has_passing_eval(record: SkillRecord) -> bool:
    return any(item.status == "passed" for item in record.eval_cases)


def _append_feedback_backlog(markdown: str, feedback: SkillFeedback) -> str:
    addition = (
        "\n\n## Feedback-Driven Review Backlog\n\n"
        f"- Feedback id: {feedback.id}\n"
        f"- Outcome: {feedback.outcome}\n"
        f"- Score: {feedback.score}/5\n"
        f"- Suggested change: {feedback.suggested_change}\n"
    )
    return (markdown.rstrip() + addition).strip()


def _description_from_frontmatter(raw: str, frontmatter: dict[str, Any]) -> str:
    value = frontmatter.get("description") or ""
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    text = str(value).strip()
    if text and text not in {">", "|", ">-", "|-"}:
        return text
    return _extract_block_scalar_description(raw)


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
        if not line.strip().startswith("description:"):
            continue
        collected: list[str] = []
        for continuation in fm_lines[index + 1 :]:
            if not continuation.startswith((" ", "\t")):
                break
            collected.append(continuation.strip())
        return " ".join(part for part in collected if part).strip()
    return ""


def _build_triggers(name: str, description: str) -> list[str]:
    triggers = [name] if name else []
    if description:
        words = re.findall(r"\b[\w-]{4,}\b", description.lower())
        triggers.extend(word for word in words[:8] if word not in triggers)
    return triggers


def _default_skill_name(skill_path: Path) -> str:
    return skill_path.parent.name if skill_path.name == "SKILL.md" else skill_path.stem


def _checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _short_id(prefix: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    digest = hashlib.sha1(stamp.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}_{stamp}_{digest}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _coerce_status(value: Any) -> SkillStatus:
    text = str(value or "").lower()
    if text in {"review", "active", "disabled", "archived"}:
        return text  # type: ignore[return-value]
    return "review"


def _max_safety(current: SafetyStatus, candidate: SafetyStatus) -> SafetyStatus:
    order = {"passed": 0, "warning": 1, "blocked": 2}
    return candidate if order[candidate] > order[current] else current


def _coerce_eval_status(value: Any) -> SkillEvalStatus:
    text = str(value or "").lower()
    if text in {"pending", "passed", "failed"}:
        return text  # type: ignore[return-value]
    return "pending"


def _bounded_int(value: Any, *, minimum: int, maximum: int, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
