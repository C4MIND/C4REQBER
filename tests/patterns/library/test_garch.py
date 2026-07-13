"""
Tests for src/patterns/library/garch.py (GARCH Model pattern)

Covers:
- GARCHPattern initialization
- can_simulate() keyword matching
- _simulate_garch() simulation
- _calculate_confidence()
- estimate_resources()
- run() async integration
- Edge cases: extreme parameters, near-unit-root
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.garch import GARCHPattern


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestGARCHPatternInit:
    def test_init(self):
        pattern = GARCHPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = GARCHPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "periods" in param_names
        assert "omega" in param_names
        assert "alpha" in param_names
        assert "beta" in param_names
        assert "var_confidence" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate Tests
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_garch(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="GARCH model", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_arch(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="ARCH effects", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_volatility(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="Volatility clustering", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_var(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="Value at Risk", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_cvar(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="Conditional VaR", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_financial_risk(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="Financial risk assessment", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_returns(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="Stock returns analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_heteroskedasticity(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="Heteroskedasticity modeling", description="test")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="Neural network", description="deep learning")
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Core Methods Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_valid_persistence(self):
        pattern = GARCHPattern()
        results = {"metrics": {"persistence": 0.95, "mean_volatility": 0.2, "var_95": -0.5}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_high_persistence(self):
        pattern = GARCHPattern()
        results = {"metrics": {"persistence": 1.1, "mean_volatility": 0.2}}  # > 1 is invalid
        confidence = pattern._calculate_confidence(results)
        assert confidence >= 0.0

    def test_low_volatility(self):
        pattern = GARCHPattern()
        results = {"metrics": {"persistence": 0.9, "mean_volatility": 0.01, "var_95": -0.1}}
        confidence = pattern._calculate_confidence(results)
        assert 0.0 <= confidence <= 0.9

    def test_positive_var(self):
        pattern = GARCHPattern()
        results = {"metrics": {"persistence": 0.9, "mean_volatility": 0.2, "var_95": 0.5}}
        confidence = pattern._calculate_confidence(results)
        # VaR should be negative, positive is suspicious
        assert confidence >= 0.0


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation Tests
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = GARCHPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_many_periods(self):
        pattern = GARCHPattern()
        h = Hypothesis(parameters={"periods": 10000})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="GARCH model", description="volatility clustering")
        result = await pattern.run(h, {"periods": 200})
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("garch_")

    async def test_run_with_config(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="GARCH model", description="volatility clustering")
        result = await pattern.run(
            h,
            {
                "periods": 200,
                "omega": 0.00001,
                "alpha": 0.15,
                "beta": 0.8,
            },
        )
        assert result.status == SimulationStatus.COMPLETED

    async def test_metrics_present(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="GARCH model", description="volatility clustering")
        result = await pattern.run(h, {"periods": 200})
        assert result.status == SimulationStatus.COMPLETED
        assert "mean_volatility" in result.metrics
        assert "persistence" in result.metrics
        assert "var_95" in result.metrics

    async def test_logs_present(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="GARCH model", description="volatility clustering")
        result = await pattern.run(h, {"periods": 200})
        assert len(result.logs) > 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_very_few_periods(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="GARCH model", description="volatility clustering")
        result = await pattern.run(h, {"periods": 100})
        assert result.status == SimulationStatus.COMPLETED

    async def test_near_unit_root(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="GARCH model", description="volatility clustering")
        # alpha + beta close to 1
        result = await pattern.run(h, {"periods": 200, "alpha": 0.15, "beta": 0.84})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_alpha(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="GARCH model", description="volatility clustering")
        result = await pattern.run(h, {"periods": 200, "alpha": 0.4})
        assert result.status == SimulationStatus.COMPLETED

    async def test_low_beta(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="GARCH model", description="volatility clustering")
        result = await pattern.run(h, {"periods": 200, "beta": 0.1})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_confidence(self):
        pattern = GARCHPattern()
        h = Hypothesis(title="GARCH model", description="volatility clustering")
        result = await pattern.run(h, {"periods": 200, "var_confidence": 0.99})
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
