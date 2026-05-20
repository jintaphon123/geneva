from __future__ import annotations

import collections
import hmac
import logging
import os
import re as _re_sec
import threading
import time as _time
from dataclasses import dataclass
from http import HTTPStatus
from ipaddress import ip_address
from typing import Any
from urllib.parse import urlparse

MAX_API_BODY_BYTES = 1_000_000
GENEVA_REQUEST_HEADER = "X-Second-Brain-Request"
REMOTE_BIND_OVERRIDE_ENV = "GENEVA_ALLOW_REMOTE_BIND"
LOCAL_HOSTNAMES = {"localhost"}
LOCAL_TEST_CLIENTS = {"testclient"}

RATE_LIMIT_RPM = int(os.environ.get("GENEVA_RATE_LIMIT_RPM", "120"))
GENEVA_AUTH_TOKEN_ENV = "GENEVA_AUTH_TOKEN"

_rate_windows: dict[str, collections.deque] = {}
_rate_lock = threading.Lock()


def check_rate_limit(client_host: str) -> bool:
    """Return True if within rate limit, False if exceeded (sliding 60s window)."""
    now = _time.monotonic()
    key = client_host.strip().lower() or "unknown"
    with _rate_lock:
        window = _rate_windows.setdefault(key, collections.deque())
        cutoff = now - 60.0
        while window and window[0] < cutoff:
            window.popleft()
        if len(window) >= RATE_LIMIT_RPM:
            return False
        window.append(now)
        return True


SECURITY_RESPONSE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "base-uri 'none'; "
        "object-src 'none'; "
        "frame-ancestors 'none'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "form-action 'self'"
    ),
}


@dataclass(frozen=True)
class SecurityFailure:
    payload: dict[str, Any]
    status: HTTPStatus


def is_origin_allowed(origin: str | None) -> bool:
    if not origin:
        return True
    parsed = urlparse(origin)
    return parsed.scheme in {"http", "https"} and _is_local_host(parsed.hostname)


def is_host_allowed(host: str | None) -> bool:
    hostname = _hostname_from_header(host)
    if not hostname:
        return False
    return _is_local_host(hostname)


def is_client_allowed(client_host: str | None) -> bool:
    if not client_host:
        return True
    if client_host.strip().lower() in LOCAL_TEST_CLIENTS:
        return True
    return _is_local_host(client_host)


def is_bind_host_allowed(host: str) -> bool:
    if _is_truthy_env(REMOTE_BIND_OVERRIDE_ENV):
        return True
    return _is_local_host(host)


def validate_request_security(
    method: str,
    *,
    origin: str | None,
    host: str | None,
    content_type: str | None = None,
    content_length: int = 0,
    client_host: str | None = None,
    geneva_header: str | None = None,
    auth_token: str | None = None,
) -> SecurityFailure | None:
    method = method.upper()
    if not is_client_allowed(client_host):
        return _security_failure("Forbidden client", HTTPStatus.FORBIDDEN)
    if not check_rate_limit(client_host or ""):
        return _security_failure("Rate limit exceeded", HTTPStatus.TOO_MANY_REQUESTS)
    expected_token = os.environ.get(GENEVA_AUTH_TOKEN_ENV, "").strip()
    if expected_token and not hmac.compare_digest(auth_token or "", expected_token):
        return _security_failure("Invalid auth token", HTTPStatus.UNAUTHORIZED)
    if not is_host_allowed(host):
        return _security_failure("Forbidden host", HTTPStatus.FORBIDDEN)
    if not is_origin_allowed(origin):
        return _security_failure("Forbidden origin", HTTPStatus.FORBIDDEN)
    if content_length > MAX_API_BODY_BYTES:
        return _security_failure("Request body too large", HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
    if method in {"POST", "PUT", "DELETE"} and geneva_header != "1":
        return _security_failure("Missing trusted request header", HTTPStatus.FORBIDDEN)
    if method in {"POST", "PUT"} and content_length > 0 and not _is_json_content_type(content_type):
        return _security_failure("Unsupported content type", HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
    return None


def security_headers() -> dict[str, str]:
    return dict(SECURITY_RESPONSE_HEADERS)


def cors_headers(origin: str | None) -> dict[str, str]:
    if not origin or not is_origin_allowed(origin):
        return {}
    return {
        "Access-Control-Allow-Origin": origin,
        "Vary": "Origin",
    }


def _security_failure(message: str, status: HTTPStatus) -> SecurityFailure:
    return SecurityFailure({"ok": False, "error": message, "code": "security_error"}, status)


def _is_json_content_type(content_type: str | None) -> bool:
    if not content_type:
        return False
    media_type = content_type.split(";", 1)[0].strip().lower()
    return media_type == "application/json" or media_type.endswith("+json")


def _hostname_from_header(host: str | None) -> str:
    if not host:
        return ""
    value = host.split(",", 1)[0].strip().lower().rstrip(".")
    if value.startswith("["):
        end = value.find("]")
        return value[1:end] if end > 0 else value
    if value.count(":") == 1:
        return value.rsplit(":", 1)[0]
    return value


def _is_local_host(hostname: str | None) -> bool:
    if not hostname:
        return False
    normalized = hostname.strip().lower().strip("[]").rstrip(".")
    if normalized in LOCAL_HOSTNAMES:
        return True
    try:
        return ip_address(normalized).is_loopback
    except ValueError:
        return False


def _is_truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


# Each pattern: group(1) = prefix to keep visible, group(2) = secret to redact.
# The redact function replaces group(2) with "***REDACTED***".
_SECRET_PATTERNS: list[tuple[_re_sec.Pattern, int]] = [
    # Anthropic: sk-ant-api03-... (show "sk-ant-", hide rest)
    (_re_sec.compile(r"(sk-ant-)(api[0-9]+-[A-Za-z0-9_-]{20,})", _re_sec.IGNORECASE), 2),
    # OpenAI / OpenRouter: sk-proj-..., sk-or-v1-..., sk-... (show "sk-", hide rest)
    (_re_sec.compile(r"(sk-(?:proj-|or-v1-)?)([A-Za-z0-9_-]{24,})", _re_sec.IGNORECASE), 2),
    # Google AI / GCP: AIzaSy... (show "AIzaSy", hide rest)
    (_re_sec.compile(r"(AIzaSy)([A-Za-z0-9_-]{30,})", _re_sec.IGNORECASE), 2),
    # Bearer tokens: show "Bearer ", hide value
    (_re_sec.compile(r"(Bearer\s+)([A-Za-z0-9\-._~+/]{16,}=*)", _re_sec.IGNORECASE), 2),
    # api_key / x-api-key assignments: show key name + operator, hide value
    (_re_sec.compile(r"((?:api[_-]?key|x-api-key)['\"]?\s*[:=]\s*['\"]?)([A-Za-z0-9_\-]{16,})", _re_sec.IGNORECASE), 2),
    # Authorization header (non-Bearer): show "Authorization: ", hide value
    (_re_sec.compile(r"(Authorization:\s*)([A-Za-z0-9+/=]{32,})", _re_sec.IGNORECASE), 2),
    # PEM private key block: keep header, redact body
    (_re_sec.compile(r"(-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)([^-]{20,})", _re_sec.IGNORECASE), 2),
]


def redact_secrets(text: str) -> str:
    for pat, secret_group in _SECRET_PATTERNS:
        def _replace(m: _re_sec.Match, g: int = secret_group) -> str:
            return m.group(0)[: m.start(g) - m.start(0)] + "***REDACTED***"
        text = pat.sub(_replace, text)
    return text


class SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        if isinstance(record.args, dict):
            record.args = {
                k: redact_secrets(v) if isinstance(v, str) else v
                for k, v in record.args.items()
            }
        elif record.args:
            record.args = tuple(
                redact_secrets(a) if isinstance(a, str) else a
                for a in (record.args if isinstance(record.args, tuple) else (record.args,))
            )
        return True


_REDACTING_FACTORY_INSTALLED = False


def install_secret_log_filter() -> None:
    """Install secret redaction via LogRecordFactory (universally applied).

    setLogRecordFactory intercepts every LogRecord at creation time — before any
    handler or filter sees it — so propagated child-logger records are covered
    regardless of when handlers are added (e.g. uvicorn configures after startup).
    """
    global _REDACTING_FACTORY_INSTALLED
    if _REDACTING_FACTORY_INSTALLED:
        return
    _original = logging.getLogRecordFactory()

    def _redacting_factory(*args, **kwargs) -> logging.LogRecord:
        record = _original(*args, **kwargs)
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        if isinstance(record.args, dict):
            record.args = {
                k: redact_secrets(v) if isinstance(v, str) else v
                for k, v in record.args.items()
            }
        elif record.args:
            record.args = tuple(
                redact_secrets(a) if isinstance(a, str) else a
                for a in (record.args if isinstance(record.args, tuple) else (record.args,))
            )
        return record

    logging.setLogRecordFactory(_redacting_factory)
    _REDACTING_FACTORY_INSTALLED = True
