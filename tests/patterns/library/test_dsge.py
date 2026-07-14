"""
Tests for src/patterns/library/dsge.py (DSGE Model pattern)

Covers:
- DSGEPattern initialization
- can_simulate() keyword matching
- _rbc_model() simulation
- _new_keynesian() simulation
- _calculate_confidence()
- estimate_resources()
- run() async integration
- Edge cases: extreme parameters, different model types
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.dsge import DSGEPattern


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestDSGEPatternInit:
    def test_init(self):
        pattern = DSGEPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = DSGEPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "model_type" in param_names
        assert "periods" in param_names
        assert "discount_factor" in param_names
        assert "capital_share" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate Tests
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_dsge(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="DSGE analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_dynamic_stochastic(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="Dynamic stochastic model", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_general_equilibrium(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="General equilibrium", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_business_cycle(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="Business cycle analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_rbc(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC model", description="real business cycle")
        assert pattern.can_simulate(h) is True

    def test_matches_productivity_shock(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="Productivity shock effects", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_monetary_policy(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="Monetary policy impact", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_impulse_response(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="Impulse response function", description="test")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="Neural network", description="deep learning")
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Core Methods Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_reasonable_volatility(self):
        pattern = DSGEPattern()
        results = {
            "metrics": {
                "output_volatility_pct": 3.0,
                "consumption_volatility_pct": 2.0,
                "consumption_output_correlation": 0.8,
                "steady_state_output": 1.5,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_high_consumption_volatility(self):
        pattern = DSGEPattern()
        results = {
            "metrics": {
                "output_volatility_pct": 3.0,
                "consumption_volatility_pct": 5.0,  # Higher than output
                "consumption_output_correlation": 0.8,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence >= 0.0

    def test_negative_correlation(self):
        pattern = DSGEPattern()
        results = {
            "metrics": {
                "output_volatility_pct": 3.0,
                "consumption_volatility_pct": 2.0,
                "consumption_output_correlation": -0.5,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence >= 0.0


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation Tests
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = DSGEPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_long_simulation(self):
        pattern = DSGEPattern()
        h = Hypothesis(parameters={"periods": 1000})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="DSGE analysis", description="business cycle")
        result = await pattern.run(h, {"periods": 50})
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("dsge_")

    async def test_run_rbc(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="DSGE analysis", description="business cycle")
        result = await pattern.run(h, {"model_type": "rbc", "periods": 50})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_new_keynesian(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="DSGE analysis", description="business cycle")
        result = await pattern.run(h, {"model_type": "nk", "periods": 50})
        assert result.status == SimulationStatus.COMPLETED

    async def test_metrics_present_rbc(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="DSGE analysis", description="business cycle")
        result = await pattern.run(h, {"model_type": "rbc", "periods": 50})
        assert result.status == SimulationStatus.COMPLETED
        # RBC should have volatility metrics
        assert "output_volatility_pct" in result.metrics or "model_type" in result.metrics

    async def test_logs_present(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="DSGE analysis", description="business cycle")
        result = await pattern.run(h, {"periods": 50})
        assert len(result.logs) > 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_very_few_periods(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="DSGE analysis", description="business cycle")
        result = await pattern.run(h, {"periods": 10})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_discount_factor(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="DSGE analysis", description="business cycle")
        result = await pattern.run(h, {"periods": 50, "discount_factor": 0.999})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_risk_aversion(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="DSGE analysis", description="business cycle")
        result = await pattern.run(h, {"periods": 50, "risk_aversion": 10.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_low_shock_std(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="DSGE analysis", description="business cycle")
        result = await pattern.run(h, {"periods": 50, "shock_std": 0.001})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_shock_std(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="DSGE analysis", description="business cycle")
        result = await pattern.run(h, {"periods": 50, "shock_std": 0.1})
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
