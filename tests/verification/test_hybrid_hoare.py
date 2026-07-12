"""HybridVerifier Hoare compile contract must match retry loop expectations."""
from __future__ import annotations

import pytest

z3 = pytest.importorskip("z3")

from src.verification.hybrid_verifier import HybridVerifier


def test_compile_hoare_valid_returns_success_status() -> None:
    hv = HybridVerifier()
    result = hv._compile_hoare("{x >= 0} x := x + 1 {x >= 1}")
    assert result["status"] == "success"
    assert result["error"] == ""


def test_compile_hoare_invalid_returns_error_key() -> None:
    hv = HybridVerifier()
    result = hv._compile_hoare("{x >= 0} x := x - 1 {x >= 1}")
    assert result["status"] == "error"
    assert result["error"]
