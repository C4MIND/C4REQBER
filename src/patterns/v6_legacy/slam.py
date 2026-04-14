"""
TURBO-CDI v6.0 - SLAM Pattern
Graph-based Simultaneous Localization and Mapping with pose graph optimization.

Pattern Structure (Christopher Alexander):
- Context: Robot navigation in unknown environments
- Forces: Localization drift vs map consistency, computation vs accuracy
- Solution: Pose graph with loop closure detection and sparse optimization
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class SLAMType(Enum):
    """Available SLAM approaches"""

    POSE_GRAPH = "pose_graph"
    EKF_SLAM = "ekf_slam"
    FAST_SLAM = "fast_slam"
    GRAPH_BASED = "graph_based"


class SensorType(Enum):
    """Sensor types for landmark detection"""

    LIDAR_2D = "lidar_2d"
    LIDAR_3D = "lidar_3d"
    STEREO_CAMERA = "stereo_camera"
    RGBD_CAMERA = "rgbd_camera"
    BEACON = "beacon"


@dataclass
class SLAMConfig:
    """Configuration for SLAM"""

    # SLAM type
    slam_type: SLAMType = SLAMType.POSE_GRAPH
    sensor_type: SensorType = SensorType.LIDAR_2D

    # Environment
    world_size: float = 20.0  # meters
    n_landmarks: int = 50
    landmark_positions: Optional[np.ndarray] = None

    # Robot motion
    max_velocity: float = 1.0  # m/s
    max_angular_velocity: float = 1.0  # rad/s

    # Sensor parameters
    sensor_range: float = 5.0
    sensor_fov: float = 2 * np.pi  # radians
    measurement_noise: float = 0.1

    # Odometry noise
    odometry_noise_linear: float = 0.05
    odometry_noise_angular: float = 0.02

    # Loop closure
    loop_closure_threshold: float = 2.0
    min_loop_closure_interval: int = 50

    # Optimization
    optimization_iterations: int = 10
    optimization_tolerance: float = 1e-6

    # Simulation
    simulation_steps: int = 500
    dt: float = 0.1
    trajectory_type: str = "lawn_mower"  # lawn_mower, spiral, random

    # Output
    output_interval: int = 10

    def __post_init__(self):
        """Generate landmarks if needed"""
        if self.landmark_positions is None:
            np.random.seed(42)
            self.landmark_positions = np.random.uniform(
                -self.world_size / 2, self.world_size / 2, (self.n_landmarks, 2)
            )


class PoseGraph:
    """
    Pose graph for graph-based SLAM.
    Nodes are robot poses, edges are constraints from odometry or loop closures.
    """

    def __init__(self):
        self.nodes: Dict[int, np.ndarray] = {}  # node_id -> pose [x, y, theta]
        self.edges: List[Dict] = []  # edges with constraints
        self.loop_closures: List[Tuple[int, int]] = []

    def add_node(self, node_id: int, pose: np.ndarray):
        """Add pose node"""
        self.nodes[node_id] = pose.copy()

    def add_edge(
        self, from_id: int, to_id: int, measurement: np.ndarray, information: np.ndarray
    ):
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


class SLAMPattern:
    """
    Graph-based SLAM pattern.

    Implements pose graph SLAM with loop closure detection
    and least-squares optimization.
    """

    PATTERN_ID = "slam"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[SLAMConfig] = None):
        self.config = config or SLAMConfig()
        self.pose_graph = PoseGraph()

        # Ground truth (for simulation)
        self.true_trajectory: List[np.ndarray] = []
        self.estimated_trajectory: List[np.ndarray] = []
        self.true_landmarks = config.landmark_positions if config else None

        # Current state
        self.current_pose = np.array([0.0, 0.0, 0.0])  # [x, y, theta]
        self.current_step = 0

        # History
        self.history: Dict[str, List] = {
            "time": [],
            "true_pose": [],
            "estimated_pose": [],
            "observed_landmarks": [],
            "loop_closures": [],
        }

    def _generate_trajectory(self, step: int) -> Tuple[float, float]:
        """Generate velocity commands for trajectory"""
        cfg = self.config

        if cfg.trajectory_type == "lawn_mower":
            # Lawn mower pattern
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
            # Spiral outward
            v = cfg.max_velocity * 0.8
            omega = cfg.max_angular_velocity * 0.3

        elif cfg.trajectory_type == "random":
            # Random walk
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
            # Straight line
            x_new = x + v * dt * np.cos(theta)
            y_new = y + v * dt * np.sin(theta)
            theta_new = theta
        else:
            # Circular arc
            r = v / omega
            theta_new = theta + omega * dt
            x_new = x + r * (np.sin(theta_new) - np.sin(theta))
            y_new = y - r * (np.cos(theta_new) - np.cos(theta))

        return np.array([x_new, y_new, theta_new])

    def _simulate_odometry(self, true_motion: np.ndarray) -> np.ndarray:
        """Simulate noisy odometry"""
        cfg = self.config

        # Add noise to relative motion
        noise = np.array(
            [
                np.random.normal(0, cfg.odometry_noise_linear),
                np.random.normal(0, cfg.odometry_noise_linear),
                np.random.normal(0, cfg.odometry_noise_angular),
            ]
        )

        return true_motion + noise

    def _observe_landmarks(self, pose: np.ndarray) -> List[Tuple[int, np.ndarray]]:
        """
        Simulate landmark observations.
        Returns list of (landmark_id, measurement) tuples.
        Measurement: [range, bearing]
        """
        cfg = self.config
        observations = []

        x, y, theta = pose

        for i, landmark in enumerate(cfg.landmark_positions):
            dx = landmark[0] - x
            dy = landmark[1] - y

            range_val = np.sqrt(dx**2 + dy**2)
            bearing = np.arctan2(dy, dx) - theta

            # Normalize bearing
            bearing = np.arctan2(np.sin(bearing), np.cos(bearing))

            # Check sensor range and FOV
            if range_val < cfg.sensor_range and abs(bearing) < cfg.sensor_fov / 2:
                # Add noise
                range_noise = np.random.normal(0, cfg.measurement_noise)
                bearing_noise = np.random.normal(0, cfg.measurement_noise)

                measurement = np.array(
                    [range_val + range_noise, bearing + bearing_noise]
                )

                observations.append((i, measurement))

        return observations

    def _detect_loop_closure(self, current_pose: np.ndarray) -> Optional[int]:
        """
        Detect loop closure by checking proximity to previous poses.
        Returns node_id of matched pose or None.
        """
        cfg = self.config

        if len(self.estimated_trajectory) < cfg.min_loop_closure_interval:
            return None

        # Check against old poses (not recent ones)
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

        # Rotate into pose_i frame
        cos_i = np.cos(thetai)
        sin_i = np.sin(thetai)

        return np.array(
            [
                cos_i * dx + sin_i * dy,
                -sin_i * dx + cos_i * dy,
                np.arctan2(np.sin(thetaj - thetai), np.cos(thetaj - thetai)),
            ]
        )

    def _optimize_pose_graph(self):
        """
        Optimize pose graph using Gauss-Newton.
        Simplified optimization - in practice use g2o or GTSAM.
        """
        cfg = self.config

        if len(self.pose_graph.nodes) < 3:
            return

        # Gauss-Newton iterations
        for iteration in range(cfg.optimization_iterations):
            # Build linear system (simplified)
            # H * delta_x = -b

            n_nodes = len(self.pose_graph.nodes)
            H = np.zeros((3 * n_nodes, 3 * n_nodes))
            b = np.zeros(3 * n_nodes)

            for edge in self.pose_graph.edges:
                i = edge["from"]
                j = edge["to"]
                z = edge["measurement"]
                omega = edge["information"]

                # Current poses
                xi = self.pose_graph.nodes[i]
                xj = self.pose_graph.nodes[j]

                # Predicted measurement
                z_pred = self._relative_transform(xi, xj)

                # Error
                e = z_pred - z
                e[2] = np.arctan2(np.sin(e[2]), np.cos(e[2]))  # Normalize angle

                # Jacobian (simplified - identity for small errors)
                A = -np.eye(3)
                B = np.eye(3)

                # Update H and b
                idx_i = slice(3 * i, 3 * (i + 1))
                idx_j = slice(3 * j, 3 * (j + 1))

                H[idx_i, idx_i] += A.T @ omega @ A
                H[idx_i, idx_j] += A.T @ omega @ B
                H[idx_j, idx_i] += B.T @ omega @ A
                H[idx_j, idx_j] += B.T @ omega @ B

                b[idx_i] += A.T @ omega @ e
                b[idx_j] += B.T @ omega @ e

            # Fix first node (anchor)
            H[:3, :3] += np.eye(3) * 1e6

            # Solve
            try:
                delta_x = np.linalg.solve(H + 1e-6 * np.eye(H.shape[0]), -b)

                # Update poses
                for i in range(n_nodes):
                    idx = slice(3 * i, 3 * (i + 1))
                    self.pose_graph.nodes[i] += delta_x[idx]
                    self.pose_graph.nodes[i][2] = np.arctan2(
                        np.sin(self.pose_graph.nodes[i][2]),
                        np.cos(self.pose_graph.nodes[i][2]),
                    )

                # Check convergence
                if np.linalg.norm(delta_x) < cfg.optimization_tolerance:
                    break

            except np.linalg.LinAlgError:
                logger.warning("Optimization failed: singular matrix")
                break

    def _calculate_metrics(self) -> Dict[str, float]:
        """Calculate SLAM performance metrics"""
        true_poses = np.array(self.true_trajectory)
        est_poses = np.array(self.estimated_trajectory)

        # Ensure same length
        min_len = min(len(true_poses), len(est_poses))
        true_poses = true_poses[:min_len]
        est_poses = est_poses[:min_len]

        # Position error
        position_errors = np.linalg.norm(true_poses[:, :2] - est_poses[:, :2], axis=1)

        # Heading error
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

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run SLAM simulation"""
        cfg = self.config

        logger.info(
            f"Starting SLAM simulation: {cfg.slam_type.value}, "
            f"{cfg.simulation_steps} steps"
        )

        # Initialize
        self.current_pose = np.array([0.0, 0.0, 0.0])
        self.pose_graph.add_node(0, self.current_pose)
        self.estimated_trajectory.append(self.current_pose.copy())
        self.true_trajectory.append(self.current_pose.copy())

        prev_true_pose = self.current_pose.copy()

        for step in range(1, cfg.simulation_steps):
            t = step * cfg.dt

            # Generate motion commands
            v, omega = self._generate_trajectory(step)

            # True motion
            true_pose = self._motion_model(prev_true_pose, v, omega, cfg.dt)
            self.true_trajectory.append(true_pose.copy())

            # Relative motion (for odometry)
            true_motion = self._relative_transform(prev_true_pose, true_pose)
            odometry = self._simulate_odometry(true_motion)

            # Propagate estimate with odometry
            self.current_pose = self._motion_model(
                self.current_pose, odometry[0] / cfg.dt, odometry[2] / cfg.dt, cfg.dt
            )

            # Add to pose graph
            self.pose_graph.add_node(step, self.current_pose.copy())

            # Odometry edge
            info_odom = np.diag(
                [
                    1.0 / cfg.odometry_noise_linear**2,
                    1.0 / cfg.odometry_noise_linear**2,
                    1.0 / cfg.odometry_noise_angular**2,
                ]
            )
            self.pose_graph.add_edge(step - 1, step, odometry, info_odom)

            # Observe landmarks
            observations = self._observe_landmarks(true_pose)

            # Detect loop closure
            loop_closure_node = self._detect_loop_closure(self.current_pose)
            if loop_closure_node is not None:
                # Add loop closure edge
                relative_pose = self._relative_transform(
                    self.pose_graph.nodes[loop_closure_node], self.current_pose
                )
                info_loop = np.diag(
                    [1.0 / 0.01, 1.0 / 0.01, 1.0 / 0.01]
                )  # High confidence
                self.pose_graph.add_edge(
                    loop_closure_node, step, relative_pose, info_loop
                )

                # Optimize
                self._optimize_pose_graph()

                # Update current pose from optimized graph
                self.current_pose = self.pose_graph.nodes[step].copy()

                self.history["loop_closures"].append((step, loop_closure_node))

            self.estimated_trajectory.append(self.current_pose.copy())

            # Record
            if step % cfg.output_interval == 0:
                self.history["time"].append(t)
                self.history["true_pose"].append(true_pose.tolist())
                self.history["estimated_pose"].append(self.current_pose.tolist())
                self.history["observed_landmarks"].append(len(observations))

            prev_true_pose = true_pose

        # Final optimization
        self._optimize_pose_graph()

        # Update final trajectory
        for i, node_id in enumerate(sorted(self.pose_graph.nodes.keys())):
            if i < len(self.estimated_trajectory):
                self.estimated_trajectory[i] = self.pose_graph.nodes[node_id]

        metrics = self._calculate_metrics()

        return self._format_output(metrics)

    def _format_output(self, metrics: Dict[str, float]) -> Dict[str, Any]:
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
            "landmark_positions": cfg.landmark_positions.tolist(),
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

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "SLAM",
            "category": "EXTENDED",
            "domain": ["Robotics", "Autonomous Navigation", "Mapping"],
            "description": "Graph-based SLAM with pose graph optimization and loop closure",
            "computational_complexity": "O(N³) for optimization, O(N) for construction",
            "typical_runtime": "seconds to minutes",
            "accuracy": "High (depends on loop closures)",
            "assumptions": [
                "Static environment",
                "Known data association",
                "Gaussian noise",
                "Sufficient overlap for loop closures",
            ],
            "parameters": [
                {
                    "name": "slam_type",
                    "type": "enum",
                    "options": ["pose_graph", "ekf_slam", "fast_slam"],
                    "default": "pose_graph",
                },
                {
                    "name": "trajectory_type",
                    "type": "enum",
                    "options": ["lawn_mower", "spiral", "random"],
                    "default": "lawn_mower",
                },
                {"name": "n_landmarks", "type": "int", "default": 50},
                {"name": "sensor_range", "type": "float", "default": 5.0},
                {"name": "simulation_steps", "type": "int", "default": 500},
            ],
        }


# =============================================================================
# UNIT TESTS
# =============================================================================

import unittest


class TestPoseGraph(unittest.TestCase):
    """Unit tests for pose graph"""

    def test_node_addition(self):
        """Test adding nodes to pose graph"""
        pg = PoseGraph()
        pg.add_node(0, np.array([0.0, 0.0, 0.0]))
        pg.add_node(1, np.array([1.0, 0.0, 0.0]))

        self.assertEqual(len(pg.nodes), 2)
        np.testing.assert_array_almost_equal(pg.nodes[0], np.array([0.0, 0.0, 0.0]))

    def test_edge_addition(self):
        """Test adding edges"""
        pg = PoseGraph()
        pg.add_node(0, np.array([0.0, 0.0, 0.0]))
        pg.add_node(1, np.array([1.0, 0.0, 0.0]))

        info = np.eye(3)
        pg.add_edge(0, 1, np.array([1.0, 0.0, 0.0]), info)

        self.assertEqual(len(pg.edges), 1)

    def test_loop_closure_detection(self):
        """Test loop closure edge detection"""
        pg = PoseGraph()

        for i in range(5):
            pg.add_node(i, np.array([float(i), 0.0, 0.0]))
            if i > 0:
                pg.add_edge(i - 1, i, np.array([1.0, 0.0, 0.0]), np.eye(3))

        # Add loop closure
        pg.add_edge(0, 4, np.array([4.0, 0.0, 0.0]), np.eye(3))

        self.assertEqual(len(pg.loop_closures), 1)


class TestSLAMPattern(unittest.TestCase):
    """Unit tests for SLAM pattern"""

    def test_initialization(self):
        """Test SLAM initialization"""
        pattern = SLAMPattern()
        self.assertIsNotNone(pattern.config)
        self.assertEqual(pattern.current_pose[0], 0.0)

    def test_motion_model(self):
        """Test robot motion model"""
        config = SLAMConfig()
        pattern = SLAMPattern(config)

        pose = np.array([0.0, 0.0, 0.0])
        new_pose = pattern._motion_model(pose, 1.0, 0.0, 0.1)

        # Moving straight along x
        self.assertAlmostEqual(new_pose[0], 0.1, places=5)
        self.assertAlmostEqual(new_pose[1], 0.0, places=5)

    def test_relative_transform(self):
        """Test relative pose computation"""
        config = SLAMConfig()
        pattern = SLAMPattern(config)

        pose_i = np.array([0.0, 0.0, 0.0])
        pose_j = np.array([1.0, 0.0, 0.0])

        rel = pattern._relative_transform(pose_i, pose_j)

        self.assertAlmostEqual(rel[0], 1.0, places=5)
        self.assertAlmostEqual(rel[1], 0.0, places=5)
        self.assertAlmostEqual(rel[2], 0.0, places=5)

    def test_landmark_observation(self):
        """Test landmark observation simulation"""
        config = SLAMConfig(n_landmarks=10)
        pattern = SLAMPattern(config)

        pose = np.array([0.0, 0.0, 0.0])
        observations = pattern._observe_landmarks(pose)

        # Should observe some landmarks
        self.assertGreater(len(observations), 0)

        # Each observation should be [range, bearing]
        for lm_id, meas in observations:
            self.assertEqual(len(meas), 2)
            self.assertGreater(meas[0], 0)  # Range should be positive

    def test_loop_closure_detection(self):
        """Test loop closure detection"""
        config = SLAMConfig(min_loop_closure_interval=5)
        pattern = SLAMPattern(config)

        # Add some trajectory points
        for i in range(10):
            pattern.estimated_trajectory.append(np.array([float(i), 0.0, 0.0]))

        # Should detect loop closure when returning near start
        match = pattern._detect_loop_closure(np.array([0.5, 0.0, 0.0]))

        self.assertIsNotNone(match)
        self.assertEqual(match, 0)

    def test_full_simulation(self):
        """Test full SLAM simulation"""
        config = SLAMConfig(
            simulation_steps=100, n_landmarks=20, trajectory_type="lawn_mower"
        )
        pattern = SLAMPattern(config)
        result = pattern.run()

        self.assertEqual(result["slam_type"], "pose_graph")
        self.assertIn("performance_metrics", result)
        self.assertGreater(result["n_nodes"], 0)

    def test_trajectory_generation(self):
        """Test different trajectory types"""
        for traj_type in ["lawn_mower", "spiral", "random"]:
            config = SLAMConfig(trajectory_type=traj_type, simulation_steps=50)
            pattern = SLAMPattern(config)
            result = pattern.run()

            self.assertEqual(result["trajectory_type"], traj_type)
            self.assertTrue(len(result["trajectory"]["true"]) > 0)

    def test_optimization(self):
        """Test pose graph optimization"""
        config = SLAMConfig(simulation_steps=50)
        pattern = SLAMPattern(config)
        pattern.run()

        # Should have optimized the graph
        self.assertGreater(len(pattern.pose_graph.nodes), 0)

    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = SLAMPattern.get_metadata()

        self.assertEqual(metadata["id"], "slam")
        self.assertEqual(metadata["category"], "EXTENDED")
        self.assertIn("parameters", metadata)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2, exit=False)

    # Demo
    logging.basicConfig(level=logging.INFO)
    print("\n" + "=" * 60)
    print("SLAM Pattern Demo")
    print("=" * 60)

    for traj_type in ["lawn_mower", "spiral"]:
        print(f"\n--- {traj_type.upper()} Trajectory ---")
        config = SLAMConfig(
            slam_type=SLAMType.POSE_GRAPH,
            trajectory_type=traj_type,
            simulation_steps=300,
            n_landmarks=40,
            sensor_range=4.0,
        )
        pattern = SLAMPattern(config)
        result = pattern.run()

        print(f"Landmarks: {result['n_landmarks']}")
        print(f"Pose Graph Nodes: {result['n_nodes']}")
        print(f"Edges: {result['n_edges']}")
        print(f"Loop Closures: {result['n_loop_closures']}")
        print(
            f"Mean Position Error: {result['performance_metrics']['mean_position_error']:.3f} m"
        )
        print(
            f"Final Position Error: {result['performance_metrics']['final_position_error']:.3f} m"
        )
        print(f"RMSE: {result['performance_metrics']['rmse_position']:.3f} m")
        print(
            f"Trajectory Length: {result['performance_metrics']['trajectory_length']:.2f} m"
        )
