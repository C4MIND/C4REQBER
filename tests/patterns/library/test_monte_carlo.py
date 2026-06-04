"""
Tests for src/patterns/library/monte_carlo.py (Monte Carlo pattern)

Covers:
- MonteCarloConfig dataclass
- MonteCarloPattern initialization
- can_simulate() keyword matching
- _build_model()
- _naive_monte_carlo()
- _stratified_sampling()
- _importance_sampling()
- _sobol_sampling()
- _calculate_confidence()
- estimate_resources()
- run() async integration
- Edge cases: different variance reduction methods, convergence
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.monte_carlo import MonteCarloPattern, MonteCarloConfig
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestMonteCarloConfig:
    def test_default_init(self):
        cfg = MonteCarloConfig()
        assert cfg.n_samples == 10000
        assert cfg.confidence_level == 0.95
        assert cfg.variance_reduction == "stratified"
        assert cfg.batch_size == 1000

    def test_custom_init(self):
        cfg = MonteCarloConfig(
            n_samples=5000,
            confidence_level=0.99,
            variance_reduction="sobol"
        )
        assert cfg.n_samples == 5000
        assert cfg.confidence_level == 0.99
        assert cfg.variance_reduction == "sobol"


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestMonteCarloPatternInit:
    def test_init(self):
        pattern = MonteCarloPattern()
        assert pattern is not None
        assert pattern.rng is not None

    def test_parameters_defined(self):
        pattern = MonteCarloPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "n_samples" in param_names
        assert "confidence_level" in param_names
        assert "variance_reduction" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate Tests
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_probability(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Probability analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_risk(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Risk assessment", description="uncertainty")
        assert pattern.can_simulate(h) is True

    def test_matches_uncertainty(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Uncertainty quantification", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_monte_carlo(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Monte Carlo simulation", description="random sampling")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Linear regression", description="statistics")
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Model Building Tests
# ═══════════════════════════════════════════════════════════════════


class TestBuildModel:
    def test_model_returns_function(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Test", description="test")
        model = pattern._build_model(h)
        assert callable(model)

    def test_model_output_shape(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Test", description="test")
        model = pattern._build_model(h)
        inputs = np.random.random((10, 5))
        outputs = model(inputs)
        assert len(outputs) == 10


# ═══════════════════════════════════════════════════════════════════
# Sampling Method Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestNaiveMonteCarlo:
    async def test_returns_samples(self):
        pattern = MonteCarloPattern()
        cfg = MonteCarloConfig(n_samples=100, batch_size=50)

        def model(inputs):
            return np.random.random(len(inputs))

        samples = await pattern._naive_monte_carlo(model, cfg)
        assert len(samples) == 100


@pytest.mark.asyncio
class TestStratifiedSampling:
    async def test_returns_samples(self):
        pattern = MonteCarloPattern()
        cfg = MonteCarloConfig(n_samples=100, batch_size=50, variance_reduction="stratified")

        def model(inputs):
            return np.random.random(len(inputs))

        samples = await pattern._stratified_sampling(model, cfg)
        assert len(samples) == 100

    async def test_variance_reduction(self):
        """Stratified sampling should produce a mean close to true expectation."""
        pattern = MonteCarloPattern()
        cfg = MonteCarloConfig(n_samples=1000, batch_size=100, variance_reduction="stratified")

        def model(inputs):
            return inputs[:, 0]  # Identity on first dimension

        samples = await pattern._stratified_sampling(model, cfg)
        # For uniform[0,1], true mean is 0.5. Stratified sampling should
        # give a very tight estimate (std error ~ 1/sqrt(12 * 1000) ≈ 0.009).
        assert np.isclose(np.mean(samples), 0.5, atol=0.01)


@pytest.mark.asyncio
class TestImportanceSampling:
    async def test_returns_samples(self):
        pattern = MonteCarloPattern()
        cfg = MonteCarloConfig(n_samples=100, batch_size=50, variance_reduction="importance")

        def model(inputs):
            return np.random.random(len(inputs))

        samples = await pattern._importance_sampling(model, cfg)
        assert len(samples) == 100


@pytest.mark.asyncio
class TestSobolSampling:
    async def test_returns_samples(self):
        pattern = MonteCarloPattern()
        cfg = MonteCarloConfig(n_samples=128, batch_size=64, variance_reduction="sobol")

        def model(inputs):
            return np.random.random(len(inputs))

        samples = await pattern._sobol_sampling(model, cfg)
        assert len(samples) == 128


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_sample_size(self):
        pattern = MonteCarloPattern()
        confidence = pattern._calculate_confidence(1.0, 0.1, 100000, MonteCarloConfig())
        assert confidence > 0.7

    def test_high_variance(self):
        pattern = MonteCarloPattern()
        confidence = pattern._calculate_confidence(1.0, 10.0, 1000, MonteCarloConfig())
        assert confidence < 0.7

    def test_capped_at_0_95(self):
        pattern = MonteCarloPattern()
        confidence = pattern._calculate_confidence(1.0, 0.01, 1000000, MonteCarloConfig())
        assert confidence <= 0.95


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation Tests
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_more_samples_more_time(self):
        pattern = MonteCarloPattern()
        h_small = Hypothesis(parameters={"n_samples": 1000})
        h_large = Hypothesis(parameters={"n_samples": 100000})

        resources_small = pattern.estimate_resources(h_small)
        resources_large = pattern.estimate_resources(h_large)

        assert resources_large["estimated_time_seconds"] > resources_small["estimated_time_seconds"]


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Probability test", description="uncertainty analysis")
        result = await pattern.run(h, {"n_samples": 100})
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("mc_")

    async def test_run_stratified(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Probability test", description="uncertainty analysis")
        result = await pattern.run(h, {
            "n_samples": 200,
            "variance_reduction": "stratified"
        })
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_importance(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Probability test", description="uncertainty analysis")
        result = await pattern.run(h, {
            "n_samples": 200,
            "variance_reduction": "importance"
        })
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_sobol(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Probability test", description="uncertainty analysis")
        result = await pattern.run(h, {
            "n_samples": 128,
            "variance_reduction": "sobol"
        })
        assert result.status == SimulationStatus.COMPLETED

    async def test_metrics_present(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Probability test", description="uncertainty analysis")
        result = await pattern.run(h, {"n_samples": 100})
        assert "mean" in result.metrics
        assert "std" in result.metrics
        assert "variance" in result.metrics
        assert "ci_lower" in result.metrics
        assert "ci_upper" in result.metrics

    async def test_confidence_interval_valid(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Probability test", description="uncertainty analysis")
        result = await pattern.run(h, {"n_samples": 100})
        assert result.metrics["ci_lower"] < result.metrics["ci_upper"]


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_very_few_samples(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Probability test", description="uncertainty analysis")
        result = await pattern.run(h, {"n_samples": 10})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_confidence_level(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Probability test", description="uncertainty analysis")
        result = await pattern.run(h, {
            "n_samples": 100,
            "confidence_level": 0.999
        })
        assert result.status == SimulationStatus.COMPLETED

    async def test_with_seed(self):
        pattern = MonteCarloPattern()
        h = Hypothesis(title="Probability test", description="uncertainty analysis")
        result = await pattern.run(h, {
            "n_samples": 100,
            "random_seed": 42
        })
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
