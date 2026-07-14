"""Tests for Falsification Engine — Popper module."""

from __future__ import annotations

import pytest

from src.falsification.popper import (
    FalsificationResult,
    FalsificationTest,
    run_falsification,
)


class TestFalsificationTest:
    def test_create_test(self):
        t = FalsificationTest(
            hypothesis="H",
            prediction="P",
            test_result="confirmed",
            confidence=0.95,
        )
        assert t.hypothesis == "H"
        assert t.prediction == "P"
        assert t.test_result == "confirmed"
        assert t.confidence == 0.95

    def test_falsified_test(self):
        t = FalsificationTest(
            hypothesis="H",
            prediction="P",
            test_result="falsified",
            confidence=0.99,
        )
        assert t.test_result == "falsified"

    def test_inconclusive_test(self):
        t = FalsificationTest(
            hypothesis="H",
            prediction="P",
            test_result="inconclusive",
            confidence=0.3,
        )
        assert t.test_result == "inconclusive"


class TestFalsificationResult:
    def test_default_values(self):
        fr = FalsificationResult(hypothesis="H0")
        assert fr.hypothesis == "H0"
        assert fr.tests == []
        assert fr.is_falsified is False
        assert fr.corroboration == 0.0

    def test_with_tests(self):
        tests = [
            FalsificationTest(hypothesis="H", prediction="P1", test_result="confirmed", confidence=0.9),
        ]
        fr = FalsificationResult(hypothesis="H", tests=tests, is_falsified=False, corroboration=0.5)
        assert len(fr.tests) == 1
        assert fr.corroboration == 0.5


class TestRunFalsification:
    def test_all_confirmed(self):
        result = run_falsification(
            hypothesis="All swans are white",
            predictions=["Swan A is white", "Swan B is white"],
            results=[("confirmed", 0.95), ("confirmed", 0.90)],
        )
        assert result.is_falsified is False
        assert result.corroboration == 1.0
        assert len(result.tests) == 2

    def test_one_falsified(self):
        result = run_falsification(
            hypothesis="All swans are white",
            predictions=["Swan A is white", "Swan B is black"],
            results=[("confirmed", 0.95), ("falsified", 0.99)],
        )
        assert result.is_falsified is True
        assert result.corroboration == 0.5

    def test_all_falsified(self):
        result = run_falsification(
            hypothesis="Cold fusion works",
            predictions=["Excess heat at 25C", "Neutron emission"],
            results=[("falsified", 0.99), ("falsified", 0.99)],
        )
        assert result.is_falsified is True
        assert result.corroboration == 0.0

    def test_empty_predictions(self):
        result = run_falsification(
            hypothesis="Untestable claim",
            predictions=[],
            results=[],
        )
        assert result.is_falsified is False
        assert result.corroboration == 0.0
        assert result.tests == []

    def test_mixed_results(self):
        result = run_falsification(
            hypothesis="Gravity bends light",
            predictions=["Solar eclipse deflection", "Galaxy lensing", "Clock drift"],
            results=[("confirmed", 0.95), ("confirmed", 0.90), ("inconclusive", 0.50)],
        )
        assert result.is_falsified is False
        assert len(result.tests) == 3
        assert result.corroboration == pytest.approx(2 / 3)

    def test_single_prediction_falsified(self):
        result = run_falsification(
            hypothesis="Earth is flat",
            predictions=["No curvature observed at sea"],
            results=[("falsified", 1.0)],
        )
        assert result.is_falsified is True
        assert result.corroboration == 0.0

    def test_corroboration_only_counts_confirmed(self):
        result = run_falsification(
            hypothesis="H",
            predictions=["P1", "P2", "P3", "P4"],
            results=[
                ("confirmed", 0.9),
                ("falsified", 0.9),
                ("inconclusive", 0.5),
                ("confirmed", 0.8),
            ],
        )
        assert result.corroboration == 0.5

    def test_reproduces_popper_logic(self):
        result = run_falsification(
            hypothesis="Einstein's general relativity",
            predictions=[
                "Mercury perihelion precession",
                "Light bending during eclipse",
                "Gravitational redshift",
            ],
            results=[("confirmed", 0.99), ("confirmed", 0.99), ("confirmed", 0.99)],
        )
        assert result.is_falsified is False
        assert result.corroboration == 1.0
