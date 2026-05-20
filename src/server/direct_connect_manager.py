from __future__ import annotations

import threading
from datetime import datetime, timezone
from uuid import uuid4

from src.query.config import QueryConfig

from .types import DirectConnectSession


class DirectConnectManager:
    def __init__(self) -> None:
        self._sessions: dict[str, DirectConnectSession] = {}
        self._lock = threading.RLock()

    def create_session(self, config: QueryConfig) -> DirectConnectSession:
        session = DirectConnectSession(
            session_id=str(uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            config=config,
            transcript=[],
        )
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> DirectConnectSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def list_sessions(self) -> list[DirectConnectSession]:
        with self._lock:
            return list(self._sessions.values())

    def close_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


_DEFAULT_MANAGER = DirectConnectManager()


def get_default_manager() -> DirectConnectManager:
    return _DEFAULT_MANAGER
