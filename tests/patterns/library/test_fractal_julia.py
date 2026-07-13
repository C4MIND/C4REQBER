"""
Tests for src/patterns/library/fractal_julia.py
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.fractal_julia import (
    JuliaConfig,
    JuliaPattern,
)


class TestJuliaConfig:
    def test_default_init(self):
        cfg = JuliaConfig()
        assert cfg.width == 800
        assert cfg.c_real == -0.7
        assert cfg.c_imag == 0.27015

    def test_custom_init(self):
        cfg = JuliaConfig(width=400, c_real=-0.5, c_imag=0.6)
        assert cfg.width == 400
        assert cfg.c_real == -0.5


class TestJuliaPatternInit:
    def test_init(self):
        pattern = JuliaPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = JuliaPattern()
        param_names = [p.name for p in pattern.parameters]
        assert "width" in param_names
        assert "c_real" in param_names


class TestCanSimulate:
    def test_matches_julia(self):
        pattern = JuliaPattern()
        h = Hypothesis(title="Julia set", description="fractal")
        assert pattern.can_simulate(h) is True

    def test_matches_complex(self):
        pattern = JuliaPattern()
        h = Hypothesis(title="Complex dynamics", description="iteration")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = JuliaPattern()
        h = Hypothesis(title="Stock market", description="trading")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_default_parsing(self):
        pattern = JuliaPattern()
        cfg = pattern._parse_config({})
        assert cfg.width == 800

    def test_custom_parsing(self):
        pattern = JuliaPattern()
        cfg = pattern._parse_config({"width": 400, "c_real": -0.5, "c_imag": 0.6})
        assert cfg.width == 400
        assert cfg.c_real == -0.5


@pytest.mark.asyncio
class TestSimulateJulia:
    async def test_simulation_completes(self):
        pattern = JuliaPattern()
        pattern.config = JuliaConfig(width=100, height=100, max_iter=50)
        result = await pattern._simulate_julia()
        assert "metrics" in result
        assert "logs" in result
        assert "iterations" in result

    async def test_connected_for_interior_c(self):
        pattern = JuliaPattern()
        pattern.config = JuliaConfig(width=50, height=50, max_iter=50, c_real=-0.1, c_imag=0.0)
        result = await pattern._simulate_julia()
        # c = -0.1 is inside Mandelbrot set, so Julia set should be connected
        assert result["metrics"]["connected"] is True

    async def test_disconnected_for_exterior_c(self):
        pattern = JuliaPattern()
        pattern.config = JuliaConfig(width=50, height=50, max_iter=50, c_real=1.0, c_imag=0.0)
        result = await pattern._simulate_julia()
        # c = 1.0 is outside Mandelbrot set
        assert result["metrics"]["connected"] is False

    async def test_area_estimate(self):
        pattern = JuliaPattern()
        pattern.config = JuliaConfig(width=100, height=100, max_iter=50)
        result = await pattern._simulate_julia()
        assert result["metrics"]["area_estimate"] >= 0

    async def test_fractal_dimension(self):
        pattern = JuliaPattern()
        pattern.config = JuliaConfig(width=100, height=100, max_iter=50)
        result = await pattern._simulate_julia()
        dim = result["metrics"]["fractal_dimension_estimate"]
        assert 0 <= dim <= 2.0


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = JuliaPattern()
        results = {
            "metrics": {
                "inside_points": 1000,
                "boundary_points": 500,
                "fractal_dimension_estimate": 1.5,
                "max_iter": 100,
            }
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = JuliaPattern()
        h = Hypothesis(title="Julia set", description="fractal")
        config = {"width": 100, "height": 100, "max_iter": 50}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = JuliaPattern.get_metadata()
        assert meta["id"] == "fractal_julia"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
