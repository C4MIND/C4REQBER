"""
Tests for src/patterns/library/bootstrap.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.bootstrap import (
    BootstrapPattern,
    BootstrapConfig,
)
from src.patterns.core import Hypothesis, SimulationStatus



class TestBootstrapConfig:
    def test_default_init(self):
        cfg = BootstrapConfig()
        assert cfg.n_bootstrap == 1000
        assert cfg.sample_size == 100
        assert cfg.statistic == "mean"

    def test_custom_init(self):
        cfg = BootstrapConfig(n_bootstrap=500, statistic="median", sample_size=50)
        assert cfg.n_bootstrap == 500
        assert cfg.statistic == "median"


class TestBootstrapPatternInit:
    def test_init(self):
        pattern = BootstrapPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = BootstrapPattern()
        param_names = [p.name for p in pattern.parameters]
        assert "n_bootstrap" in param_names
        assert "statistic" in param_names


class TestCanSimulate:
    def test_matches_bootstrap(self):
        pattern = BootstrapPattern()
        h = Hypothesis(title="Bootstrap", description="confidence interval")
        assert pattern.can_simulate(h) is True

    def test_matches_resampling(self):
        pattern = BootstrapPattern()
        h = Hypothesis(title="Resampling", description="standard error")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = BootstrapPattern()
        h = Hypothesis(title="Stock market", description="trading")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_default_parsing(self):
        pattern = BootstrapPattern()
        cfg = pattern._parse_config({})
        assert cfg.n_bootstrap == 1000

    def test_custom_parsing(self):
        pattern = BootstrapPattern()
        cfg = pattern._parse_config({"n_bootstrap": 500, "statistic": "median"})
        assert cfg.n_bootstrap == 500
        assert cfg.statistic == "median"


@pytest.mark.asyncio
class TestSimulateBootstrap:
    async def test_simulation_completes(self):
        pattern = BootstrapPattern()
        pattern.config = BootstrapConfig(n_bootstrap=100, sample_size=50)
        result = await pattern._simulate_bootstrap()
        assert "metrics" in result
        assert "logs" in result
        assert "bootstrap_statistics" in result

    async def test_mean_statistic(self):
        pattern = BootstrapPattern()
        pattern.config = BootstrapConfig(n_bootstrap=200, sample_size=50, statistic="mean", seed=42)
        result = await pattern._simulate_bootstrap()
        assert result["metrics"]["statistic"] == "mean"
        assert result["metrics"]["true_value"] == pytest.approx(5.0, abs=0.5)

    async def test_median_statistic(self):
        pattern = BootstrapPattern()
        pattern.config = BootstrapConfig(n_bootstrap=200, sample_size=50, statistic="median", seed=42)
        result = await pattern._simulate_bootstrap()
        assert result["metrics"]["statistic"] == "median"

    async def test_std_statistic(self):
        pattern = BootstrapPattern()
        pattern.config = BootstrapConfig(n_bootstrap=200, sample_size=50, statistic="std", seed=42)
        result = await pattern._simulate_bootstrap()
        assert result["metrics"]["statistic"] == "std"
        assert result["metrics"]["true_value"] == pytest.approx(2.0, abs=0.5)

    async def test_correlation_statistic(self):
        pattern = BootstrapPattern()
        pattern.config = BootstrapConfig(n_bootstrap=200, sample_size=50, statistic="correlation", seed=42)
        result = await pattern._simulate_bootstrap()
        assert result["metrics"]["statistic"] == "correlation"
        assert result["metrics"]["true_value"] == pytest.approx(0.5, abs=0.2)

    async def test_ci_contains_true_value(self):
        pattern = BootstrapPattern()
        pattern.config = BootstrapConfig(n_bootstrap=500, sample_size=100, statistic="mean", seed=42)
        result = await pattern._simulate_bootstrap()
        assert result["metrics"]["coverage"] == 1.0

    async def test_ci_width_positive(self):
        pattern = BootstrapPattern()
        pattern.config = BootstrapConfig(n_bootstrap=100, sample_size=50, statistic="mean", seed=42)
        result = await pattern._simulate_bootstrap()
        assert result["metrics"]["ci_width"] > 0

    async def test_standard_error_positive(self):
        pattern = BootstrapPattern()
        pattern.config = BootstrapConfig(n_bootstrap=100, sample_size=50, statistic="mean", seed=42)
        result = await pattern._simulate_bootstrap()
        assert result["metrics"]["standard_error"] > 0

    async def test_bias_small(self):
        pattern = BootstrapPattern()
        pattern.config = BootstrapConfig(n_bootstrap=500, sample_size=100, statistic="mean", seed=42)
        result = await pattern._simulate_bootstrap()
        true_val = result["metrics"]["true_value"]
        assert abs(result["metrics"]["bias"]) < abs(true_val) * 0.2


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = BootstrapPattern()
        results = {"metrics": {"coverage": 1.0, "bias": 0.01, "standard_error": 0.2, "n_bootstrap": 1000}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = BootstrapPattern()
        h = Hypothesis(title="Bootstrap", description="confidence interval")
        config = {"n_bootstrap": 100, "sample_size": 50}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = BootstrapPattern.get_metadata()
        assert meta["id"] == "bootstrap"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
