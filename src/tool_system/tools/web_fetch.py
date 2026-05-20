from __future__ import annotations

import html
import ipaddress
import re
import socket
import urllib.parse
import urllib.request
from typing import Any

from ..context import ToolContext
from ..errors import ToolInputError, ToolPermissionError
from ..protocol import ToolResult
from ..registry import ToolSpec


_TAG_RE = re.compile(r"<[^>]+>")
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+\w+", re.IGNORECASE),
    re.compile(r"act\s+as\s+(?:a|an)\s+\w+", re.IGNORECASE),
    re.compile(r"new\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"\[system\]", re.IGNORECASE),
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
    re.compile(r"override\s+(?:your\s+)?(?:previous\s+)?instructions?", re.IGNORECASE),
    re.compile(r"forget\s+(?:all\s+)?(?:your\s+)?(?:previous\s+)?instructions?", re.IGNORECASE),
    re.compile(r"print\s+(?:your\s+)?(?:system\s+)?prompt", re.IGNORECASE),
    re.compile(r"reveal\s+(?:your\s+)?(?:system\s+)?instructions?", re.IGNORECASE),
]


def _detect_prompt_injection(text: str) -> list[str]:
    """Return list of matched injection pattern descriptions, empty if clean."""
    matched: list[str] = []
    for pat in _INJECTION_PATTERNS:
        m = pat.search(text)
        if m:
            matched.append(m.group(0)[:80])
    return matched


def _is_private_host(hostname: str) -> bool:
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False
    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return True
    return False


def _html_to_text(raw: str) -> str:
    without_tags = _TAG_RE.sub(" ", raw)
    without_tags = re.sub(r"\s+", " ", without_tags).strip()
    return html.unescape(without_tags)


class WebFetchTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="WebFetch",
            description="Fetch a URL and return extracted text content.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {"url": {"type": "string"}},
                "required": ["url"],
            },
            is_read_only=True,
            is_concurrency_safe=True,
            max_result_size_chars=50_000,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        url = tool_input["url"]
        if not isinstance(url, str) or not url:
            raise ToolInputError("url must be a non-empty string")

        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise ToolPermissionError("only http/https URLs are allowed")
        if not parsed.netloc:
            raise ToolInputError("url must include a network location")

        hostname = parsed.hostname or ""
        if hostname in {"localhost"} or hostname.endswith(".localhost") or _is_private_host(hostname):
            raise ToolPermissionError("refusing to fetch localhost/private network URLs")

        req = urllib.request.Request(url, headers={"User-Agent": "geneva/0.1"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw_bytes = resp.read(1_000_000)
            content_type = resp.headers.get("Content-Type", "")

        text = raw_bytes.decode("utf-8", errors="replace")
        if "text/html" in content_type:
            text = _html_to_text(text)

        if len(text) > 100_000:
            text = text[:100_000] + "\n\n... [truncated] ..."

        injection_hits = _detect_prompt_injection(text)
        if injection_hits:
            quarantine_summary = "; ".join(injection_hits[:3])
            return ToolResult(
                name="WebFetch",
                output={
                    "url": url,
                    "content_type": content_type,
                    "prompt_injection_detected": True,
                    "injection_patterns": injection_hits[:5],
                    "content": (
                        f"[QUARANTINED — PROMPT INJECTION DETECTED]\n"
                        f"Patterns found: {quarantine_summary}\n\n"
                        f"[UNTRUSTED SOURCE — content withheld for safety]"
                    ),
                    "warning": "This page contains content that attempted to override system instructions. Content has been quarantined.",
                },
            )

        return ToolResult(
            name="WebFetch",
            output={"url": url, "content_type": content_type, "content": "[UNTRUSTED SOURCE]\n" + text},
        )
