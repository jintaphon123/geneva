from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TokenBudget:
    max_tokens: int
    used_tokens: int = 0

    @property
    def remaining(self) -> int:
        return max(self.max_tokens - self.used_tokens, 0)

    def is_exceeded(self) -> bool:
        return self.used_tokens >= self.max_tokens

    def add_usage(self, tokens: int) -> None:
        self.used_tokens += max(0, tokens)

    def enforce_dumb_zone_cap(self) -> int:
        cap = int(self.max_tokens * 0.4)
        return min(self.remaining, cap)
