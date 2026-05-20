from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


_OBSERVERS: list[Observer] = []


def watch_team_memory(
    team_mem_dir: Path,
    on_change: Callable[[Path], None],
    debounce_seconds: float = 1.0,
) -> None:
    team_mem_dir.mkdir(parents=True, exist_ok=True)
    timers: dict[Path, threading.Timer] = {}

    class Handler(FileSystemEventHandler):
        def on_any_event(self, event: FileSystemEvent) -> None:
            if event.is_directory:
                return
            path = Path(event.src_path)
            existing = timers.pop(path, None)
            if existing is not None:
                existing.cancel()
            timer = threading.Timer(debounce_seconds, on_change, args=(path,))
            timer.daemon = True
            timers[path] = timer
            timer.start()

    observer = Observer()
    observer.daemon = True
    observer.schedule(Handler(), str(team_mem_dir), recursive=True)
    observer.start()
    _OBSERVERS.append(observer)
