"""
Tests for src/patterns/library/flocking.py (Flocking pattern)

Covers:
- FlockingModel enum
- FlockingConfig dataclass
- FlockingPattern initialization
- _initialize() and _distance_matrix()
- Boids rules: _separation, _alignment, _cohesion
- _avoid_obstacles()
- _limit_magnitude()
- _boids_step() and _vicsek_step()
- _apply_boundaries()
- Order parameter and clustering
- run() integration
- get_metadata()
- Edge cases: different models, boundary conditions, obstacles
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.flocking import FlockingPattern, FlockingConfig, FlockingModel



# ═══════════════════════════════════════════════════════════════════
# Enum and Config Tests
# ═══════════════════════════════════════════════════════════════════


class TestFlockingModel:
    def test_enum_values(self):
        assert FlockingModel.BOIDS.value == "boids"
        assert FlockingModel.VICSEK.value == "vicsek"


class TestFlockingConfig:
    def test_default_init(self):
        cfg = FlockingConfig()
        assert cfg.model == FlockingModel.BOIDS
        assert cfg.n_agents == 200
        assert cfg.space_size == (100.0, 100.0)
        assert cfg.boundary_mode == "periodic"
        assert cfg.perception_radius == 10.0
        assert cfg.separation_distance == 3.0
        assert cfg.max_speed == 2.0

    def test_custom_init(self):
        cfg = FlockingConfig(
            model=FlockingModel.VICSEK,
            n_agents=100,
            space_size=(50.0, 50.0),
            boundary_mode="reflective"
        )
        assert cfg.model == FlockingModel.VICSEK
        assert cfg.n_agents == 100
        assert cfg.space_size == (50.0, 50.0)
        assert cfg.boundary_mode == "reflective"

    def test_boids_weights(self):
        cfg = FlockingConfig(
            separation_weight=2.0,
            alignment_weight=1.5,
            cohesion_weight=0.5
        )
        assert cfg.separation_weight == 2.0
        assert cfg.alignment_weight == 1.5
        assert cfg.cohesion_weight == 0.5


# ═══════════════════════════════════════════════════════════════════
# Initialization Tests
# ═══════════════════════════════════════════════════════════════════


class TestFlockingPatternInit:
    def test_default_init(self):
        pattern = FlockingPattern()
        assert pattern.PATTERN_ID == "flocking"
        assert pattern.positions is not None
        assert pattern.velocities is not None
        assert len(pattern.history) == 1  # Initial state recorded

    def test_positions_shape(self):
        cfg = FlockingConfig(n_agents=50)
        pattern = FlockingPattern(cfg)
        assert pattern.positions.shape == (50, 2)
        assert pattern.velocities.shape == (50, 2)

    def test_positions_in_bounds(self):
        cfg = FlockingConfig(n_agents=50, space_size=(50.0, 50.0))
        pattern = FlockingPattern(cfg)
        assert np.all(pattern.positions >= 0)
        assert np.all(pattern.positions[:, 0] < 50.0)
        assert np.all(pattern.positions[:, 1] < 50.0)

    def test_velocities_nonzero(self):
        pattern = FlockingPattern()
        speeds = np.linalg.norm(pattern.velocities, axis=1)
        assert np.all(speeds > 0)
        assert np.all(speeds <= pattern.config.max_speed)


# ═══════════════════════════════════════════════════════════════════
# Distance Matrix Tests
# ═══════════════════════════════════════════════════════════════════


class TestDistanceMatrix:
    def test_distance_matrix_shape(self):
        pattern = FlockingPattern(FlockingConfig(n_agents=10))
        dist = pattern._distance_matrix()
        assert dist.shape == (10, 10)

    def test_zero_diagonal(self):
        pattern = FlockingPattern(FlockingConfig(n_agents=10))
        dist = pattern._distance_matrix()
        assert np.allclose(np.diag(dist), 0)

    def test_symmetry(self):
        pattern = FlockingPattern(FlockingConfig(n_agents=10))
        dist = pattern._distance_matrix()
        assert np.allclose(dist, dist.T)

    def test_periodic_boundary_distances(self):
        cfg = FlockingConfig(n_agents=10, space_size=(10.0, 10.0), boundary_mode="periodic")
        pattern = FlockingPattern(cfg)
        # Place agents at edges
        pattern.positions[0] = [0.5, 5.0]
        pattern.positions[1] = [9.5, 5.0]
        dist = pattern._distance_matrix()
        # Periodic distance should be small (1.0)
        assert dist[0, 1] < 2.0


# ═══════════════════════════════════════════════════════════════════
# Boids Rules Tests
# ═══════════════════════════════════════════════════════════════════


class TestSeparation:
    def test_separation_pushes_apart(self):
        pattern = FlockingPattern(FlockingConfig(n_agents=2))
        # Place agents close together
        pattern.positions[0] = [5.0, 5.0]
        pattern.positions[1] = [5.5, 5.0]
        neighbors = np.array([True, True])
        sep = pattern._separation(0, neighbors)
        # Should push away from neighbor (negative x)
        assert sep[0] < 0

    def test_no_separation_when_far(self):
        pattern = FlockingPattern(FlockingConfig(n_agents=2, separation_distance=1.0))
        pattern.positions[0] = [5.0, 5.0]
        pattern.positions[1] = [10.0, 5.0]
        neighbors = np.array([True, True])
        sep = pattern._separation(0, neighbors)
        # When far apart, no separation force
        assert np.linalg.norm(sep) < 0.1


class TestAlignment:
    def test_alignment_average_velocity(self):
        pattern = FlockingPattern(FlockingConfig(n_agents=3))
        pattern.velocities[0] = [1.0, 0.0]
        pattern.velocities[1] = [2.0, 0.0]
        pattern.velocities[2] = [0.0, 0.0]  # Self
        neighbors = np.array([True, True, False])
        ali = pattern._alignment(2, neighbors)
        # Should steer towards average of neighbors (1.5, 0)
        assert ali[0] > 0

    def test_no_alignment_alone(self):
        pattern = FlockingPattern(FlockingConfig(n_agents=1))
        neighbors = np.array([False])
        ali = pattern._alignment(0, neighbors)
        assert np.allclose(ali, 0)


class TestCohesion:
    def test_cohesion_towards_center(self):
        pattern = FlockingPattern(FlockingConfig(n_agents=3))
        pattern.positions[0] = [0.0, 0.0]  # Self
        pattern.positions[1] = [10.0, 0.0]
        pattern.positions[2] = [0.0, 10.0]
        neighbors = np.array([False, True, True])
        coh = pattern._cohesion(0, neighbors)
        # Should steer towards center (5, 5)
        assert coh[0] > 0
        assert coh[1] > 0


# ═══════════════════════════════════════════════════════════════════
# Obstacle and Utility Tests
# ═══════════════════════════════════════════════════════════════════


class TestAvoidObstacles:
    def test_obstacle_avoidance(self):
        cfg = FlockingConfig(
            n_agents=1,
            obstacle_positions=np.array([[5.0, 5.0]]),
            obstacle_radius=2.0
        )
        pattern = FlockingPattern(cfg)
        pattern.positions[0] = [5.0, 3.0]  # Close to obstacle
        avoid = pattern._avoid_obstacles(0)
        # Should push away from obstacle
        assert avoid[1] < 0  # Push down

    def test_no_avoidance_when_far(self):
        cfg = FlockingConfig(
            n_agents=1,
            obstacle_positions=np.array([[50.0, 50.0]]),
            obstacle_radius=5.0
        )
        pattern = FlockingPattern(cfg)
        pattern.positions[0] = [5.0, 5.0]
        avoid = pattern._avoid_obstacles(0)
        assert np.allclose(avoid, 0)


class TestLimitMagnitude:
    def test_limits_excess(self):
        pattern = FlockingPattern()
        vec = np.array([10.0, 0.0])
        limited = pattern._limit_magnitude(vec, 2.0)
        assert np.linalg.norm(limited) == pytest.approx(2.0)

    def test_no_change_when_small(self):
        pattern = FlockingPattern()
        vec = np.array([1.0, 0.0])
        limited = pattern._limit_magnitude(vec, 2.0)
        assert np.allclose(limited, vec)


# ═══════════════════════════════════════════════════════════════════
# Step Integration Tests
# ═══════════════════════════════════════════════════════════════════


class TestBoidsStep:
    def test_positions_change(self):
        pattern = FlockingPattern(FlockingConfig(n_agents=10))
        pos_before = pattern.positions.copy()
        pattern._boids_step()
        assert not np.allclose(pattern.positions, pos_before)

    def test_velocities_limited(self):
        pattern = FlockingPattern(FlockingConfig(n_agents=10, max_speed=2.0))
        pattern._boids_step()
        speeds = np.linalg.norm(pattern.velocities, axis=1)
        assert np.all(speeds <= 2.0 + 0.01)


class TestVicsekStep:
    def test_constant_speed(self):
        cfg = FlockingConfig(model=FlockingModel.VICSEK, n_agents=10, velocity=1.5)
        pattern = FlockingPattern(cfg)
        pattern._vicsek_step()
        speeds = np.linalg.norm(pattern.velocities, axis=1)
        assert np.allclose(speeds, 1.5, atol=0.01)

    def test_noise_changes_direction(self):
        np.random.seed(42)
        cfg = FlockingConfig(
            model=FlockingModel.VICSEK,
            n_agents=10,
            noise_strength=0.5
        )
        pattern = FlockingPattern(cfg)
        vel_before = pattern.velocities.copy()
        pattern._vicsek_step()
        assert not np.allclose(pattern.velocities, vel_before)


class TestApplyBoundaries:
    def test_periodic_boundary(self):
        cfg = FlockingConfig(n_agents=1, boundary_mode="periodic", space_size=(10.0, 10.0))
        pattern = FlockingPattern(cfg)
        pattern.positions[0] = [10.5, 5.0]  # Past boundary
        pattern._apply_boundaries()
        assert pattern.positions[0, 0] < 10.0
        assert pattern.positions[0, 0] >= 0

    def test_reflective_boundary(self):
        cfg = FlockingConfig(n_agents=1, boundary_mode="reflective", space_size=(10.0, 10.0))
        pattern = FlockingPattern(cfg)
        pattern.positions[0] = [-0.5, 5.0]  # Past boundary
        pattern.velocities[0] = [-1.0, 0.0]  # Moving outward
        pattern._apply_boundaries()
        assert pattern.positions[0, 0] >= 0
        # Velocity should have been flipped
        assert pattern.velocities[0, 0] > 0


# ═══════════════════════════════════════════════════════════════════
# Order Parameter Tests
# ═══════════════════════════════════════════════════════════════════


class TestOrderParameter:
    def test_order_zero_when_random(self):
        pattern = FlockingPattern(FlockingConfig(n_agents=100))
        order = pattern._calculate_order_parameter()
        # Random initial velocities should have low order
        assert order < 0.3

    def test_order_one_when_aligned(self):
        pattern = FlockingPattern(FlockingConfig(n_agents=10))
        # Align all velocities
        pattern.velocities = np.ones((10, 2))
        order = pattern._calculate_order_parameter()
        assert order > 0.7


class TestClustering:
    def test_clustering_positive(self):
        pattern = FlockingPattern(FlockingConfig(n_agents=10))
        clustering = pattern._calculate_clustering()
        assert clustering > 0


# ═══════════════════════════════════════════════════════════════════
# Run Integration Tests
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_boids(self):
        cfg = FlockingConfig(model=FlockingModel.BOIDS, n_agents=20, n_steps=50)
        pattern = FlockingPattern(cfg)
        result = pattern.run()
        assert result["config"]["model"] == "boids"
        assert "final_positions" in result
        assert "order_parameter" in result

    def test_run_vicsek(self):
        cfg = FlockingConfig(model=FlockingModel.VICSEK, n_agents=20, n_steps=50)
        pattern = FlockingPattern(cfg)
        result = pattern.run()
        assert result["config"]["model"] == "vicsek"
        assert "order_parameter" in result

    def test_order_increases(self):
        """Flocking should increase order over time"""
        cfg = FlockingConfig(
            model=FlockingModel.BOIDS,
            n_agents=50,
            n_steps=200,
            separation_weight=1.0,
            alignment_weight=2.0,
            cohesion_weight=1.0
        )
        pattern = FlockingPattern(cfg)
        result = pattern.run()
        # Average order should be higher than random
        assert result["order_parameter"]["average"] > 0.05

    def test_trajectory_recorded(self):
        cfg = FlockingConfig(n_agents=20, n_steps=100)
        pattern = FlockingPattern(cfg)
        result = pattern.run()
        assert "trajectory" in result
        assert len(result["trajectory"]) > 0

    def test_statistics_present(self):
        cfg = FlockingConfig(n_agents=20, n_steps=50)
        pattern = FlockingPattern(cfg)
        result = pattern.run()
        stats = result["statistics"]
        assert "mean_speed" in stats
        assert "speed_variance" in stats
        assert "clustering_distance" in stats


# ═══════════════════════════════════════════════════════════════════
# Metadata Tests
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = FlockingPattern.get_metadata()
        assert meta["id"] == "flocking"
        assert "name" in meta
        assert "category" in meta
        assert "domain" in meta
        assert "parameters" in meta

    def test_model_parameter(self):
        meta = FlockingPattern.get_metadata()
        model_param = next(p for p in meta["parameters"] if p["name"] == "model")
        assert "boids" in model_param["options"]
        assert "vicsek" in model_param["options"]


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_single_agent(self):
        cfg = FlockingConfig(n_agents=1, n_steps=20)
        pattern = FlockingPattern(cfg)
        result = pattern.run()
        assert result["statistics"]["mean_speed"] > 0

    def test_zero_steps(self):
        cfg = FlockingConfig(n_agents=10, n_steps=0)
        pattern = FlockingPattern(cfg)
        result = pattern.run()
        assert len(result["trajectory"]) == 1  # Just initial state

    def test_very_high_noise(self):
        """High noise should prevent flocking"""
        cfg = FlockingConfig(
            model=FlockingModel.VICSEK,
            n_agents=50,
            n_steps=100,
            noise_strength=3.0  # Very high noise
        )
        pattern = FlockingPattern(cfg)
        result = pattern.run()
        # Order should remain low with high noise
        assert result["order_parameter"]["final"] < 0.5

    def test_zero_noise(self):
        """Zero noise should allow perfect alignment"""
        cfg = FlockingConfig(
            model=FlockingModel.VICSEK,
            n_agents=20,
            n_steps=50,
            noise_strength=0.0
        )
        pattern = FlockingPattern(cfg)
        # Start with some alignment
        pattern.velocities = np.random.randn(20, 2) * 0.1 + 1.0
        result = pattern.run()
        # Order should be high
        assert result["order_parameter"]["final"] > 0.45


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
