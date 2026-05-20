from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.bootstrap.state import add_to_total_cost_state, reset_cost_state


@dataclass
class CostEntry:
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    cost_usd: float
    timestamp: str


class CostTracker:
    def __init__(self) -> None:
        self._entries: list[CostEntry] = []
        self._legacy_records: dict[str, int] = {}
        self._lock = threading.RLock()

    def add_cost(self, entry: CostEntry) -> None:
        normalized = CostEntry(
            model=entry.model,
            input_tokens=entry.input_tokens,
            output_tokens=entry.output_tokens,
            cache_read_tokens=entry.cache_read_tokens,
            cache_write_tokens=entry.cache_write_tokens,
            cost_usd=entry.cost_usd,
            timestamp=entry.timestamp or datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._entries.append(normalized)
            add_to_total_cost_state(
                model=normalized.model,
                cost_usd=normalized.cost_usd,
                input_tokens=normalized.input_tokens,
                output_tokens=normalized.output_tokens,
                cache_read=normalized.cache_read_tokens,
                cache_write=normalized.cache_write_tokens,
            )

    def record(self, label: str, units: int) -> None:
        with self._lock:
            self._legacy_records[label] = self._legacy_records.get(label, 0) + int(units)

    def get_total_cost_usd(self) -> float:
        with self._lock:
            return sum(entry.cost_usd for entry in self._entries)

    def get_per_model_breakdown(self) -> dict[str, float]:
        with self._lock:
            breakdown: dict[str, float] = {}
            for entry in self._entries:
                breakdown[entry.model] = breakdown.get(entry.model, 0.0) + entry.cost_usd
            return breakdown

    def format_cost_summary(self) -> str:
        with self._lock:
            if not self._entries:
                return "model | tokens | cost\n----- | ------ | ----\n(none) | 0 | $0.0000"

            aggregates: dict[str, dict[str, float]] = {}
            for entry in self._entries:
                bucket = aggregates.setdefault(
                    entry.model,
                    {"tokens": 0.0, "cost": 0.0},
                )
                bucket["tokens"] += (
                    entry.input_tokens
                    + entry.output_tokens
                    + entry.cache_read_tokens
                    + entry.cache_write_tokens
                )
                bucket["cost"] += entry.cost_usd

            lines = ["model | tokens | cost", "----- | ------ | ----"]
            for model in sorted(aggregates):
                token_count = int(aggregates[model]["tokens"])
                cost = aggregates[model]["cost"]
                lines.append(f"{model} | {token_count} | ${cost:.4f}")
            lines.append(f"TOTAL | {sum(int(v['tokens']) for v in aggregates.values())} | ${self.get_total_cost_usd():.4f}")
            return "\n".join(lines)

    def save_to_disk(self, session_id: str) -> None:
        with self._lock:
            path = self._session_cost_path(session_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "session_id": session_id,
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "entries": [asdict(entry) for entry in self._entries],
            }
            path.write_text(json.dumps(payload, indent=2))

    def restore_from_disk(self, session_id: str) -> None:
        path = self._session_cost_path(session_id)
        if not path.exists():
            return

        payload = json.loads(path.read_text())
        entries = payload.get("entries", [])
        with self._lock:
            self._entries = []
            self._legacy_records = {}
            reset_cost_state()
            for raw_entry in entries:
                entry = CostEntry(
                    model=str(raw_entry["model"]),
                    input_tokens=int(raw_entry["input_tokens"]),
                    output_tokens=int(raw_entry["output_tokens"]),
                    cache_read_tokens=int(raw_entry["cache_read_tokens"]),
                    cache_write_tokens=int(raw_entry["cache_write_tokens"]),
                    cost_usd=float(raw_entry["cost_usd"]),
                    timestamp=str(raw_entry.get("timestamp") or datetime.now(timezone.utc).isoformat()),
                )
                self.add_cost(entry)

    def _session_cost_path(self, session_id: str) -> Path:
        return Path.home() / ".geneva" / "sessions" / session_id / "costs.json"
