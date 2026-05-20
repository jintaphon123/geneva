from __future__ import annotations

import hashlib

from pydantic import BaseModel


class TeamMemoryContent(BaseModel):
    name: str
    description: str
    type: str
    content: str
    author: str | None = None
    created_at: str | None = None
    content_hash: str = ""

    def compute_hash(self) -> str:
        self.content_hash = hashlib.sha256(self.content.encode("utf-8")).hexdigest()[:16]
        return self.content_hash
