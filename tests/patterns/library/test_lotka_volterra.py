"""
Tests for src/patterns/library/lotka_volterra.py (Lotka-Volterra Pattern)

Covers:
- LotkaVolterraConfig dataclass
- LotkaVolterraPattern initialization
- can_simulate() keyword matching
- _parse_config()
- _simulate()
- _analyze_results()
- _estimate_lyapunov()
- _calculate_confidence()
- estimate_resources()
- run() async integration
- Edge cases: different model types, extreme parameters
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.lotka_volterra import (
    LotkaVolterraPattern,
    LotkaVolterraConfig,
)
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestLotkaVolterraConfig:
    def test_default_init(self):
        cfg = LotkaVolterraConfig()
        assert cfg.n_species == 2
        assert cfg.model_type == "predator_prey"
        assert cfg.t_max == 100.0
        assert cfg.dt == 0.01

    def test_post_init_predator_prey(self):
        cfg = LotkaVolterraConfig(model_type="predator_prey")
        assert cfg.initial_populations == [10.0, 5.0]
        assert cfg.growth_rates == [1.0, 0.5]

    def test_post_init_competitive(self):
        cfg = LotkaVolterraConfig(model_type="competitive", n_species=3)
        assert cfg.initial_populations == [1.0, 1.0, 1.0]
        assert cfg.growth_rates == [1.0, 1.0, 1.0]

    def test_invalid_model_type(self):
        cfg = LotkaVolterraConfig(model_type="invalid")
        assert cfg.model_type == "predator_prey"  # Falls back to default


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestLotkaVolterraPatternInit:
    def test_init(self):
        pattern = LotkaVolterraPattern()
        assert pattern is not None
        assert pattern.rng is not None

    def test_parameters_defined(self):
        pattern = LotkaVolterraPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "n_species" in param_names
        assert "model_type" in param_names
        assert "alpha" in param_names
        assert "beta" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate Tests
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_lotka_volterra(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Lotka-Volterra model", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_predator_prey(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Predator-prey dynamics", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_population_dynamics(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Population dynamics", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_ecological(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Ecological model", description="species interaction")
        assert pattern.can_simulate(h) is True

    def test_matches_competition(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Competitive exclusion", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_carrying_capacity(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Carrying capacity analysis", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_food_web(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Food web dynamics", description="trophic levels")
        assert pattern.can_simulate(h) is True

    def test_matches_bifurcation(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Bifurcation analysis", description="limit cycle")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Neural network", description="deep learning")
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing Tests
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_config(self):
        pattern = LotkaVolterraPattern()
        config = pattern._parse_config({})
        assert config.n_species == 2
        assert config.model_type == "predator_prey"

    def test_predator_prey_forces_two_species(self):
        pattern = LotkaVolterraPattern()
        config = pattern._parse_config({"n_species": 5, "model_type": "predator_prey"})
        assert config.n_species == 2  # Predator-prey requires exactly 2 species

    def test_competitive_keeps_species(self):
        pattern = LotkaVolterraPattern()
        config = pattern._parse_config({"n_species": 5, "model_type": "competitive"})
        assert config.n_species == 5


# ═══════════════════════════════════════════════════════════════════
# Core Methods Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_good_simulation(self):
        pattern = LotkaVolterraPattern()
        pattern.config = LotkaVolterraConfig(t_max=100.0)
        results = {
            "metrics": {
                "is_stable": 1.0,
                "coexistence": 1.0,
                "lyapunov_estimate": 0.0,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_oscillating_system(self):
        pattern = LotkaVolterraPattern()
        pattern.config = LotkaVolterraConfig(t_max=100.0)
        results = {
            "metrics": {
                "oscillation_period": 5.0,
                "coexistence": 1.0,
                "lyapunov_estimate": 0.01,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.0


class TestEstimateLyapunov:
    def test_insufficient_data(self):
        pattern = LotkaVolterraPattern()
        pattern.populations = np.array([[1, 2], [3, 4]])
        lyap = pattern._estimate_lyapunov()
        assert lyap == 0.0

    def test_with_sufficient_data(self):
        pattern = LotkaVolterraPattern()
        pattern.populations = np.random.random((2, 200))
        pattern.time_points = np.linspace(0, 100, 200)
        lyap = pattern._estimate_lyapunov()
        assert isinstance(lyap, float)


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation Tests
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_more_species_more_memory(self):
        pattern = LotkaVolterraPattern()
        h_small = Hypothesis(parameters={"n_species": 2})
        h_large = Hypothesis(parameters={"n_species": 10})

        resources_small = pattern.estimate_resources(h_small)
        resources_large = pattern.estimate_resources(h_large)

        assert resources_large["memory_gb"] > resources_small["memory_gb"]


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Lotka-Volterra", description="predator-prey dynamics")
        result = await pattern.run(h, {"t_max": 50.0})
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("lv_")

    async def test_run_predator_prey(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Lotka-Volterra", description="predator-prey dynamics")
        result = await pattern.run(h, {"model_type": "predator_prey", "t_max": 50.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_competitive(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Lotka-Volterra", description="species competition")
        result = await pattern.run(h, {"model_type": "competitive", "n_species": 3, "t_max": 50.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_cooperative(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Lotka-Volterra", description="species cooperation")
        result = await pattern.run(h, {"model_type": "cooperative", "n_species": 3, "t_max": 50.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_metrics_present(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Lotka-Volterra", description="predator-prey dynamics")
        result = await pattern.run(h, {"t_max": 50.0})
        assert "final_populations" in result.metrics

    async def test_logs_present(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Lotka-Volterra", description="predator-prey dynamics")
        result = await pattern.run(h, {"t_max": 50.0})
        assert len(result.logs) > 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_very_short_simulation(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Lotka-Volterra", description="predator-prey dynamics")
        result = await pattern.run(h, {"t_max": 10.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_growth_rate(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Lotka-Volterra", description="predator-prey dynamics")
        result = await pattern.run(h, {"t_max": 50.0, "alpha": 5.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_low_predation_rate(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Lotka-Volterra", description="predator-prey dynamics")
        result = await pattern.run(h, {"t_max": 50.0, "beta": 0.01})
        assert result.status == SimulationStatus.COMPLETED

    async def test_with_seed(self):
        pattern = LotkaVolterraPattern()
        h = Hypothesis(title="Lotka-Volterra", description="predator-prey dynamics")
        result = await pattern.run(h, {"t_max": 50.0, "random_seed": 42})
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
