"""
Tests for src/patterns/library/quantum_harmonic_oscillator.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.quantum_harmonic_oscillator import (
    QuantumHarmonicOscillatorPattern,
    QHOConfig,
)
from src.patterns.core import Hypothesis, SimulationStatus



class TestQHOConfig:
    def test_default_init(self):
        cfg = QHOConfig()
        assert cfg.mass == 1.0
        assert cfg.omega == 1.0
        assert cfg.n_levels == 10
        assert cfg.x_max == 10.0

    def test_custom_init(self):
        cfg = QHOConfig(mass=2.0, omega=0.5, n_levels=5)
        assert cfg.mass == 2.0
        assert cfg.omega == 0.5
        assert cfg.n_levels == 5


class TestQuantumHarmonicOscillatorPatternInit:
    def test_init(self):
        pattern = QuantumHarmonicOscillatorPattern()
        assert pattern is not None
        assert hasattr(pattern, "config")

    def test_parameters_defined(self):
        pattern = QuantumHarmonicOscillatorPattern()
        assert hasattr(pattern, "parameters")
        assert len(pattern.parameters) > 0
        param_names = [p.name for p in pattern.parameters]
        assert "mass" in param_names
        assert "omega" in param_names
        assert "n_levels" in param_names


class TestCanSimulate:
    def test_matches_harmonic(self):
        pattern = QuantumHarmonicOscillatorPattern()
        h = Hypothesis(title="Quantum harmonic oscillator", description="energy levels")
        assert pattern.can_simulate(h) is True

    def test_matches_wavefunction(self):
        pattern = QuantumHarmonicOscillatorPattern()
        h = Hypothesis(title="Wavefunction analysis", description="hermite polynomials")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = QuantumHarmonicOscillatorPattern()
        h = Hypothesis(title="Stock market", description="price prediction")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_default_parsing(self):
        pattern = QuantumHarmonicOscillatorPattern()
        cfg = pattern._parse_config({})
        assert cfg.mass == 1.0
        assert cfg.omega == 1.0

    def test_custom_parsing(self):
        pattern = QuantumHarmonicOscillatorPattern()
        cfg = pattern._parse_config({"mass": 2.0, "omega": 0.5, "n_levels": 5})
        assert cfg.mass == 2.0
        assert cfg.omega == 0.5
        assert cfg.n_levels == 5


@pytest.mark.asyncio
class TestSimulateQHO:
    async def test_simulation_completes(self):
        pattern = QuantumHarmonicOscillatorPattern()
        pattern.config = QHOConfig(n_levels=5, x_max=5.0, n_points=200)
        result = await pattern._simulate_qho()
        assert "metrics" in result
        assert "logs" in result
        assert "energies" in result
        assert "wavefunctions" in result

    async def test_energy_levels(self):
        pattern = QuantumHarmonicOscillatorPattern()
        pattern.config = QHOConfig(n_levels=5, x_max=5.0, n_points=200)
        result = await pattern._simulate_qho()
        energies = np.array(result["energies"])
        # E_n = (n + 0.5) * hbar * omega
        expected = np.array([0.5, 1.5, 2.5, 3.5, 4.5])
        np.testing.assert_allclose(energies, expected, rtol=0.01)

    async def test_ground_state_energy(self):
        pattern = QuantumHarmonicOscillatorPattern()
        pattern.config = QHOConfig(n_levels=3, x_max=5.0, n_points=200)
        result = await pattern._simulate_qho()
        assert result["metrics"]["ground_state_energy"] == pytest.approx(0.5, abs=0.01)

    async def test_uncertainty_product(self):
        pattern = QuantumHarmonicOscillatorPattern()
        pattern.config = QHOConfig(n_levels=3, x_max=5.0, n_points=200)
        result = await pattern._simulate_qho()
        # Heisenberg: sigma_x * sigma_p >= 0.5
        assert result["metrics"]["uncertainty_product_ground"] >= 0.49

    async def test_wavefunction_normalization(self):
        pattern = QuantumHarmonicOscillatorPattern()
        pattern.config = QHOConfig(n_levels=3, x_max=5.0, n_points=200)
        result = await pattern._simulate_qho()
        x = np.array(result["x"])
        dx = x[1] - x[0]
        for i, prob in enumerate(result["probabilities"]):
            prob_arr = np.array(prob)
            integral = np.trapezoid(prob_arr, x)
            assert integral == pytest.approx(1.0, abs=0.05)


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = QuantumHarmonicOscillatorPattern()
        results = {
            "metrics": {
                "ground_state_energy": 0.5,
                "uncertainty_product_ground": 0.5,
                "energy_spacing": 1.0,
                "n_levels": 10,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5

    def test_low_confidence(self):
        pattern = QuantumHarmonicOscillatorPattern()
        results = {"metrics": {"ground_state_energy": 0.0, "uncertainty_product_ground": 0.0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence < 0.9


class TestEstimateResources:
    def test_default_params(self):
        pattern = QuantumHarmonicOscillatorPattern()
        h = Hypothesis(parameters={})
        resources = pattern.estimate_resources(h)
        assert "cpu_cores" in resources
        assert "memory_gb" in resources
        assert resources["gpu_required"] is False


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = QuantumHarmonicOscillatorPattern()
        h = Hypothesis(title="Quantum harmonic oscillator", description="energy levels")
        config = {"n_levels": 5, "x_max": 5.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED
        assert result.simulation_id.startswith("qho_")

    async def test_run_logs_present(self):
        pattern = QuantumHarmonicOscillatorPattern()
        h = Hypothesis(title="QHO", description="test")
        config = {"n_levels": 3}
        result = await pattern.run(h, config)
        assert len(result.logs) > 0


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = QuantumHarmonicOscillatorPattern.get_metadata()
        assert meta["id"] == "quantum_harmonic_oscillator"
        assert "parameters" in meta
        assert "references" in meta


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
