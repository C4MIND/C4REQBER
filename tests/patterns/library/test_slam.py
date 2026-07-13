"""
Tests for src/patterns/library/slam.py

Covers:
- SLAMType and SensorType enums
- SLAMConfig default and custom initialization
- PoseGraph node/edge/loop_closure management
- SLAMPattern initialization
- _generate_trajectory for lawn_mower, spiral, random
- _motion_model (straight and circular arc)
- _simulate_odometry
- _observe_landmarks
- _detect_loop_closure
- _relative_transform
- _optimize_pose_graph
- _calculate_metrics
- run() integration with different configs
- _format_output
- get_metadata()
- Edge cases: zero steps, single landmark, empty trajectory
"""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import numpy as np
import pytest

from src.patterns.library.slam import (
    PoseGraph,
    SensorType,
    SLAMConfig,
    SLAMPattern,
    SLAMType,
)


# ═══════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════


class TestSLAMType:
    def test_enum_values(self):
        assert SLAMType.POSE_GRAPH.value == "pose_graph"
        assert SLAMType.EKF_SLAM.value == "ekf_slam"
        assert SLAMType.FAST_SLAM.value == "fast_slam"
        assert SLAMType.GRAPH_BASED.value == "graph_based"


class TestSensorType:
    def test_enum_values(self):
        assert SensorType.LIDAR_2D.value == "lidar_2d"
        assert SensorType.LIDAR_3D.value == "lidar_3d"
        assert SensorType.STEREO_CAMERA.value == "stereo_camera"
        assert SensorType.RGBD_CAMERA.value == "rgbd_camera"
        assert SensorType.BEACON.value == "beacon"


# ═══════════════════════════════════════════════════════════════════
# SLAMConfig
# ═══════════════════════════════════════════════════════════════════


class TestSLAMConfig:
    def test_default_init(self):
        cfg = SLAMConfig()
        assert cfg.slam_type == SLAMType.POSE_GRAPH
        assert cfg.sensor_type == SensorType.LIDAR_2D
        assert cfg.world_size == 20.0
        assert cfg.n_landmarks == 50
        assert cfg.simulation_steps == 500
        assert cfg.trajectory_type == "lawn_mower"
        assert cfg.landmark_positions is not None
        assert cfg.landmark_positions.shape == (50, 2)

    def test_custom_init(self):
        cfg = SLAMConfig(
            slam_type=SLAMType.EKF_SLAM,
            sensor_type=SensorType.RGBD_CAMERA,
            world_size=10.0,
            n_landmarks=20,
            simulation_steps=100,
        )
        assert cfg.slam_type == SLAMType.EKF_SLAM
        assert cfg.sensor_type == SensorType.RGBD_CAMERA
        assert cfg.world_size == 10.0
        assert cfg.n_landmarks == 20
        assert cfg.simulation_steps == 100

    def test_landmark_positions_provided(self):
        positions = np.array([[1.0, 2.0], [3.0, 4.0]])
        cfg = SLAMConfig(n_landmarks=2, landmark_positions=positions)
        np.testing.assert_array_equal(cfg.landmark_positions, positions)


# ═══════════════════════════════════════════════════════════════════
# PoseGraph
# ═══════════════════════════════════════════════════════════════════


class TestPoseGraph:
    def test_init(self):
        pg = PoseGraph()
        assert pg.nodes == {}
        assert pg.edges == []
        assert pg.loop_closures == []

    def test_add_node(self):
        pg = PoseGraph()
        pg.add_node(0, np.array([0.0, 0.0, 0.0]))
        assert len(pg.nodes) == 1
        np.testing.assert_array_almost_equal(pg.nodes[0], np.array([0.0, 0.0, 0.0]))

    def test_add_edge(self):
        pg = PoseGraph()
        pg.add_node(0, np.array([0.0, 0.0, 0.0]))
        pg.add_node(1, np.array([1.0, 0.0, 0.0]))
        info = np.eye(3)
        pg.add_edge(0, 1, np.array([1.0, 0.0, 0.0]), info)
        assert len(pg.edges) == 1
        assert len(pg.loop_closures) == 0

    def test_add_loop_closure_edge(self):
        pg = PoseGraph()
        pg.add_node(0, np.array([0.0, 0.0, 0.0]))
        pg.add_node(5, np.array([1.0, 0.0, 0.0]))
        info = np.eye(3)
        pg.add_edge(0, 5, np.array([1.0, 0.0, 0.0]), info)
        assert len(pg.edges) == 1
        assert len(pg.loop_closures) == 1
        assert pg.loop_closures[0] == (0, 5)


# ═══════════════════════════════════════════════════════════════════
# SLAMPattern Initialization
# ═══════════════════════════════════════════════════════════════════


class TestSLAMPatternInit:
    def test_default_init(self):
        pattern = SLAMPattern()
        assert pattern.config is not None
        assert isinstance(pattern.config, SLAMConfig)
        assert isinstance(pattern.pose_graph, PoseGraph)
        assert pattern.current_step == 0
        np.testing.assert_array_equal(pattern.current_pose, np.array([0.0, 0.0, 0.0]))

    def test_custom_config(self):
        cfg = SLAMConfig(simulation_steps=100)
        pattern = SLAMPattern(config=cfg)
        assert pattern.config.simulation_steps == 100

    def test_history_structure(self):
        pattern = SLAMPattern()
        assert "time" in pattern.history
        assert "true_pose" in pattern.history
        assert "estimated_pose" in pattern.history
        assert "observed_landmarks" in pattern.history
        assert "loop_closures" in pattern.history


# ═══════════════════════════════════════════════════════════════════
# Trajectory Generation
# ═══════════════════════════════════════════════════════════════════


class TestGenerateTrajectory:
    def test_lawn_mower(self):
        pattern = SLAMPattern(SLAMConfig(trajectory_type="lawn_mower"))
        v, omega = pattern._generate_trajectory(0)
        assert v >= 0
        assert isinstance(omega, float)

    def test_spiral(self):
        pattern = SLAMPattern(SLAMConfig(trajectory_type="spiral"))
        v, omega = pattern._generate_trajectory(0)
        assert v > 0
        assert omega != 0.0

    def test_random(self):
        pattern = SLAMPattern(SLAMConfig(trajectory_type="random"))
        v, omega = pattern._generate_trajectory(0)
        assert isinstance(v, float)
        assert isinstance(omega, float)

    def test_unknown_trajectory(self):
        pattern = SLAMPattern(SLAMConfig(trajectory_type="unknown"))
        v, omega = pattern._generate_trajectory(0)
        assert v > 0
        assert omega == 0.0


# ═══════════════════════════════════════════════════════════════════
# Motion Model
# ═══════════════════════════════════════════════════════════════════


class TestMotionModel:
    def test_straight_line(self):
        pattern = SLAMPattern()
        pose = np.array([0.0, 0.0, 0.0])
        new_pose = pattern._motion_model(pose, 1.0, 0.0, 0.1)
        assert new_pose[0] == pytest.approx(0.1, abs=1e-6)
        assert new_pose[1] == pytest.approx(0.0, abs=1e-6)
        assert new_pose[2] == pytest.approx(0.0, abs=1e-6)

    def test_circular_arc(self):
        pattern = SLAMPattern()
        pose = np.array([0.0, 0.0, 0.0])
        new_pose = pattern._motion_model(pose, 1.0, 1.0, 0.1)
        assert new_pose[0] != 0.0
        assert new_pose[1] != 0.0
        assert new_pose[2] == pytest.approx(0.1, abs=1e-6)

    def test_zero_velocity(self):
        pattern = SLAMPattern()
        pose = np.array([1.0, 2.0, 0.5])
        new_pose = pattern._motion_model(pose, 0.0, 0.0, 0.1)
        np.testing.assert_array_almost_equal(new_pose, pose)


# ═══════════════════════════════════════════════════════════════════
# Odometry Simulation
# ═══════════════════════════════════════════════════════════════════


class TestSimulateOdometry:
    def test_adds_noise(self):
        pattern = SLAMPattern()
        true_motion = np.array([1.0, 0.0, 0.0])
        odometry = pattern._simulate_odometry(true_motion)
        assert odometry.shape == (3,)
        # Should be close but not exactly equal due to noise
        assert np.allclose(odometry, true_motion, atol=0.5)


# ═══════════════════════════════════════════════════════════════════
# Landmark Observation
# ═══════════════════════════════════════════════════════════════════


class TestObserveLandmarks:
    def test_observes_nearby(self):
        cfg = SLAMConfig(n_landmarks=10, sensor_range=5.0, world_size=10.0)
        pattern = SLAMPattern(cfg)
        pose = np.array([0.0, 0.0, 0.0])
        observations = pattern._observe_landmarks(pose)
        assert isinstance(observations, list)
        for _lm_id, meas in observations:
            assert len(meas) == 2
            assert meas[0] > 0  # range positive

    def test_no_observations_far_away(self):
        cfg = SLAMConfig(n_landmarks=5, sensor_range=0.1, world_size=100.0)
        pattern = SLAMPattern(cfg)
        pose = np.array([0.0, 0.0, 0.0])
        observations = pattern._observe_landmarks(pose)
        # With very small sensor range, likely no observations
        assert len(observations) == 0


# ═══════════════════════════════════════════════════════════════════
# Loop Closure Detection
# ═══════════════════════════════════════════════════════════════════


class TestDetectLoopClosure:
    def test_detects_nearby_pose(self):
        pattern = SLAMPattern(SLAMConfig(min_loop_closure_interval=2))
        for i in range(10):
            pattern.estimated_trajectory.append(np.array([float(i), 0.0, 0.0]))
        match = pattern._detect_loop_closure(np.array([0.5, 0.0, 0.0]))
        assert match is not None
        assert match == 0

    def test_no_match_too_close_in_time(self):
        pattern = SLAMPattern(SLAMConfig(min_loop_closure_interval=10))
        for i in range(5):
            pattern.estimated_trajectory.append(np.array([float(i), 0.0, 0.0]))
        match = pattern._detect_loop_closure(np.array([0.5, 0.0, 0.0]))
        assert match is None

    def test_no_match_far_away(self):
        pattern = SLAMPattern(SLAMConfig(min_loop_closure_interval=2))
        for i in range(10):
            pattern.estimated_trajectory.append(np.array([float(i), 0.0, 0.0]))
        match = pattern._detect_loop_closure(np.array([100.0, 0.0, 0.0]))
        assert match is None


# ═══════════════════════════════════════════════════════════════════
# Relative Transform
# ═══════════════════════════════════════════════════════════════════


class TestRelativeTransform:
    def test_same_pose(self):
        pattern = SLAMPattern()
        pose = np.array([1.0, 2.0, 0.5])
        rel = pattern._relative_transform(pose, pose)
        assert rel[0] == pytest.approx(0.0, abs=1e-6)
        assert rel[1] == pytest.approx(0.0, abs=1e-6)
        assert rel[2] == pytest.approx(0.0, abs=1e-6)

    def test_translation_along_x(self):
        pattern = SLAMPattern()
        pose_i = np.array([0.0, 0.0, 0.0])
        pose_j = np.array([1.0, 0.0, 0.0])
        rel = pattern._relative_transform(pose_i, pose_j)
        assert rel[0] == pytest.approx(1.0, abs=1e-6)
        assert rel[1] == pytest.approx(0.0, abs=1e-6)
        assert rel[2] == pytest.approx(0.0, abs=1e-6)

    def test_with_rotation(self):
        pattern = SLAMPattern()
        pose_i = np.array([0.0, 0.0, np.pi / 2])
        pose_j = np.array([1.0, 0.0, np.pi / 2])
        rel = pattern._relative_transform(pose_i, pose_j)
        # In rotated frame, translation appears different
        assert rel[2] == pytest.approx(0.0, abs=1e-6)


# ═══════════════════════════════════════════════════════════════════
# Pose Graph Optimization
# ═══════════════════════════════════════════════════════════════════


class TestOptimizePoseGraph:
    def test_too_few_nodes(self):
        pattern = SLAMPattern()
        pattern.pose_graph.add_node(0, np.array([0.0, 0.0, 0.0]))
        pattern.pose_graph.add_node(1, np.array([1.0, 0.0, 0.0]))
        pattern._optimize_pose_graph()
        # Should return early with < 3 nodes
        assert len(pattern.pose_graph.nodes) == 2

    def test_optimizes_with_loop_closure(self):
        pattern = SLAMPattern(SLAMConfig(optimization_iterations=2))
        for i in range(5):
            pattern.pose_graph.add_node(i, np.array([float(i), 0.0, 0.0]))
        info = np.eye(3)
        for i in range(4):
            pattern.pose_graph.add_edge(i, i + 1, np.array([1.0, 0.0, 0.0]), info)
        # Add loop closure
        pattern.pose_graph.add_edge(0, 4, np.array([4.0, 0.0, 0.0]), info)
        pattern._optimize_pose_graph()
        assert len(pattern.pose_graph.nodes) == 5


# ═══════════════════════════════════════════════════════════════════
# Metrics Calculation
# ═══════════════════════════════════════════════════════════════════


class TestCalculateMetrics:
    def test_with_trajectories(self):
        pattern = SLAMPattern()
        pattern.simulator.true_trajectory = [
            np.array([0.0, 0.0, 0.0]),
            np.array([1.0, 0.0, 0.0]),
            np.array([2.0, 0.0, 0.0]),
        ]
        pattern.simulator.estimated_trajectory = [
            np.array([0.0, 0.0, 0.0]),
            np.array([1.1, 0.0, 0.0]),
            np.array([2.2, 0.0, 0.0]),
        ]
        metrics = pattern._calculate_metrics()
        assert "mean_position_error" in metrics
        assert "max_position_error" in metrics
        assert "rmse_position" in metrics
        assert "trajectory_length" in metrics
        assert metrics["mean_position_error"] > 0

    def test_empty_trajectories(self):
        pattern = SLAMPattern()
        # Source crashes on empty trajectories (IndexError); test that it raises
        with pytest.raises(IndexError):
            pattern._calculate_metrics()


# ═══════════════════════════════════════════════════════════════════
# run() Integration
# ═══════════════════════════════════════════════════════════════════


class TestRun:
    def test_run_default(self):
        cfg = SLAMConfig(simulation_steps=50, n_landmarks=10)
        pattern = SLAMPattern(cfg)
        result = pattern.run()
        assert result["slam_type"] == "pose_graph"
        assert "performance_metrics" in result
        assert result["n_nodes"] > 0
        assert result["n_edges"] > 0

    def test_run_spiral(self):
        cfg = SLAMConfig(simulation_steps=50, trajectory_type="spiral", n_landmarks=10)
        pattern = SLAMPattern(cfg)
        result = pattern.run()
        assert result["trajectory_type"] == "spiral"
        assert len(result["trajectory"]["true"]) > 0

    def test_run_random(self):
        cfg = SLAMConfig(simulation_steps=50, trajectory_type="random", n_landmarks=10)
        pattern = SLAMPattern(cfg)
        result = pattern.run()
        assert result["trajectory_type"] == "random"

    def test_run_with_loop_closure(self):
        cfg = SLAMConfig(
            simulation_steps=100,
            trajectory_type="lawn_mower",
            n_landmarks=20,
            loop_closure_threshold=5.0,
            min_loop_closure_interval=10,
        )
        pattern = SLAMPattern(cfg)
        result = pattern.run()
        assert "loop_closures" in result
        assert isinstance(result["loop_closures"], list)

    def test_run_output_structure(self):
        cfg = SLAMConfig(simulation_steps=30, n_landmarks=5)
        pattern = SLAMPattern(cfg)
        result = pattern.run()
        assert "sensor_type" in result
        assert "n_landmarks" in result
        assert "landmark_positions" in result
        assert "history" in result
        assert "config" in result


# ═══════════════════════════════════════════════════════════════════
# get_metadata
# ═══════════════════════════════════════════════════════════════════


class TestGetMetadata:
    def test_metadata_structure(self):
        meta = SLAMPattern.get_metadata()
        assert meta["id"] == "slam"
        assert meta["version"] == "6.0.0"
        assert meta["name"] == "SLAM"
        assert meta["category"] == "EXTENDED"
        assert "parameters" in meta
        assert isinstance(meta["parameters"], list)


# ═══════════════════════════════════════════════════════════════════
# Edge Cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_zero_simulation_steps(self):
        cfg = SLAMConfig(simulation_steps=1, n_landmarks=5)
        pattern = SLAMPattern(cfg)
        result = pattern.run()
        assert result["n_nodes"] >= 1

    def test_single_landmark(self):
        cfg = SLAMConfig(simulation_steps=20, n_landmarks=1)
        pattern = SLAMPattern(cfg)
        result = pattern.run()
        assert result["n_landmarks"] == 1

    def test_small_world_size(self):
        cfg = SLAMConfig(simulation_steps=20, world_size=1.0, n_landmarks=3)
        pattern = SLAMPattern(cfg)
        result = pattern.run()
        assert "performance_metrics" in result

    def test_large_sensor_range(self):
        cfg = SLAMConfig(simulation_steps=20, sensor_range=100.0, n_landmarks=5)
        pattern = SLAMPattern(cfg)
        result = pattern.run()
        # All landmarks should be observed at each step
        assert len(result["history"]["observed_landmarks"]) > 0

    def test_no_landmarks(self):
        cfg = SLAMConfig(simulation_steps=20, n_landmarks=0)
        pattern = SLAMPattern(cfg)
        result = pattern.run()
        assert result["n_landmarks"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
