"""
Tests for src/patterns/library/phase_field.py (Phase Field Pattern)

Covers:
- PhaseFieldConfig dataclass
- PhaseFieldPattern initialization
- can_simulate() keyword matching
- _parse_config()
- _chemical_potential()
- _record()
- _analyze_results()
- _calculate_confidence()
- estimate_resources()
- run() async integration
- Edge cases: small grids, short simulations
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.phase_field import (
    PhaseFieldPattern,
    PhaseFieldConfig,
)
from src.patterns.core import Hypothesis, SimulationStatus



# ═══════════════════════════════════════════════════════════════════
# Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestPhaseFieldConfig:
    def test_default_init(self):
        cfg = PhaseFieldConfig()
        assert cfg.grid_size == 128
        assert cfg.dx == 1.0
        assert cfg.dt == 0.01
        assert cfg.n_steps == 10000
        assert cfg.M == 1.0
        assert cfg.gamma == 0.5
        assert cfg.epsilon == 2.0

    def test_custom_init(self):
        cfg = PhaseFieldConfig(
            grid_size=64,
            dt=0.005,
            n_steps=5000,
            M=0.5,
        )
        assert cfg.grid_size == 64
        assert cfg.dt == 0.005
        assert cfg.n_steps == 5000
        assert cfg.M == 0.5


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestPhaseFieldPatternInit:
    def test_init(self):
        pattern = PhaseFieldPattern()
        assert pattern is not None
        assert pattern.rng is not None
        assert pattern.history == []

    def test_parameters_defined(self):
        pattern = PhaseFieldPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "grid_size" in param_names
        assert "dt" in param_names
        assert "n_steps" in param_names
        assert "M" in param_names


# ═══════════════════════════════════════════════════════════════════
# can_simulate Tests
# ═══════════════════════════════════════════════════════════════════


class TestCanSimulate:
    def test_matches_phase_field(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Phase field model", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_cahn_hilliard(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Cahn-Hilliard equation", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_phase_separation(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Phase separation", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_spinodal(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Spinodal decomposition", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_coarsening(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Coarsening dynamics", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_microstructure(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Microstructure evolution", description="test")
        assert pattern.can_simulate(h) is True

    def test_matches_interface(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Interface dynamics", description="surface tension")
        assert pattern.can_simulate(h) is True

    def test_matches_binary_mixture(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Binary mixture demixing", description="test")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Neural network", description="deep learning")
        assert pattern.can_simulate(h) is False


# ═══════════════════════════════════════════════════════════════════
# Config Parsing Tests
# ═══════════════════════════════════════════════════════════════════


class TestParseConfig:
    def test_default_config(self):
        pattern = PhaseFieldPattern()
        config = pattern._parse_config({})
        assert config.grid_size == 128
        assert config.dt == 0.01
        assert config.n_steps == 10000

    def test_custom_config(self):
        pattern = PhaseFieldPattern()
        config = pattern._parse_config({
            "grid_size": 64,
            "dt": 0.005,
            "n_steps": 1000,
            "M": 0.5,
            "gamma": 0.3,
        })
        assert config.grid_size == 64
        assert config.dt == 0.005
        assert config.n_steps == 1000
        assert config.M == 0.5
        assert config.gamma == 0.3


# ═══════════════════════════════════════════════════════════════════
# Chemical Potential Tests
# ═══════════════════════════════════════════════════════════════════


class TestChemicalPotential:
    def test_chemical_potential_shape(self):
        pattern = PhaseFieldPattern()
        pattern.config = PhaseFieldConfig(grid_size=32, dx=1.0)
        phi = np.random.random((32, 32))
        mu = pattern._chemical_potential(phi, epsilon=2.0)
        assert mu.shape == (32, 32)

    def test_chemical_potential_uniform(self):
        pattern = PhaseFieldPattern()
        pattern.config = PhaseFieldConfig(grid_size=32, dx=1.0)
        phi = np.ones((32, 32))  # Uniform field
        mu = pattern._chemical_potential(phi, epsilon=2.0)
        # For uniform field, Laplacian is zero, so mu = phi^3 - phi = 0 when phi=1
        assert np.allclose(mu, 0.0, atol=1e-10)


# ═══════════════════════════════════════════════════════════════════
# Record Tests
# ═══════════════════════════════════════════════════════════════════


class TestRecord:
    def test_record_structure(self):
        pattern = PhaseFieldPattern()
        pattern.config = PhaseFieldConfig(grid_size=32)
        pattern.phi = np.random.random((32, 32))
        pattern._record(step=0)
        assert len(pattern.history) == 1
        assert pattern.history[0]["step"] == 0
        assert "concentration_mean" in pattern.history[0]
        assert "concentration_var" in pattern.history[0]


# ═══════════════════════════════════════════════════════════════════
# Core Methods Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateConfidence:
    def test_good_simulation(self):
        pattern = PhaseFieldPattern()
        results = {
            "metrics": {
                "n_records": 100,
                "phase_separated": 1.0,
                "growth_exponent": 0.3,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.7

    def test_few_records(self):
        pattern = PhaseFieldPattern()
        results = {"metrics": {"n_records": 10}}
        confidence = pattern._calculate_confidence(results)
        assert 0 <= confidence < 0.7

    def test_no_phase_separation(self):
        pattern = PhaseFieldPattern()
        results = {"metrics": {"n_records": 100, "phase_separated": 0.0}}
        confidence = pattern._calculate_confidence(results)
        assert 0 <= confidence < 0.7


# ═══════════════════════════════════════════════════════════════════
# Resource Estimation Tests
# ═══════════════════════════════════════════════════════════════════


class TestEstimateResources:
    def test_default_params(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert "gpu_required" in resources
        assert "estimated_time_seconds" in resources
        assert resources["gpu_required"] is False

    def test_larger_grid_more_memory(self):
        pattern = PhaseFieldPattern()
        h_small = Hypothesis(parameters={"grid_size": 64})
        h_large = Hypothesis(parameters={"grid_size": 256})

        resources_small = pattern.estimate_resources(h_small)
        resources_large = pattern.estimate_resources(h_large)

        assert resources_large["memory_gb"] > resources_small["memory_gb"]


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Phase field", description="cahn-hilliard")
        result = await pattern.run(h, {"grid_size": 32, "n_steps": 100})
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("phasefield_")

    async def test_run_with_config(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Phase field", description="cahn-hilliard")
        result = await pattern.run(h, {
            "grid_size": 32,
            "n_steps": 100,
            "dt": 0.005,
            "M": 0.5,
        })
        assert result.status == SimulationStatus.COMPLETED

    async def test_metrics_present(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Phase field", description="cahn-hilliard")
        result = await pattern.run(h, {"grid_size": 32, "n_steps": 100})
        assert "final_concentration" in result.metrics
        assert "final_variance" in result.metrics
        assert "n_records" in result.metrics

    async def test_logs_present(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Phase field", description="cahn-hilliard")
        result = await pattern.run(h, {"grid_size": 32, "n_steps": 100})
        assert len(result.logs) > 0


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEdgeCases:
    async def test_small_grid(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Phase field", description="cahn-hilliard")
        result = await pattern.run(h, {"grid_size": 32, "n_steps": 50})
        assert result.status == SimulationStatus.COMPLETED

    async def test_short_simulation(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Phase field", description="cahn-hilliard")
        result = await pattern.run(h, {"grid_size": 32, "n_steps": 10})
        assert result.status == SimulationStatus.COMPLETED

    async def test_low_mobility(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Phase field", description="cahn-hilliard")
        result = await pattern.run(h, {"grid_size": 32, "n_steps": 100, "M": 0.1})
        assert result.status == SimulationStatus.COMPLETED

    async def test_high_mobility(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Phase field", description="cahn-hilliard")
        result = await pattern.run(h, {"grid_size": 32, "n_steps": 100, "M": 5.0})
        assert result.status == SimulationStatus.COMPLETED

    async def test_with_seed(self):
        pattern = PhaseFieldPattern()
        h = Hypothesis(title="Phase field", description="cahn-hilliard")
        result = await pattern.run(h, {"grid_size": 32, "n_steps": 100, "random_seed": 42})
        assert result.status == SimulationStatus.COMPLETED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
