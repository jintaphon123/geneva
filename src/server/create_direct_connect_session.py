from __future__ import annotations

from src.query.config import QueryConfig

from .direct_connect_manager import get_default_manager
from .types import DirectConnectSession


def create_direct_connect_session(config: QueryConfig) -> DirectConnectSession:
    return get_default_manager().create_session(config)
