from __future__ import annotations

import inspect
import re
from typing import Callable

from .memory_scan import MemoryHeader, format_memory_manifest
from ..utils.asyncio_tools import run_awaitable_sync


def _keyword_score(header: MemoryHeader, terms: list[str]) -> float:
    haystack = f"{header.name} {header.description} {header.type}".lower()
    if not haystack:
        return 0.0
    score = 0.0
    for term in terms:
        if term in haystack:
            score += 3.0 if term in header.name.lower() else 1.0
    score += max(0.0, 7.0 - min(header.age_days, 7.0)) * 0.05
    return score


def _extract_terms(query: str) -> list[str]:
    return [term for term in re.findall(r"[A-Za-z0-9_/-]+", query.lower()) if len(term) > 1]


def _coerce_selected(result: object, by_name: dict[str, MemoryHeader]) -> list[MemoryHeader]:
    if isinstance(result, list):
        selected: list[MemoryHeader] = []
        for item in result:
            if isinstance(item, MemoryHeader):
                selected.append(item)
            elif isinstance(item, str) and item in by_name:
                selected.append(by_name[item])
        return selected
    if isinstance(result, dict):
        raw = result.get("selected") or result.get("memories") or result.get("files")
        if isinstance(raw, list):
            return [by_name[item] for item in raw if isinstance(item, str) and item in by_name]
    return []


def find_relevant_memories(
    headers: list[MemoryHeader],
    query: str,
    llm_caller: Callable | None = None,
) -> list[MemoryHeader]:
    if not headers:
        return []

    by_name = {header.path.name: header for header in headers}
    if llm_caller is not None:
        manifest = format_memory_manifest(headers)
        prompt = (
            "Select up to 5 relevant memory files for the query.\n"
            f"Query: {query}\n\nManifest:\n{manifest}"
        )
        try:
            result = llm_caller(prompt)
            if inspect.isawaitable(result):
                result = run_awaitable_sync(result)
            selected = _coerce_selected(result, by_name)
            if selected:
                return selected[:5]
        except Exception:
            pass

    terms = _extract_terms(query)
    ranked = sorted(
        headers,
        key=lambda header: (_keyword_score(header, terms), -header.age_days),
        reverse=True,
    )
    return [header for header in ranked if _keyword_score(header, terms) > 0][:5]
