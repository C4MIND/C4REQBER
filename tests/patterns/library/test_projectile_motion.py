"""
Tests for src/patterns/library/projectile_motion.py
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.core import Hypothesis, SimulationStatus
from src.patterns.library.projectile_motion import (
    ProjectileConfig,
    ProjectileMotionPattern,
)


class TestProjectileConfig:
    def test_default_init(self):
        cfg = ProjectileConfig()
        assert cfg.v0 == 50.0
        assert cfg.angle == 45.0
        assert cfg.mass == 0.5

    def test_custom_init(self):
        cfg = ProjectileConfig(v0=100.0, angle=30.0, mass=1.0)
        assert cfg.v0 == 100.0
        assert cfg.angle == 30.0


class TestProjectileMotionPatternInit:
    def test_init(self):
        pattern = ProjectileMotionPattern()
        assert pattern is not None

    def test_parameters_defined(self):
        pattern = ProjectileMotionPattern()
        param_names = [p.name for p in pattern.parameters]
        assert "v0" in param_names
        assert "angle" in param_names


class TestCanSimulate:
    def test_matches_projectile(self):
        pattern = ProjectileMotionPattern()
        h = Hypothesis(title="Projectile motion", description="trajectory")
        assert pattern.can_simulate(h) is True

    def test_matches_ballistics(self):
        pattern = ProjectileMotionPattern()
        h = Hypothesis(title="Ballistics", description="air resistance")
        assert pattern.can_simulate(h) is True

    def test_no_match(self):
        pattern = ProjectileMotionPattern()
        h = Hypothesis(title="Heat transfer", description="conduction")
        assert pattern.can_simulate(h) is False


class TestParseConfig:
    def test_default_parsing(self):
        pattern = ProjectileMotionPattern()
        cfg = pattern._parse_config({})
        assert cfg.v0 == 50.0

    def test_custom_parsing(self):
        pattern = ProjectileMotionPattern()
        cfg = pattern._parse_config({"v0": 100.0, "angle": 30.0})
        assert cfg.v0 == 100.0
        assert cfg.angle == 30.0


@pytest.mark.asyncio
class TestSimulateProjectile:
    async def test_simulation_completes(self):
        pattern = ProjectileMotionPattern()
        pattern.config = ProjectileConfig(v0=50.0, angle=45.0, t_max=10.0)
        result = await pattern._simulate_projectile()
        assert "metrics" in result
        assert "logs" in result
        assert "x" in result
        assert "y" in result

    async def test_range_positive(self):
        pattern = ProjectileMotionPattern()
        pattern.config = ProjectileConfig(v0=50.0, angle=45.0, t_max=10.0)
        result = await pattern._simulate_projectile()
        assert result["metrics"]["range"] > 0

    async def test_apogee_positive(self):
        pattern = ProjectileMotionPattern()
        pattern.config = ProjectileConfig(v0=50.0, angle=45.0, t_max=10.0)
        result = await pattern._simulate_projectile()
        assert result["metrics"]["apogee"] > 0

    async def test_range_less_than_vacuum(self):
        pattern = ProjectileMotionPattern()
        pattern.config = ProjectileConfig(v0=50.0, angle=45.0, drag_coefficient=0.47, t_max=10.0)
        result = await pattern._simulate_projectile()
        assert result["metrics"]["range"] <= result["metrics"]["range_vacuum"]

    async def test_time_of_flight_positive(self):
        pattern = ProjectileMotionPattern()
        pattern.config = ProjectileConfig(v0=50.0, angle=45.0, t_max=10.0)
        result = await pattern._simulate_projectile()
        assert result["metrics"]["time_of_flight"] > 0

    async def test_zero_drag_matches_vacuum(self):
        pattern = ProjectileMotionPattern()
        pattern.config = ProjectileConfig(v0=50.0, angle=45.0, drag_coefficient=0.0, t_max=10.0)
        result = await pattern._simulate_projectile()
        assert result["metrics"]["range"] == pytest.approx(
            result["metrics"]["range_vacuum"], rel=0.05
        )


class TestCalculateConfidence:
    def test_high_confidence(self):
        pattern = ProjectileMotionPattern()
        results = {
            "metrics": {"range": 100.0, "range_vacuum": 150.0, "apogee": 50.0, "impact_speed": 40.0}
        }
        confidence = pattern._calculate_confidence(results)
        assert confidence > 0.5


@pytest.mark.asyncio
class TestRun:
    async def test_run_default(self):
        pattern = ProjectileMotionPattern()
        h = Hypothesis(title="Projectile motion", description="trajectory")
        config = {"v0": 50.0, "angle": 45.0}
        result = await pattern.run(h, config)
        assert result.status == SimulationStatus.COMPLETED


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = ProjectileMotionPattern.get_metadata()
        assert meta["id"] == "projectile_motion"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
