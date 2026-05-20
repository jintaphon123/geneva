from __future__ import annotations

from pathlib import Path

from ...memdir.memdir import ENTRYPOINT_NAME
from ...memdir.brain_engine import Memory


def build_consolidation_prompt(
    sessions: list[Path],
    memory_dir: Path,
    episodes: list[Memory] | None = None,
    skill_suggestions: list[str] | None = None,
) -> str:
    session_lines = []
    for session in sessions:
        session_lines.append(f"- {session.name}")

    memory_state = ""
    entrypoint = memory_dir / ENTRYPOINT_NAME
    if entrypoint.exists():
        try:
            memory_state = entrypoint.read_text(encoding="utf-8").strip()
        except OSError:
            memory_state = ""

    sections = [
        "You are consolidating recent session activity into durable memory.",
        "Return ONLY valid JSON in this shape:",
        "{",
        '  "memories": [{"type": "user|feedback|project|reference", "content": "...", "scope": null}],',
        '  "dream_report": {',
        '    "recommendations": ["..."],',
        '    "skill_suggestions": ["..."]',
        "  }",
        "}",
        "dream_report.recommendations: max 4 items — specific actions the owner can take.",
        "dream_report.skill_suggestions: max 3 workflows worth turning into skills; copy from SKILL OPPORTUNITIES when useful.",
        "Do not include generic tips. Only include concrete, specific recommendations based on the session content.",
        "Do not include episodic memories. Do not store low-value chat transcript. Preserve Thai when the source is Thai.",
        "",
        "Stages:",
        "1. Orient: review the existing memory index and current project context.",
        "2. Gather: inspect the touched sessions listed below.",
        "3. Consolidate: identify durable facts, decisions, and preferences.",
        "4. Prune: merge duplicate memories and avoid low-value notes.",
        "",
        "Sessions to review:",
    ]
    sections.extend(session_lines or ["- (none)"])
    sections.extend(
        [
            "",
            "Current MEMORY.md state:",
            memory_state or "(empty)",
        ]
    )
    if skill_suggestions:
        sections.extend(
            [
                "",
                "SKILL OPPORTUNITIES (workflow patterns repeated 3+ times — suggest creating a skill if useful):",
            ]
        )
        sections.extend(f"- {suggestion}" for suggestion in skill_suggestions[:3])
    if episodes:
        sections.extend(["", "Recent episodic memories:"])
        for episode in episodes[:10]:
            scope = f" scope={episode.scope}" if episode.scope else ""
            sections.append(f"\n--- episode {episode.id}{scope} ---\n{episode.content[:2000]}")
    return "\n".join(sections)
