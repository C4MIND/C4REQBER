"""Tests for src/bayesian/models.py."""


import pytest

from src.bayesian.models import (
    BMAResult,
    DSTResult,
    FuzzyResult,
    MCMCSample,
    Model,
    OptimizationResult,
)


class TestMCMCSample:
    def test_create_default(self):
        s = MCMCSample(samples=[1.0, 2.0], acceptance_rate=0.5, mean=1.5, std=0.5)
        assert s.samples == [1.0, 2.0]
        assert s.acceptance_rate == 0.5
        assert s.mean == 1.5
        assert s.std == 0.5

    def test_empty_samples(self):
        s = MCMCSample(samples=[], acceptance_rate=0.0, mean=0.0, std=0.0)
        assert s.samples == []
        assert s.mean == 0.0


class TestBMAResult:
    def test_create(self):
        m = Model(name="M1", posterior_prob=0.6, prediction=2.0)
        r = BMAResult(models=[m], weighted_prediction=2.0, uncertainty=0.3)
        assert len(r.models) == 1
        assert r.weighted_prediction == 2.0
        assert r.uncertainty == 0.3

    def test_multiple_models(self):
        m1 = Model(name="M1", posterior_prob=0.3, prediction=1.0)
        m2 = Model(name="M2", posterior_prob=0.7, prediction=3.0)
        r = BMAResult(models=[m1, m2], weighted_prediction=2.4, uncertainty=0.9)
        assert len(r.models) == 2
        assert r.models[0].name == "M1"


class TestOptimizationResult:
    def test_create(self):
        r = OptimizationResult(best_x=0.5, best_y=0.1, history=[(0.5, 0.1)], iterations=10)
        assert r.best_x == 0.5
        assert r.best_y == 0.1
        assert r.iterations == 10
        assert len(r.history) == 1

    def test_default_factory(self):
        r = OptimizationResult(best_x=0.0, best_y=0.0)
        assert r.history == []
        assert r.iterations == 0


class TestDSTResult:
    def test_create(self):
        r = DSTResult(belief={"A": 0.3}, plausibility={"A": 0.7}, conflict=0.2)
        assert r.belief == {"A": 0.3}
        assert r.plausibility == {"A": 0.7}
        assert r.conflict == 0.2

    def test_multiple_elements(self):
        r = DSTResult(
            belief={"A": 0.2, "B": 0.4},
            plausibility={"A": 0.8, "B": 0.6},
            conflict=0.1,
        )
        assert len(r.belief) == 2
        assert r.belief["B"] == 0.4


class TestFuzzyResult:
    def test_create(self):
        r = FuzzyResult(crisp_output=12.5, membership_values={"hot": 0.8}, rule_strengths=[0.6])
        assert r.crisp_output == 12.5
        assert r.membership_values == {"hot": 0.8}
        assert r.rule_strengths == [0.6]

    def test_empty_rules(self):
        r = FuzzyResult(crisp_output=0.0, membership_values={}, rule_strengths=[])
        assert r.rule_strengths == []
