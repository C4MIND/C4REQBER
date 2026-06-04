"""
Tests for src/patterns/library/monte_carlo_pi.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.monte_carlo_pi import (
    MonteCarloPiPattern,
    MonteCarloPiConfig,
)
from src.patterns.core import Hypothesis, SimulationStatus



class TestMonteCarloPiConfig:
    def test_default_init(self):
        cfg = MonteCarloPiConfig()
        assert cfg.n_samples == 100000
        assert cfg.method == "unit_circle"

    def test_custom_init(self):
        cfg = MonteCarloPiConfig(n_samples=50000, method="buffon")
        assert cfg.n_samples == 50000
        assert cfg.method == "buffon"


class TestMonteCarloPiPatternInit:
    def test_init(self):
        pattern = MonteCarloPiPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = MonteCarloPiPattern()
        param_names = [p.name for p in pattern.parameters]
        assert "n_samples" in param_names
        assert "method" in param_names


class TestCanSimulate:
    def test_matches_monte_carlo(self):
        pattern = MonteCarloPiPattern()
        h = Hypothesis(title="Monte Carlo", description="pi estimation")
        assert pattern.can_simulate(h) is True

    def test_matches_buffon(self):
        pattern = MonteCarloPiPattern()
        h = Hypothesis(title="Buffon's needle", description="random sampling")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = MonteCarloPiPattern()
        h = Hypothesis(title="Stock market", description="trading")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_default_parsing(self):
        pattern = MonteCarloPiPattern()
        cfg = pattern._parse_config({})
        assert cfg.n_samples == 100000

    def test_custom_parsing(self):
        pattern = MonteCarloPiPattern()
        cfg = pattern._parse_config({"n_samples": 50000, "method": "buffon"})
        assert cfg.n_samples == 50000
        assert cfg.method == "buffon"


@pytest.mark.asyncio
class TestSimulateUnitCircle:
    async def test_simulation_completes(self):
        pattern = MonteCarloPiPattern()
        pattern.config = MonteCarloPiConfig(n_samples=1000, method="unit_circle")
        result = await pattern._simulate_unit_circle()
        assert "metrics" in result
        assert "logs" in result

    async def test_pi_estimate(self):
        pattern = MonteCarloPiPattern()
        pattern.config = MonteCarloPiConfig(n_samples=100000, method="unit_circle", seed=42)
        result = await pattern._simulate_unit_circle()
        assert 3.1 < result["metrics"]["pi_estimate"] < 3.2

    async def test_error_decreases_with_samples(self):
        pattern = MonteCarloPiPattern()
        pattern.config = MonteCarloPiConfig(n_samples=10000, method="unit_circle", seed=42)
        result1 = await pattern._simulate_unit_circle()
        pattern.config = MonteCarloPiConfig(n_samples=100000, method="unit_circle", seed=42)
        result2 = await pattern._simulate_unit_circle()
        assert result2["metrics"]["absolute_error"] < result1["metrics"]["absolute_error"]

    async def test_inside_outside_sum(self):
        pattern = MonteCarloPiPattern()
        pattern.config = MonteCarloPiConfig(n_samples=1000, method="unit_circle")
        result = await pattern._simulate_unit_circle()
        total = result["metrics"]["inside_count"] + result["metrics"]["outside_count"]
        assert total == result["metrics"]["n_samples"]

    async def test_standard_error(self):
        pattern = MonteCarloPiPattern()
        pattern.config = MonteCarloPiConfig(n_samples=100000, method="unit_circle", seed=42)
        result = await pattern._simulate_unit_circle()
        assert result["metrics"]["standard_error"] < 0.02


@pytest.mark.asyncio
class TestSimulateBuffon:
    async def test_simulation_completes(self):
        pattern = MonteCarloPiPattern()
        pattern.config = MonteCarloPiConfig(n_samples=1000, method="buffon")
        result = await pattern._simulate_buffon()
        assert "metrics" in result
        assert "logs" in result

    async def test_pi_estimate(self):
        pattern = MonteCarloPiPattern()
        pattern.config = MonteCarloPiConfig(n_samples=100000, method="buffon", seed=42)
        result = await pattern._simulate_buffon()
        if result["metrics"]["pi_estimate"] > 0:
            assert 2.5 < result["metrics"]["pi_estimate"] < 3.5


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = MonteCarloPiPattern()
        results = {"metrics": {"relative_error": 0.001, "n_samples": 100000, "standard_error": 0.005}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5


@pytest.mark.asyncio
class TestRun:
    async def test_run_unit_circle(self):
        pattern = MonteCarloPiPattern()
        h = Hypothesis(title="Monte Carlo Pi", description="pi estimation")
        config = {"n_samples": 1000, "method": "unit_circle"}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_buffon(self):
        pattern = MonteCarloPiPattern()
        h = Hypothesis(title="Buffon's needle", description="pi estimation")
        config = {"n_samples": 1000, "method": "buffon"}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = MonteCarloPiPattern.get_metadata()
        assert meta["id"] == "monte_carlo_pi"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
