"""Tests for src/utils/safe_eval.py — SafeExpressionEvaluator."""
from __future__ import annotations

import pytest

from src.utils.safe_eval import SafeExpressionEvaluator, safe_eval


class TestEvaluateSimpleMath:
    def test_addition(self) -> None:
        result = safe_eval("2 + 2")
        assert result == 4

    def test_multiplication(self) -> None:
        result = safe_eval("3 * 7")
        assert result == 21

    def test_complex_expression(self) -> None:
        result = safe_eval("(10 + 2) * 3 / 2")
        assert result == 18.0


class TestRejectsDangerousCode:
    def test_rejects_import(self) -> None:
        with pytest.raises((ValueError, NameError)):
            safe_eval("__import__('os')")

    def test_rejects_exec(self) -> None:
        with pytest.raises((ValueError, NameError)):
            safe_eval("exec('1+1')")

    def test_rejects_dunder(self) -> None:
        with pytest.raises(ValueError):
            safe_eval("().__class__.__bases__")

    def test_rejects_attribute_access(self) -> None:
        with pytest.raises(ValueError):
            safe_eval("[].__class__")

    def test_rejects_empty_expression(self) -> None:
        with pytest.raises(ValueError):
            safe_eval("")


class TestAllowsSafeFunctions:
    def test_abs(self) -> None:
        result = safe_eval("abs(-5)")
        assert result == 5

    def test_min(self) -> None:
        result = safe_eval("min(3, 1, 2)")
        assert result == 1

    def test_max(self) -> None:
        result = safe_eval("max(3, 1, 2)")
        assert result == 3

    def test_sin(self) -> None:
        evaluator = SafeExpressionEvaluator()
        result = evaluator.evaluate("sin(0)")
        assert result == 0.0

    def test_sqrt(self) -> None:
        evaluator = SafeExpressionEvaluator()
        result = evaluator.evaluate("sqrt(16)")
        assert result == 4.0

    def test_variables(self) -> None:
        evaluator = SafeExpressionEvaluator()
        result = evaluator.evaluate("x + y", variables={"x": 10, "y": 5})
        assert result == 15

    def test_comparison(self) -> None:
        result = safe_eval("5 > 3")
        assert result is True

    def test_bool_expression(self) -> None:
        result = safe_eval("(5 > 3) and (2 < 4)")
        assert result is True
