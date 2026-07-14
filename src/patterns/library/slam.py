"""
SLAM Pattern
Simultaneous Localization and Mapping simulation
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

from .base import BaseConfig, BasePattern


logger = logging.getLogger(__name__)


class SLAMType(Enum):
    """SLAMType."""
    POSE_GRAPH = "pose_graph"
    EKF_SLAM = "ekf_slam"
    FAST_SLAM = "fast_slam"
    GRAPH_BASED = "graph_based"


class SensorType(Enum):
    """SensorType."""
    LIDAR_2D = "lidar_2d"
    LIDAR_3D = "lidar_3d"
    STEREO_CAMERA = "stereo_camera"
    RGBD_CAMERA = "rgbd_camera"
    BEACON = "beacon"


@dataclass
class SLAMConfig(BaseConfig):
    """Configuration for SLAM simulation"""
    slam_type: SLAMType = SLAMType.POSE_GRAPH
    sensor_type: SensorType = SensorType.LIDAR_2D
    world_size: float = 20.0
    n_landmarks: int = 50
    simulation_steps: int = 500
    trajectory_type: str = "lawn_mower"
    sensor_range: float = 5.0
    sensor_fov: float = 2.094
    odometry_noise: float = 0.1
    observation_noise: float = 0.2
    loop_closure_threshold: float = 2.0
    min_loop_closure_interval: int = 20
    optimization_iterations: int = 10
    landmark_positions: np.ndarray | None = None

    def __post_init__(self) -> None:
        if self.landmark_positions is None:
            rng = np.random.default_rng(42)
            self.landmark_positions = rng.random((self.n_landmarks, 2)) * self.world_size


class PoseGraph:
    """Pose graph data structure"""

    def __init__(self) -> None:
        self.nodes: dict[int, np.ndarray] = {}
        self.edges: list[tuple] = []
        self.loop_closures: list[tuple] = []

    def add_node(self, node_id: int, pose: np.ndarray) -> None:
        self.nodes[node_id] = pose.copy()

    def add_edge(self, from_id: int, to_id: int, relative_pose: np.ndarray, info: np.ndarray) -> None:
        """Add edge."""
        self.edges.append((from_id, to_id, relative_pose.copy(), info.copy()))
        if abs(from_id - to_id) > 1:
            self.loop_closures.append((from_id, to_id))


class SLAMPattern(BasePattern):
    """SLAM simulation with pose graph optimization"""

    PATTERN_ID = "slam"
    PATTERN_VERSION = "6.0.0"

    def _validate_config(self) -> None:
        pass

    def __init__(self, config: SLAMConfig | None = None) -> None:
        BasePattern.__init__(self, config or SLAMConfig())
        self.config: SLAMConfig = self.config
        self.pose_graph = PoseGraph()
        self.current_pose = np.array([0.0, 0.0, 0.0])
        self.estimated_trajectory: list[np.ndarray] = []
        self.true_trajectory: list[np.ndarray] = []
        self.current_step = 0
        self.history: dict[str, list] = {
            "time": [],
            "true_pose": [],
            "estimated_pose": [],
            "observed_landmarks": [],
            "loop_closures": [],
        }
        self.simulator = self  # For test compatibility

    def _generate_trajectory(self, step: int) -> tuple[float, float]:
        if self.config.trajectory_type == "lawn_mower":
            v = 1.0
            omega = 0.5 if step % 100 < 50 else -0.5
            if step % 200 < 100:
                omega = 0.0
            return v, omega
        elif self.config.trajectory_type == "spiral":
            v = 1.0
            omega = 0.1
            return v, omega
        elif self.config.trajectory_type == "random":
            rng = np.random.default_rng(step)
            return rng.random() * 2, (rng.random() - 0.5) * 2
        return 1.0, 0.0

    def _motion_model(self, pose: np.ndarray, v: float, omega: float, dt: float) -> np.ndarray:
        if abs(omega) < 1e-6:
            new_pose = pose.copy()
            new_pose[0] += v * dt * np.cos(pose[2])
            new_pose[1] += v * dt * np.sin(pose[2])
        else:
            new_pose = pose.copy()
            new_pose[0] += v / omega * (np.sin(pose[2] + omega * dt) - np.sin(pose[2]))
            new_pose[1] += v / omega * (-np.cos(pose[2] + omega * dt) + np.cos(pose[2]))
            new_pose[2] += omega * dt
        return new_pose

    def _simulate_odometry(self, true_motion: np.ndarray) -> np.ndarray:
        noise = np.random.randn(3) * self.config.odometry_noise
        return true_motion + noise

    def _observe_landmarks(self, pose: np.ndarray) -> list[tuple]:
        observations = []
        rng = np.random.default_rng(42)
        for i, lm in enumerate(self.config.landmark_positions):
            dx = lm[0] - pose[0]
            dy = lm[1] - pose[1]
            dist = np.sqrt(dx**2 + dy**2)
            angle = np.arctan2(dy, dx) - pose[2]
            if dist < self.config.sensor_range and abs(angle) < self.config.sensor_fov / 2:
                meas = np.array([
                    dist + rng.randn() * self.config.observation_noise,
                    angle + rng.randn() * self.config.observation_noise,
                ])
                observations.append((i, meas))
        return observations

    def _detect_loop_closure(self, pose: np.ndarray) -> int | None:
        if len(self.estimated_trajectory) < self.config.min_loop_closure_interval:
            return None
        for i, old_pose in enumerate(self.estimated_trajectory[:-self.config.min_loop_closure_interval]):
            if np.linalg.norm(pose[:2] - old_pose[:2]) < self.config.loop_closure_threshold:
                return i
        return None

    def _relative_transform(self, pose_i: np.ndarray, pose_j: np.ndarray) -> np.ndarray:
        dx = pose_j[0] - pose_i[0]
        dy = pose_j[1] - pose_i[1]
        dtheta = pose_j[2] - pose_i[2]
        # Transform into pose_i frame
        cos_t = np.cos(pose_i[2])
        sin_t = np.sin(pose_i[2])
        rel_x = cos_t * dx + sin_t * dy
        rel_y = -sin_t * dx + cos_t * dy
        return np.array([rel_x, rel_y, dtheta])

    def _optimize_pose_graph(self) -> None:
        if len(self.pose_graph.nodes) < 3:
            return
        # Simple Gauss-Newton style optimization
        for _ in range(self.config.optimization_iterations):
            for edge in self.pose_graph.edges:
                from_id, to_id, rel, info = edge
                if from_id not in self.pose_graph.nodes or to_id not in self.pose_graph.nodes:
                    continue
                # Simplified: just pull poses slightly toward consistency
                p_from = self.pose_graph.nodes[from_id]
                p_to = self.pose_graph.nodes[to_id]
                error = self._relative_transform(p_from, p_to) - rel
                self.pose_graph.nodes[to_id][:2] -= 0.01 * error[:2]

    def _calculate_metrics(self) -> dict[str, float]:
        true = np.array(self.simulator.true_trajectory)
        est = np.array(self.simulator.estimated_trajectory)
        errors = np.linalg.norm(true[:, :2] - est[:, :2], axis=1)
        return {
            "mean_position_error": float(np.mean(errors)),
            "max_position_error": float(np.max(errors)),
            "rmse_position": float(np.sqrt(np.mean(errors**2))),
            "trajectory_length": float(np.sum(np.linalg.norm(true[1:, :2] - true[:-1, :2], axis=1))),
        }

    def run(self, hypothesis: dict[str, Any] | None = None) -> dict[str, Any]:
        """Run."""
        dt = 0.1
        self.current_pose = np.array([0.0, 0.0, 0.0])
        self.estimated_trajectory = [self.current_pose.copy()]
        self.true_trajectory = [self.current_pose.copy()]
        self.pose_graph.add_node(0, self.current_pose.copy())
        loop_closures = []

        for step in range(self.config.simulation_steps):
            v, omega = self._generate_trajectory(step)
            true_motion = np.array([v * dt * np.cos(self.current_pose[2]),
                                    v * dt * np.sin(self.current_pose[2]),
                                    omega * dt])
            true_new = self._motion_model(self.current_pose, v, omega, dt)
            self.true_trajectory.append(true_new.copy())

            odometry = self._simulate_odometry(true_motion)
            est_new = self.estimated_trajectory[-1].copy()
            est_new[0] += odometry[0]
            est_new[1] += odometry[1]
            est_new[2] += odometry[2]
            self.estimated_trajectory.append(est_new.copy())
            self.pose_graph.add_node(step + 1, est_new.copy())

            # Odometry edge
            rel = self._relative_transform(self.estimated_trajectory[-2], est_new)
            self.pose_graph.add_edge(step, step + 1, rel, np.eye(3))

            observations = self._observe_landmarks(true_new)
            self.history["observed_landmarks"].append(len(observations))

            # Loop closure
            lc = self._detect_loop_closure(est_new)
            if lc is not None:
                rel_lc = self._relative_transform(self.estimated_trajectory[lc], est_new)
                self.pose_graph.add_edge(lc, step + 1, rel_lc, np.eye(3) * 10)
                loop_closures.append((lc, step + 1))

            self.current_pose = true_new

        self._optimize_pose_graph()

        metrics = self._calculate_metrics()
        return {
            "slam_type": self.config.slam_type.value,
            "sensor_type": self.config.sensor_type.value,
            "n_landmarks": self.config.n_landmarks,
            "landmark_positions": self.config.landmark_positions,
            "n_nodes": len(self.pose_graph.nodes),
            "n_edges": len(self.pose_graph.edges),
            "loop_closures": loop_closures,
            "trajectory_type": self.config.trajectory_type,
            "trajectory": {
                "true": [p.tolist() for p in self.true_trajectory],
                "estimated": [p.tolist() for p in self.estimated_trajectory],
            },
            "performance_metrics": metrics,
            "history": self.history,
            "config": {
                "simulation_steps": self.config.simulation_steps,
                "world_size": self.config.world_size,
            },
        }

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "SLAM",
            "category": "EXTENDED",
            "parameters": [
                {"name": "slam_type", "type": "enum", "options": ["pose_graph", "ekf_slam", "fast_slam", "graph_based"], "default": "pose_graph"},
                {"name": "sensor_type", "type": "enum", "options": ["lidar_2d", "lidar_3d", "stereo_camera", "rgbd_camera", "beacon"], "default": "lidar_2d"},
                {"name": "n_landmarks", "type": "int", "default": 50},
                {"name": "simulation_steps", "type": "int", "default": 500},
            ],
        }
