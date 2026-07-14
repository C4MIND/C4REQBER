"""Tests for src/bayesian/fuzzy.py."""

from __future__ import annotations

import numpy as np
import pytest

from src.bayesian.fuzzy import (
    FuzzyCognitiveMap,
    FuzzySet,
    FuzzyVariable,
    MamdaniInference,
    gaussian,
    trapezoidal,
    triangular,
)


class TestFuzzySet:
    def test_call(self):
        tri = triangular(0.0, 5.0, 10.0)
        fs = FuzzySet("test", tri)
        x = np.array([5.0])
        result = fs(x)
        assert result[0] == pytest.approx(1.0, abs=0.01)

    def test_and_operator(self):
        tri = triangular(0.0, 5.0, 10.0)
        fs1 = FuzzySet("low", tri)
        fs2 = FuzzySet("high", tri)
        combined = fs1 & fs2
        x = np.array([5.0])
        result = combined(x)
        assert 0.0 <= result[0] <= 1.0

    def test_or_operator(self):
        tri = triangular(0.0, 5.0, 10.0)
        fs1 = FuzzySet("low", tri)
        fs2 = FuzzySet("high", tri)
        combined = fs1 | fs2
        x = np.array([5.0])
        result = combined(x)
        assert result[0] == pytest.approx(1.0, abs=0.01)

    def test_not_operator(self):
        tri = triangular(0.0, 5.0, 10.0)
        fs = FuzzySet("test", tri)
        neg = ~fs
        x = np.array([5.0])
        result = neg(x)
        assert result[0] == pytest.approx(0.0, abs=0.01)


class TestTriangularMF:
    def test_peak(self):
        mf = triangular(0.0, 5.0, 10.0)
        assert mf(np.array([5.0]))[0] == pytest.approx(1.0, abs=0.01)

    def test_boundaries(self):
        mf = triangular(0.0, 5.0, 10.0)
        assert mf(np.array([0.0]))[0] == pytest.approx(0.0, abs=0.01)
        assert mf(np.array([10.0]))[0] == pytest.approx(0.0, abs=0.01)

    def test_between(self):
        mf = triangular(0.0, 5.0, 10.0)
        assert mf(np.array([2.5]))[0] == pytest.approx(0.5, abs=0.01)


class TestTrapezoidalMF:
    def test_plateau(self):
        mf = trapezoidal(0.0, 3.0, 7.0, 10.0)
        result = mf(np.array([5.0]))
        assert result[0] == pytest.approx(1.0, abs=0.01)

    def test_boundaries(self):
        mf = trapezoidal(0.0, 3.0, 7.0, 10.0)
        assert mf(np.array([0.0]))[0] == pytest.approx(0.0, abs=0.01)
        assert mf(np.array([10.0]))[0] == pytest.approx(0.0, abs=0.01)


class TestGaussianMF:
    def test_center(self):
        mf = gaussian(5.0, 1.0)
        assert mf(np.array([5.0]))[0] == pytest.approx(1.0, abs=0.01)

    def test_tail(self):
        mf = gaussian(5.0, 1.0)
        result = mf(np.array([10.0]))
        assert 0.0 < result[0] < 0.01


class TestFuzzyVariable:
    def test_fuzzify(self):
        var = FuzzyVariable("temperature", np.linspace(0, 100, 101))
        var.add_term("low", triangular(0, 0, 50))
        var.add_term("high", triangular(50, 100, 100))
        memberships = var.fuzzify(25.0)
        assert "low" in memberships
        assert "high" in memberships
        assert memberships["low"] > memberships["high"]

    def test_fuzzify_peak(self):
        var = FuzzyVariable("speed", np.linspace(0, 10, 11))
        var.add_term("fast", triangular(5, 10, 10))
        memberships = var.fuzzify(10.0)
        assert memberships["fast"] == pytest.approx(1.0, abs=0.01)


class TestMamdaniInference:
    def test_infer_centroid(self):
        universe = np.linspace(0, 10, 100)
        antecedent = FuzzySet("hot", triangular(0, 5, 10))
        consequent = FuzzySet("fan_speed", triangular(0, 10, 10))

        rule = antecedent & FuzzySet("dummy", lambda x: np.ones_like(x))
        from src.bayesian.fuzzy import FuzzyRule

        fuzzy_rule = FuzzyRule(rule, consequent, universe)
        engine = MamdaniInference()
        engine.add_rule(fuzzy_rule)

        result = engine.infer([0.5])
        assert result > 0.0

    def test_infer_raises_mismatch(self):
        universe = np.linspace(0, 1, 10)
        antecedent = FuzzySet("x", triangular(0, 0.5, 1))
        consequent = FuzzySet("y", triangular(0, 0.5, 1))
        from src.bayesian.fuzzy import FuzzyRule

        fuzzy_rule = FuzzyRule(antecedent, consequent, universe)
        engine = MamdaniInference()
        engine.add_rule(fuzzy_rule)
        with pytest.raises(ValueError, match="Firing strengths"):
            engine.infer([0.5, 0.3])


class TestFuzzyCognitiveMap:
    def test_create_and_set(self):
        fcm = FuzzyCognitiveMap(["A", "B"])
        fcm.set_weight("A", "B", 0.5)
        fcm.set_state("A", 0.8)
        assert fcm.get_state("A") == pytest.approx(0.8)

    def test_update_sigmoid(self):
        fcm = FuzzyCognitiveMap(["A", "B"])
        fcm.set_weight("A", "B", 1.0)
        fcm.set_state("A", 0.5)
        fcm.update(iterations=5, activation="sigmoid", lambda_param=2.0)
        assert 0.0 <= fcm.get_state("B") <= 1.0

    def test_steady_state(self):
        fcm = FuzzyCognitiveMap(["A", "B"])
        fcm.set_weight("A", "B", 0.3)
        fcm.set_state("A", 1.0)
        result = fcm.steady_state(tol=1e-6, max_iter=100)
        assert result.shape == (2,)

    def test_scenario_analysis(self):
        fcm = FuzzyCognitiveMap(["A", "B", "C"])
        fcm.set_weight("A", "B", 0.5)
        fcm.set_weight("B", "C", 0.5)
        fcm.set_state("A", 1.0)
        result = fcm.scenario_analysis({"A": 1.0}, iterations=10)
        assert "A" in result
        assert "B" in result
        assert "C" in result
