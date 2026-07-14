"""
Tests for src/patterns/library/double_pendulum.py
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.double_pendulum import (
    DoublePendulumConfig,
    DoublePendulumPattern,
)


class TestDoublePendulumConfig:
    def test_default_init(self):
        cfg = DoublePendulumConfig()
        assert cfg.m1 == 1.0
        assert cfg.m2 == 1.0
        assert cfg.L1 == 1.0
        assert cfg.L2 == 1.0
        assert cfg.g == 9.81

    def test_custom_init(self):
        cfg = DoublePendulumConfig(m1=2.0, L1=1.5, t_max=20.0)
        assert cfg.m1 == 2.0
        assert cfg.L1 == 1.5
        assert cfg.t_max == 20.0


class TestDoublePendulumPatternInit:
    def test_init(self):
        pattern = DoublePendulumPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = DoublePendulumPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "m1" in param_names
        assert "L1" in param_names
        assert "theta1_0" in param_names


class TestCanSimulate:
    def test_matches_pendulum(self):
        pattern = DoublePendulumPattern()
        h = Hypothesis(title="Double pendulum", description="chaotic dynamics")
        assert pattern.can_simulate(h) is True

    def test_matches_chaos(self):
        pattern = DoublePendulumPattern()
        h = Hypothesis(title="Chaotic system", description="sensitive dependence")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = DoublePendulumPattern()
        h = Hypothesis(title="Linear regression", description="statistics")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_default_parsing(self):
        pattern = DoublePendulumPattern()
        cfg = pattern._parse_config({})
        assert cfg.m1 == 1.0
        assert cfg.L1 == 1.0

    def test_angle_conversion(self):
        pattern = DoublePendulumPattern()
        cfg = pattern._parse_config({"angle": 90.0})
        assert cfg.theta1_0 == pytest.approx(np.pi / 2)


@pytest.mark.asyncio
class TestSimulateDP:
    async def test_simulation_completes(self):
        pattern = DoublePendulumPattern()
        pattern.config = DoublePendulumConfig(t_max=2.0, dt=0.01)
        result = await pattern._simulate_dp()
        assert "metrics" in result
        assert "logs" in result
        assert "time" in result
        assert "x1" in result

    async def test_positions_exist(self):
        pattern = DoublePendulumPattern()
        pattern.config = DoublePendulumConfig(t_max=2.0, dt=0.01)
        result = await pattern._simulate_dp()
        assert len(result["x1"]) > 0
        assert len(result["y1"]) > 0
        assert len(result["x2"]) > 0
        assert len(result["y2"]) > 0

    async def test_energy_negative(self):
        pattern = DoublePendulumPattern()
        pattern.config = DoublePendulumConfig(t_max=2.0, dt=0.01)
        result = await pattern._simulate_dp()
        assert result["metrics"]["initial_energy"] < 0  # Bound state

    async def test_lyapunov_non_negative(self):
        pattern = DoublePendulumPattern()
        pattern.config = DoublePendulumConfig(t_max=5.0, dt=0.01)
        result = await pattern._simulate_dp()
        assert result["metrics"]["max_lyapunov"] >= 0

    async def test_period_estimate(self):
        pattern = DoublePendulumPattern()
        pattern.config = DoublePendulumConfig(t_max=5.0, dt=0.01)
        result = await pattern._simulate_dp()
        assert "period_estimate" in result["metrics"]


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = DoublePendulumPattern()
        results = {
            "metrics": {
                "energy_drift": 0.001,
                "max_lyapunov": 0.5,
                "period_estimate": 2.0,
                "initial_energy": -10.0,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5


class TestEstimateResources:
    def test_default_params(self):
        pattern = DoublePendulumPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert resources["gpu_required"] is False


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = DoublePendulumPattern()
        h = Hypothesis(title="Double pendulum", description="chaos")
        config = {"t_max": 2.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("dp_")


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = DoublePendulumPattern.get_metadata()
        assert meta["id"] == "double_pendulum"
        assert "parameters" in meta


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
