"""
Tests for src/metamodels/mp/profiles.py
Covers MPRotationEngine, MPProfiler, AgentPerspective, RotationResult.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from c4.engine import C4State
from metamodels.mp.core import Metaprogram, MPDimension
from metamodels.mp.patterns import MPLibrary
from metamodels.mp.profiles import (
    AgentPerspective,
    MPProfiler,
    MPRotationEngine,
    RotationResult,
)


class TestAgentPerspective:
    def test_creation_defaults(self):
        ap = AgentPerspective(
            agent_id="a1",
            profile_name="Systems Thinker",
            profile_name_ru="Системный мыслитель",
            c4_state=C4State(1, 1, 1),
        )
        assert ap.agent_id == "a1"
        assert ap.analysis == ""
        assert ap.confidence == 0.0
        assert ap.key_insights == []
        assert ap.blind_spots == []
        assert ap.duration_ms == 0.0

    def test_to_dict(self):
        ap = AgentPerspective(
            agent_id="a1",
            profile_name="Test",
            profile_name_ru="Тест",
            c4_state=C4State(1, 1, 1),
            analysis="Analysis text",
            confidence=0.85,
            key_insights=["insight1"],
            blind_spots=["spot1"],
            duration_ms=100.0,
        )
        d = ap.to_dict()
        assert d["agent_id"] == "a1"
        assert d["profile_name"] == "Test"
        assert d["c4_state"] == (1, 1, 1)
        assert d["analysis"] == "Analysis text"
        assert d["confidence"] == 0.85
        assert d["key_insights"] == ["insight1"]
        assert d["blind_spots"] == ["spot1"]
        assert d["duration_ms"] == 100.0


class TestRotationResult:
    def test_defaults(self):
        rr = RotationResult(problem="Test")
        assert rr.problem == "Test"
        assert rr.perspectives == []
        assert rr.synthesized_view == ""
        assert rr.consensus_score == 0.0
        assert rr.total_duration_ms == 0.0

    def test_to_dict(self):
        ap = AgentPerspective(
            agent_id="a1",
            profile_name="Test",
            profile_name_ru="Тест",
            c4_state=C4State(1, 1, 1),
        )
        rr = RotationResult(
            problem="P",
            perspectives=[ap],
            synthesized_view="view",
            consensus_score=0.8,
            total_duration_ms=200.0,
        )
        d = rr.to_dict()
        assert d["problem"] == "P"
        assert len(d["perspectives"]) == 1
        assert d["synthesized_view"] == "view"
        assert d["consensus_score"] == 0.8
        assert d["total_duration_ms"] == 200.0


class TestMPRotationEngine:
    def test_init_default_library(self):
        engine = MPRotationEngine()
        assert engine.mp is not None
        assert type(engine.mp).__name__ == "MPLibrary"

    def test_init_custom_library(self):
        lib = MPLibrary()
        engine = MPRotationEngine(mp_library=lib)
        assert engine.mp is lib

    def test_analyze_returns_rotation_result(self):
        engine = MPRotationEngine()
        result = engine.analyze("How to solve this problem?", n_profiles=3)
        assert isinstance(result, RotationResult)
        assert result.problem == "How to solve this problem?"
        assert len(result.perspectives) == 3
        assert result.total_duration_ms >= 0.0

    def test_analyze_n_profiles_2(self):
        engine = MPRotationEngine()
        result = engine.analyze("Test", n_profiles=2)
        assert len(result.perspectives) == 2

    def test_analyze_with_custom_c4_state(self):
        engine = MPRotationEngine()
        state = C4State(0, 2, 1)
        result = engine.analyze("Test", n_profiles=3, c4_state=state)
        for p in result.perspectives:
            assert p.c4_state is not None

    def test_perspectives_have_insights_and_blind_spots(self):
        engine = MPRotationEngine()
        result = engine.analyze("Design a new product")
        for p in result.perspectives:
            assert p.agent_id.startswith("agent_")
            assert p.profile_name != ""
            assert len(p.key_insights) > 0
            assert len(p.blind_spots) > 0
            assert 0.0 <= p.confidence <= 1.0

    def test_synthesized_view_contains_info(self):
        engine = MPRotationEngine()
        result = engine.analyze("Test")
        assert "Synthesized view" in result.synthesized_view
        assert str(len(result.perspectives)) in result.synthesized_view

    def test_consensus_score_range(self):
        engine = MPRotationEngine()
        result = engine.analyze("Test")
        assert 0.0 <= result.consensus_score <= 1.0

    def test_adjust_state_systems(self):
        engine = MPRotationEngine()
        lib = MPLibrary()
        profile = lib.get_profile("systems")
        state = C4State(1, 1, 1)
        adjusted = engine._adjust_state_for_profile(state, profile)
        assert adjusted.S == 2
        assert adjusted.A == 2

    def test_adjust_state_pragmatic(self):
        engine = MPRotationEngine()
        lib = MPLibrary()
        profile = lib.get_profile("pragmatic")
        state = C4State(1, 1, 1)
        adjusted = engine._adjust_state_for_profile(state, profile)
        assert adjusted.S == 0
        assert adjusted.A == 0

    def test_adjust_state_creative(self):
        engine = MPRotationEngine()
        lib = MPLibrary()
        profile = lib.get_profile("creative")
        state = C4State(1, 1, 1)
        adjusted = engine._adjust_state_for_profile(state, profile)
        assert adjusted.T == 2
        assert adjusted.S == 2

    def test_adjust_state_critical(self):
        engine = MPRotationEngine()
        lib = MPLibrary()
        profile = lib.get_profile("critical")
        state = C4State(1, 1, 1)
        adjusted = engine._adjust_state_for_profile(state, profile)
        assert adjusted.T == 1
        assert adjusted.A == 2

    def test_adjust_state_intuitive(self):
        engine = MPRotationEngine()
        lib = MPLibrary()
        profile = lib.get_profile("intuitive")
        state = C4State(1, 1, 1)
        adjusted = engine._adjust_state_for_profile(state, profile)
        assert adjusted.T == 1
        assert adjusted.A == 1

    def test_adjust_state_unknown_profile(self):
        engine = MPRotationEngine()
        lib = MPLibrary()
        profile = lib.get_profile("systems")
        profile.name = "Unknown Profile"
        state = C4State(1, 1, 1)
        adjusted = engine._adjust_state_for_profile(state, profile)
        assert adjusted.to_tuple() == state.to_tuple()

    def test_generate_insights_systems(self):
        engine = MPRotationEngine()
        lib = MPLibrary()
        profile = lib.get_profile("systems")
        insights = engine._generate_insights_for_profile(profile, "Test")
        assert "feedback loops" in insights[0].lower()

    def test_generate_insights_unknown(self):
        engine = MPRotationEngine()
        mock_profile = MagicMock()
        mock_profile.name = "Unknown"
        insights = engine._generate_insights_for_profile(mock_profile, "Test")
        assert insights == ["Analyze from multiple angles"]

    def test_generate_blind_spots_systems(self):
        engine = MPRotationEngine()
        lib = MPLibrary()
        profile = lib.get_profile("systems")
        spots = engine._generate_blind_spots_for_profile(profile)
        assert len(spots) > 0

    def test_generate_blind_spots_unknown(self):
        engine = MPRotationEngine()
        mock_profile = MagicMock()
        mock_profile.name = "Unknown"
        spots = engine._generate_blind_spots_for_profile(mock_profile)
        assert spots == ["Unknown blind spots"]

    def test_compute_consensus_single(self):
        engine = MPRotationEngine()
        p = AgentPerspective("a1", "Test", "Тест", C4State(1, 1, 1), confidence=0.8)
        score = engine._compute_consensus([p])
        assert score == 1.0

    def test_compute_consensus_multiple(self):
        engine = MPRotationEngine()
        p1 = AgentPerspective("a1", "Test1", "Тест1", C4State(1, 1, 1), confidence=0.8)
        p2 = AgentPerspective("a2", "Test2", "Тест2", C4State(1, 1, 1), confidence=0.9)
        score = engine._compute_consensus([p1, p2])
        assert 0.0 <= score <= 1.0

    def test_compute_consensus_empty(self):
        engine = MPRotationEngine()
        score = engine._compute_consensus([])
        assert score == 1.0

    def test_synthesize(self):
        engine = MPRotationEngine()
        lib = MPLibrary()
        profiles = lib.rotate_profiles("Test", n=2)
        perspectives = [
            AgentPerspective(
                f"a{i+1}", p.name, p.name_ru, C4State(1, 1, 1), confidence=0.85
            )
            for i, p in enumerate(profiles)
        ]
        view = engine._synthesize(profiles, perspectives)
        assert "Synthesized view" in view


class TestMPProfiler:
    def test_analyze_returns_dict(self):
        profiler = MPProfiler()
        result = profiler.analyze("Design a rocket engine", "engineering")
        assert isinstance(result, dict)
        assert "perspectives" in result
        assert "total_lenses_available" in result
        assert "selected_lenses" in result
        assert "recommended_view" in result

    def test_analyze_has_perspectives(self):
        profiler = MPProfiler()
        result = profiler.analyze("Analyze historical system trends", "logistics")
        assert len(result["perspectives"]) > 0
        for p in result["perspectives"]:
            assert "lens" in p
            assert "category" in p
            assert "question" in p
            assert "relevance_score" in p
            assert "insight" in p

    def test_analyze_sorted_by_relevance(self):
        profiler = MPProfiler()
        result = profiler.analyze("How does nature solve this?", "biology")
        scores = [p["relevance_score"] for p in result["perspectives"]]
        assert scores == sorted(scores, reverse=True)

    def test_analyze_max_8_perspectives(self):
        profiler = MPProfiler()
        result = profiler.analyze("Test", "general")
        assert len(result["perspectives"]) <= 8

    def test_analyze_total_lenses(self):
        profiler = MPProfiler()
        result = profiler.analyze("Test")
        assert result["total_lenses_available"] == 12

    def test_analyze_recommended_view(self):
        profiler = MPProfiler()
        result = profiler.analyze("Test")
        assert result["recommended_view"] in {
            "temporal", "structural", "functional", "analogical", "general"
        }

    def test_analyze_empty_problem(self):
        profiler = MPProfiler()
        result = profiler.analyze("")
        # Should still work, likely no relevance matches
        assert isinstance(result["perspectives"], list)

    def test_lenses_have_categories(self):
        profiler = MPProfiler()
        result = profiler.analyze("Build system")
        categories = {p["category"] for p in result["perspectives"]}
        valid = {"temporal", "structural", "functional", "analogical"}
        assert categories.issubset(valid)
