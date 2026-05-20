from __future__ import annotations

import os


def is_auto_dream_enabled() -> bool:
    return os.environ.get("GENEVA_AUTO_DREAM", "0") == "1"
