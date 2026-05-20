from __future__ import annotations

import os
import tempfile
from pathlib import Path


_TEST_ROOT = Path(tempfile.mkdtemp(prefix="geneva-pytest."))

os.environ.setdefault("GENEVA_BRAIN_DB_PATH", str(_TEST_ROOT / "brain.db"))
os.environ.setdefault("GENEVA_MEMORY_EVENTS_DIR", str(_TEST_ROOT / "events"))
os.environ.setdefault("GENEVA_AUTO_MEM_PATH", str(_TEST_ROOT / "memory"))
os.environ.setdefault("GENEVA_SKILLS_DIR", str(_TEST_ROOT / "skills"))

_consult_skill = Path(os.environ["GENEVA_SKILLS_DIR"]) / "consult" / "SKILL.md"
_consult_skill.parent.mkdir(parents=True, exist_ok=True)
if not _consult_skill.exists():
    _consult_skill.write_text(
        "---\n"
        "name: consult\n"
        "description: General consultation helper\n"
        "---\n\n"
        "Provide structured consultation for open-ended requests.\n",
        encoding="utf-8",
    )
