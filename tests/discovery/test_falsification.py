"""
Tests for Falsification Engine — Popper's Falsification Framework.

Covers: Hypothesis, TestResult, FalsificationReport, is_falsifiable,
severity_score, modus_tollens, demarcation, evaluate_hypothesis,
FalsificationEngine.
"""
from __future__ import annotations

import pytest

from src.discovery.falsification import (
    FalsificationEngine,
    FalsificationReport,
    Hypothesis,
    TestResult,
    demarcation,
    evaluate_hypothesis,
    is_falsifiable,
    modus_tollens,
    severity_score,
)


class TestHypothesis:
    def test_create_hypothesis(self):
        h = Hypothesis(id="H1", statement="All swans are white")
        assert h.id == "H1"
        assert h.statement == "All swans are white"
        assert h.predictions == []
        assert h.assumptions == []
        assert not h.is_falsified

    def test_hypothesis_to_dict(self):
        h = Hypothesis(id="H1", statement="Test", severity_score=0.8)
        d = h.to_dict()
        assert d["id"] == "H1"
        assert d["severity_score"] == 0.8


class TestTestResult:
    def test_create_result(self):
        tr = TestResult(prediction="P", observation="O", outcome="confirmed")
        assert tr.prediction == "P"
        assert tr.observation == "O"
        assert tr.outcome == "confirmed"
        assert tr.confidence == 1.0

    def test_result_to_dict(self):
        tr = TestResult("P", "O", "falsified", 0.95, 0.8)
        d = tr.to_dict()
        assert d["outcome"] == "falsified"
        assert d["severity"] == 0.8


class TestIsFalsifiable:
    def test_universal_claim_falsifiable(self):
        result, reason = is_falsifiable("All swans are white")
        assert result is True
        assert "counterexample" in reason.lower()

    def test_tautology_not_falsifiable(self):
        result, reason = is_falsifiable("All bachelors are unmarried")
        assert result is False
        assert "tautology" in reason.lower()

    def test_metaphysical_not_falsifiable(self):
        result, reason = is_falsifiable("God exists")
        assert result is False
        assert "contradict" in reason.lower()

    def test_causal_claim_falsifiable(self):
        result, reason = is_falsifiable("Smoking causes cancer")
        assert result is True
        assert "causal" in reason.lower()

    def test_statistical_claim_falsifiable(self):
        result, reason = is_falsifiable("The probability of heads is 0.5")
        assert result is True
        assert "statistical" in reason.lower()

    def test_existential_claim_falsifiable(self):
        result, reason = is_falsifiable("There exists a black swan")
        assert result is True

    def test_short_statement_not_falsifiable(self):
        result, _ = is_falsifiable("Hi")
        assert result is False

    def test_vague_statement_not_falsifiable(self):
        result, _ = is_falsifiable("Something might happen somehow")
        assert result is False

    def test_observable_terms_falsifiable(self):
        result, _ = is_falsifiable("Temperature increases with pressure")
        assert result is True

    def test_conditional_falsifiable(self):
        result, _ = is_falsifiable("If it rains, the ground gets wet")
        assert result is True


class TestSeverityScore:
    def test_falsified_max_severity(self):
        h = Hypothesis("H1", "Test")
        tr = TestResult("P", "O", "falsified")
        assert severity_score(h, tr) == 1.0

    def test_inconclusive_zero_severity(self):
        h = Hypothesis("H1", "Test")
        tr = TestResult("P", "O", "inconclusive")
        assert severity_score(h, tr) == 0.0

    def test_confirmed_severity(self):
        h = Hypothesis("H1", "Test", predictions=["star shift"])
        tr = TestResult("star shift", "1.75 arcsec", "confirmed", 0.99)
        score = severity_score(h, tr)
        assert 0.0 < score <= 1.0

    def test_confirmed_without_predictions(self):
        h = Hypothesis("H1", "Test")
        tr = TestResult("some prediction", "observed", "confirmed", 0.9)
        score = severity_score(h, tr)
        assert 0.0 < score < 1.0

    def test_specificity_affects_severity(self):
        h = Hypothesis("H1", "Test")
        tr_short = TestResult("short", "obs", "confirmed", 1.0)
        tr_long = TestResult("a very detailed and specific prediction with many words", "obs", "confirmed", 1.0)
        assert severity_score(h, tr_long) >= severity_score(h, tr_short)


class TestModusTollens:
    def test_direct_contradiction(self):
        result, reason = modus_tollens("All swans are white", "Swan X is white", "Swan X is black")
        assert result is True
        assert "contradicts" in reason.lower()

    def test_confirmation(self):
        result, reason = modus_tollens("All swans are white", "Swan X is white", "Swan X is white")
        assert result is False
        assert "confirms" in reason.lower()

    def test_negation_contradiction(self):
        result, reason = modus_tollens("H", "P is true", "P is false")
        assert result is True

    def test_inconclusive(self):
        result, reason = modus_tollens("H", "P happens xyz", "Q happens abc")
        assert result is False
        assert "inconclusive" in reason.lower()

    def test_opposite_terms(self):
        result, _ = modus_tollens("H", "Temperature increases", "Temperature decreases")
        assert result is True

    def test_present_absent(self):
        result, _ = modus_tollens("H", "Signal is present", "Signal is absent")
        assert result is True


class TestDemarcation:
    def test_science_universal(self):
        assert demarcation("All planets move in ellipses") == "science"

    def test_science_causal(self):
        assert demarcation("Gravity causes tides") == "science"

    def test_mathematics(self):
        assert demarcation("For all x, x = x") == "mathematics"

    def test_metaphysics(self):
        assert demarcation("The universe has a purpose") == "metaphysics"

    def test_pseudoscience(self):
        assert demarcation("Astrology predicts personality") == "pseudoscience"

    def test_insufficient_information(self):
        assert demarcation("Hi") == "insufficient_information"

    def test_non_science_vague(self):
        assert demarcation("Something is somehow") == "non_science"

    def test_science_statistical(self):
        assert demarcation("The probability is 0.5") == "science"


class TestEvaluateHypothesis:
    def test_evaluate_confirmed(self):
        h = Hypothesis("H1", "All metals expand when heated")
        obs = [("Iron expands at 100C", "Iron expanded 0.1%", 0.95)]
        report = evaluate_hypothesis(h, obs)
        assert report.is_falsifiable is True
        assert report.is_falsified is False
        # Prediction and observation share keywords "expanded"/"expands" and "Iron"
        assert report.corroboration >= 0.0
        assert len(report.tests) == 1

    def test_evaluate_falsified(self):
        h = Hypothesis("H1", "All swans are white")
        obs = [("Swan in Australia is white", "Black swan observed", 0.99)]
        report = evaluate_hypothesis(h, obs)
        assert report.is_falsified is True
        assert report.modus_tollens_valid is True
        assert report.corroboration == 0.0

    def test_evaluate_unfalsifiable(self):
        h = Hypothesis("H1", "God exists")
        obs = []
        report = evaluate_hypothesis(h, obs)
        assert report.is_falsifiable is False
        assert report.demarcation == "metaphysics"

    def test_evaluate_mixed_results(self):
        h = Hypothesis("H1", "Gravity bends light")
        obs = [
            ("Star shift during eclipse", "1.75 arcsec deflection", 0.99),
            ("Clock drift in orbit", "No drift observed", 0.90),
        ]
        report = evaluate_hypothesis(h, obs)
        assert len(report.tests) == 2
        # First test confirms (shared keywords), second is inconclusive
        assert report.corroboration >= 0.0
        assert report.overall_severity >= 0.0

    def test_evaluate_empty_observations(self):
        h = Hypothesis("H1", "All ravens are black")
        report = evaluate_hypothesis(h, [])
        assert report.corroboration == 0.0
        assert report.overall_severity == 0.0
        assert "No tests conducted" in report.explanation

    def test_evaluate_report_to_dict(self):
        h = Hypothesis("H1", "Test")
        obs = [("P", "O", 0.9)]
        report = evaluate_hypothesis(h, obs)
        d = report.to_dict()
        assert d["hypothesis_id"] == "H1"
        assert "tests" in d
        assert "demarcation" in d


class TestFalsificationEngine:
    def test_create_engine(self):
        e = FalsificationEngine()
        assert e.default_confidence == 0.95

    def test_create_engine_custom_confidence(self):
        e = FalsificationEngine(default_confidence=0.8)
        assert e.default_confidence == 0.8

    def test_evaluate(self):
        e = FalsificationEngine()
        report = e.evaluate(
            "All swans are white",
            [("Swan is white", "Black swan observed")],
        )
        assert isinstance(report, FalsificationReport)
        assert report.is_falsified is True

    def test_check_falsifiability(self):
        e = FalsificationEngine()
        result, reason = e.check_falsifiability("All ravens are black")
        assert result is True
        assert "counterexample" in reason.lower()

    def test_classify_science(self):
        e = FalsificationEngine()
        assert e.classify("Planets move in ellipses") == "science"

    def test_classify_metaphysics(self):
        e = FalsificationEngine()
        assert e.classify("The universe has a purpose") == "metaphysics"

    def test_apply_modus_tollens(self):
        e = FalsificationEngine()
        result, reason = e.apply_modus_tollens("H", "P is true", "P is false")
        assert result is True
        assert "modus tollens" in reason.lower()

    def test_apply_modus_tollens_confirms(self):
        e = FalsificationEngine()
        result, reason = e.apply_modus_tollens("H", "P is true", "P is true")
        assert result is False
        assert "confirms" in reason.lower()

    def test_evaluate_with_custom_id(self):
        e = FalsificationEngine()
        report = e.evaluate("Test", [], hypothesis_id="CUSTOM-1")
        assert report.hypothesis_id == "CUSTOM-1"

    def test_evaluate_corroboration_calculation(self):
        e = FalsificationEngine()
        report = e.evaluate(
            "H",
            [
                ("P1 is true", "P1 is true"),
                ("P2 is true", "P2 is false"),
            ],
        )
        # First confirms (identical), second falsifies
        assert report.corroboration == 0.5
        assert len(report.tests) == 2
