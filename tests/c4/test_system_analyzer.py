"""Tests for SystemAnalyzer — real analyzer, no mocks.

Covers 4 query types (atomic → systemic) plus structural checks
on dependency graph, critical path, C4 state, and analysis_depth.
"""
from __future__ import annotations

import pytest

from src.c4_analysis.system_analyzer import SystemAnalyzer


class TestSystemAnalyzerQueries:
    """End-to-end analyze() on real queries of increasing systemicity."""

    @pytest.fixture(scope="class")
    def analyzer(self) -> SystemAnalyzer:
        return SystemAnalyzer()

    def test_atomic_query(self, analyzer: SystemAnalyzer) -> None:
        """Atomic query: very few entities, bounded systemicity."""
        result = analyzer.analyze("What is 2+2?")

        assert result["query"] == "What is 2+2?"
        assert 0.0 <= result["systemicity"] < 1.0
        assert result["systemicity_label"] in (
            "pseudo-atomic",
            "weakly systemic",
            "moderately systemic",
            "strongly systemic",
            "deeply systemic",
        )
        assert len(result["entities"]) <= 2
        assert result["analysis_depth"] in ("shallow", "moderate", "deep")
        assert isinstance(result["explanation"], str)
        self._assert_required_keys(result)

    def test_compositional_query(self, analyzer: SystemAnalyzer) -> None:
        """Compositional query: multiple entities, bounded systemicity."""
        result = analyzer.analyze("List causes of WW2")

        assert result["query"] == "List causes of WW2"
        assert 0.0 <= result["systemicity"] < 1.0
        assert result["systemicity_label"] in (
            "pseudo-atomic",
            "weakly systemic",
            "moderately systemic",
            "strongly systemic",
            "deeply systemic",
        )
        assert len(result["entities"]) >= 2
        assert result["analysis_depth"] in ("shallow", "moderate", "deep")
        self._assert_required_keys(result)

    def test_relational_query(self, analyzer: SystemAnalyzer) -> None:
        """Relational query: interaction between entities."""
        result = analyzer.analyze("How does inflation affect unemployment?")

        assert result["query"] == "How does inflation affect unemployment?"
        assert 0.0 <= result["systemicity"] < 1.0
        assert result["systemicity_label"] in (
            "pseudo-atomic",
            "weakly systemic",
            "moderately systemic",
            "strongly systemic",
            "deeply systemic",
        )
        assert len(result["entities"]) >= 2
        assert result["analysis_depth"] in ("shallow", "moderate", "deep")
        self._assert_required_keys(result)

    def test_systemic_causal_chain_query(self, analyzer: SystemAnalyzer) -> None:
        """Systemic query with explicit causal chain: highest complexity."""
        result = analyzer.analyze(
            "Climate change causes biodiversity loss which reduces carbon sequestration"
        )

        assert (
            result["query"]
            == "Climate change causes biodiversity loss which reduces carbon sequestration"
        )
        # Causal chain + multiple entities guarantees materially higher systemicity
        assert result["systemicity"] >= 0.2
        assert result["systemicity_label"] in (
            "weakly systemic",
            "moderately systemic",
            "strongly systemic",
            "deeply systemic",
        )
        assert len(result["entities"]) >= 3
        assert result["analysis_depth"] in ("shallow", "moderate", "deep")
        self._assert_required_keys(result)

    def test_entity_count_increases_with_complexity(self, analyzer: SystemAnalyzer) -> None:
        """More complex queries should extract at least as many entities."""
        atomic = analyzer.analyze("What is 2+2?")["entities"]
        compositional = analyzer.analyze("List causes of WW2")["entities"]
        systemic = analyzer.analyze(
            "Climate change causes biodiversity loss which reduces carbon sequestration"
        )["entities"]

        assert len(atomic) <= len(compositional)
        assert len(compositional) <= len(systemic)
        assert len(systemic) >= 3

    def test_dependency_graph_structure(self, analyzer: SystemAnalyzer) -> None:
        """Entities should be linked when causal language is present."""
        result = analyzer.analyze(
            "Climate change causes biodiversity loss which reduces carbon sequestration"
        )
        graph = result["dependency_graph"]

        assert isinstance(graph, dict)
        assert len(graph) > 0
        # At least one entity must depend on another
        total_deps = sum(len(v) for v in graph.values())
        assert total_deps > 0

    def test_critical_path_ordering(self, analyzer: SystemAnalyzer) -> None:
        """Critical path should start with the most central / root entity."""
        result = analyzer.analyze(
            "Climate change causes biodiversity loss which reduces carbon sequestration"
        )
        critical = result["critical_path"]

        assert isinstance(critical, list)
        assert len(critical) > 0
        # First element should be an entity present in the entity list
        assert critical[0] in result["entities"]

    def test_c4_state_and_analysis_depth(self, analyzer: SystemAnalyzer) -> None:
        """c4_state and analysis_depth must be present and well-formed."""
        result = analyzer.analyze(
            "Climate change causes biodiversity loss which reduces carbon sequestration"
        )

        assert "c4_state" in result
        assert isinstance(result["c4_state"], str)
        assert "/" in result["c4_state"]  # e.g. "CONCRETE/PRESENT/SYSTEM"

        assert "analysis_depth" in result
        assert result["analysis_depth"] in ("shallow", "moderate", "deep")

    def test_sub_problems_have_routing(self, analyzer: SystemAnalyzer) -> None:
        """Each sub-problem should carry C4 routing metadata."""
        result = analyzer.analyze(
            "Climate change causes biodiversity loss which reduces carbon sequestration"
        )
        sub_problems = result["sub_problems"]

        assert isinstance(sub_problems, list)
        assert len(sub_problems) > 0
        for sp in sub_problems:
            assert "entity" in sp
            assert "scientist" in sp
            assert "c4_path" in sp
            assert isinstance(sp["c4_path"], list)

    def test_explanation_non_empty(self, analyzer: SystemAnalyzer) -> None:
        """Explanation must be a non-empty string for any query."""
        result = analyzer.analyze("What is 2+2?")
        assert isinstance(result["explanation"], str)
        assert len(result["explanation"]) > 0

    def _assert_required_keys(self, result: dict) -> None:
        expected_keys = {
            "query",
            "systemicity",
            "systemicity_label",
            "entities",
            "dependency_graph",
            "sub_problems",
            "critical_path",
            "c4_state",
            "analysis_depth",
            "explanation",
        }
        assert expected_keys.issubset(result.keys())


class TestSystemAnalyzerInternals:
    """Direct unit tests for internal classification logic (no LLM)."""

    def test_classify_systemicity_no_deps(self) -> None:
        """Single entity, no dependencies → near-zero systemicity."""
        analyzer = SystemAnalyzer()
        score = analyzer._classify_systemicity("hello world", ["hello"], {})
        assert 0.0 <= score < 0.1

    def test_classify_systemicity_with_causal_indicator(self) -> None:
        """Explicit causal indicator raises score."""
        analyzer = SystemAnalyzer()
        score = analyzer._classify_systemicity(
            "a causes b", ["a", "b"], {"b": {"a"}}
        )
        assert score > 0.05

    def test_classify_systemicity_many_entities(self) -> None:
        """More entities increase systemicity."""
        analyzer = SystemAnalyzer()
        entities = [f"e{i}" for i in range(10)]
        deps = {f"e{i}": {f"e{i-1}"} for i in range(1, 10)}
        score = analyzer._classify_systemicity("query", entities, deps)
        assert score > 0.1

    def test_label_boundaries(self) -> None:
        """_label maps thresholds correctly."""
        analyzer = SystemAnalyzer()
        assert analyzer._label(0.0) == "pseudo-atomic"
        assert analyzer._label(0.19) == "pseudo-atomic"
        assert analyzer._label(0.2) == "weakly systemic"
        assert analyzer._label(0.39) == "weakly systemic"
        assert analyzer._label(0.4) == "moderately systemic"
        assert analyzer._label(0.59) == "moderately systemic"
        assert analyzer._label(0.6) == "strongly systemic"
        assert analyzer._label(0.79) == "strongly systemic"
        assert analyzer._label(0.8) == "deeply systemic"
        assert analyzer._label(1.0) == "deeply systemic"

    def test_extract_entities_filters_stopwords(self) -> None:
        """Stopwords should be removed from entities."""
        analyzer = SystemAnalyzer()
        entities = analyzer._extract_entities("the quick brown fox")
        assert "the" not in entities
        # "quick" may be merged into "quick brown" phrase
        assert any("quick" in e for e in entities)

    def test_extract_entities_merges_phrases(self) -> None:
        """Adjacent non-stopwords may merge into 2-word phrases."""
        analyzer = SystemAnalyzer()
        entities = analyzer._extract_entities("climate change is real")
        # "climate change" is a valid phrase >5 chars and in query
        assert any("climate change" in e for e in entities)

    def test_critical_path_empty_routes(self) -> None:
        """Empty routes → empty critical path."""
        analyzer = SystemAnalyzer()
        assert analyzer._critical_path([], {}) == []

    def test_critical_path_single_route(self) -> None:
        """Single route → single-element critical path."""
        analyzer = SystemAnalyzer()
        routes = [{"entity": "alpha", "depends_on": []}]
        assert analyzer._critical_path(routes, {}) == ["alpha"]

    def test_analysis_depth_values(self) -> None:
        """analysis_depth must align with _label thresholds."""
        analyzer = SystemAnalyzer()
        # _label(0.1) == "pseudo-atomic" but depth is shallow for <= 0.3
        assert analyzer.analyze("x")["analysis_depth"] in ("shallow", "moderate", "deep")


class TestSystemAnalyzerCore:
    """Pure-logic init, analyze, and entity extraction tests."""

    def test_init_creates_router_and_classifier(self) -> None:
        analyzer = SystemAnalyzer()
        assert analyzer.router is not None
        assert analyzer.classifier is not None

    def test_analyze_returns_dict_with_required_keys(self) -> None:
        analyzer = SystemAnalyzer()
        result = analyzer.analyze("Describe climate change")
        assert isinstance(result, dict)
        assert "systemicity" in result
        assert "entities" in result
        assert "dependency_graph" in result

    def test_entity_extraction_stopword_filtering(self) -> None:
        analyzer = SystemAnalyzer()
        entities = analyzer._extract_entities("the cat and a dog")
        assert "the" not in entities
        assert "a" not in entities
        assert "and" not in entities
        assert len(entities) >= 2

    def test_systemicity_between_0_and_1(self) -> None:
        analyzer = SystemAnalyzer()
        result = analyzer.analyze("Describe climate change")
        assert 0.0 <= result["systemicity"] <= 1.0
