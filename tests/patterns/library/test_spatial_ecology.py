"""
Tests for src/patterns/library/spatial_ecology.py (Spatial Ecology Pattern)

Covers:
- SpatialEcologyConfig dataclass
- SpatialEcologyPattern initialization
- can_simulate() keyword matching
- _parse_config()
- _simulate() with different models
- _step_fisher_kpp() invasion waves
- _step_turing() pattern formation
- _step_competition() competitive dynamics
- _step_invasion() Allee effect
- _record() state recording
- _analyze_results()
- _calculate_confidence()
- estimate_resources()
- run() integration
- Edge cases: small grid, single species, boundary effects
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.spatial_ecology import SpatialEcologyPattern, SpatialEcologyConfig
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Dataclass
# ═══════════════════════════════════════════════════════════════════


class TestSpatialEcologyConfig:
    def test_default_init(self):
        cfg = SpatialEcologyConfig()
        assert cfg.grid_size == 100
        assert cfg.dx == 1.0
        assert cfg.dt == 0.01
        assert cfg.n_steps == 5000
        assert cfg.model_type == "fisher_kpp"
        assert cfg.n_species == 1
        assert cfg.record_interval == 100
        assert cfg.random_seed is None

    def test_custom_init(self):
        cfg = SpatialEcologyConfig(
            grid_size=50,
            model_type="turing",
            n_species=2,
            activator_diffusion=0.02,
        )
        assert cfg.grid_size == 50
        assert cfg.model_type == "turing"
        assert cfg.n_species == 2
        assert cfg.activator_diffusion == 0.02


# ═══════════════════════════════════════════════════════════════════
# SpatialEcologyPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestSpatialEcologyPatternInit:
    def test_init(self):
        pattern = SpatialEcologyPattern()
        assert pattern is not None
        assert pattern.rng is not None
        assert pattern.config is None
        assert pattern.fields == []

    def test_parameters_defined(self):
        pattern = SpatialEcologyPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "grid_size" in param_names
        assert "model_type" in param_names
        assert "D" in param_names
        assert "r" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_spatial_ecology(self):
        pattern = SpatialEcologyPattern()
        h = Hypothesis(title="Spatial ecology", description="diffusion")
        assert pattern.can_simulate(h) is True

    def test_matches_turing(self):
        pattern = SpatialEcologyPattern()
        h = Hypothesis(title="Turing pattern", description="morphogenesis")
        assert pattern.can_simulate(h) is True

    def test_matches_invasion(self):
        pattern = SpatialEcologyPattern()
        h = Hypothesis(title="Invasion wave", description="range expansion")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = SpatialEcologyPattern()
        h = Hypothesis(title="Stock market", description="trading")
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_parsing(self):
        pattern = SpatialEcologyPattern()
        cfg = pattern._parse_config({})
        assert cfg.grid_size == 100
        assert cfg.model_type == "fisher_kpp"

    def test_turing_sets_n_species(self):
        pattern = SpatialEcologyPattern()
        cfg = pattern._parse_config({"model_type": "turing"})
        assert cfg.n_species == 2

    def test_custom_parsing(self):
        pattern = SpatialEcologyPattern()
        cfg = pattern._parse_config({"grid_size": 50, "D": 0.2, "r": 2.0})
        assert cfg.grid_size == 50
        assert cfg.diffusion_coeffs == [0.2]
        assert cfg.growth_rates == [2.0]


# ═══════════════════════════════════════════════════════════════════
# Simulation
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestSimulate:
    async def test_fisher_kpp_simulation(self):
        pattern = SpatialEcologyPattern()
        pattern.config = SpatialEcologyConfig(
            grid_size=20, n_steps=100, model_type="fisher_kpp"
        )
        h = Hypothesis()
        result = await pattern._simulate(h)
        assert "metrics" in result
        assert "logs" in result

    async def test_turing_simulation(self):
        pattern = SpatialEcologyPattern()
        pattern.config = SpatialEcologyConfig(
            grid_size=20, n_steps=100, model_type="turing"
        )
        h = Hypothesis()
        result = await pattern._simulate(h)
        assert "metrics" in result

    async def test_competition_simulation(self):
        pattern = SpatialEcologyPattern()
        pattern.config = SpatialEcologyConfig(
            grid_size=20, n_steps=100, model_type="competition", n_species=2
        )
        h = Hypothesis()
        result = await pattern._simulate(h)
        assert "metrics" in result

    async def test_invasion_simulation(self):
        pattern = SpatialEcologyPattern()
        pattern.config = SpatialEcologyConfig(
            grid_size=20, n_steps=100, model_type="invasion"
        )
        h = Hypothesis()
        result = await pattern._simulate(h)
        assert "metrics" in result


# ═══════════════════════════════════════════════════════════════════
# Step Methods
# ═══════════════════════════════════════════════════════════════════


class TestStepMethods:
    def test_fisher_kpp_step(self):
        pattern = SpatialEcologyPattern()
        pattern.config = SpatialEcologyConfig(grid_size=20)
        pattern.fields = [np.zeros((20, 20))]
        pattern.fields[0][10, 10] = 0.5
        pattern._step_fisher_kpp(1.0, 0.01)
        assert np.all(pattern.fields[0] >= 0)

    def test_turing_step(self):
        pattern = SpatialEcologyPattern()
        pattern.config = SpatialEcologyConfig(grid_size=20, activator_diffusion=0.01, inhibitor_diffusion=0.5)
        pattern.fields = [np.ones((20, 20)), np.ones((20, 20))]
        pattern._step_turing(1.0, 0.01)
        assert len(pattern.fields) == 2

    def test_competition_step(self):
        pattern = SpatialEcologyPattern()
        pattern.config = SpatialEcologyConfig(
            grid_size=20, n_species=2,
            growth_rates=[1.0, 1.0],
            carrying_capacities=[1.0, 1.0],
            diffusion_coeffs=[0.1, 0.1]
        )
        pattern.fields = [np.random.random((20, 20)), np.random.random((20, 20))]
        pattern._step_competition(1.0, 0.01)
        assert len(pattern.fields) == 2
        assert np.all(pattern.fields[0] >= 0)


# ═══════════════════════════════════════════════════════════════════
# Recording
# ═══════════════════════════════════════════════════════════════════


class TestRecord:
    def test_record_adds_entry(self):
        pattern = SpatialEcologyPattern()
        pattern.config = SpatialEcologyConfig(grid_size=20, carrying_capacities=[1.0])
        pattern.fields = [np.random.random((20, 20))]
        pattern.history = []
        pattern._record(0.0)
        assert len(pattern.history) == 1
        assert "time" in pattern.history[0]
        assert "total" in pattern.history[0]


# ═══════════════════════════════════════════════════════════════════
# Results Analysis
# ═══════════════════════════════════════════════════════════════════


class TestAnalyzeResults:
    def test_empty_history(self):
        pattern = SpatialEcologyPattern()
        result = pattern._analyze_results()
        assert result["metrics"] == {}
        assert "No simulation data" in result["logs"]

    def test_fisher_kpp_metrics(self):
        pattern = SpatialEcologyPattern()
        pattern.config = SpatialEcologyConfig(
            model_type="fisher_kpp",
            grid_size=20,
            diffusion_coeffs=[0.1],
            growth_rates=[1.0]
        )
        pattern.history = []
        for i in range(12):
            pattern.history.append({
                "time": float(i),
                "total": 10.0 + i,
                "mean": 0.1 + i * 0.02,
                "max": 0.5 + i * 0.05,
                "spread_radius": float(i * 2),
                "wavelength": 0,
            })
        result = pattern._analyze_results()
        assert "wave_speed" in result["metrics"]
        assert "theoretical_wave_speed" in result["metrics"]

    def test_turing_metrics(self):
        pattern = SpatialEcologyPattern()
        pattern.config = SpatialEcologyConfig(model_type="turing", grid_size=20)
        pattern.history = [
            {"time": 0, "total": 10.0, "mean": 0.1, "max": 0.5, "spread_radius": 0, "wavelength": 5.0},
            {"time": 1, "total": 10.0, "mean": 0.1, "max": 0.5, "spread_radius": 0, "wavelength": 5.0},
        ]
        result = pattern._analyze_results()
        assert "pattern_wavelength" in result["metrics"]


# ═══════════════════════════════════════════════════════════════════
# Confidence Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_high_confidence_fisher(self):
        pattern = SpatialEcologyPattern()
        pattern.config = SpatialEcologyConfig(n_steps=5000, model_type="fisher_kpp")
        results = {"metrics": {"wave_speed": 0.6, "wave_speed_error": 0.1, "final_total": 100}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_high_confidence_turing(self):
        pattern = SpatialEcologyPattern()
        pattern.config = SpatialEcologyConfig(n_steps=5000, model_type="turing")
        results = {"metrics": {"pattern_wavelength": 5.0, "final_total": 100}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = SpatialEcologyPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_large_grid(self):
        pattern = SpatialEcologyPattern()
        h = Hypothesis(parameters={"grid_size": 200, "n_steps": 10000})
        resources = pattern.estimate_resources(h)
        assert resources["memory_gb"] > 0.1


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_fisher_kpp(self):
        pattern = SpatialEcologyPattern()
        h = Hypothesis(title="Spatial ecology", description="invasion")
        config = {"grid_size": 20, "n_steps": 100, "model_type": "fisher_kpp"}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_turing(self):
        pattern = SpatialEcologyPattern()
        h = Hypothesis(title="Turing patterns", description="morphogenesis")
        config = {"grid_size": 20, "n_steps": 100, "model_type": "turing"}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_with_seed(self):
        pattern = SpatialEcologyPattern()
        h = Hypothesis(title="Spatial ecology", description="test")
        config = {"grid_size": 20, "n_steps": 100, "random_seed": 42}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_small_grid(self):
        pattern = SpatialEcologyPattern()
        h = Hypothesis(title="Spatial ecology", description="small")
        config = {"grid_size": 10, "n_steps": 50}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_growth_rate(self):
        pattern = SpatialEcologyPattern()
        h = Hypothesis(title="Spatial ecology", description="high growth")
        config = {"grid_size": 20, "n_steps": 50, "r": 5.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_diffusion(self):
        pattern = SpatialEcologyPattern()
        h = Hypothesis(title="Spatial ecology", description="high diffusion")
        config = {"grid_size": 20, "n_steps": 50, "D": 1.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
