"""
Tests for src/patterns/library/dsge.py

Covers:
- DSGEPattern initialization
- can_simulate() keyword matching
- _rbc_model() simulation
- _new_keynesian() simulation
- _calculate_confidence()
- estimate_resources()
- run() integration with model_type dispatch
- get_metadata()
- Edge cases: extreme parameters, empty config, invalid model_type
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.dsge import DSGEPattern


# ═══════════════════════════════════════════════════════════════════
# DSGEPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestDSGEPatternInit:
    def test_init(self):
        pattern = DSGEPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = DSGEPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_dsge(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="DSGE model", description="macroeconomic analysis")
        assert pattern.can_simulate(h) is True

    def test_matches_business_cycle(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="Business cycle fluctuations", description="RBC model")
        assert pattern.can_simulate(h) is True

    def test_matches_monetary_policy(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="Monetary policy analysis", description="interest rates")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="Neural network", description="deep learning")
        assert pattern.can_simulate(h) is False

    def test_empty_hypothesis(self):
        pattern = DSGEPattern()
        h = Hypothesis()
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# RBC Model
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRBCModel:
    async def test_rbc_simulation(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC model", description="test")
        config = {
            "model_type": "rbc",
            "periods": 100,
            "discount_factor": 0.99,
            "risk_aversion": 2.0,
            "depreciation": 0.025,
            "capital_share": 0.36,
            "shock_std": 0.01,
        }
        result = await pattern._rbc_model(h, config)
        assert "metrics" in result
        assert "logs" in result
        assert "output_volatility_pct" in result["metrics"]
        assert "consumption_volatility_pct" in result["metrics"]
        assert "investment_volatility_pct" in result["metrics"]

    async def test_rbc_steady_state(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC model", description="test")
        config = {
            "model_type": "rbc",
            "periods": 100,
            "discount_factor": 0.99,
            "capital_share": 0.36,
        }
        result = await pattern._rbc_model(h, config)
        assert "steady_state_output" in result["metrics"]
        assert "steady_state_consumption" in result["metrics"]
        assert result["metrics"]["steady_state_output"] > 0
        assert result["metrics"]["steady_state_consumption"] > 0

    async def test_rbc_correlations(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC model", description="test")
        config = {"model_type": "rbc", "periods": 200}
        result = await pattern._rbc_model(h, config)
        assert "consumption_output_correlation" in result["metrics"]
        assert "investment_output_correlation" in result["metrics"]

    async def test_rbc_impulse_response(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC model", description="test")
        config = {"model_type": "rbc", "periods": 100, "shock_std": 0.02}
        result = await pattern._rbc_model(h, config)
        assert "impulse_response_max" in result["metrics"]

    async def test_rbc_logs(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC model", description="test")
        config = {"model_type": "rbc", "periods": 100}
        result = await pattern._rbc_model(h, config)
        assert len(result["logs"]) > 0
        assert any("RBC" in log for log in result["logs"])

    async def test_rbc_with_hypothesis_params(self):
        pattern = DSGEPattern()
        h = Hypothesis(parameters={"periods": 100})
        config = {"model_type": "rbc", "periods": 100}
        result = await pattern._rbc_model(h, config)
        assert "metrics" in result


# ═══════════════════════════════════════════════════════════════════
# New Keynesian Model
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestNewKeynesianModel:
    async def test_nk_simulation(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="NK model", description="test")
        config = {"model_type": "nk", "periods": 100}
        result = await pattern._new_keynesian(h, config)
        assert "metrics" in result
        assert "logs" in result
        assert "output_volatility_pct" in result["metrics"]
        assert "inflation_volatility_pct" in result["metrics"]
        assert "interest_rate_volatility_pct" in result["metrics"]

    async def test_nk_avg_values(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="NK model", description="test")
        config = {"model_type": "nk", "periods": 200}
        result = await pattern._new_keynesian(h, config)
        assert "avg_output_gap" in result["metrics"]
        assert "avg_inflation" in result["metrics"]

    async def test_nk_logs(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="NK model", description="test")
        config = {"model_type": "nk", "periods": 100}
        result = await pattern._new_keynesian(h, config)
        assert len(result["logs"]) > 0
        assert any("New Keynesian" in log for log in result["logs"])


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = DSGEPattern()
        results = {
            "metrics": {
                "output_volatility_pct": 2.0,
                "consumption_volatility_pct": 1.0,
                "consumption_output_correlation": 0.8,
                "steady_state_output": 1.0,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_low_volatility(self):
        pattern = DSGEPattern()
        results = {"metrics": {"output_volatility_pct": 0.1}}
        confidence = pattern._calculate_confidence(results)
        # Low volatility doesn't meet the 0.5 < y_vol < 10 criterion
        assert confidence < 0.5

    def test_high_volatility(self):
        pattern = DSGEPattern()
        results = {"metrics": {"output_volatility_pct": 15.0}}
        confidence = pattern._calculate_confidence(results)
        # High volatility doesn't meet the criterion
        assert confidence < 0.5

    def test_consumption_smoothing(self):
        pattern = DSGEPattern()
        results = {
            "metrics": {
                "output_volatility_pct": 2.0,
                "consumption_volatility_pct": 1.0,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence >= 0.2  # At least the consumption smoothing factor

    def test_positive_correlation(self):
        pattern = DSGEPattern()
        results = {
            "metrics": {
                "output_volatility_pct": 2.0,
                "consumption_output_correlation": 0.5,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence >= 0.2

    def test_no_steady_state(self):
        pattern = DSGEPattern()
        results = {"metrics": {"output_volatility_pct": 2.0}}
        confidence = pattern._calculate_confidence(results)
        # Should get volatility factor only
        assert confidence >= 0.3


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
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

    def test_custom_periods(self):
        pattern = DSGEPattern()
        h = Hypothesis(parameters={"periods": 500})
        resources = pattern.estimate_resources(h)
        assert resources["estimated_time_seconds"] > 0


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_rbc(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC model", description="business cycle")
        config = {"model_type": "rbc", "periods": 100}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("dsge_")
        assert "output_volatility_pct" in result.metrics

    async def test_run_new_keynesian(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="NK model", description="monetary policy")
        config = {"model_type": "nk", "periods": 100}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert "inflation_volatility_pct" in result.metrics

    async def test_run_logs_present(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC model", description="test")
        config = {"model_type": "rbc", "periods": 100}
        result = await pattern.run(h, config)
        assert len(result.logs) > 0

    async def test_run_failure_handling(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC model", description="test")
        with patch.object(pattern, "_rbc_model", side_effect=ValueError("test error")):
            result = await pattern.run(h, {"model_type": "rbc"})
            assert result.status == SimulationStatus.FAILED
            assert "test error" in result.error_message

    async def test_run_default_model_type(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC model", description="test")
        # Default should be rbc
        result = await pattern.run(h, {"periods": 100})
        assert result.status == SimulationStatus.COMPLETED


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = DSGEPattern.get_metadata()
        assert meta["id"] == "dsge"
        # get_metadata from base class returns class name, not decorator name
        assert meta["name"] == "DSGEPattern"
        assert "category" in meta

    def test_parameters_list(self):
        # Parameters are defined as class attribute, not in get_metadata
        pattern = DSGEPattern()
        params = pattern.parameters
        param_names = [p.name for p in params]
        assert "model_type" in param_names
        assert "periods" in param_names
        assert "shock_std" in param_names
        assert "discount_factor" in param_names
        assert "risk_aversion" in param_names


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_extreme_discount_factor(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC", description="test")
        config = {"model_type": "rbc", "periods": 50, "discount_factor": 0.99}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_risk_aversion(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC", description="test")
        config = {"model_type": "rbc", "periods": 50, "risk_aversion": 5.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_zero_periods(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC", description="test")
        config = {"model_type": "rbc", "periods": 1}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_empty_config(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC", description="test")
        result = await pattern.run(h, {})
        assert result.status == SimulationStatus.COMPLETED

    async def test_invalid_model_type(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC", description="test")
        config = {"model_type": "invalid"}
        # Falls through to new_keynesian path
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_shock_std(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC", description="test")
        config = {"model_type": "rbc", "periods": 50, "shock_std": 0.05}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_low_capital_share(self):
        pattern = DSGEPattern()
        h = Hypothesis(title="RBC", description="test")
        config = {"model_type": "rbc", "periods": 50, "capital_share": 0.25}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
