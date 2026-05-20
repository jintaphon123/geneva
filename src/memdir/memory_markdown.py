from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable

from ..skills.frontmatter import parse_frontmatter
from .memdir import ENTRYPOINT_NAME
from .memory_models import Memory
from .memory_types import MemoryType
from .memory_utils import atomic_write_text, safe_name_from_content, scope_value
from .paths import get_auto_mem_path

MemoryRootProvider = Callable[[Path], Path]


def frontmatter_text(memory: Memory, description: str) -> str:
    meta = {
        "id": memory.id,
        "name": memory.name,
        "description": description,
        "type": memory.type,
        "status": memory.status,
        "scope": memory.scope,
        "confidence": memory.confidence,
        "importance": memory.importance,
        "memory_kind": memory.memory_kind,
        "source_type": memory.source_type,
        "source_session_id": memory.source_session_id,
        "captured_at": memory.captured_at,
        "last_validated_at": memory.last_validated_at,
        "created_at": memory.created_at,
        "updated_at": memory.updated_at,
        "retention_days": memory.retention_days,
        "expires_at": memory.expires_at,
        "superseded_by": memory.superseded_by,
    }
    lines = ["---"]
    for key, value in meta.items():
        lines.append(f"{key}: {json.dumps(value) if value is None else value}")
    lines.append("---")
    lines.append("")
    lines.append(memory.content.strip())
    lines.append("")
    return "\n".join(lines)


def read_markdown_memory(path: Path) -> tuple[dict[str, object], str]:
    parsed = parse_frontmatter(path.read_text(encoding="utf-8"))
    return parsed.frontmatter, parsed.body.strip()


def description_for_memory(memory: Memory) -> str:
    path = Path(memory.path)
    if path.exists():
        try:
            frontmatter, _body = read_markdown_memory(path)
            description = frontmatter.get("description")
            if scope_value(description) is not None:
                return str(description)
        except Exception:
            pass
    return safe_name_from_content(memory.content, memory.type)[1]


def write_memory_markdown(memory: Memory, description: str | None = None) -> None:
    atomic_write_text(Path(memory.path), frontmatter_text(memory, description or description_for_memory(memory)))


def memory_root(cwd: Path | None = None, root_provider: MemoryRootProvider = get_auto_mem_path) -> Path:
    return root_provider(cwd or Path.cwd())


def memory_file_path(
    memory_type: str,
    memory_id: str,
    name: str,
    cwd: Path | None = None,
    root_provider: MemoryRootProvider = get_auto_mem_path,
) -> Path:
    root = memory_root(cwd, root_provider)
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", name.strip().lower()).strip("-") or memory_id
    return root / f"{memory_type}s" / f"{slug}-{memory_id}.md"


def entrypoint_path(cwd: Path | None = None, root_provider: MemoryRootProvider = get_auto_mem_path) -> Path:
    return memory_root(cwd, root_provider) / ENTRYPOINT_NAME


def load_entrypoint_lines(cwd: Path | None = None, root_provider: MemoryRootProvider = get_auto_mem_path) -> list[str]:
    entrypoint = entrypoint_path(cwd, root_provider)
    if not entrypoint.exists():
        return []
    try:
        return entrypoint.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []


def write_entrypoint_lines(
    lines: list[str],
    cwd: Path | None = None,
    root_provider: MemoryRootProvider = get_auto_mem_path,
) -> None:
    entrypoint = entrypoint_path(cwd, root_provider)
    entrypoint.parent.mkdir(parents=True, exist_ok=True)
    normalized = [line for line in lines if line.strip()]
    atomic_write_text(entrypoint, "\n".join(normalized).strip() + ("\n" if normalized else ""))


def relative_to_root(
    path: Path,
    cwd: Path | None = None,
    root_provider: MemoryRootProvider = get_auto_mem_path,
) -> str:
    root = memory_root(cwd, root_provider)
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return path.name


def upsert_entrypoint(
    memory: Memory,
    description: str,
    cwd: Path | None = None,
    root_provider: MemoryRootProvider = get_auto_mem_path,
) -> None:
    if memory.type == MemoryType.episodic.value:
        remove_entrypoint(memory.path, cwd, root_provider)
        return
    if memory.status != "active":
        remove_entrypoint(memory.path, cwd, root_provider)
        return
    rel = relative_to_root(Path(memory.path), cwd, root_provider)
    line = f"- [{memory.name}]({rel}) - {description}"
    prefix = f"- [{memory.name}]("
    existing = [line for line in load_entrypoint_lines(cwd, root_provider) if rel not in line and not line.startswith(prefix)]
    existing.append(line)
    write_entrypoint_lines(existing, cwd, root_provider)


def remove_entrypoint(
    path: str,
    cwd: Path | None = None,
    root_provider: MemoryRootProvider = get_auto_mem_path,
) -> None:
    candidate = Path(path)
    if cwd is None:
        for parent in candidate.parents:
            entrypoint = parent / ENTRYPOINT_NAME
            if entrypoint.exists():
                root = parent
                rel = str(candidate.relative_to(root)).replace("\\", "/")
                lines = [line for line in entrypoint.read_text(encoding="utf-8").splitlines() if rel not in line]
                atomic_write_text(entrypoint, "\n".join(lines).strip() + ("\n" if lines else ""))
                return
        return
    rel = relative_to_root(candidate, cwd, root_provider)
    lines = [line for line in load_entrypoint_lines(cwd, root_provider) if rel not in line]
    write_entrypoint_lines(lines, cwd, root_provider)
