from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from src.memdir.paths import get_auto_mem_path, get_data_dir


DNA_FILENAMES = ("me.md", "work.md", "team.md", "current-priorities.md", "goals.md")
MAX_BLOCK_CHARS = 24_000
MAX_DNA_FILE_CHARS = 8_000


@dataclass(frozen=True)
class RuntimeIdentityBlock:
    source_type: str
    label: str
    text: str
    reason: str
    metadata: dict[str, str]


def load_runtime_identity_blocks() -> list[RuntimeIdentityBlock]:
    blocks: list[RuntimeIdentityBlock] = []
    soul = _load_soul_block()
    if soul is not None:
        blocks.append(soul)
    brain = _load_brain_block()
    if brain is not None:
        blocks.append(brain)
    dna = _load_dna_block()
    if dna is not None:
        blocks.append(dna)
    return blocks


def _load_soul_block() -> RuntimeIdentityBlock | None:
    from src.geneva.soul import SoulLoader

    text = SoulLoader().get_injected_block().strip()
    if not text:
        return None
    return RuntimeIdentityBlock(
        source_type="soul_identity",
        label="Soul — Identity Contract",
        text=_trim(text, MAX_BLOCK_CHARS),
        reason="Geneva's core identity contract is pinned before durable memory.",
        metadata={"path": str(SoulLoader().resolved_soul_path() or "")},
    )


def _load_brain_block() -> RuntimeIdentityBlock | None:
    path = _first_existing([get_data_dir() / "BRAIN.md", get_auto_mem_path(Path.cwd()).parent / "BRAIN.md"])
    if path is None:
        return None
    raw = _read_text(path)
    if not raw:
        return None
    text = "## BRAIN — Runtime Contract\n" + _strip_frontmatter(raw)
    return RuntimeIdentityBlock(
        source_type="brain_runtime_contract",
        label="BRAIN — Runtime Contract",
        text=_trim(text, MAX_BLOCK_CHARS),
        reason="BRAIN.md contains the high-level runtime contract and operating DNA.",
        metadata={"path": str(path)},
    )


def _load_dna_block() -> RuntimeIdentityBlock | None:
    data_dir = get_data_dir()
    memory_dir = get_auto_mem_path(Path.cwd())
    parts: list[str] = []
    used: list[str] = []
    for filename in DNA_FILENAMES:
        path = _first_existing(
            [
                data_dir / "context" / filename,
                data_dir / filename,
                memory_dir / filename,
            ]
        )
        if path is None:
            continue
        raw = _read_text(path)
        if not raw:
            continue
        parts.append(f"### {filename}\n{_trim(_strip_frontmatter(raw), MAX_DNA_FILE_CHARS)}")
        used.append(str(path))
    if not parts:
        return None
    text = "## DNA — Owner Context\n" + "\n\n".join(parts)
    return RuntimeIdentityBlock(
        source_type="owner_dna_context",
        label="DNA — Owner Context",
        text=_trim(text, MAX_BLOCK_CHARS),
        reason="Owner DNA files are pinned so Geneva can answer identity/team/work questions reliably.",
        metadata={"paths": "\n".join(used)},
    )


def _first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists() and path.is_file():
            return path
    return None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _strip_frontmatter(text: str) -> str:
    return re.sub(r"^---\n.*?\n---\n?", "", text, flags=re.DOTALL).strip()


def _trim(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return "[truncated]\n" + text[-max_chars:].lstrip()
