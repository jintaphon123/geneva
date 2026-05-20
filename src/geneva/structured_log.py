from __future__ import annotations

import json
import logging
import os
import sys
import traceback
from typing import Any

_STANDARD_ATTRS = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
})


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        doc: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
            "module": record.module,
            "lineno": record.lineno,
        }
        if record.exc_info:
            doc["exception"] = "".join(traceback.format_exception(*record.exc_info))
        ctx = {
            k: v for k, v in record.__dict__.items()
            if k not in _STANDARD_ATTRS and not k.startswith("_")
        }
        if ctx:
            doc["context"] = ctx
        return json.dumps(doc, ensure_ascii=False, default=str)


_metrics_logger = logging.getLogger("geneva.metrics")


def log_metric(event: str, **kwargs: Any) -> None:
    try:
        _metrics_logger.info("", extra={"event": event, **kwargs})
    except Exception:
        pass


def setup_structured_logging(log_path: str | None = None, level: int = logging.INFO) -> None:
    if not log_path and os.environ.get("GENEVA_STRUCTURED_LOGS") != "1":
        return
    root = logging.getLogger()
    for h in root.handlers:
        if isinstance(h.formatter, JsonFormatter):
            return
    handler: logging.Handler
    if log_path:
        handler = logging.FileHandler(log_path, encoding="utf-8")
    else:
        handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level)
