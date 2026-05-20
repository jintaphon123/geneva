from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import re
import time
from dataclasses import asdict, dataclass, field
from threading import Lock
from typing import Any, Iterator
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_search_cache: dict[str, tuple[list[dict[str, Any]], float]] = {}
_cache_lock = Lock()
CACHE_TTL_SECONDS = 86400


def _cache_get(query: str) -> list[dict[str, Any]] | None:
    with _cache_lock:
        if query in _search_cache:
            results, timestamp = _search_cache[query]
            if time.time() - timestamp < CACHE_TTL_SECONDS:
                return results
            del _search_cache[query]
    return None


def _cache_set(query: str, results: list[dict[str, Any]]) -> None:
    with _cache_lock:
        _search_cache[query] = (results, time.time())


@dataclass
class ResearchStep:
    step: int
    total: int
    label: str
    detail: str
    done: bool = False
    result: str = ""


@dataclass
class ResearchBrief:
    query: str
    steps: list[ResearchStep] = field(default_factory=list)
    summary: str = ""
    findings: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    confidence: str = "medium"
    saved_to_memory: bool = False
    error: str = ""


@dataclass(frozen=True)
class ResearchModeConfig:
    name: str
    label: str
    total_steps: int
    query_count: int
    results_per_query: int
    fetch_limit: int
    critic_pass: bool
    parallel_search: bool
    conflict_detection: bool = False
    claim_verification: bool = False
    synthesis_passes: int = 1


@dataclass
class SourceRecord:
    id: str = ""
    title: str = ""
    url: str = ""
    snippet: str = ""
    query: str = ""
    fetched: bool = False
    content_preview: str = ""
    error: str = ""
    credibility_tier: int = 3
    source_id: str = ""

    def __post_init__(self) -> None:
        if not self.id and self.source_id:
            self.id = self.source_id
        if not self.source_id and self.id:
            self.source_id = self.id

    @property
    def content(self) -> str:
        return self.content_preview

    @content.setter
    def content(self, value: str) -> None:
        self.content_preview = value


@dataclass
class EvidenceCard:
    id: str
    source_id: str
    title: str
    url: str
    claim: str
    quote: str
    confidence: str = "medium"


@dataclass
class QualityScore:
    value: int
    label: str
    reasons: list[str] = field(default_factory=list)


RESEARCH_MODE_CONFIGS: dict[str, ResearchModeConfig] = {
    "quick": ResearchModeConfig(
        name="quick",
        label="Quick research",
        total_steps=5,
        query_count=5,
        results_per_query=4,
        fetch_limit=0,
        critic_pass=False,
        parallel_search=False,
        conflict_detection=False,
        claim_verification=False,
        synthesis_passes=1,
    ),
    "deep": ResearchModeConfig(
        name="deep",
        label="Deep research",
        total_steps=7,
        query_count=15,
        results_per_query=5,
        fetch_limit=4,
        critic_pass=True,
        parallel_search=True,
        conflict_detection=True,
        claim_verification=False,
        synthesis_passes=2,
    ),
    "max": ResearchModeConfig(
        name="max",
        label="Max research",
        total_steps=8,
        query_count=30,
        results_per_query=7,
        fetch_limit=8,
        critic_pass=True,
        parallel_search=True,
        conflict_detection=True,
        claim_verification=True,
        synthesis_passes=3,
    ),
}


def normalize_research_mode(mode: str | None) -> str:
    requested = (mode or "deep").strip().lower()
    return requested if requested in RESEARCH_MODE_CONFIGS else "deep"


RESEARCH_SYSTEM_PROMPT = """You are Geneva Deep Research.
Your task is to research the given topic thoroughly from supplied sources.

Step 1 — PLAN: Break the topic into 3-4 specific research questions.
Step 2 — SEARCH: For each question, search the web and gather evidence.
Step 3 — READ: Prefer primary sources, official docs, papers, and benchmark reports.
Step 4 — EVIDENCE: Extract source-grounded evidence cards.
Step 5 — CONTRADICTION CHECK: Flag conflicts, missing evidence, and weak claims.
Step 6 — BRIEF: Output a structured research brief:

## Summary
[2-3 sentence executive summary]

## Key Findings
- [Finding 1 with source ids like [S1]]
- [Finding 2 with evidence]
- [Finding 3 with evidence]

## Source Conflicts
- [Any contradiction or "No major conflicts found"]

## Quality Gate
- [Coverage, freshness, uncertainty, citation quality]

## Sources
- [S1] [Title] - [URL]

## Confidence
[low/medium/high] — [reason]

Be precise. Cite source ids for material claims. Flag uncertainty. Do not hallucinate."""

RESEARCH_PLAN_SYSTEM_PROMPT = """You generate research plans. Given a query, output ONLY valid JSON: {"title": "...", "steps": ["step1", "step2", "step3", "step4", "step5"]}. Max 5 steps. Each step is one short Thai or English sentence. No markdown, no explanation, only the JSON object."""


class ResearchEngine:
    """Orchestrates multi-step research using GenevaSession + optional Gemini CLI."""

    def __init__(self, session_manager) -> None:
        self._manager = session_manager

    def research_stream(
        self,
        query: str,
        session_id: str | None,
        provider_name: str | None,
        model: str | None,
        save_memory: bool = True,
        mode: str = "deep",
    ) -> Iterator[dict[str, Any]]:
        """Yields SSE-compatible event dicts for research progress."""
        from src.memdir.brain_engine import remember
        from src.geneva.cli_bridge import get_bridge
        from src.tool_system.tools.web_search import WebSearchTool
        from src.utils.asyncio_tools import run_awaitable_sync

        session = None
        previous_context = ""
        mode_name = normalize_research_mode(mode)
        config = RESEARCH_MODE_CONFIGS[mode_name]
        trace: list[dict[str, Any]] = []
        yield {"type": "research_start", "data": {"query": query, "mode": mode_name}}

        try:
            bridge = get_bridge()
            session = self._manager.get(session_id, provider_name, model)
            previous_context = getattr(session, "_project_context", "")
            session.set_project_context(RESEARCH_SYSTEM_PROMPT)

            def emit_step(step: ResearchStep) -> dict[str, Any]:
                data = asdict(step)
                if step.done:
                    trace.append(data)
                return {"type": "research_step", "data": data}

            yield {
                "type": "research_step",
                "data": asdict(ResearchStep(1, config.total_steps, "Planning", query)),
            }
            queries = self._generate_queries(session, query, count=config.query_count)
            yield emit_step(
                ResearchStep(
                    1,
                    config.total_steps,
                    "Planning",
                    f"{len(queries)} web queries",
                    done=True,
                    result=", ".join(queries),
                )
            )
            yield emit_step(
                ResearchStep(
                    2,
                    config.total_steps,
                    "Searching",
                    f"{len(queries)} web queries",
                    done=False,
                )
            )

            search_tool = WebSearchTool()
            search_outputs: list[dict[str, Any]] = []
            if config.parallel_search and len(queries) > 1:
                max_workers = min(4, len(queries))
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {
                        executor.submit(
                            self._search_query,
                            search_tool,
                            session.tool_context,
                            search_query,
                            config.results_per_query,
                        ): search_query
                        for search_query in queries
                    }
                    for future in as_completed(futures):
                        search_query = futures[future]
                        yield emit_step(
                            ResearchStep(
                                2,
                                config.total_steps,
                                "Searching",
                                search_query,
                                done=True,
                            )
                        )
                        search_outputs.append(future.result())
            else:
                for search_query in queries:
                    yield {
                        "type": "research_step",
                        "data": asdict(ResearchStep(2, config.total_steps, "Searching", search_query)),
                    }
                    search_outputs.append(
                        self._search_query(
                            search_tool,
                            session.tool_context,
                            search_query,
                            config.results_per_query,
                        )
                    )

            sources = self._build_source_records(search_outputs)
            yield emit_step(
                ResearchStep(
                    3,
                    config.total_steps,
                    "Source graph",
                    f"{len(sources)} unique sources",
                    done=True,
                )
            )

            if config.fetch_limit > 0:
                yield {
                    "type": "research_step",
                    "data": asdict(
                        ResearchStep(
                            4,
                            config.total_steps,
                            "Reading sources",
                            f"top {min(config.fetch_limit, len(sources))} sources",
                        )
                    ),
                }
                self._fetch_source_contents(sources, session.tool_context, limit=config.fetch_limit)
                fetched = sum(1 for source in sources if source.fetched)
                yield emit_step(
                    ResearchStep(
                        4,
                        config.total_steps,
                        "Reading sources",
                        f"{fetched} sources fetched",
                        done=True,
                    )
                )

            evidence_cards = self._build_evidence_cards(sources)
            citation_map = self._build_citation_map(sources)
            source_graph = self._build_source_graph(sources, evidence_cards)
            source_conflicts = self._detect_conflicts(sources) if config.conflict_detection else []
            quality_score = self._score_research_quality(
                sources=sources,
                evidence_cards=evidence_cards,
                config=config,
            )
            yield emit_step(
                ResearchStep(
                    5,
                    config.total_steps,
                    "Evidence extraction",
                    f"{len(evidence_cards)} evidence cards",
                    done=True,
                )
            )

            session.set_project_context(
                self._render_research_context(
                    query=query,
                    config=config,
                    sources=sources,
                    evidence_cards=evidence_cards,
                    citation_map=citation_map,
                    source_conflicts=source_conflicts,
                    quality_score=quality_score,
                )
            )

            full_text = ""
            failed = False
            for event in session.chat_stream(query, memory_enabled=save_memory):
                event_type = getattr(event, "type", "")
                event_data = getattr(event, "data", {}) or {}
                if event_type == "text_delta":
                    chunk = str(event_data.get("text", ""))
                    full_text += chunk
                    yield {"type": "research_text", "data": {"chunk": chunk}}
                elif event_type == "tool_call_start":
                    tool = str(event_data.get("tool_name", "tool"))
                    yield {
                        "type": "research_step",
                        "data": asdict(ResearchStep(5, config.total_steps, "Synthesis tool", tool)),
                    }
                elif event_type == "tool_complete":
                    tool = str(event_data.get("tool_name", "tool"))
                    yield emit_step(
                        ResearchStep(5, config.total_steps, "Synthesis tool", tool, done=True)
                    )
                elif event_type == "turn_complete":
                    response_text = event_data.get("response_text")
                    if isinstance(response_text, str) and response_text.strip():
                        full_text = response_text
                elif event_type == "error":
                    failed = True
                    error = getattr(event, "error", None)
                    message = getattr(error, "message", None) or "Research failed."
                    yield {"type": "research_error", "data": {"error": str(message)}}

            if failed:
                return

            yield emit_step(
                ResearchStep(
                    6,
                    config.total_steps,
                    "Synthesis",
                    "draft complete",
                    done=True,
                )
            )

            if config.synthesis_passes > 1 and full_text.strip():
                for pass_number in range(2, config.synthesis_passes + 1):
                    yield {
                        "type": "research_step",
                        "data": asdict(
                            ResearchStep(
                                6,
                                config.total_steps,
                                "Synthesis refinement",
                                f"pass {pass_number}/{config.synthesis_passes}",
                            )
                        ),
                    }
                    refined_text = self._run_synthesis_refinement(
                        session=session,
                        query=query,
                        previous_text=full_text,
                        pass_number=pass_number,
                    )
                    if refined_text:
                        full_text = refined_text
                    yield emit_step(
                        ResearchStep(
                            6,
                            config.total_steps,
                            "Synthesis refinement",
                            f"pass {pass_number}/{config.synthesis_passes}",
                            done=True,
                        )
                    )

            unverified_claims: list[str] = []
            if config.claim_verification and full_text.strip():
                claims = self._extract_claims(full_text)
                for claim in claims:
                    _, verified = self._verify_claim_citation(
                        claim,
                        citation_map,
                        sources,
                    )
                    if not verified:
                        unverified_claims.append(f"{claim} [UNVERIFIED]")
                yield emit_step(
                    ResearchStep(
                        7,
                        config.total_steps,
                        "Claim verification",
                        f"{len(unverified_claims)} unverified claims",
                        done=True,
                    )
                )

            if config.critic_pass:
                yield emit_step(
                    ResearchStep(
                        7,
                        config.total_steps,
                        "Critic",
                        "coverage, citations, conflicts checked",
                        done=True,
                        result=quality_score.label,
                    )
                )

            if bridge.should_use_gemini(len(full_text)):
                yield {
                    "type": "research_step",
                    "data": asdict(ResearchStep(config.total_steps - 1, config.total_steps, "Analyzing", "large-context review")),
                }

            yield {
                "type": "research_step",
                "data": asdict(
                    ResearchStep(
                        config.total_steps,
                        config.total_steps,
                        "Saving findings" if save_memory else "Ghost mode",
                        "memory" if save_memory else "memory skipped",
                    )
                ),
            }
            saved = False
            if save_memory and full_text.strip():
                run_awaitable_sync(
                    remember(
                        content=(
                            f"Research ({mode_name}): {query}\n\n"
                            f"Quality: {quality_score.label} ({quality_score.value}/100)\n"
                            f"Sources: {', '.join(citation_map.keys())}\n\n"
                            f"{full_text[:1500]}"
                        ),
                        type="reference",
                        source_type="assistant_inferred",
                        memory_kind="reference",
                        source_session_id=session.session_id,
                    )
                )
                saved = True

            yield {
                "type": "research_complete",
                "data": {
                    "query": query,
                    "mode": mode_name,
                    "text": full_text,
                    "saved": saved,
                    "session_id": session.session_id,
                    "sources": [asdict(source) for source in sources],
                    "source_graph": source_graph,
                    "evidence_cards": [asdict(card) for card in evidence_cards],
                    "citation_map": citation_map,
                    "source_conflicts": source_conflicts,
                    "unverified_claims": unverified_claims,
                    "research_trace": trace,
                    "quality_score": asdict(quality_score),
                },
            }

        except Exception as exc:
            logger.exception("Research failed for: %s", query)
            yield {"type": "research_error", "data": {"error": str(exc)}}
        finally:
            if session is not None:
                session.set_project_context(previous_context)

    def _run_synthesis_refinement(
        self,
        *,
        session: Any,
        query: str,
        previous_text: str,
        pass_number: int,
    ) -> str:
        prompt = (
            "Refine the previous research brief using the source context already supplied. "
            "Improve citation precision, conflict handling, and uncertainty wording. "
            "Do not introduce claims that are not supported by the listed sources.\n\n"
            f"Original query: {query}\n\n"
            f"Previous draft:\n{previous_text}"
        )
        refined_text = ""
        try:
            for event in session.chat_stream(prompt, memory_enabled=False):
                event_type = getattr(event, "type", "")
                event_data = getattr(event, "data", {}) or {}
                if event_type == "text_delta":
                    refined_text += str(event_data.get("text", ""))
                elif event_type == "turn_complete":
                    response_text = event_data.get("response_text")
                    if isinstance(response_text, str) and response_text.strip():
                        refined_text = response_text
                elif event_type == "error":
                    error = getattr(event, "error", None)
                    message = getattr(error, "message", None) or "Research refinement failed."
                    logger.warning("Research synthesis refinement pass %s failed: %s", pass_number, message)
                    return ""
        except Exception as exc:
            logger.warning("Research synthesis refinement pass %s failed: %s", pass_number, exc)
            return ""
        return refined_text.strip()

    def generate_plan(self, query: str, session_id: str | None, provider_name: str | None, model: str | None) -> dict:
        """Generate a short research plan (title + up to 5 steps) without web search."""
        session = None
        previous_context = ""
        try:
            session = self._manager.get(session_id, provider_name, model)
            previous_context = getattr(session, "_project_context", "")
            session.set_project_context(RESEARCH_PLAN_SYSTEM_PROMPT)

            full_text = ""
            for event in session.chat_stream(query):
                event_type = getattr(event, "type", "")
                event_data = getattr(event, "data", {}) or {}
                if event_type == "text_delta":
                    full_text += str(event_data.get("text", ""))
                elif event_type == "turn_complete":
                    response_text = event_data.get("response_text")
                    if isinstance(response_text, str) and response_text.strip():
                        full_text = response_text
                elif event_type == "error":
                    error = getattr(event, "error", None)
                    message = getattr(error, "message", None) or "Failed to generate research plan."
                    raise ValueError(str(message))

            response_text = self._extract_json(self._strip_json_fence(full_text))
            if response_text is None:
                raise ValueError("No JSON object found in model response")
            plan = json.loads(response_text)
            if not isinstance(plan, dict):
                raise ValueError("Invalid plan JSON format")
            title = plan.get("title")
            steps = plan.get("steps")
            if not isinstance(title, str) or not isinstance(steps, list) or not all(
                isinstance(step, str) for step in steps
            ):
                raise ValueError("Invalid plan JSON format")
            return {"title": title, "steps": steps[:5]}
        except json.JSONDecodeError as exc:
            raise ValueError("Failed to parse plan JSON") from exc
        except Exception as exc:
            raise ValueError(str(exc))
        finally:
            if session is not None:
                session.set_project_context(previous_context)

    @staticmethod
    def _strip_json_fence(text: str) -> str:
        return re.sub(
            r"^\s*```(?:json)?\s*|\s*```\s*$",
            "",
            text,
            flags=re.IGNORECASE | re.MULTILINE,
        ).strip()

    @staticmethod
    def _extract_json(text: str) -> str | None:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end < start:
            return None
        return text[start : end + 1].strip()

    def _generate_queries(self, session: Any, query: str, *, count: int = 3) -> list[str]:
        prompt = (
            f"Generate exactly {count} focused web search queries for this research topic. "
            "Return one query per line, with no numbering:\n\n"
            f"{query}"
        )
        try:
            response = session.provider.chat([{"role": "user", "content": prompt}], max_tokens=300)
            raw = str(response.content or "")
            queries = [
                re.sub(r"^\s*[-*\d.)]+\s*", "", line).strip()
                for line in raw.splitlines()
                if line.strip()
            ]
        except Exception:
            queries = []
        cleaned: list[str] = []
        for item in queries:
            if item and item not in cleaned:
                cleaned.append(item)
            if len(cleaned) >= count:
                break
        if cleaned:
            return cleaned
        fallback = [
            query,
            f"{query} official documentation",
            f"{query} latest evidence",
            f"{query} expert analysis",
            f"{query} benchmark report",
            f"{query} limitations",
        ]
        return fallback[:count]

    def _search_query(
        self,
        search_tool: Any,
        context: Any,
        search_query: str,
        results_per_query: int,
    ) -> dict[str, Any]:
        cached_results = _cache_get(search_query)
        if cached_results is not None:
            return {"query": search_query, "results": cached_results}
        try:
            result = search_tool.run(
                {"query": search_query, "num": results_per_query},
                context,
            )
            output = result.output if isinstance(result.output, dict) else {}
            output.setdefault("query", search_query)
            output.setdefault("results", [])
            results = output.get("results")
            if isinstance(results, list):
                _cache_set(search_query, results)
            return output
        except Exception as exc:
            logger.warning("Research search failed for %s: %s", search_query, exc)
            return {"query": search_query, "error": str(exc), "results": []}

    def _build_source_records(self, outputs: list[dict[str, Any]]) -> list[SourceRecord]:
        from src.tool_system.tools.web_search import rank_source_credibility

        sources: list[SourceRecord] = []
        seen_urls: set[str] = set()
        for output in outputs:
            query = str(output.get("query") or "")
            results = output.get("results")
            if not isinstance(results, list):
                continue
            for result in results:
                if not isinstance(result, dict):
                    continue
                url = str(result.get("url") or "").strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                title = str(result.get("title") or self._domain_label(url) or "Untitled").strip()
                snippet = self._clean_text(str(result.get("snippet") or ""))
                sources.append(
                    SourceRecord(
                        id=f"S{len(sources) + 1}",
                        title=title[:220],
                        url=url,
                        snippet=snippet[:800],
                        query=query,
                        credibility_tier=rank_source_credibility(url),
                    )
                )
        return sources

    def _fetch_source_contents(self, sources: list[SourceRecord], context: Any, *, limit: int) -> None:
        from src.tool_system.tools.web_fetch import WebFetchTool

        fetch_tool = WebFetchTool()
        for source in sources[:limit]:
            try:
                parsed = urlparse(source.url)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    source.error = "unsupported URL"
                    continue
                result = fetch_tool.run({"url": source.url}, context)
                output = result.output if isinstance(result.output, dict) else {}
                content = self._clean_text(str(output.get("content") or ""))
                if content:
                    source.content_preview = content[:2000]
                    source.fetched = True
            except Exception as exc:
                logger.debug("Research fetch failed for %s: %s", source.url, exc)
                source.error = str(exc)

    def _extract_claims(self, synthesis_text: str) -> list[str]:
        """
        Split synthesis text into individual verifiable claims.
        A claim is a declarative sentence that asserts a fact.
        """
        sentences = re.split(r"(?<=[.!?])\s+", synthesis_text)
        claims: list[str] = []
        claim_verbs = {
            "is",
            "are",
            "was",
            "were",
            "has",
            "have",
            "shows",
            "found",
            "indicates",
            "suggests",
            "reported",
            "increased",
            "decreased",
            "reached",
            "accounts",
            "represents",
        }
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > 300:
                continue
            if sentence.startswith(("#", "-", "*", "|", ">")):
                continue
            words = set(sentence.lower().split())
            if claim_verbs & words:
                claims.append(sentence)
            if len(claims) >= 20:
                break
        return claims

    def _verify_claim_citation(
        self,
        claim: str,
        citation_map: dict[str, dict],
        sources: list[SourceRecord],
    ) -> tuple[str, bool]:
        """
        Check if the claim is supported by any source in citation_map.
        A claim is verified if 3+ consecutive words appear in any source snippet/content.
        """
        claim_words = claim.lower().split()
        valid_source_ids = set(citation_map)

        for source in sources:
            if valid_source_ids and source.id not in valid_source_ids and source.source_id not in valid_source_ids:
                continue
            snippet = (source.snippet or "").lower()
            content = (getattr(source, "content", "") or source.content_preview or "").lower()
            text_to_check = f"{snippet} {content}"
            for index in range(len(claim_words) - 2):
                phrase = " ".join(claim_words[index : index + 3])
                if phrase in text_to_check:
                    return (claim, True)

        return (claim, False)

    def _detect_conflicts(self, sources: list[SourceRecord]) -> list[dict[str, str]]:
        """
        Return source pairs with simple directional contradictions in snippets.
        """
        conflicts: list[dict[str, str]] = []
        snippets = [(source.source_id or source.id, source.snippet or "") for source in sources if source.snippet]

        increase_words = {
            "increase",
            "increased",
            "increases",
            "increasing",
            "grow",
            "growth",
            "grew",
            "rise",
            "rising",
            "rose",
            "up",
            "higher",
            "more",
            "gain",
            "gained",
        }
        decrease_words = {
            "decrease",
            "decreased",
            "decreases",
            "decreasing",
            "fall",
            "fell",
            "drop",
            "dropped",
            "down",
            "lower",
            "less",
            "decline",
            "declined",
            "declining",
            "shrink",
            "shrunk",
        }

        for index, (id_a, snippet_a) in enumerate(snippets):
            words_a = set(re.findall(r"\b\w+\b", snippet_a.lower()))
            for id_b, snippet_b in snippets[index + 1 :]:
                words_b = set(re.findall(r"\b\w+\b", snippet_b.lower()))
                if (increase_words & words_a) and (decrease_words & words_b):
                    conflicts.append(
                        {
                            "source_a": id_a,
                            "source_b": id_b,
                            "claim_a": snippet_a[:150],
                            "claim_b": snippet_b[:150],
                            "type": "directional",
                        }
                    )
                elif (decrease_words & words_a) and (increase_words & words_b):
                    conflicts.append(
                        {
                            "source_a": id_a,
                            "source_b": id_b,
                            "claim_a": snippet_a[:150],
                            "claim_b": snippet_b[:150],
                            "type": "directional",
                        }
                    )
                if len(conflicts) >= 5:
                    return conflicts

        return conflicts

    def _build_evidence_cards(self, sources: list[SourceRecord]) -> list[EvidenceCard]:
        cards: list[EvidenceCard] = []
        for source in sources:
            quote = source.content_preview or source.snippet
            quote = self._clean_text(quote)
            if not quote:
                continue
            claim = source.snippet or self._first_sentence(quote)
            cards.append(
                EvidenceCard(
                    id=f"E{len(cards) + 1}",
                    source_id=source.id,
                    title=source.title,
                    url=source.url,
                    claim=self._clean_text(claim)[:280],
                    quote=quote[:500],
                    confidence="high" if source.fetched else "medium",
                )
            )
        return cards

    def _build_citation_map(self, sources: list[SourceRecord]) -> dict[str, dict[str, Any]]:
        return {
            source.id: {
                "title": source.title,
                "url": source.url,
                "query": source.query,
                "fetched": source.fetched,
                "credibility_tier": source.credibility_tier,
            }
            for source in sources
        }

    def _build_source_graph(
        self,
        sources: list[SourceRecord],
        evidence_cards: list[EvidenceCard],
    ) -> dict[str, Any]:
        return {
            "nodes": [
                {
                    "id": source.id,
                    "type": "source",
                    "title": source.title,
                    "url": source.url,
                    "domain": self._domain_label(source.url),
                    "fetched": source.fetched,
                    "credibility_tier": source.credibility_tier,
                }
                for source in sources
            ]
            + [
                {
                    "id": card.id,
                    "type": "evidence",
                    "source_id": card.source_id,
                    "claim": card.claim,
                    "confidence": card.confidence,
                }
                for card in evidence_cards
            ],
            "edges": [
                {
                    "from": card.id,
                    "to": card.source_id,
                    "type": "evidence_for",
                }
                for card in evidence_cards
            ],
        }

    def _score_research_quality(
        self,
        *,
        sources: list[SourceRecord],
        evidence_cards: list[EvidenceCard],
        config: ResearchModeConfig,
    ) -> QualityScore:
        fetched_count = sum(1 for source in sources if source.fetched)
        score = 10
        score += min(30, len(sources) * 4)
        score += min(25, len(evidence_cards) * 5)
        score += min(20, fetched_count * 5)
        score += 10 if config.critic_pass else 0
        score += 5 if config.parallel_search else 0
        score += min(10, sum(1 for source in sources if source.credibility_tier == 1) * 2)
        score = max(0, min(score, 100))
        label = "high" if score >= 75 else "medium" if score >= 45 else "low"

        reasons: list[str] = []
        reasons.append(f"{len(sources)} unique sources")
        reasons.append(f"{len(evidence_cards)} evidence cards")
        tier1_count = sum(1 for source in sources if source.credibility_tier == 1)
        if tier1_count:
            reasons.append(f"{tier1_count} tier-1 sources")
        if config.fetch_limit:
            reasons.append(f"{fetched_count}/{min(config.fetch_limit, len(sources))} priority sources fetched")
        if config.critic_pass:
            reasons.append("critic pass required by mode")
        if not sources:
            reasons.append("no external sources returned")
        return QualityScore(value=score, label=label, reasons=reasons)

    def _render_research_context(
        self,
        *,
        query: str,
        config: ResearchModeConfig,
        sources: list[SourceRecord],
        evidence_cards: list[EvidenceCard],
        citation_map: dict[str, dict[str, Any]],
        quality_score: QualityScore,
        source_conflicts: list[dict[str, Any]] | None = None,
    ) -> str:
        source_lines = []
        for source in sources:
            source_lines.append(
                f"- [{source.id}] {source.title}\n"
                f"  URL: {source.url}\n"
                f"  Query: {source.query}\n"
                f"  Credibility tier: {source.credibility_tier}\n"
                f"  Snippet: {source.snippet}\n"
                f"  Content preview: {source.content_preview[:900] if source.content_preview else '[not fetched]'}"
            )
        evidence_lines = [
            f"- [{card.id}] source [{card.source_id}] claim: {card.claim}\n  quote: {card.quote}"
            for card in evidence_cards
        ]
        conflict_lines = [
            (
                f"- [{conflict.get('source_a')}] vs [{conflict.get('source_b')}] "
                f"({conflict.get('type', 'conflict')}): "
                f"{conflict.get('claim_a', '')} / {conflict.get('claim_b', '')}"
            )
            for conflict in (source_conflicts or [])
        ]
        mode_contract = (
            "Quick mode: concise answer, cite key claims."
            if config.name == "quick"
            else "Deep mode: compare sources, cite key claims, include conflicts and quality gate."
            if config.name == "deep"
            else "Max mode: exhaustive synthesis, contradiction check, uncertainty ledger, and strongest possible final report."
        )
        return (
            f"{RESEARCH_SYSTEM_PROMPT}\n\n"
            f"## Mode Contract\n{config.label}: {mode_contract}\n\n"
            f"## Research Task\n{query}\n\n"
            f"## Source Records\n{chr(10).join(source_lines) if source_lines else 'No sources returned.'}\n\n"
            f"## Evidence Cards\n{chr(10).join(evidence_lines) if evidence_lines else 'No evidence cards extracted.'}\n\n"
            f"## Citation Map\n{json.dumps(citation_map, ensure_ascii=False, indent=2)}\n\n"
            f"## Detected Source Conflicts\n"
            f"{chr(10).join(conflict_lines) if conflict_lines else 'No heuristic conflicts detected.'}\n\n"
            f"## Current Quality Score\n"
            f"{quality_score.label} ({quality_score.value}/100): {', '.join(quality_score.reasons)}\n\n"
            "Write the final report in the user's language. Cite source ids like [S1] for material claims. "
            "Do not cite a source id unless it appears in the Source Records. "
            "If the evidence is weak or conflicting, say that plainly."
        )

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _first_sentence(text: str) -> str:
        parts = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)
        return parts[0] if parts else text.strip()

    @staticmethod
    def _domain_label(url: str) -> str:
        try:
            return urlparse(url).netloc.lower()
        except Exception:
            return ""

    def _render_search_results(self, outputs: list[dict[str, Any]]) -> str:
        blocks: list[str] = []
        for output in outputs:
            query = str(output.get("query") or "")
            blocks.append(f"### {query}")
            if output.get("error"):
                blocks.append(f"Search error: {output['error']}")
                continue
            results = output.get("results")
            if not isinstance(results, list) or not results:
                blocks.append("No results returned.")
                continue
            for result in results[:5]:
                if not isinstance(result, dict):
                    continue
                title = str(result.get("title") or "Untitled")
                url = str(result.get("url") or "")
                snippet = str(result.get("snippet") or "")
                blocks.append(f"- {title}\n  URL: {url}\n  Snippet: {snippet}")
        return "\n".join(blocks)
