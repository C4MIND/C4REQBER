"""
C4REQBER v6.0 - Kalman Filter Pattern[str] Configuration
Configuration enums and dataclasses for Kalman filter variants.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np


class FilterType(Enum):
    """Available Kalman filter variants"""

    KF = "kf"  # Standard Kalman Filter (linear)
    EKF = "ekf"  # Extended Kalman Filter
    UKF = "ukf"  # Unscented Kalman Filter
    ENKF = "enkf"  # Ensemble Kalman Filter

class SystemModel(Enum):
    """Predefined system models"""

    CONSTANT_VELOCITY = "constant_velocity"
    CONSTANT_ACCELERATION = "constant_acceleration"
    NONLINEAR_PENDULUM = "nonlinear_pendulum"
    ROBOT_LOCALIZATION = "robot_localization"
    CUSTOM = "custom"

@dataclass
class KalmanFilterConfig:
    """Configuration for Kalman filter"""

    # Filter type
    filter_type: FilterType = FilterType.EKF
    system_model: SystemModel = SystemModel.CONSTANT_VELOCITY

    # State dimensions
    state_dim: int = 2
    measurement_dim: int = 1

    # System matrices (for linear KF)
    F: np.ndarray | None = None  # State transition
    H: np.ndarray | None = None  # Measurement matrix
    B: np.ndarray | None = None  # Control input matrix

    # Noise covariances
    Q: np.ndarray | None = None  # Process noise
    R: np.ndarray | None = None  # Measurement noise
    P0: np.ndarray | None = None  # Initial covariance

    # UKF parameters
    ukf_alpha: float = 1e-3
    ukf_beta: float = 2.0
    ukf_kappa: float = 0.0

    # Simulation
    dt: float = 0.01
    simulation_steps: int = 1000
    initial_state: np.ndarray | None = None

    # Output
    output_interval: int = 10

    def __post_init__(self) -> None:
        """Initialize default matrices"""
        if self.system_model == SystemModel.CONSTANT_VELOCITY:
            # [position, velocity]
            self.state_dim = 2
            self.measurement_dim = 1
            self.F = np.array([[1.0, self.dt], [0.0, 1.0]])
            self.H = np.array([[1.0, 0.0]])
            self.B = np.zeros((2, 1))

        elif self.system_model == SystemModel.CONSTANT_ACCELERATION:
            # [position, velocity, acceleration]
            self.state_dim = 3
            self.measurement_dim = 1
            dt = self.dt
            self.F = np.array([[1.0, dt, 0.5 * dt**2], [0.0, 1.0, dt], [0.0, 0.0, 1.0]])
            self.H = np.array([[1.0, 0.0, 0.0]])
            self.B = np.zeros((3, 1))

        elif self.system_model == SystemModel.NONLINEAR_PENDULUM:
            # [theta, theta_dot]
            self.state_dim = 2
            self.measurement_dim = 1
            # F and H not used directly for nonlinear models

        elif self.system_model == SystemModel.ROBOT_LOCALIZATION:
            # [x, y, theta]
            self.state_dim = 3
            self.measurement_dim = 2  # Range and bearing

        # Default noise covariances
        if self.Q is None:
            self.Q = 0.01 * np.eye(self.state_dim)
        if self.R is None:
            self.R = 0.1 * np.eye(self.measurement_dim)
        if self.P0 is None:
            self.P0 = np.eye(self.state_dim)

        # Default initial state
        if self.initial_state is None:
            self.initial_state = np.zeros(self.state_dim)
