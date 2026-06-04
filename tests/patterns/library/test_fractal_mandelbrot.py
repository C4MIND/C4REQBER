"""
Tests for src/patterns/library/fractal_mandelbrot.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.fractal_mandelbrot import (
    MandelbrotPattern,
    MandelbrotConfig,
)
from src.patterns.core import Hypothesis, SimulationStatus



class TestMandelbrotConfig:
    def test_default_init(self):
        cfg = MandelbrotConfig()
        assert cfg.width == 800
        assert cfg.height == 600
        assert cfg.max_iter == 100

    def test_custom_init(self):
        cfg = MandelbrotConfig(width=400, max_iter=50)
        assert cfg.width == 400
        assert cfg.max_iter == 50


class TestMandelbrotPatternInit:
    def test_init(self):
        pattern = MandelbrotPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = MandelbrotPattern()
        param_names = [p.name for p in pattern.parameters]
        assert "width" in param_names
        assert "max_iter" in param_names


class TestCanSimulate:
    def test_matches_mandelbrot(self):
        pattern = MandelbrotPattern()
        h = Hypothesis(title="Mandelbrot set", description="fractal")
        assert pattern.can_simulate(h) is True

    def test_matches_fractal(self):
        pattern = MandelbrotPattern()
        h = Hypothesis(title="Fractal geometry", description="complex dynamics")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = MandelbrotPattern()
        h = Hypothesis(title="Stock market", description="trading")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_default_parsing(self):
        pattern = MandelbrotPattern()
        cfg = pattern._parse_config({})
        assert cfg.width == 800

    def test_custom_parsing(self):
        pattern = MandelbrotPattern()
        cfg = pattern._parse_config({"width": 400, "max_iter": 50})
        assert cfg.width == 400
        assert cfg.max_iter == 50


@pytest.mark.asyncio
class TestSimulateMandelbrot:
    async def test_simulation_completes(self):
        pattern = MandelbrotPattern()
        pattern.config = MandelbrotConfig(width=100, height=100, max_iter=50)
        result = await pattern._simulate_mandelbrot()
        assert "metrics" in result
        assert "logs" in result
        assert "iterations" in result

    async def test_inside_points(self):
        pattern = MandelbrotPattern()
        pattern.config = MandelbrotConfig(width=100, height=100, max_iter=50)
        result = await pattern._simulate_mandelbrot()
        assert result["metrics"]["inside_points"] > 0

    async def test_area_estimate(self):
        pattern = MandelbrotPattern()
        pattern.config = MandelbrotConfig(width=100, height=100, max_iter=50)
        result = await pattern._simulate_mandelbrot()
        # Known area ~1.506
        assert 1.0 < result["metrics"]["area_estimate"] < 2.5

    async def test_boundary_points(self):
        pattern = MandelbrotPattern()
        pattern.config = MandelbrotConfig(width=100, height=100, max_iter=50)
        result = await pattern._simulate_mandelbrot()
        assert result["metrics"]["boundary_points"] >= 0

    async def test_cardioid_points(self):
        pattern = MandelbrotPattern()
        pattern.config = MandelbrotConfig(width=100, height=100, max_iter=50)
        result = await pattern._simulate_mandelbrot()
        assert result["metrics"]["cardioid_points"] >= 0

    async def test_iterations_shape(self):
        pattern = MandelbrotPattern()
        pattern.config = MandelbrotConfig(width=50, height=40, max_iter=50)
        result = await pattern._simulate_mandelbrot()
        iterations = np.array(result["iterations"])
        assert iterations.shape == (40, 50)


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = MandelbrotPattern()
        results = {"metrics": {"area_estimate": 1.5, "inside_points": 1000, "boundary_points": 500, "max_iter": 100, "cardioid_points": 10}}
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = MandelbrotPattern()
        h = Hypothesis(title="Mandelbrot set", description="fractal")
        config = {"width": 100, "height": 100, "max_iter": 50}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = MandelbrotPattern.get_metadata()
        assert meta["id"] == "fractal_mandelbrot"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
