"""
Tests for src/trends/evolution.py

Covers:
- EvolutionStage enum
- SCurveAnalysis dataclass
- TrendsOfEvolution.analyze_technology (keyword + metrics paths)
- TRIZ trends constants
- render_s_curve ASCII output
- get_trends_analyzer singleton
"""
from __future__ import annotations

import sys


sys.path.insert(0, "/Users/figuramax/LocalProjects/TURBO-CDI/src")

import pytest

from src.trends.evolution import (
    EvolutionStage,
    SCurveAnalysis,
    TrendsOfEvolution,
    get_trends_analyzer,
)


# ═══════════════════════════════════════════════════════════════════
# EvolutionStage
# ═══════════════════════════════════════════════════════════════════


class TestEvolutionStage:
    """Test EvolutionStage enum."""

    def test_all_stages_present(self):
        expected = {"birth", "growth", "maturity", "decline"}
        actual = {s.value for s in EvolutionStage}
        assert actual == expected

    def test_stage_values(self):
        assert EvolutionStage.BIRTH.value == "birth"
        assert EvolutionStage.GROWTH.value == "growth"
        assert EvolutionStage.MATURITY.value == "maturity"
        assert EvolutionStage.DECLINE.value == "decline"


# ═══════════════════════════════════════════════════════════════════
# SCurveAnalysis
# ═══════════════════════════════════════════════════════════════════


class TestSCurveAnalysis:
    """Test SCurveAnalysis dataclass."""

    def test_creation(self):
        analysis = SCurveAnalysis(
            technology="Test",
            current_stage=EvolutionStage.GROWTH,
            maturity_percent=45.0,
            performance_trend="improving",
            patent_activity="high",
            market_growth="high",
            time_to_maturity=10,
            next_paradigm="Next",
            strategy="Scale",
            investment_recommendation="HIGH",
        )
        assert analysis.technology == "Test"
        assert analysis.maturity_percent == 45.0


# ═══════════════════════════════════════════════════════════════════
# TrendsOfEvolution — Keyword Estimation
# ═══════════════════════════════════════════════════════════════════


class TestAnalyzeTechnologyKeywords:
    """Test analyze_technology with keyword estimation."""

    def test_emerging_technology(self):
        analyzer = TrendsOfEvolution()
        result = analyzer.analyze_technology("quantum computing")

        assert result.current_stage == EvolutionStage.BIRTH
        assert result.maturity_percent == 15.0
        assert result.performance_trend == "improving"
        assert result.patent_activity == "low"
        assert result.market_growth == "low"

    def test_growth_technology(self):
        analyzer = TrendsOfEvolution()
        result = analyzer.analyze_technology("electric vehicle")

        assert result.current_stage == EvolutionStage.GROWTH
        assert result.maturity_percent == 45.0
        assert result.performance_trend == "improving"
        assert result.patent_activity == "high"
        assert result.market_growth == "high"

    def test_mature_technology(self):
        analyzer = TrendsOfEvolution()
        result = analyzer.analyze_technology("lithium-ion battery")

        assert result.current_stage == EvolutionStage.MATURITY
        assert result.maturity_percent == 75.0
        assert result.performance_trend == "stable"
        assert result.patent_activity == "medium"

    def test_declining_technology(self):
        analyzer = TrendsOfEvolution()
        result = analyzer.analyze_technology("coal power plant")

        assert result.current_stage == EvolutionStage.DECLINE
        assert result.maturity_percent == 90.0
        assert result.performance_trend == "declining"
        assert result.patent_activity == "low"

    def test_unknown_technology_defaults(self):
        analyzer = TrendsOfEvolution()
        result = analyzer.analyze_technology("foobar")

        assert result.current_stage == EvolutionStage.GROWTH
        assert result.maturity_percent == 45.0


# ═══════════════════════════════════════════════════════════════════
# TrendsOfEvolution — Metrics Calculation
# ═══════════════════════════════════════════════════════════════════


class TestAnalyzeTechnologyMetrics:
    """Test analyze_technology with explicit metrics."""

    def test_growth_from_metrics(self):
        analyzer = TrendsOfEvolution()
        # Strong positive growth with acceleration
        metrics = [1.0, 1.5, 2.5]
        result = analyzer.analyze_technology("X", metrics=metrics)

        assert result.current_stage == EvolutionStage.GROWTH
        assert result.maturity_percent == 40.0

    def test_maturity_from_metrics(self):
        analyzer = TrendsOfEvolution()
        # Moderate positive growth
        metrics = [1.0, 1.1, 1.2]
        result = analyzer.analyze_technology("X", metrics=metrics)

        assert result.current_stage == EvolutionStage.MATURITY
        assert result.maturity_percent == 70.0

    def test_decline_from_metrics(self):
        analyzer = TrendsOfEvolution()
        # Negative growth
        metrics = [1.0, 0.9, 0.8]
        result = analyzer.analyze_technology("X", metrics=metrics)

        assert result.current_stage == EvolutionStage.DECLINE
        assert result.maturity_percent == 85.0

    def test_birth_from_metrics(self):
        analyzer = TrendsOfEvolution()
        # Near-zero growth
        metrics = [1.0, 1.01, 1.01]
        result = analyzer.analyze_technology("X", metrics=metrics)

        assert result.current_stage == EvolutionStage.BIRTH
        assert result.maturity_percent == 20.0

    def test_single_metric_fallback(self):
        analyzer = TrendsOfEvolution()
        result = analyzer.analyze_technology("X", metrics=[1.0])

        assert result.current_stage == EvolutionStage.GROWTH
        assert result.maturity_percent == 50.0

    def test_two_metrics(self):
        analyzer = TrendsOfEvolution()
        # Only 2 metrics — can't compute acceleration, growth=0.5 > 0.05 -> maturity
        metrics = [1.0, 1.5]
        result = analyzer.analyze_technology("X", metrics=metrics)
        assert result.current_stage == EvolutionStage.MATURITY

    def test_zero_division_in_metrics(self):
        analyzer = TrendsOfEvolution()
        metrics = [0.0, 1.0, 2.0]
        result = analyzer.analyze_technology("X", metrics=metrics)
        # Should not raise ZeroDivisionError
        assert isinstance(result, SCurveAnalysis)


# ═══════════════════════════════════════════════════════════════════
# TrendsOfEvolution — Predictions & Recommendations
# ═══════════════════════════════════════════════════════════════════


class TestPredictionsAndRecommendations:
    """Test prediction and recommendation methods."""

    def test_predict_time_to_maturity_birth(self):
        analyzer = TrendsOfEvolution()
        years = analyzer._predict_time_to_maturity(EvolutionStage.BIRTH, 15.0)
        assert years == 40  # (95-15) * 0.5

    def test_predict_time_to_maturity_growth(self):
        analyzer = TrendsOfEvolution()
        years = analyzer._predict_time_to_maturity(EvolutionStage.GROWTH, 45.0)
        assert years == 15  # (95-45) * 0.3

    def test_predict_time_to_maturity_maturity(self):
        analyzer = TrendsOfEvolution()
        years = analyzer._predict_time_to_maturity(EvolutionStage.MATURITY, 75.0)
        assert years == 16  # (95-75) * 0.8

    def test_predict_time_to_maturity_decline(self):
        analyzer = TrendsOfEvolution()
        years = analyzer._predict_time_to_maturity(EvolutionStage.DECLINE, 90.0)
        assert years == 0

    def test_predict_next_paradigm_known(self):
        analyzer = TrendsOfEvolution()
        assert analyzer._predict_next_paradigm("lithium-ion", EvolutionStage.MATURITY) == "solid-state batteries"
        assert analyzer._predict_next_paradigm("silicon solar", EvolutionStage.MATURITY) == "perovskite solar"
        assert analyzer._predict_next_paradigm("lcd display", EvolutionStage.MATURITY) == "microled"

    def test_predict_next_paradigm_unknown(self):
        analyzer = TrendsOfEvolution()
        assert analyzer._predict_next_paradigm("foobar", EvolutionStage.BIRTH) is None

    def test_recommend_strategy_birth(self):
        analyzer = TrendsOfEvolution()
        assert "R&D" in analyzer._recommend_strategy(EvolutionStage.BIRTH)

    def test_recommend_strategy_growth(self):
        analyzer = TrendsOfEvolution()
        assert "Scale" in analyzer._recommend_strategy(EvolutionStage.GROWTH)

    def test_recommend_strategy_maturity(self):
        analyzer = TrendsOfEvolution()
        assert "Optimize" in analyzer._recommend_strategy(EvolutionStage.MATURITY)

    def test_recommend_strategy_decline(self):
        analyzer = TrendsOfEvolution()
        assert "transition" in analyzer._recommend_strategy(EvolutionStage.DECLINE)

    def test_recommend_investment_growth(self):
        analyzer = TrendsOfEvolution()
        assert "HIGH" in analyzer._recommend_investment(EvolutionStage.GROWTH, 50.0)

    def test_recommend_investment_birth_low_maturity(self):
        analyzer = TrendsOfEvolution()
        assert "MODERATE" in analyzer._recommend_investment(EvolutionStage.BIRTH, 15.0)

    def test_recommend_investment_maturity(self):
        analyzer = TrendsOfEvolution()
        assert "LOW" in analyzer._recommend_investment(EvolutionStage.MATURITY, 75.0)

    def test_recommend_investment_decline(self):
        analyzer = TrendsOfEvolution()
        assert "AVOID" in analyzer._recommend_investment(EvolutionStage.DECLINE, 90.0)


# ═══════════════════════════════════════════════════════════════════
# TrendsOfEvolution — render_s_curve
# ═══════════════════════════════════════════════════════════════════


class TestRenderSCurve:
    """Test ASCII S-curve rendering."""

    def test_render_contains_title(self):
        analyzer = TrendsOfEvolution()
        analysis = analyzer.analyze_technology("test tech")
        rendered = analyzer.render_s_curve(analysis)

        assert "S-Curve: test tech" in rendered

    def test_render_contains_stage(self):
        analyzer = TrendsOfEvolution()
        analysis = analyzer.analyze_technology("quantum")
        rendered = analyzer.render_s_curve(analysis)

        assert "BIRTH" in rendered

    def test_render_contains_maturity(self):
        analyzer = TrendsOfEvolution()
        analysis = analyzer.analyze_technology("electric vehicle")
        rendered = analyzer.render_s_curve(analysis)

        assert "Maturity: 45%" in rendered
        assert "▲ Current" in rendered

    def test_render_contains_time_to_maturity(self):
        analyzer = TrendsOfEvolution()
        analysis = analyzer.analyze_technology("electric vehicle")
        rendered = analyzer.render_s_curve(analysis)

        assert "Time to maturity" in rendered

    def test_render_no_time_for_decline(self):
        analyzer = TrendsOfEvolution()
        analysis = analyzer.analyze_technology("coal")
        rendered = analyzer.render_s_curve(analysis)

        assert "Time to maturity" not in rendered

    def test_render_contains_next_paradigm(self):
        analyzer = TrendsOfEvolution()
        analysis = analyzer.analyze_technology("lithium-ion")
        rendered = analyzer.render_s_curve(analysis)

        assert "Next paradigm: solid-state batteries" in rendered

    def test_render_has_axis_labels(self):
        analyzer = TrendsOfEvolution()
        analysis = analyzer.analyze_technology("test")
        rendered = analyzer.render_s_curve(analysis)

        assert "Birth" in rendered
        assert "Growth" in rendered
        assert "Maturity" in rendered
        assert "Decline" in rendered


# ═══════════════════════════════════════════════════════════════════
# TrendsOfEvolution — TRIZ Trends
# ═══════════════════════════════════════════════════════════════════


class TestTrizTrends:
    """Test TRIZ trends constants."""

    def test_all_8_trends_present(self):
        assert len(TrendsOfEvolution.TRENDS) == 8

    def test_trend_names(self):
        expected_keys = {
            "s_curve",
            "idealization",
            "dynamization",
            "automation",
            "structural",
            "coordination",
            "complexity",
            "controllability",
        }
        assert set(TrendsOfEvolution.TRENDS.keys()) == expected_keys


# ═══════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════


class TestGetTrendsAnalyzer:
    """Test get_trends_analyzer singleton."""

    def test_returns_same_instance(self):
        a1 = get_trends_analyzer()
        a2 = get_trends_analyzer()
        assert a1 is a2

    def test_is_trends_of_evolution(self):
        analyzer = get_trends_analyzer()
        assert isinstance(analyzer, TrendsOfEvolution)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
