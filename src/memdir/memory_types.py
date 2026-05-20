from __future__ import annotations

import enum


class MemoryType(enum.Enum):
    user = "user"
    feedback = "feedback"
    project = "project"
    reference = "reference"
    episodic = "episodic"


MEMORY_FRONTMATTER_EXAMPLE = """---
id: mem_20260512_001
name: Example Memory
description: One-line description of what this memory contains
type: user
status: active
scope: null
confidence: 0.9
importance: 0.5
source_type: user_direct
created_at: 2026-05-12T14:30:00+07:00
updated_at: null
retention_days: 365
expires_at: null
superseded_by: null
---

Memory content here.
"""


MEMORY_TYPE_GUIDANCE: dict[MemoryType, str] = {
    MemoryType.user: "User's role, preferences, expertise, and working style",
    MemoryType.feedback: "How the user wants the agent to behave — corrections and confirmations",
    MemoryType.project: "Ongoing work, goals, decisions, deadlines (absolute dates)",
    MemoryType.reference: "Pointers to external resources, tools, dashboards",
    MemoryType.episodic: "Exact chat episodes that make closed conversations searchable later",
}
