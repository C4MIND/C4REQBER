"""
Tests for src/patterns/library/spring_mass.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.spring_mass import (
    SpringMassPattern,
    SpringMassConfig,
)
from src.patterns.core import Hypothesis, SimulationStatus



class TestSpringMassConfig:
    def test_default_init(self):
        cfg = SpringMassConfig()
        assert cfg.n_masses == 3
        assert cfg.mass == 1.0
        assert cfg.k == 1.0

    def test_custom_init(self):
        cfg = SpringMassConfig(n_masses=5, k=2.0, t_max=20.0)
        assert cfg.n_masses == 5
        assert cfg.k == 2.0


class TestSpringMassPatternInit:
    def test_init(self):
        pattern = SpringMassPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = SpringMassPattern()
        param_names = [p.name for p in pattern.parameters]
        assert "n_masses" in param_names
        assert "k" in param_names


class TestCanSimulate:
    def test_matches_oscillator(self):
        pattern = SpringMassPattern()
        h = Hypothesis(title="Coupled oscillator", description="normal modes")
        assert pattern.can_simulate(h) is True

    def test_matches_vibration(self):
        pattern = SpringMassPattern()
        h = Hypothesis(title="Mechanical vibration", description="resonance")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = SpringMassPattern()
        h = Hypothesis(title="Stock market", description="trading")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_default_parsing(self):
        pattern = SpringMassPattern()
        cfg = pattern._parse_config({})
        assert cfg.n_masses == 3

    def test_custom_parsing(self):
        pattern = SpringMassPattern()
        cfg = pattern._parse_config({"n_masses": 5, "k": 2.0})
        assert cfg.n_masses == 5
        assert cfg.k == 2.0


@pytest.mark.asyncio
class TestSimulateSpringMass:
    async def test_simulation_completes(self):
        pattern = SpringMassPattern()
        pattern.config = SpringMassConfig(n_masses=3, t_max=5.0, dt=0.01)
        result = await pattern._simulate_spring_mass()
        assert "metrics" in result
        assert "logs" in result
        assert "frequencies" in result
        assert "positions" in result

    async def test_frequencies_positive(self):
        pattern = SpringMassPattern()
        pattern.config = SpringMassConfig(n_masses=3, t_max=5.0, dt=0.01)
        result = await pattern._simulate_spring_mass()
        freqs = np.array(result["frequencies"])
        assert np.all(freqs >= 0)

    async def test_fundamental_frequency(self):
        pattern = SpringMassPattern()
        pattern.config = SpringMassConfig(n_masses=3, t_max=5.0, dt=0.01)
        result = await pattern._simulate_spring_mass()
        assert result["metrics"]["fundamental_frequency"] > 0

    async def test_energy_conservation(self):
        pattern = SpringMassPattern()
        pattern.config = SpringMassConfig(n_masses=3, t_max=5.0, dt=0.01)
        result = await pattern._simulate_spring_mass()
        assert result["metrics"]["energy_drift"] < 0.1

    async def test_frequency_ratio(self):
        pattern = SpringMassPattern()
        pattern.config = SpringMassConfig(n_masses=3, t_max=5.0, dt=0.01)
        result = await pattern._simulate_spring_mass()
        assert result["metrics"]["frequency_ratio"] > 1.0


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = SpringMassPattern()
        results = {"metrics": {"energy_drift": 0.001, "fundamental_frequency": 0.5, "frequency_ratio": 2.0, "max_displacement": 1.0}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = SpringMassPattern()
        h = Hypothesis(title="Coupled oscillators", description="normal modes")
        config = {"n_masses": 3, "t_max": 5.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = SpringMassPattern.get_metadata()
        assert meta["id"] == "spring_mass"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
