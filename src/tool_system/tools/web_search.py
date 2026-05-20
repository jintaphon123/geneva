from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request
from typing import Any

from ..context import ToolContext
from ..errors import ToolInputError
from ..protocol import ToolResult
from ..registry import ToolSpec


_RESULT_RE = re.compile(
    r'<a[^>]+class="result__a"[^>]+href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?'
    r'<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
    re.DOTALL,
)


def rank_source_credibility(url: str) -> int:
    """Return 1 (highest), 2, or 3 (lowest) credibility tier based on domain heuristic."""
    domain = re.sub(r"https?://(?:www\.)?([^/]+).*", r"\1", url.lower())

    tier1_tld = {".gov", ".edu", ".ac.th", ".ac.uk", ".ac.jp"}
    tier1_domains = {
        "nature.com",
        "sciencedirect.com",
        "pubmed.ncbi.nlm.nih.gov",
        "scholar.google.com",
        "arxiv.org",
        "ncbi.nlm.nih.gov",
        "who.int",
        "reuters.com",
        "apnews.com",
        "bbc.com",
        "nytimes.com",
        "theguardian.com",
        "bloomberg.com",
        "wsj.com",
        "ft.com",
        "economist.com",
        "wikipedia.org",
    }
    tier2_domains = {
        "medium.com",
        "substack.com",
        "forbes.com",
        "techcrunch.com",
        "venturebeat.com",
        "wired.com",
        "theverge.com",
        "zdnet.com",
        "stackoverflow.com",
        "github.com",
        "dev.to",
    }

    if any(domain.endswith(tld) for tld in tier1_tld):
        return 1
    if any(domain == trusted or domain.endswith(f".{trusted}") for trusted in tier1_domains):
        return 1
    if any(domain == trusted or domain.endswith(f".{trusted}") for trusted in tier2_domains):
        return 2
    return 3


def _strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


class WebSearchTool:
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="WebSearch",
            description="Search the web and return top results.",
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "query": {"type": "string"},
                    "num": {"type": "integer"},
                },
                "required": ["query"],
            },
            is_read_only=True,
            is_concurrency_safe=True,
            max_result_size_chars=50_000,
        )

    def run(self, tool_input: dict[str, Any], context: ToolContext) -> ToolResult:
        query = tool_input["query"]
        if not isinstance(query, str) or not query.strip():
            raise ToolInputError("query must be a non-empty string")
        num = tool_input.get("num", 5)
        if not isinstance(num, int) or num < 1 or num > 10:
            raise ToolInputError("num must be an integer between 1 and 10")

        url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
        req = urllib.request.Request(url, headers={"User-Agent": "geneva/0.1"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read(1_000_000).decode("utf-8", errors="replace")

        results: list[dict[str, str]] = []
        for match in _RESULT_RE.finditer(raw):
            results.append(
                {
                    "title": _strip_tags(match.group("title")),
                    "url": html.unescape(match.group("url")),
                    "snippet": _strip_tags(match.group("snippet")),
                }
            )
            if len(results) >= num:
                break

        return ToolResult(name="WebSearch", output={"query": query, "results": results})
