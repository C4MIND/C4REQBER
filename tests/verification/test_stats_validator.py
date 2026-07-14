"""Tests for StatisticalValidator."""
from __future__ import annotations

import importlib
import sys

import pytest

from src.verification.stats_validator import StatisticalValidator


@pytest.fixture(autouse=True)
def _restore_real_scipy():
    """Restore real scipy in sys.modules for stats tests.

    Some earlier tests mock scipy globally in sys.modules; we need the
    real thing for statistical validation.
    """
    saved = {}
    keys = [k for k in sys.modules if k == "scipy" or k.startswith("scipy.")]
    for k in keys:
        saved[k] = sys.modules.pop(k)
    # Force re-import of the real scipy package
    try:
        import scipy.stats  # noqa: F401
    except Exception:
        pass
    yield
    # Restore whatever was there before
    for k in keys:
        if k in sys.modules:
            del sys.modules[k]
    for k, v in saved.items():
        sys.modules[k] = v


@pytest.fixture
def validator():
    return StatisticalValidator()


class TestStatisticalValidator:
    def test_available(self, validator):
        assert validator.available is True

    @pytest.mark.anyio(backend="asyncio")
    async def test_ttest_verified(self, validator):
        result = await validator.verify(
            "Group A mean differs from Group B",
            context={
                "test_type": "ttest",
                "group_a": [1.0, 2.0, 3.0, 2.5, 2.0],
                "group_b": [10.0, 11.0, 12.0, 10.5, 11.5],
                "alpha": 0.05,
            },
        )
        assert result["status"] == "verified"
        assert result["confidence"] > 0.95
        assert "t-statistic" in result["proof_output"]

    @pytest.mark.anyio(backend="asyncio")
    async def test_ttest_rejected(self, validator):
        result = await validator.verify(
            "Group A mean differs from Group B",
            context={
                "test_type": "ttest",
                "group_a": [1.0, 2.0, 3.0],
                "group_b": [1.1, 2.1, 3.1],
                "alpha": 0.05,
            },
        )
        assert result["status"] == "rejected"

    @pytest.mark.anyio(backend="asyncio")
    async def test_no_data(self, validator):
        result = await validator.verify("Some hypothesis", context={})
        assert result["status"] == "uncertain"
        assert "No data" in result["error_message"]

    @pytest.mark.anyio(backend="asyncio")
    async def test_correlation_verified(self, validator):
        result = await validator.verify(
            "X and Y are positively correlated",
            context={
                "test_type": "correlation",
                "x": [1, 2, 3, 4, 5],
                "y": [2, 4, 6, 8, 10],
                "alpha": 0.05,
            },
        )
        assert result["status"] == "verified"
        assert result["confidence"] > 0.95

    @pytest.mark.anyio(backend="asyncio")
    async def test_chi2(self, validator):
        result = await validator.verify(
            "Variables are dependent",
            context={
                "test_type": "chi2",
                "observed": [[10, 10, 20], [20, 5, 15]],
                "alpha": 0.05,
            },
        )
        assert result["status"] in ("verified", "rejected")
        assert result["proof_output"].startswith("chi2=")
