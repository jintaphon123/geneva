"""Provider health monitor — rolling 10-minute failure rate tracking."""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque

WINDOW_SECONDS = 600
FAIL_RATE_THRESHOLD = 0.20


@dataclass
class ProviderHealth:
    provider_name: str
    _events: Deque[tuple[float, bool]] = field(default_factory=deque, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, success: bool) -> None:
        now = time.time()
        with self._lock:
            self._events.append((now, success))
            cutoff = now - WINDOW_SECONDS
            while self._events and self._events[0][0] < cutoff:
                self._events.popleft()

    def fail_rate(self) -> float:
        now = time.time()
        cutoff = now - WINDOW_SECONDS
        with self._lock:
            recent = [(t, ok) for t, ok in self._events if t >= cutoff]
        if not recent:
            return 0.0
        failures = sum(1 for _, ok in recent if not ok)
        return failures / len(recent)

    def is_healthy(self) -> bool:
        return self.fail_rate() < FAIL_RATE_THRESHOLD

    def consecutive_failures(self) -> int:
        with self._lock:
            events = list(self._events)
        count = 0
        for _, ok in reversed(events):
            if not ok:
                count += 1
            else:
                break
        return count


_registry: dict[str, ProviderHealth] = {}
_registry_lock = threading.Lock()


def get_health(provider_name: str) -> ProviderHealth:
    with _registry_lock:
        if provider_name not in _registry:
            _registry[provider_name] = ProviderHealth(provider_name=provider_name)
        return _registry[provider_name]


def record_provider_outcome(provider_name: str, success: bool) -> None:
    get_health(provider_name).record(success)


def should_switch_provider(provider_name: str) -> bool:
    """Return True if provider's fail rate exceeds threshold OR 3 consecutive failures."""
    health = get_health(provider_name)
    return not health.is_healthy() or health.consecutive_failures() >= 3


def get_all_health() -> dict[str, dict]:
    with _registry_lock:
        providers = list(_registry.items())
    return {
        name: {
            "fail_rate": h.fail_rate(),
            "is_healthy": h.is_healthy(),
            "consecutive_failures": h.consecutive_failures(),
        }
        for name, h in providers
    }
