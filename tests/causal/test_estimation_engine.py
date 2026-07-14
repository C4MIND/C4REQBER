"""Tests for CausalEstimationEngine."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.causal.estimation_engine import CausalEstimationEngine, EstimationResult


class TestEstimationResult:
    def test_to_dict_valid(self) -> None:
        r = EstimationResult(ate=1.5, ci_lower=1.0, ci_upper=2.0, method="test", treatment="T", outcome="Y")
        d = r.to_dict()
        assert d["ate"] == 1.5
        assert d["valid"] is True

    def test_to_dict_invalid(self) -> None:
        r = EstimationResult(ate=0.0, ci_lower=0.0, ci_upper=0.0, method="test", treatment="T", outcome="Y", valid=False, error="fail")
        d = r.to_dict()
        assert d["ate"] is None
        assert d["error"] == "fail"


class TestCausalEstimationEngine:
    @pytest.fixture
    def engine(self) -> CausalEstimationEngine:
        return CausalEstimationEngine()

    @pytest.fixture
    def simple_data(self) -> pd.DataFrame:
        """Simple data where T=1 adds 2.0 to Y."""
        rng = np.random.default_rng(42)
        n = 200
        c = rng.normal(0, 1, n)
        t = (c + rng.normal(0, 0.5, n) > 0).astype(int)
        y = 2.0 * t + 1.0 * c + rng.normal(0, 0.3, n)
        return pd.DataFrame({"T": t, "Y": y, "C": c})

    def test_estimate_ate_basic(self, engine: CausalEstimationEngine, simple_data: pd.DataFrame) -> None:
        result = engine.estimate_ate(simple_data, "T", "Y", ["C"], method="backdoor.linear_regression")
        assert result.valid is True
        assert result.ate > 1.0  # Should be close to 2.0
        assert result.ci_lower < result.ate < result.ci_upper

    def test_missing_columns(self, engine: CausalEstimationEngine) -> None:
        df = pd.DataFrame({"A": [1, 2, 3]})
        result = engine.estimate_ate(df, "T", "Y", ["C"])
        assert result.valid is False
        assert "Missing columns" in result.error

    def test_unknown_method(self, engine: CausalEstimationEngine, simple_data: pd.DataFrame) -> None:
        result = engine.estimate_ate(simple_data, "T", "Y", ["C"], method="unknown")
        assert result.valid is False
        assert "Unknown method" in result.error

    def test_build_graph(self, engine: CausalEstimationEngine) -> None:
        graph = engine._build_graph("T", "Y", ["C1", "C2"])
        assert "C1 -> T" in graph
        assert "C2 -> Y" in graph
        assert "T -> Y" in graph
