from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path


def memory_age_days(path: Path) -> float:
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return math.inf
    age_seconds = max(0.0, datetime.now(timezone.utc).timestamp() - mtime)
    return age_seconds / 86_400.0


def memory_age(path: Path) -> str:
    days = memory_age_days(path)
    if days == math.inf:
        return "unknown"
    if days < 1:
        return "today"
    if days < 2:
        return "1 day"
    if days < 7:
        return f"{int(days)} days"
    if days < 30:
        weeks = max(1, int(days // 7))
        return f"{weeks} week" if weeks == 1 else f"{weeks} weeks"
    months = max(1, int(days // 30))
    return f"{months} month" if months == 1 else f"{months} months"
