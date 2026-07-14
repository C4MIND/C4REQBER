"""
C4REQBER v6.0 - SLAM Pattern[str] Core
Core simulation logic for graph-based SLAM.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from .config import SLAMConfig


logger = logging.getLogger(__name__)

class PoseGraph:
    """
    Pose graph for graph-based SLAM.
    Nodes are robot poses, edges are constraints from odometry or loop closures.
    """

    def __init__(self) -> None:
        self.nodes: dict[int, np.ndarray] = {}  # node_id -> pose [x, y, theta]
        self.edges: list[dict[str, Any]] = []  # edges with constraints
        self.loop_closures: list[tuple[int, int]] = []

    def add_node(self, node_id: int, pose: np.ndarray) -> None:
        """Add pose node"""
        self.nodes[node_id] = pose.copy()

    def add_edge(
        self, from_id: int, to_id: int, measurement: np.ndarray, information: np.ndarray
    ) -> None:
        """
        Add edge between nodes.
        measurement: [dx, dy, dtheta] from from_id to to_id
        information: 3x3 information matrix (inverse covariance)
        """
        self.edges.append(
            {
                "from": from_id,
                "to": to_id,
                "measurement": measurement,
                "information": information,
            }
        )

        if abs(to_id - from_id) > 1:
            self.loop_closures.append((from_id, to_id))

class SLAMSimulator:
    """SLAM simulation engine"""

    def __init__(self, config: SLAMConfig) -> None:
        self.config = config
        self.pose_graph = PoseGraph()

        # Ground truth (for simulation)
        self.true_trajectory: list[np.ndarray] = []
        self.estimated_trajectory: list[np.ndarray] = []
        self.true_landmarks = config.landmark_positions

        # Current state
        self.current_pose = np.array([0.0, 0.0, 0.0])  # [x, y, theta]
        self.current_step = 0

        # History
        self.history: dict[str, list[Any]] = {
            "time": [],
            "true_pose": [],
            "estimated_pose": [],
            "observed_landmarks": [],
            "loop_closures": [],
        }

    def _generate_trajectory(self, step: int) -> tuple[float, float]:
        """Generate velocity commands for trajectory"""
        cfg = self.config

        if cfg.trajectory_type == "lawn_mower":
            period = int(4 * cfg.world_size / (cfg.max_velocity * cfg.dt))
            phase = (step % period) / period

            if phase < 0.25:
                v = cfg.max_velocity
                omega = 0.0
            elif phase < 0.3:
                v = 0.5
                omega = cfg.max_angular_velocity
            elif phase < 0.5:
                v = cfg.max_velocity
                omega = 0.0
            elif phase < 0.55:
                v = 0.5
                omega = -cfg.max_angular_velocity
            else:
                v = cfg.max_velocity
                omega = 0.0

        elif cfg.trajectory_type == "spiral":
            v = cfg.max_velocity * 0.8
            omega = cfg.max_angular_velocity * 0.3

        elif cfg.trajectory_type == "random":
            v = cfg.max_velocity * (0.5 + 0.5 * np.sin(step * 0.1))
            omega = cfg.max_angular_velocity * np.sin(step * 0.05)

        else:
            v, omega = cfg.max_velocity * 0.5, 0.0

        return v, omega

    def _motion_model(
        self, pose: np.ndarray, v: float, omega: float, dt: float
    ) -> np.ndarray:
        """Bicycle model for robot motion"""
        x, y, theta = pose

        if abs(omega) < 1e-6:
            x_new = x + v * dt * np.cos(theta)
            y_new = y + v * dt * np.sin(theta)
            theta_new = theta
        else:
            r = v / omega
            theta_new = theta + omega * dt
            x_new = x + r * (np.sin(theta_new) - np.sin(theta))
            y_new = y - r * (np.cos(theta_new) - np.cos(theta))

        return np.array([x_new, y_new, theta_new])

    def _simulate_odometry(self, true_motion: np.ndarray) -> np.ndarray:
        """Simulate noisy odometry"""
        cfg = self.config

        noise = np.array(
            [
                np.random.normal(0, cfg.odometry_noise_linear),
                np.random.normal(0, cfg.odometry_noise_linear),
                np.random.normal(0, cfg.odometry_noise_angular),
            ]
        )

        return true_motion + noise  # type: ignore[no-any-return]

    def _observe_landmarks(self, pose: np.ndarray) -> list[tuple[int, np.ndarray]]:
        """
        Simulate landmark observations.
        Returns list[Any] of (landmark_id, measurement) tuples.
        Measurement: [range, bearing]
        """
        cfg = self.config
        observations = []

        x, y, theta = pose

        for i, landmark in enumerate(cfg.landmark_positions):  # type: ignore[arg-type]
            dx = landmark[0] - x
            dy = landmark[1] - y

            range_val = np.sqrt(dx**2 + dy**2)
            bearing = np.arctan2(dy, dx) - theta
            bearing = np.arctan2(np.sin(bearing), np.cos(bearing))

            if range_val < cfg.sensor_range and abs(bearing) < cfg.sensor_fov / 2:
                range_noise = np.random.normal(0, cfg.measurement_noise)
                bearing_noise = np.random.normal(0, cfg.measurement_noise)

                measurement = np.array(
                    [range_val + range_noise, bearing + bearing_noise]
                )

                observations.append((i, measurement))

        return observations

    def _detect_loop_closure(self, current_pose: np.ndarray) -> int | None:
        """
        Detect loop closure by checking proximity to previous poses.
        Returns node_id of matched pose or None.
        """
        cfg = self.config

        if len(self.estimated_trajectory) < cfg.min_loop_closure_interval:
            return None

        for i, pose in enumerate(
            self.estimated_trajectory[: -cfg.min_loop_closure_interval]
        ):
            distance = np.linalg.norm(current_pose[:2] - pose[:2])
            angle_diff = abs(
                np.arctan2(
                    np.sin(current_pose[2] - pose[2]), np.cos(current_pose[2] - pose[2])
                )
            )

            if distance < cfg.loop_closure_threshold and angle_diff < np.pi / 4:
                return i

        return None

    def _relative_transform(self, pose_i: np.ndarray, pose_j: np.ndarray) -> np.ndarray:
        """Compute relative transform from pose_i to pose_j"""
        xi, yi, thetai = pose_i
        xj, yj, thetaj = pose_j

        dx = xj - xi
        dy = yj - yi

        cos_i = np.cos(thetai)
        sin_i = np.sin(thetai)

        return np.array(
            [
                cos_i * dx + sin_i * dy,
                -sin_i * dx + cos_i * dy,
                np.arctan2(np.sin(thetaj - thetai), np.cos(thetaj - thetai)),
            ]
        )

    def _optimize_pose_graph(self) -> None:
        """
        Optimize pose graph using Gauss-Newton.
        Simplified optimization - in practice use g2o or GTSAM.
        """
        cfg = self.config

        if len(self.pose_graph.nodes) < 3:
            return

        for _iteration in range(cfg.optimization_iterations):
            n_nodes = len(self.pose_graph.nodes)
            H = np.zeros((3 * n_nodes, 3 * n_nodes))
            b = np.zeros(3 * n_nodes)

            for edge in self.pose_graph.edges:
                i = edge["from"]
                j = edge["to"]
                z = edge["measurement"]
                omega = edge["information"]

                xi = self.pose_graph.nodes[i]
                xj = self.pose_graph.nodes[j]

                z_pred = self._relative_transform(xi, xj)

                e = z_pred - z
                e[2] = np.arctan2(np.sin(e[2]), np.cos(e[2]))

                A = -np.eye(3)
                B = np.eye(3)

                idx_i = slice(3 * i, 3 * (i + 1))
                idx_j = slice(3 * j, 3 * (j + 1))

                H[idx_i, idx_i] += A.T @ omega @ A
                H[idx_i, idx_j] += A.T @ omega @ B
                H[idx_j, idx_i] += B.T @ omega @ A
                H[idx_j, idx_j] += B.T @ omega @ B

                b[idx_i] += A.T @ omega @ e
                b[idx_j] += B.T @ omega @ e

            H[:3, :3] += np.eye(3) * 1e6

            try:
                delta_x = np.linalg.solve(H + 1e-6 * np.eye(H.shape[0]), -b)

                for i in range(n_nodes):
                    idx = slice(3 * i, 3 * (i + 1))
                    self.pose_graph.nodes[i] += delta_x[idx]
                    self.pose_graph.nodes[i][2] = np.arctan2(
                        np.sin(self.pose_graph.nodes[i][2]),
                        np.cos(self.pose_graph.nodes[i][2]),
                    )

                if np.linalg.norm(delta_x) < cfg.optimization_tolerance:
                    break

            except np.linalg.LinAlgError:
                logger.warning("Optimization failed: singular matrix")
                break

    def _calculate_metrics(self) -> dict[str, float]:
        """Calculate SLAM performance metrics"""
        true_poses = np.array(self.true_trajectory)
        est_poses = np.array(self.estimated_trajectory)

        min_len = min(len(true_poses), len(est_poses))
        true_poses = true_poses[:min_len]
        est_poses = est_poses[:min_len]

        position_errors = np.linalg.norm(true_poses[:, :2] - est_poses[:, :2], axis=1)

        heading_errors = np.abs(
            np.arctan2(
                np.sin(true_poses[:, 2] - est_poses[:, 2]),
                np.cos(true_poses[:, 2] - est_poses[:, 2]),
            )
        )

        return {
            "mean_position_error": float(np.mean(position_errors)),
            "max_position_error": float(np.max(position_errors)),
            "final_position_error": float(position_errors[-1]),
            "mean_heading_error": float(np.mean(heading_errors)),
            "max_heading_error": float(np.max(heading_errors)),
            "rmse_position": float(np.sqrt(np.mean(position_errors**2))),
            "trajectory_length": float(
                np.sum(np.linalg.norm(np.diff(true_poses[:, :2], axis=0), axis=1))
            ),
        }

    def run_simulation(self) -> dict[str, Any]:
        """Run SLAM simulation"""
        cfg = self.config

        # Initialize
        self.current_pose = np.array([0.0, 0.0, 0.0])
        self.pose_graph.add_node(0, self.current_pose)
        self.estimated_trajectory.append(self.current_pose.copy())
        self.true_trajectory.append(self.current_pose.copy())

        prev_true_pose = self.current_pose.copy()

        for step in range(1, cfg.simulation_steps):
            t = step * cfg.dt

            v, omega = self._generate_trajectory(step)

            true_pose = self._motion_model(prev_true_pose, v, omega, cfg.dt)
            self.true_trajectory.append(true_pose.copy())

            true_motion = self._relative_transform(prev_true_pose, true_pose)
            odometry = self._simulate_odometry(true_motion)

            self.current_pose = self._motion_model(
                self.current_pose, odometry[0] / cfg.dt, odometry[2] / cfg.dt, cfg.dt
            )

            self.pose_graph.add_node(step, self.current_pose.copy())

            info_odom = np.diag(
                [
                    1.0 / cfg.odometry_noise_linear**2,
                    1.0 / cfg.odometry_noise_linear**2,
                    1.0 / cfg.odometry_noise_angular**2,
                ]
            )
            self.pose_graph.add_edge(step - 1, step, odometry, info_odom)

            observations = self._observe_landmarks(true_pose)

            loop_closure_node = self._detect_loop_closure(self.current_pose)
            if loop_closure_node is not None:
                relative_pose = self._relative_transform(
                    self.pose_graph.nodes[loop_closure_node], self.current_pose
                )
                info_loop = np.diag([1.0 / 0.01, 1.0 / 0.01, 1.0 / 0.01])
                self.pose_graph.add_edge(
                    loop_closure_node, step, relative_pose, info_loop
                )

                self._optimize_pose_graph()
                self.current_pose = self.pose_graph.nodes[step].copy()
                self.history["loop_closures"].append((step, loop_closure_node))

            self.estimated_trajectory.append(self.current_pose.copy())

            if step % cfg.output_interval == 0:
                self.history["time"].append(t)
                self.history["true_pose"].append(true_pose.tolist())
                self.history["estimated_pose"].append(self.current_pose.tolist())
                self.history["observed_landmarks"].append(len(observations))

            prev_true_pose = true_pose

        self._optimize_pose_graph()

        for i, node_id in enumerate(sorted(self.pose_graph.nodes.keys())):
            if i < len(self.estimated_trajectory):
                self.estimated_trajectory[i] = self.pose_graph.nodes[node_id]

        metrics = self._calculate_metrics()

        return self._format_output(metrics)

    def _format_output(self, metrics: dict[str, float]) -> dict[str, Any]:
        """Format output"""
        cfg = self.config

        return {
            "slam_type": cfg.slam_type.value,
            "sensor_type": cfg.sensor_type.value,
            "trajectory_type": cfg.trajectory_type,
            "performance_metrics": metrics,
            "n_landmarks": cfg.n_landmarks,
            "n_nodes": len(self.pose_graph.nodes),
            "n_edges": len(self.pose_graph.edges),
            "n_loop_closures": len(self.pose_graph.loop_closures),
            "landmark_positions": cfg.landmark_positions.tolist(),  # type: ignore[union-attr]
            "trajectory": {
                "true": [p.tolist() for p in self.true_trajectory[::10]],
                "estimated": [p.tolist() for p in self.estimated_trajectory[::10]],
            },
            "loop_closures": self.history["loop_closures"],
            "history": {
                "time": self.history["time"],
                "observed_landmarks": self.history["observed_landmarks"],
            },
            "config": {
                "simulation_steps": cfg.simulation_steps,
                "dt": cfg.dt,
                "sensor_range": cfg.sensor_range,
                "measurement_noise": cfg.measurement_noise,
            },
        }
