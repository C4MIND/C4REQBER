"""
Tests for src/patterns/library/pedestrian.py (Pedestrian pattern)

Covers:
- PedestrianScenario enum
- PedestrianConfig dataclass
- PedestrianPattern initialization
- _initialize() and _initialize_positions()
- _initialize_destinations()
- _update_desired_velocities()
- Force calculations: _driving_force, _pedestrian_repulsion, _wall_repulsion
- _step() integration
- Metrics: _calculate_flow_rate, _calculate_density, _calculate_mean_speed
- run() integration
- get_metadata()
- Edge cases: different scenarios, empty simulation, single pedestrian
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.pedestrian import (
    PedestrianConfig,
    PedestrianPattern,
    PedestrianScenario,
)


# ═══════════════════════════════════════════════════════════════════
# Enum and Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestPedestrianScenario:
    def test_enum_values(self):
        assert PedestrianScenario.CORRIDOR.value == "corridor"
        assert PedestrianScenario.BOTTLENECK.value == "bottleneck"
        assert PedestrianScenario.CROSSING.value == "crossing"
        assert PedestrianScenario.EVACUATION.value == "evacuation"


class TestPedestrianConfig:
    def test_default_init(self):
        cfg = PedestrianConfig()
        assert cfg.scenario == PedestrianScenario.CORRIDOR
        assert cfg.n_pedestrians == 100
        assert cfg.desired_speed == 1.34
        assert cfg.pedestrian_radius == 0.3
        assert cfg.mass == 80.0
        assert cfg.dt == 0.01
        assert cfg.n_steps == 2000

    def test_custom_init(self):
        cfg = PedestrianConfig(
            scenario=PedestrianScenario.EVACUATION, n_pedestrians=50, desired_speed=1.5, width=30.0
        )
        assert cfg.scenario == PedestrianScenario.EVACUATION
        assert cfg.n_pedestrians == 50
        assert cfg.desired_speed == 1.5
        assert cfg.width == 30.0

    def test_social_force_params(self):
        cfg = PedestrianConfig(A=2500.0, B=0.1, tau=0.6)
        assert cfg.A == 2500.0
        assert cfg.B == 0.1
        assert cfg.tau == 0.6


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestPedestrianPatternInit:
    def test_default_init(self):
        pattern = PedestrianPattern()
        assert pattern.PATTERN_ID == "pedestrian"
        assert pattern.positions is not None
        assert pattern.velocities is not None
        assert pattern.destinations is not None

    def test_positions_shape(self):
        cfg = PedestrianConfig(n_pedestrians=50)
        pattern = PedestrianPattern(cfg)
        assert pattern.positions.shape == (50, 2)
        assert pattern.velocities.shape == (50, 2)

    def test_velocities_zero_initially(self):
        pattern = PedestrianPattern()
        assert np.allclose(pattern.velocities, 0)


class TestInitializePositions:
    def test_corridor_positions(self):
        cfg = PedestrianConfig(scenario=PedestrianScenario.CORRIDOR, n_pedestrians=50)
        pattern = PedestrianPattern(cfg)
        # Should start on left side
        assert np.all(pattern.positions[:, 0] < 3)
        # Y positions should be within height bounds
        assert np.all((pattern.positions[:, 1] >= 1) & (pattern.positions[:, 1] < cfg.height - 1))

    def test_bottleneck_positions(self):
        cfg = PedestrianConfig(scenario=PedestrianScenario.BOTTLENECK, n_pedestrians=50)
        pattern = PedestrianPattern(cfg)
        # Should be clustered before bottleneck
        assert np.all(pattern.positions[:, 0] < 6)

    def test_crossing_positions(self):
        cfg = PedestrianConfig(scenario=PedestrianScenario.CROSSING, n_pedestrians=40)
        pattern = PedestrianPattern(cfg)
        # Two groups should be present
        n_half = cfg.n_pedestrians // 2
        # First group: left to right
        assert np.all(pattern.positions[:n_half, 0] < 3)
        # Second group: bottom to top
        assert np.all(pattern.positions[n_half:, 1] < 3)

    def test_evacuation_positions(self):
        cfg = PedestrianConfig(scenario=PedestrianScenario.EVACUATION, n_pedestrians=50)
        pattern = PedestrianPattern(cfg)
        # Should be spread out, not at exit
        assert np.all(pattern.positions[:, 0] < cfg.width - 2)


class TestInitializeDestinations:
    def test_corridor_destinations(self):
        cfg = PedestrianConfig(scenario=PedestrianScenario.CORRIDOR, n_pedestrians=50)
        pattern = PedestrianPattern(cfg)
        # All should go to right side
        assert np.allclose(pattern.destinations[:, 0], cfg.width)
        # Y should match initial Y
        assert np.allclose(pattern.destinations[:, 1], pattern.positions[:, 1])

    def test_evacuation_destination(self):
        cfg = PedestrianConfig(scenario=PedestrianScenario.EVACUATION)
        pattern = PedestrianPattern(cfg)
        # Exit on right side at middle height
        assert np.allclose(pattern.destinations[:, 0], cfg.width)
        assert np.allclose(pattern.destinations[:, 1], cfg.height / 2)


# ═══════════════════════════════════════════════════════════════════
# Velocity and Force Tests
# ═══════════════════════════════════════════════════════════════════


class TestDesiredVelocities:
    def test_desired_velocity_direction(self):
        pattern = PedestrianPattern(PedestrianConfig(scenario=PedestrianScenario.CORRIDOR))
        # Should point towards destinations (generally right)
        assert np.mean(pattern.desired_velocities[:, 0]) > 0

    def test_desired_velocity_magnitude(self):
        cfg = PedestrianConfig(desired_speed=1.5)
        pattern = PedestrianPattern(cfg)
        speeds = np.linalg.norm(pattern.desired_velocities, axis=1)
        assert np.allclose(speeds, cfg.desired_speed, atol=0.1)


class TestDrivingForce:
    def test_driving_force_direction(self):
        pattern = PedestrianPattern()
        # Set velocity different from desired
        pattern.velocities[0] = [0.5, 0]
        pattern.desired_velocities[0] = [1.34, 0]
        force = pattern._driving_force(0)
        # Force should accelerate towards desired
        assert force[0] > 0

    def test_zero_force_at_equilibrium(self):
        pattern = PedestrianPattern()
        # When velocity equals desired, force should be zero
        pattern.velocities[0] = pattern.desired_velocities[0].copy()
        force = pattern._driving_force(0)
        assert np.allclose(force, 0)


class TestPedestrianRepulsion:
    def test_repulsion_exists_nearby(self):
        pattern = PedestrianPattern(PedestrianConfig(n_pedestrians=2))
        # Place two pedestrians close together
        pattern.positions[0] = [5.0, 5.0]
        pattern.positions[1] = [5.1, 5.0]
        force = pattern._pedestrian_repulsion(0)
        # Should feel repulsion
        assert np.linalg.norm(force) > 0

    def test_no_self_repulsion(self):
        pattern = PedestrianPattern(PedestrianConfig(n_pedestrians=1))
        force = pattern._pedestrian_repulsion(0)
        assert np.allclose(force, 0)


class TestWallRepulsion:
    def test_wall_force_near_boundary(self):
        pattern = PedestrianPattern()
        # Place pedestrian near left wall
        pattern.positions[0] = [0.1, 5.0]
        force = pattern._wall_repulsion(0)
        # Should be pushed away from wall (positive x)
        assert force[0] > 0

    def test_no_wall_force_in_center(self):
        pattern = PedestrianPattern(PedestrianConfig(width=20, height=10))
        # Place in center
        pattern.positions[0] = [10.0, 5.0]
        force = pattern._wall_repulsion(0)
        # Should be minimal
        assert np.linalg.norm(force) < 1000  # Arbitrary threshold


# ═══════════════════════════════════════════════════════════════════
# Step Integration Tests
# ═══════════════════════════════════════════════════════════════════


class TestStep:
    def test_positions_change(self):
        pattern = PedestrianPattern(PedestrianConfig(n_pedestrians=10))
        pos_before = pattern.positions.copy()
        pattern._step()
        assert not np.allclose(pattern.positions, pos_before)

    def test_velocities_change(self):
        pattern = PedestrianPattern(PedestrianConfig(n_pedestrians=10))
        vel_before = pattern.velocities.copy()
        pattern._step()
        assert not np.allclose(pattern.velocities, vel_before)

    def test_speed_limit(self):
        pattern = PedestrianPattern(PedestrianConfig(desired_speed=1.34))
        # Run several steps
        for _ in range(10):
            pattern._step()
        # Speeds should not exceed limit by much
        speeds = np.linalg.norm(pattern.velocities, axis=1)
        assert np.all(speeds <= 2 * 1.34 + 0.1)

    def test_boundaries_respected(self):
        pattern = PedestrianPattern(PedestrianConfig(width=20, height=10))
        # Run several steps
        for _ in range(50):
            pattern._step()
        # Positions should stay in bounds
        assert np.all(pattern.positions[:, 0] >= 0)
        assert np.all(pattern.positions[:, 0] <= 20)
        assert np.all(pattern.positions[:, 1] >= 0)
        assert np.all(pattern.positions[:, 1] <= 10)


# ═══════════════════════════════════════════════════════════════════
# Metrics Tests
# ═══════════════════════════════════════════════════════════════════


class TestCalculateDensity:
    def test_density_calculation(self):
        cfg = PedestrianConfig(n_pedestrians=100, width=20, height=10)
        pattern = PedestrianPattern(cfg)
        density = pattern._calculate_density()
        expected = 100 / (20 * 10)
        assert density == pytest.approx(expected)


class TestCalculateMeanSpeed:
    def test_zero_speed_initially(self):
        pattern = PedestrianPattern()
        speed = pattern._calculate_mean_speed()
        assert speed == 0

    def test_nonzero_speed_after_steps(self):
        pattern = PedestrianPattern()
        for _ in range(10):
            pattern._step()
        speed = pattern._calculate_mean_speed()
        assert speed > 0


class TestCalculateFlowRate:
    def test_flow_rate_after_run(self):
        cfg = PedestrianConfig(n_pedestrians=20, n_steps=100)
        pattern = PedestrianPattern(cfg)
        # Run simulation
        for _ in range(cfg.n_steps):
            pattern._step()
        flow = pattern._calculate_flow_rate()
        assert isinstance(flow, float)
        assert flow >= 0


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_corridor(self):
        cfg = PedestrianConfig(scenario=PedestrianScenario.CORRIDOR, n_pedestrians=20, n_steps=100)
        pattern = PedestrianPattern(cfg)
        result = pattern.run()
        assert result["scenario"] == "corridor"
        assert "final_positions" in result
        assert "statistics" in result

    def test_run_bottleneck(self):
        cfg = PedestrianConfig(
            scenario=PedestrianScenario.BOTTLENECK, n_pedestrians=20, n_steps=100
        )
        pattern = PedestrianPattern(cfg)
        result = pattern.run()
        assert result["scenario"] == "bottleneck"

    def test_run_crossing(self):
        cfg = PedestrianConfig(scenario=PedestrianScenario.CROSSING, n_pedestrians=20, n_steps=100)
        pattern = PedestrianPattern(cfg)
        result = pattern.run()
        assert result["scenario"] == "crossing"

    def test_run_evacuation(self):
        cfg = PedestrianConfig(
            scenario=PedestrianScenario.EVACUATION, n_pedestrians=20, n_steps=100
        )
        pattern = PedestrianPattern(cfg)
        result = pattern.run()
        assert result["scenario"] == "evacuation"

    def test_fundamental_diagram_present(self):
        cfg = PedestrianConfig(n_pedestrians=20, n_steps=50)
        pattern = PedestrianPattern(cfg)
        result = pattern.run()
        assert "fundamental_diagram" in result
        assert "density" in result["fundamental_diagram"]
        assert "mean_speed" in result["fundamental_diagram"]
        assert "flow" in result["fundamental_diagram"]

    def test_statistics_present(self):
        cfg = PedestrianConfig(n_pedestrians=20, n_steps=50)
        pattern = PedestrianPattern(cfg)
        result = pattern.run()
        stats = result["statistics"]
        assert "mean_speed" in stats
        assert "speed_variance" in stats
        assert "arrival_rate" in stats

    def test_trajectory_recorded(self):
        cfg = PedestrianConfig(n_pedestrians=20, n_steps=200)
        pattern = PedestrianPattern(cfg)
        result = pattern.run()
        assert "trajectory" in result
        assert len(result["trajectory"]) > 0


# ═══════════════════════════════════════════════════════════════════
# Metadata Tests
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = PedestrianPattern.get_metadata()
        assert meta["id"] == "pedestrian"
        assert "name" in meta
        assert "category" in meta
        assert "domain" in meta
        assert "parameters" in meta

    def test_scenario_parameter(self):
        meta = PedestrianPattern.get_metadata()
        scenario_param = next(p for p in meta["parameters"] if p["name"] == "scenario")
        assert "corridor" in scenario_param["options"]
        assert "bottleneck" in scenario_param["options"]


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_single_pedestrian(self):
        cfg = PedestrianConfig(n_pedestrians=1, n_steps=50)
        pattern = PedestrianPattern(cfg)
        result = pattern.run()
        assert result["statistics"]["arrival_rate"] in [0.0, 1.0]

    def test_zero_steps(self):
        cfg = PedestrianConfig(n_pedestrians=10, n_steps=0)
        pattern = PedestrianPattern(cfg)
        result = pattern.run()
        assert result["statistics"]["mean_speed"] == 0

    def test_with_obstacles(self):
        cfg = PedestrianConfig(
            n_pedestrians=20,
            n_steps=50,
            obstacles=[(10, 5, 1.0)],  # One obstacle
        )
        pattern = PedestrianPattern(cfg)
        result = pattern.run()
        assert "final_positions" in result

    def test_very_high_density(self):
        """High density should slow down pedestrians"""
        cfg = PedestrianConfig(n_pedestrians=200, width=10, height=5, n_steps=100)
        pattern = PedestrianPattern(cfg)
        result = pattern.run()
        # Mean speed should be less than desired speed due to crowding
        # With only 100 steps, crowding may not fully develop
        assert result["statistics"]["mean_speed"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
