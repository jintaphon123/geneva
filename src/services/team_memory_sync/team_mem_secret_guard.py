from __future__ import annotations

from .secret_scanner import SecretFinding, detect_secret_patterns
from .types import TeamMemoryContent


def check_team_mem_secrets(content: TeamMemoryContent) -> list[SecretFinding]:
    return detect_secret_patterns(content.content)
