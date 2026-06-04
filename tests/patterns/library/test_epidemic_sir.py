"""
Tests for src/patterns/library/epidemic_sir.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.epidemic_sir import (
    SIREpidemicPattern,
    SIRConfig,
)
from src.patterns.core import Hypothesis, SimulationStatus



class TestSIRConfig:
    def test_default_init(self):
        cfg = SIRConfig()
        assert cfg.N == 1000000.0
        assert cfg.beta == 0.3
        assert cfg.gamma == 0.1

    def test_custom_init(self):
        cfg = SIRConfig(N=10000, beta=0.5, gamma=0.2)
        assert cfg.N == 10000
        assert cfg.beta == 0.5


class TestSIREpidemicPatternInit:
    def test_init(self):
        pattern = SIREpidemicPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = SIREpidemicPattern()
        param_names = [p.name for p in pattern.parameters]
        assert "beta" in param_names
        assert "gamma" in param_names


class TestCanSimulate:
    def test_matches_sir(self):
        pattern = SIREpidemicPattern()
        h = Hypothesis(title="SIR model", description="epidemic")
        assert pattern.can_simulate(h) is True

    def test_matches_r0(self):
        pattern = SIREpidemicPattern()
        h = Hypothesis(title="Basic reproduction number", description="herd immunity")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = SIREpidemicPattern()
        h = Hypothesis(title="Stock market", description="trading")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_default_parsing(self):
        pattern = SIREpidemicPattern()
        cfg = pattern._parse_config({})
        assert cfg.N == 1000000.0

    def test_custom_parsing(self):
        pattern = SIREpidemicPattern()
        cfg = pattern._parse_config({"N": 10000, "beta": 0.5, "gamma": 0.2})
        assert cfg.N == 10000
        assert cfg.beta == 0.5


@pytest.mark.asyncio
class TestSimulateSIR:
    async def test_simulation_completes(self):
        pattern = SIREpidemicPattern()
        pattern.config = SIRConfig(N=10000, t_max=50.0)
        result = await pattern._simulate_sir()
        assert "metrics" in result
        assert "logs" in result
        assert "S" in result
        assert "I" in result
        assert "R" in result

    async def test_r0_calculation(self):
        pattern = SIREpidemicPattern()
        pattern.config = SIRConfig(N=10000, beta=0.3, gamma=0.1, t_max=50.0)
        result = await pattern._simulate_sir()
        assert result["metrics"]["R0"] == pytest.approx(3.0, abs=0.01)

    async def test_peak_infections(self):
        pattern = SIREpidemicPattern()
        pattern.config = SIRConfig(N=10000, beta=0.3, gamma=0.1, t_max=100.0)
        result = await pattern._simulate_sir()
        assert result["metrics"]["peak_infections"] > 0

    async def test_attack_rate(self):
        pattern = SIREpidemicPattern()
        pattern.config = SIRConfig(N=10000, beta=0.3, gamma=0.1, t_max=100.0)
        result = await pattern._simulate_sir()
        assert 0 < result["metrics"]["attack_rate"] < 1

    async def test_herd_immunity(self):
        pattern = SIREpidemicPattern()
        pattern.config = SIRConfig(N=10000, beta=0.3, gamma=0.1, t_max=100.0)
        result = await pattern._simulate_sir()
        assert result["metrics"]["herd_immunity_threshold"] == pytest.approx(2/3, abs=0.01)

    async def test_conservation(self):
        pattern = SIREpidemicPattern()
        pattern.config = SIRConfig(N=10000, beta=0.3, gamma=0.1, t_max=50.0)
        result = await pattern._simulate_sir()
        S = np.array(result["S"])
        I = np.array(result["I"])
        R = np.array(result["R"])
        total = S + I + R
        assert np.allclose(total, total[0], rtol=0.01)

    async def test_r0_less_than_one_no_epidemic(self):
        pattern = SIREpidemicPattern()
        pattern.config = SIRConfig(N=10000, beta=0.05, gamma=0.1, t_max=50.0)
        result = await pattern._simulate_sir()
        assert result["metrics"]["R0"] < 1.0
        assert result["metrics"]["peak_infections"] < 100  # Small peak


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = SIREpidemicPattern()
        results = {"metrics": {"R0": 3.0, "peak_infections": 1000, "attack_rate": 0.5, "herd_immunity_threshold": 0.67, "generation_time_days": 10}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = SIREpidemicPattern()
        h = Hypothesis(title="SIR model", description="epidemic")
        config = {"N": 10000, "t_max": 50.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = SIREpidemicPattern.get_metadata()
        assert meta["id"] == "epidemic_sir"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
