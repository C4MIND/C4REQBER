"""
Tests for src/patterns/library/wave_equation.py
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.wave_equation import (
    WaveEquationConfig,
    WaveEquationPattern,
)


class TestWaveEquationConfig:
    def test_default_init(self):
        cfg = WaveEquationConfig()
        assert cfg.dimension == "1d"
        assert cfg.c == 1.0
        assert cfg.nx == 200

    def test_custom_init(self):
        cfg = WaveEquationConfig(dimension="2d", c=2.0, nx=100)
        assert cfg.dimension == "2d"
        assert cfg.c == 2.0
        assert cfg.nx == 100


class TestWaveEquationPatternInit:
    def test_init(self):
        pattern = WaveEquationPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = WaveEquationPattern()
        param_names = [p.name for p in pattern.parameters]
        assert "dimension" in param_names
        assert "c" in param_names


class TestCanSimulate:
    def test_matches_wave(self):
        pattern = WaveEquationPattern()
        h = Hypothesis(title="Wave propagation", description="acoustic wave")
        assert pattern.can_simulate(h) is True

    def test_matches_string(self):
        pattern = WaveEquationPattern()
        h = Hypothesis(title="String vibration", description="standing wave")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = WaveEquationPattern()
        h = Hypothesis(title="Heat transfer", description="conduction")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_default_parsing(self):
        pattern = WaveEquationPattern()
        cfg = pattern._parse_config({})
        assert cfg.dimension == "1d"
        assert cfg.c == 1.0

    def test_custom_parsing(self):
        pattern = WaveEquationPattern()
        cfg = pattern._parse_config({"dimension": "2d", "c": 2.0, "nx": 100})
        assert cfg.dimension == "2d"
        assert cfg.c == 2.0
        assert cfg.nx == 100


@pytest.mark.asyncio
class TestSimulate1D:
    async def test_simulation_completes(self):
        pattern = WaveEquationPattern()
        pattern.config = WaveEquationConfig(dimension="1d", nx=50, t_max=1.0, dt=0.01)
        result = await pattern._simulate_1d()
        assert "metrics" in result
        assert "logs" in result
        assert "snapshots" in result

    async def test_cfl_stable(self):
        pattern = WaveEquationPattern()
        pattern.config = WaveEquationConfig(dimension="1d", nx=50, t_max=1.0, dt=0.01)
        result = await pattern._simulate_1d()
        assert result["metrics"]["cfl_number"] <= 1.0

    async def test_max_amplitude_positive(self):
        pattern = WaveEquationPattern()
        pattern.config = WaveEquationConfig(dimension="1d", nx=50, t_max=1.0, dt=0.01)
        result = await pattern._simulate_1d()
        assert result["metrics"]["max_amplitude"] > 0

    async def test_energy_conservation(self):
        pattern = WaveEquationPattern()
        pattern.config = WaveEquationConfig(dimension="1d", nx=50, t_max=1.0, dt=0.01)
        result = await pattern._simulate_1d()
        # Energy should not grow unboundedly
        assert result["metrics"]["energy_drift"] < 1.0


@pytest.mark.asyncio
class TestSimulate2D:
    async def test_simulation_completes(self):
        pattern = WaveEquationPattern()
        pattern.config = WaveEquationConfig(dimension="2d", nx=30, t_max=0.5, dt=0.01)
        result = await pattern._simulate_2d()
        assert "metrics" in result
        assert "logs" in result
        assert "final_state" in result

    async def test_cfl_stable(self):
        pattern = WaveEquationPattern()
        pattern.config = WaveEquationConfig(dimension="2d", nx=30, t_max=0.5, dt=0.01)
        result = await pattern._simulate_2d()
        assert result["metrics"]["cfl_number"] <= 0.5


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = WaveEquationPattern()
        results = {
            "metrics": {
                "cfl_number": 0.5,
                "max_amplitude": 1.0,
                "energy_drift": 0.01,
                "n_steps": 100,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5


@pytest.mark.asyncio
class TestRun:
    async def test_run_1d(self):
        pattern = WaveEquationPattern()
        h = Hypothesis(title="Wave equation", description="1D propagation")
        config = {"dimension": "1d", "nx": 50, "t_max": 1.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED

    async def test_run_2d(self):
        pattern = WaveEquationPattern()
        h = Hypothesis(title="Wave equation", description="2D propagation")
        config = {"dimension": "2d", "nx": 30, "t_max": 0.5}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = WaveEquationPattern.get_metadata()
        assert meta["id"] == "wave_equation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
