"""Session management with persistence."""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from .conversation import Conversation


@dataclass
class Session:
    """Session manager with persistence."""
    session_id: str
    provider: str
    model: str
    conversation: Conversation = field(default_factory=Conversation)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    title: str = ""
    pinned: bool = False
    skill_context: str = ""
    active_skill_name: str | None = None
    ghost_mode: bool = False

    def save(self):
        """Save session to disk."""
        session_dir = Path.home() / ".geneva" / "sessions"
        session_dir.mkdir(parents=True, exist_ok=True)

        session_file = session_dir / f"{self.session_id}.json"
        updated_at = datetime.now().isoformat()

        if not self.title:
            try:
                _existing = json.loads(session_file.read_text(encoding="utf-8")) if session_file.exists() else {}
                self.title = str(_existing.get("title", ""))
            except Exception:
                pass

        session_data = {
            "session_id": self.session_id,
            "provider": self.provider,
            "model": self.model,
            "conversation": self.conversation.to_dict(),
            "created_at": self.created_at,
            "updated_at": updated_at,
            "title": self.title,
            "pinned": self.pinned,
            "skill_context": self.skill_context,
            "active_skill_name": self.active_skill_name,
            "ghost_mode": self.ghost_mode,
        }

        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=session_dir,
                prefix=f".{self.session_id}.",
                suffix=".tmp",
                delete=False,
            ) as f:
                temp_path = Path(f.name)
                json.dump(session_data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, session_file)
            temp_path = None
            try:
                dir_fd = os.open(session_dir, os.O_RDONLY)
            except OSError:
                dir_fd = None
            if dir_fd is not None:
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            self.updated_at = updated_at
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    @classmethod
    def load(cls, session_id: str) -> Optional['Session']:
        """Load session from disk."""
        session_file = Path.home() / ".geneva" / "sessions" / f"{session_id}.json"

        if not session_file.exists():
            return None

        with open(session_file, 'r', encoding="utf-8") as f:
            data = json.load(f)

        return cls(
            session_id=data["session_id"],
            provider=data["provider"],
            model=data["model"],
            conversation=Conversation.from_dict(data["conversation"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            title=data.get("title", ""),
            pinned=bool(data.get("pinned", False)),
            skill_context=str(data.get("skill_context", "")),
            active_skill_name=data.get("active_skill_name") or None,
            ghost_mode=bool(data.get("ghost_mode", False)),
        )

    @classmethod
    def delete(cls, session_id: str) -> bool:
        """Delete session file from disk. Returns True if deleted, False if not found."""
        session_file = Path.home() / ".geneva" / "sessions" / f"{session_id}.json"

        if not session_file.exists():
            return False
        try:
            session_file.unlink()
            return True
        except OSError:
            return False

    @classmethod
    def create(cls, provider: str, model: str) -> 'Session':
        """Create a new session."""
        session_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{uuid.uuid4().hex[:8]}"
        return cls(
            session_id=session_id,
            provider=provider,
            model=model
        )
