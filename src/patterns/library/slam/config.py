"""
C4REQBER v6.0 - SLAM Pattern[str] Configuration
Configuration classes for SLAM simulation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np


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
    landmark_positions: np.ndarray | None = None

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

    def __post_init__(self) -> None:
        """Generate landmarks if needed"""
        if self.landmark_positions is None:
            np.random.seed(42)
            self.landmark_positions = np.random.uniform(
                -self.world_size / 2, self.world_size / 2, (self.n_landmarks, 2)
            )
