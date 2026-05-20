"""Unit tests for E2P.1-E2P.6 research engine helpers."""

import pytest

from src.geneva.research_engine import RESEARCH_MODE_CONFIGS, ResearchEngine, SourceRecord
from src.tool_system.tools.web_search import rank_source_credibility


class TestSourceCredibilityRank:
    def test_gov_is_tier1(self):
        assert rank_source_credibility("https://www.cdc.gov/report") == 1

    def test_edu_is_tier1(self):
        assert rank_source_credibility("https://mit.edu/paper") == 1

    def test_reuters_is_tier1(self):
        assert rank_source_credibility("https://reuters.com/story") == 1

    def test_medium_is_tier2(self):
        assert rank_source_credibility("https://medium.com/post") == 2

    def test_unknown_is_tier3(self):
        assert rank_source_credibility("https://someblog.xyz/post") == 3


class TestResearchModeConfigs:
    def test_quick_has_no_conflict_detection(self):
        assert RESEARCH_MODE_CONFIGS["quick"].conflict_detection is False

    def test_deep_has_conflict_detection(self):
        assert RESEARCH_MODE_CONFIGS["deep"].conflict_detection is True

    def test_max_has_claim_verification(self):
        assert RESEARCH_MODE_CONFIGS["max"].claim_verification is True

    def test_quick_5_queries(self):
        assert RESEARCH_MODE_CONFIGS["quick"].query_count == 5

    def test_deep_15_queries(self):
        assert RESEARCH_MODE_CONFIGS["deep"].query_count == 15

    def test_max_30_queries(self):
        assert RESEARCH_MODE_CONFIGS["max"].query_count == 30

    def test_max_3_synthesis_passes(self):
        assert RESEARCH_MODE_CONFIGS["max"].synthesis_passes == 3


class TestClaimExtractor:
    def setup_method(self):
        self.engine = ResearchEngine.__new__(ResearchEngine)

    def test_extracts_declarative_sentences(self):
        text = "The company reported 30% growth in Q3. This is a major milestone. Analysts are optimistic."
        claims = self.engine._extract_claims(text)
        assert len(claims) >= 1
        assert any("growth" in c for c in claims)

    def test_skips_short_sentences(self):
        claims = self.engine._extract_claims("Yes. OK. Sure thing.")
        assert len(claims) == 0

    def test_skips_headers(self):
        claims = self.engine._extract_claims("## Section Title\n- Bullet point")
        assert len(claims) == 0


class TestConflictDetection:
    def setup_method(self):
        self.engine = ResearchEngine.__new__(ResearchEngine)

    def test_detects_directional_conflict(self):
        sources = [
            SourceRecord(source_id="s1", url="http://a.com", title="A", snippet="Revenue increased by 20% this year"),
            SourceRecord(source_id="s2", url="http://b.com", title="B", snippet="Revenue declined significantly this quarter"),
        ]
        conflicts = self.engine._detect_conflicts(sources)
        assert len(conflicts) >= 1
        assert conflicts[0]["source_a"] == "s1" or conflicts[0]["source_b"] == "s2"

    def test_no_conflict_same_direction(self):
        sources = [
            SourceRecord(source_id="s1", url="http://a.com", title="A", snippet="Growth increased significantly"),
            SourceRecord(source_id="s2", url="http://b.com", title="B", snippet="Revenue increase was notable"),
        ]
        conflicts = self.engine._detect_conflicts(sources)
        assert len(conflicts) == 0


class TestSearchCache:
    def test_cache_miss_returns_none(self):
        from src.geneva.research_engine import _cache_get

        assert _cache_get("nonexistent query xyz") is None

    def test_cache_set_and_get(self):
        from src.geneva.research_engine import _cache_get, _cache_set

        _cache_set("test query abc", [{"title": "Test", "url": "http://t.com"}])
        result = _cache_get("test query abc")
        assert result is not None
        assert result[0]["title"] == "Test"
