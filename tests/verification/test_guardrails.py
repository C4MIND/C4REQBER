from __future__ import annotations

import pytest

from src.verification.guardrails import (
    BACKEND_GUARDS,
    estimate_complexity,
    preflight_check,
)


EXPECTED_BACKENDS = {
    "lean4",
    "coq",
    "dafny",
    "agda",
    "z3",
    "cvc5",
    "hoare",
    "haskell-typecheck",
    "haskell-quickcheck",
    "alloy",
    "tla",
}

EXPECTED_PREFLIGHT_KEYS = {
    "backend",
    "complexity",
    "risks",
    "skip",
    "fallback_to_z3",
    "recommendation",
}


class TestEstimateComplexity:
    def test_returns_valid_range(self) -> None:
        code = "lemma id (x : Nat) : x = x := rfl"
        score = estimate_complexity(code, "lean4")
        assert 0.0 <= score <= 1.0

    def test_simple_claim_low_complexity(self) -> None:
        code = "def add (a b : Nat) : Nat := a + b"
        score = estimate_complexity(code, "lean4")
        assert score < 0.3

    def test_complex_with_simp_higher_complexity(self) -> None:
        simple = estimate_complexity("def add (a b : Nat) : Nat := a + b", "lean4")
        complex_long = """lemma complex (x y z : Nat) (h : forall n, n > 0 -> exists m, m = n)
            : (x + y) + z = x + (y + z) := by
          induction x with
          | zero =>
            simp
            apply rfl
          | succ n ih =>
            induction y with
            | zero =>
              simp
              rw [Nat.zero_add]
              apply rfl
            | succ m ihm =>
              simp
              rw [ih, ihm]
              apply rfl"""
        score = estimate_complexity(complex_long, "lean4")
        assert score > simple


class TestPreflightCheck:
    def test_has_all_expected_keys(self) -> None:
        result = preflight_check("lemma id (x : Nat) : x = x := rfl", "lean4")
        assert set(result.keys()) == EXPECTED_PREFLIGHT_KEYS


class TestBackendGuards:
    def test_has_all_backends(self) -> None:
        assert set(BACKEND_GUARDS.keys()) == EXPECTED_BACKENDS
