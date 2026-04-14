"""
TURBO-CDI v6.0 - Kalman Filter Pattern
Extended Kalman Filter (EKF) and Unscented Kalman Filter (UKF) for state estimation.

Pattern Structure (Christopher Alexander):
- Context: State estimation with noisy measurements and uncertain dynamics
- Forces: Linearity assumptions vs accuracy, computational cost vs robustness
- Solution: Gaussian filter with linearization or sigma-point transformation
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


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
    F: Optional[np.ndarray] = None  # State transition
    H: Optional[np.ndarray] = None  # Measurement matrix
    B: Optional[np.ndarray] = None  # Control input matrix

    # Noise covariances
    Q: Optional[np.ndarray] = None  # Process noise
    R: Optional[np.ndarray] = None  # Measurement noise
    P0: Optional[np.ndarray] = None  # Initial covariance

    # UKF parameters
    ukf_alpha: float = 1e-3
    ukf_beta: float = 2.0
    ukf_kappa: float = 0.0

    # Simulation
    dt: float = 0.01
    simulation_steps: int = 1000
    initial_state: Optional[np.ndarray] = None

    # Output
    output_interval: int = 10

    def __post_init__(self):
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


class KalmanFilterBase:
    """Base class for Kalman filters"""

    def __init__(self, state_dim: int, measurement_dim: int):
        self.state_dim = state_dim
        self.measurement_dim = measurement_dim

        # State estimate
        self.x = np.zeros(state_dim)
        self.P = np.eye(state_dim)

        # History
        self.state_history = []
        self.covariance_history = []
        self.innovation_history = []

    def predict(self, u: np.ndarray = None) -> np.ndarray:
        """Prediction step"""
        raise NotImplementedError

    def update(self, z: np.ndarray) -> np.ndarray:
        """Update step with measurement"""
        raise NotImplementedError

    def reset(self, x0: np.ndarray, P0: np.ndarray):
        """Reset filter state"""
        self.x = x0.copy()
        self.P = P0.copy()


class StandardKF(KalmanFilterBase):
    """Standard Kalman Filter for linear systems"""

    def __init__(
        self, F: np.ndarray, H: np.ndarray, B: np.ndarray, Q: np.ndarray, R: np.ndarray
    ):
        super().__init__(F.shape[0], H.shape[0])
        self.F = F
        self.H = H
        self.B = B if B is not None else np.zeros((F.shape[0], 1))
        self.Q = Q
        self.R = R

    def predict(self, u: np.ndarray = None) -> np.ndarray:
        """Prediction step: x_pred = F*x + B*u, P_pred = F*P*F' + Q"""
        if u is None:
            u = np.zeros(self.B.shape[1])

        self.x = self.F @ self.x + self.B @ u
        self.P = self.F @ self.P @ self.F.T + self.Q

        self.state_history.append(self.x.copy())
        self.covariance_history.append(self.P.copy())

        return self.x

    def update(self, z: np.ndarray) -> np.ndarray:
        """Update step with measurement"""
        # Innovation
        y = z - self.H @ self.x  # Measurement residual
        S = self.H @ self.P @ self.H.T + self.R  # Innovation covariance

        # Kalman gain
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # State update
        self.x = self.x + K @ y

        # Covariance update (Joseph form for numerical stability)
        I_KH = np.eye(self.state_dim) - K @ self.H
        self.P = I_KH @ self.P @ I_KH.T + K @ self.R @ K.T

        self.innovation_history.append(y.copy())

        return self.x


class ExtendedKF(KalmanFilterBase):
    """Extended Kalman Filter for nonlinear systems"""

    def __init__(
        self,
        state_dim: int,
        measurement_dim: int,
        f: Callable,
        h: Callable,
        F_jacobian: Callable,
        H_jacobian: Callable,
        Q: np.ndarray,
        R: np.ndarray,
    ):
        super().__init__(state_dim, measurement_dim)
        self.f = f  # Nonlinear state transition
        self.h = h  # Nonlinear measurement function
        self.F_jacobian = F_jacobian  # Jacobian of f
        self.H_jacobian = H_jacobian  # Jacobian of h
        self.Q = Q
        self.R = R

    def predict(self, u: np.ndarray = None) -> np.ndarray:
        """Prediction with linearization"""
        # Nonlinear prediction
        self.x = self.f(self.x, u)

        # Linearize
        F = self.F_jacobian(self.x, u)

        # Covariance prediction
        self.P = F @ self.P @ F.T + self.Q

        self.state_history.append(self.x.copy())
        self.covariance_history.append(self.P.copy())

        return self.x

    def update(self, z: np.ndarray) -> np.ndarray:
        """Update with linearized measurement"""
        # Linearize measurement
        H = self.H_jacobian(self.x)

        # Predicted measurement
        z_pred = self.h(self.x)

        # Innovation
        y = z - z_pred
        S = H @ self.P @ H.T + self.R

        # Kalman gain
        K = self.P @ H.T @ np.linalg.inv(S)

        # State update
        self.x = self.x + K @ y

        # Covariance update
        I_KH = np.eye(self.state_dim) - K @ H
        self.P = I_KH @ self.P @ I_KH.T + K @ self.R @ K.T

        self.innovation_history.append(y.copy())

        return self.x


class UnscentedKF(KalmanFilterBase):
    """Unscented Kalman Filter using sigma points"""

    def __init__(
        self,
        state_dim: int,
        measurement_dim: int,
        f: Callable,
        h: Callable,
        Q: np.ndarray,
        R: np.ndarray,
        alpha: float = 1e-3,
        beta: float = 2.0,
        kappa: float = 0.0,
    ):
        super().__init__(state_dim, measurement_dim)
        self.f = f
        self.h = h
        self.Q = Q
        self.R = R

        # UKF parameters
        self.alpha = alpha
        self.beta = beta
        self.kappa = kappa

        # Calculate weights
        self.lambda_ = alpha**2 * (state_dim + kappa) - state_dim

        self.Wm = np.zeros(2 * state_dim + 1)
        self.Wc = np.zeros(2 * state_dim + 1)

        self.Wm[0] = self.lambda_ / (state_dim + self.lambda_)
        self.Wc[0] = self.Wm[0] + (1 - alpha**2 + beta)

        for i in range(1, 2 * state_dim + 1):
            self.Wm[i] = 1.0 / (2 * (state_dim + self.lambda_))
            self.Wc[i] = self.Wm[i]

    def _generate_sigma_points(self, x: np.ndarray, P: np.ndarray) -> np.ndarray:
        """Generate sigma points"""
        n = self.state_dim
        sigma_points = np.zeros((2 * n + 1, n))

        sigma_points[0] = x

        # Matrix square root
        try:
            U = np.linalg.cholesky((n + self.lambda_) * P).T
        except:
            # Fallback if not positive definite
            U = np.sqrt(n + self.lambda_) * np.eye(n)

        for i in range(n):
            sigma_points[i + 1] = x + U[i]
            sigma_points[n + i + 1] = x - U[i]

        return sigma_points

    def predict(self, u: np.ndarray = None) -> np.ndarray:
        """Prediction using unscented transform"""
        # Generate sigma points
        sigma_points = self._generate_sigma_points(self.x, self.P)

        # Propagate through nonlinear function
        sigma_points_pred = np.array([self.f(sp, u) for sp in sigma_points])

        # Calculate mean
        self.x = np.sum(self.Wm[:, np.newaxis] * sigma_points_pred, axis=0)

        # Calculate covariance
        self.P = self.Q.copy()
        for i in range(2 * self.state_dim + 1):
            diff = sigma_points_pred[i] - self.x
            self.P += self.Wc[i] * np.outer(diff, diff)

        self.state_history.append(self.x.copy())
        self.covariance_history.append(self.P.copy())

        return self.x

    def update(self, z: np.ndarray) -> np.ndarray:
        """Update using unscented transform"""
        # Generate sigma points
        sigma_points = self._generate_sigma_points(self.x, self.P)

        # Propagate through measurement function
        Z_sigma = np.array([self.h(sp) for sp in sigma_points])

        # Predicted measurement mean
        z_pred = np.sum(self.Wm[:, np.newaxis] * Z_sigma, axis=0)

        # Predicted measurement covariance
        Pzz = self.R.copy()
        for i in range(2 * self.state_dim + 1):
            diff = Z_sigma[i] - z_pred
            Pzz += self.Wc[i] * np.outer(diff, diff)

        # Cross covariance
        Pxz = np.zeros((self.state_dim, self.measurement_dim))
        for i in range(2 * self.state_dim + 1):
            dx = sigma_points[i] - self.x
            dz = Z_sigma[i] - z_pred
            Pxz += self.Wc[i] * np.outer(dx, dz)

        # Kalman gain
        K = Pxz @ np.linalg.inv(Pzz)

        # Update
        self.x = self.x + K @ (z - z_pred)
        self.P = self.P - K @ Pzz @ K.T

        self.innovation_history.append(z - z_pred)

        return self.x


class KalmanFilterPattern:
    """
    Kalman Filter pattern with EKF and UKF variants.

    Implements state estimation for linear and nonlinear
    systems with Gaussian noise assumptions.
    """

    PATTERN_ID = "kalman_filter"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[KalmanFilterConfig] = None):
        self.config = config or KalmanFilterConfig()
        self.filter: Optional[KalmanFilterBase] = None
        self.history: Dict[str, List] = {
            "time": [],
            "true_state": [],
            "estimated_state": [],
            "measurement": [],
            "covariance_trace": [],
            "error": [],
        }

    def _initialize_filter(self):
        """Initialize appropriate filter"""
        cfg = self.config

        if cfg.filter_type == FilterType.KF:
            self.filter = StandardKF(cfg.F, cfg.H, cfg.B, cfg.Q, cfg.R)

        elif cfg.filter_type == FilterType.EKF:
            # Define nonlinear functions based on system model
            if cfg.system_model == SystemModel.NONLINEAR_PENDULUM:
                # Pendulum: [theta, theta_dot]
                g, L = 9.81, 1.0
                dt = cfg.dt

                def f(x, u):
                    theta, theta_dot = x
                    if u is None:
                        u = 0.0
                    theta_ddot = -g / L * np.sin(theta) + u
                    return np.array(
                        [theta + theta_dot * dt, theta_dot + theta_ddot * dt]
                    )

                def h(x):
                    return np.array([x[0]])  # Measure angle

                def F_jacobian(x, u):
                    theta = x[0]
                    return np.array([[1.0, dt], [-g / L * np.cos(theta) * dt, 1.0]])

                def H_jacobian(x):
                    return np.array([[1.0, 0.0]])

                self.filter = ExtendedKF(
                    cfg.state_dim,
                    cfg.measurement_dim,
                    f,
                    h,
                    F_jacobian,
                    H_jacobian,
                    cfg.Q,
                    cfg.R,
                )

            elif cfg.system_model == SystemModel.ROBOT_LOCALIZATION:
                # Robot: [x, y, theta]
                dt = cfg.dt

                def f(x, u):
                    if u is None:
                        u = np.array([0.0, 0.0])
                    v, omega = u
                    theta = x[2]
                    return np.array(
                        [
                            x[0] + v * np.cos(theta) * dt,
                            x[1] + v * np.sin(theta) * dt,
                            x[2] + omega * dt,
                        ]
                    )

                def h(x):
                    # Range and bearing to landmark at origin
                    r = np.sqrt(x[0] ** 2 + x[1] ** 2)
                    bearing = np.arctan2(x[1], x[0]) - x[2]
                    return np.array([r, bearing])

                def F_jacobian(x, u):
                    if u is None:
                        u = np.array([0.0, 0.0])
                    v, omega = u
                    theta = x[2]
                    return np.array(
                        [
                            [1.0, 0.0, -v * np.sin(theta) * dt],
                            [0.0, 1.0, v * np.cos(theta) * dt],
                            [0.0, 0.0, 1.0],
                        ]
                    )

                def H_jacobian(x):
                    r = np.sqrt(x[0] ** 2 + x[1] ** 2) + 1e-10
                    return np.array(
                        [[x[0] / r, x[1] / r, 0.0], [-x[1] / r**2, x[0] / r**2, -1.0]]
                    )

                self.filter = ExtendedKF(
                    cfg.state_dim,
                    cfg.measurement_dim,
                    f,
                    h,
                    F_jacobian,
                    H_jacobian,
                    cfg.Q,
                    cfg.R,
                )
            else:
                # Default to linear
                self.filter = StandardKF(cfg.F, cfg.H, cfg.B, cfg.Q, cfg.R)

        elif cfg.filter_type == FilterType.UKF:
            # UKF uses the same nonlinear functions as EKF
            if cfg.system_model == SystemModel.NONLINEAR_PENDULUM:
                g, L = 9.81, 1.0
                dt = cfg.dt

                def f(x, u):
                    theta, theta_dot = x
                    if u is None:
                        u = 0.0
                    theta_ddot = -g / L * np.sin(theta) + u
                    return np.array(
                        [theta + theta_dot * dt, theta_dot + theta_ddot * dt]
                    )

                def h(x):
                    return np.array([x[0]])

                self.filter = UnscentedKF(
                    cfg.state_dim,
                    cfg.measurement_dim,
                    f,
                    h,
                    cfg.Q,
                    cfg.R,
                    cfg.ukf_alpha,
                    cfg.ukf_beta,
                    cfg.ukf_kappa,
                )
            else:
                # Linear system for UKF
                def f(x, u):
                    return cfg.F @ x + (cfg.B @ u if u is not None else 0)

                def h(x):
                    return cfg.H @ x

                self.filter = UnscentedKF(
                    cfg.state_dim,
                    cfg.measurement_dim,
                    f,
                    h,
                    cfg.Q,
                    cfg.R,
                    cfg.ukf_alpha,
                    cfg.ukf_beta,
                    cfg.ukf_kappa,
                )

        # Initialize state
        self.filter.reset(cfg.initial_state, cfg.P0)

    def _simulate_true_system(
        self, x: np.ndarray, u: np.ndarray = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Simulate true system with noise"""
        cfg = self.config

        if cfg.system_model == SystemModel.NONLINEAR_PENDULUM:
            g, L = 9.81, 1.0
            dt = cfg.dt
            theta, theta_dot = x
            if u is None:
                u = 0.0
            theta_ddot = -g / L * np.sin(theta) + u
            x_next = np.array([theta + theta_dot * dt, theta_dot + theta_ddot * dt])
            # Measure angle
            z = np.array([x_next[0]])

        elif cfg.system_model == SystemModel.ROBOT_LOCALIZATION:
            # Simple robot motion
            dt = cfg.dt
            if u is None:
                u = np.array([1.0, 0.1])  # Constant velocity and rotation
            v, omega = u
            theta = x[2]
            x_next = np.array(
                [
                    x[0] + v * np.cos(theta) * dt,
                    x[1] + v * np.sin(theta) * dt,
                    x[2] + omega * dt,
                ]
            )
            # Measure range and bearing
            r = np.sqrt(x_next[0] ** 2 + x_next[1] ** 2)
            bearing = np.arctan2(x_next[1], x_next[0]) - x_next[2]
            z = np.array([r, bearing])

        else:
            # Linear system
            if u is None:
                u = np.zeros(cfg.B.shape[1])
            x_next = cfg.F @ x + cfg.B @ u
            z = cfg.H @ x_next

        # Add process noise
        w = np.random.multivariate_normal(np.zeros(cfg.state_dim), cfg.Q)
        x_next = x_next + w

        # Add measurement noise
        v = np.random.multivariate_normal(np.zeros(cfg.measurement_dim), cfg.R)
        z = z + v

        return x_next, z

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run Kalman filter simulation"""
        cfg = self.config

        logger.info(
            f"Starting Kalman filter: {cfg.filter_type.value}, {cfg.system_model.value}"
        )

        self._initialize_filter()

        # True state (unknown to filter)
        x_true = cfg.initial_state.copy()

        for step in range(cfg.simulation_steps):
            t = step * cfg.dt

            # Simulate true system
            x_true, z = self._simulate_true_system(x_true)

            # Filter prediction and update
            self.filter.predict()
            self.filter.update(z)

            # Record
            if step % cfg.output_interval == 0:
                self.history["time"].append(t)
                self.history["true_state"].append(x_true.copy())
                self.history["estimated_state"].append(self.filter.x.copy())
                self.history["measurement"].append(z.copy())
                self.history["covariance_trace"].append(np.trace(self.filter.P))
                self.history["error"].append(np.linalg.norm(x_true - self.filter.x))

        return self._format_output()

    def _format_output(self) -> Dict[str, Any]:
        """Format output"""
        cfg = self.config

        errors = np.array(self.history["error"])
        cov_traces = np.array(self.history["covariance_trace"])

        metrics = {
            "mean_error": float(np.mean(errors)),
            "max_error": float(np.max(errors)),
            "final_error": float(errors[-1]),
            "mean_covariance_trace": float(np.mean(cov_traces)),
            "final_covariance_trace": float(cov_traces[-1]),
            "rmse": float(np.sqrt(np.mean(errors**2))),
        }

        # Calculate NEES (Normalized Estimation Error Squared)
        nees_values = []
        for i, (x_true, x_est) in enumerate(
            zip(self.history["true_state"], self.history["estimated_state"])
        ):
            if i < len(self.history["covariance_trace"]):
                P = (
                    self.filter.covariance_history[i]
                    if i < len(self.filter.covariance_history)
                    else np.eye(cfg.state_dim)
                )
                error = x_true - x_est
                try:
                    nees = (
                        error @ np.linalg.inv(P + 1e-6 * np.eye(cfg.state_dim)) @ error
                    )
                    nees_values.append(nees)
                except:
                    pass

        if nees_values:
            metrics["mean_nees"] = float(np.mean(nees_values))

        return {
            "filter_type": cfg.filter_type.value,
            "system_model": cfg.system_model.value,
            "performance_metrics": metrics,
            "history": {
                "time": self.history["time"],
                "true_state": [s.tolist() for s in self.history["true_state"]],
                "estimated_state": [
                    s.tolist() for s in self.history["estimated_state"]
                ],
                "measurement": [m.tolist() for m in self.history["measurement"]],
                "covariance_trace": self.history["covariance_trace"],
                "error": self.history["error"],
            },
            "final_estimate": self.filter.x.tolist(),
            "final_covariance": self.filter.P.tolist(),
            "noise_parameters": {
                "Q": cfg.Q.tolist(),
                "R": cfg.R.tolist(),
            },
            "config": {
                "state_dim": cfg.state_dim,
                "measurement_dim": cfg.measurement_dim,
                "dt": cfg.dt,
                "simulation_steps": cfg.simulation_steps,
            },
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Kalman Filter",
            "category": "EXTENDED",
            "domain": [
                "State Estimation",
                "Navigation",
                "Robotics",
                "Signal Processing",
            ],
            "description": "EKF and UKF for state estimation in linear and nonlinear systems",
            "computational_complexity": "O(n³) per update",
            "typical_runtime": "microseconds to milliseconds",
            "accuracy": "High (optimal for linear-Gaussian)",
            "assumptions": [
                "Gaussian noise",
                "Known system model",
                "Linear or mildly nonlinear dynamics",
            ],
            "parameters": [
                {
                    "name": "filter_type",
                    "type": "enum",
                    "options": ["kf", "ekf", "ukf"],
                    "default": "ekf",
                },
                {
                    "name": "system_model",
                    "type": "enum",
                    "options": [
                        "constant_velocity",
                        "constant_acceleration",
                        "nonlinear_pendulum",
                    ],
                    "default": "constant_velocity",
                },
                {"name": "state_dim", "type": "int", "default": 2},
                {"name": "dt", "type": "float", "default": 0.01},
            ],
        }


# =============================================================================
# UNIT TESTS
# =============================================================================

import unittest


class TestStandardKF(unittest.TestCase):
    """Unit tests for standard Kalman filter"""

    def test_kf_prediction(self):
        """Test KF prediction step"""
        F = np.array([[1.0, 0.1], [0.0, 1.0]])
        H = np.array([[1.0, 0.0]])
        B = np.zeros((2, 1))
        Q = 0.01 * np.eye(2)
        R = np.array([[0.1]])

        kf = StandardKF(F, H, B, Q, R)
        kf.x = np.array([1.0, 0.5])

        x_pred = kf.predict()

        self.assertEqual(x_pred.shape, (2,))
        self.assertAlmostEqual(x_pred[0], 1.05, places=5)

    def test_kf_update(self):
        """Test KF update step"""
        F = np.array([[1.0, 0.1], [0.0, 1.0]])
        H = np.array([[1.0, 0.0]])
        B = np.zeros((2, 1))
        Q = 0.01 * np.eye(2)
        R = np.array([[0.1]])

        kf = StandardKF(F, H, B, Q, R)
        kf.x = np.array([1.0, 0.0])
        kf.P = np.eye(2)

        # Measurement
        z = np.array([1.2])

        x_updated = kf.update(z)

        # Estimate should move toward measurement
        self.assertGreater(x_updated[0], 1.0)
        self.assertLess(x_updated[0], 1.2)

    def test_kf_convergence(self):
        """Test KF convergence to true state"""
        F = np.array([[1.0, 0.1], [0.0, 1.0]])
        H = np.array([[1.0, 0.0]])
        B = np.zeros((2, 1))
        Q = 0.001 * np.eye(2)
        R = np.array([[0.1]])

        kf = StandardKF(F, H, B, Q, R)
        kf.x = np.array([0.0, 0.0])
        kf.P = 10 * np.eye(2)

        # Constant true state
        x_true = np.array([5.0, 0.0])

        for _ in range(100):
            kf.predict()
            z = H @ x_true + np.random.normal(0, np.sqrt(R[0, 0]))
            kf.update(z)

        # Should converge close to true state
        self.assertAlmostEqual(kf.x[0], x_true[0], delta=0.5)


class TestExtendedKF(unittest.TestCase):
    """Unit tests for Extended Kalman Filter"""

    def test_ekf_initialization(self):
        """Test EKF initialization"""

        def f(x, u):
            return x

        def h(x):
            return x[:1]

        def F_jac(x, u):
            return np.eye(2)

        def H_jac(x):
            return np.array([[1.0, 0.0]])

        ekf = ExtendedKF(2, 1, f, h, F_jac, H_jac, 0.01 * np.eye(2), np.array([[0.1]]))

        self.assertEqual(ekf.state_dim, 2)
        self.assertEqual(ekf.measurement_dim, 1)

    def test_ekf_nonlinear_prediction(self):
        """Test EKF with nonlinear prediction"""
        dt = 0.1

        def f(x, u):
            return np.array([x[0] + x[1] * dt, x[1] + np.sin(x[0]) * dt])

        def h(x):
            return np.array([x[0]])

        def F_jac(x, u):
            return np.array([[1.0, dt], [np.cos(x[0]) * dt, 1.0]])

        def H_jac(x):
            return np.array([[1.0, 0.0]])

        ekf = ExtendedKF(2, 1, f, h, F_jac, H_jac, 0.01 * np.eye(2), np.array([[0.1]]))
        ekf.x = np.array([0.5, 0.1])

        x_pred = ekf.predict()

        self.assertEqual(x_pred.shape, (2,))


class TestUnscentedKF(unittest.TestCase):
    """Unit tests for Unscented Kalman Filter"""

    def test_ukf_initialization(self):
        """Test UKF initialization"""

        def f(x, u):
            return x

        def h(x):
            return x[:1]

        ukf = UnscentedKF(2, 1, f, h, 0.01 * np.eye(2), np.array([[0.1]]))

        self.assertEqual(ukf.state_dim, 2)
        self.assertEqual(len(ukf.Wm), 5)  # 2n+1 sigma points

    def test_sigma_points_generation(self):
        """Test sigma point generation"""

        def f(x, u):
            return x

        def h(x):
            return x[:1]

        ukf = UnscentedKF(2, 1, f, h, 0.01 * np.eye(2), np.array([[0.1]]))

        x = np.array([1.0, 2.0])
        P = np.eye(2)

        sigma_points = ukf._generate_sigma_points(x, P)

        self.assertEqual(sigma_points.shape, (5, 2))
        np.testing.assert_array_almost_equal(sigma_points[0], x)

    def test_ukf_prediction(self):
        """Test UKF prediction step"""
        dt = 0.1

        def f(x, u):
            return np.array([x[0] + x[1] * dt, x[1]])

        def h(x):
            return np.array([x[0]])

        ukf = UnscentedKF(2, 1, f, h, 0.01 * np.eye(2), np.array([[0.1]]))
        ukf.x = np.array([1.0, 0.5])
        ukf.P = np.eye(2)

        x_pred = ukf.predict()

        self.assertEqual(x_pred.shape, (2,))
        self.assertAlmostEqual(x_pred[0], 1.05, places=5)


class TestKalmanFilterPattern(unittest.TestCase):
    """Unit tests for Kalman filter pattern"""

    def test_initialization(self):
        """Test pattern initialization"""
        pattern = KalmanFilterPattern()
        self.assertIsNotNone(pattern.config)

    def test_kf_simulation(self):
        """Test standard KF simulation"""
        config = KalmanFilterConfig(
            filter_type=FilterType.KF,
            system_model=SystemModel.CONSTANT_VELOCITY,
            simulation_steps=200,
        )
        pattern = KalmanFilterPattern(config)
        result = pattern.run()

        self.assertEqual(result["filter_type"], "kf")
        self.assertIn("performance_metrics", result)
        self.assertIn("rmse", result["performance_metrics"])

    def test_ekf_pendulum(self):
        """Test EKF on nonlinear pendulum"""
        config = KalmanFilterConfig(
            filter_type=FilterType.EKF,
            system_model=SystemModel.NONLINEAR_PENDULUM,
            simulation_steps=200,
            Q=np.array([[0.001, 0.0], [0.0, 0.001]]),
            R=np.array([[0.01]]),
        )
        pattern = KalmanFilterPattern(config)
        result = pattern.run()

        self.assertEqual(result["filter_type"], "ekf")
        self.assertEqual(result["system_model"], "nonlinear_pendulum")

    def test_ukf_pendulum(self):
        """Test UKF on nonlinear pendulum"""
        config = KalmanFilterConfig(
            filter_type=FilterType.UKF,
            system_model=SystemModel.NONLINEAR_PENDULUM,
            simulation_steps=200,
            ukf_alpha=1e-3,
            ukf_beta=2.0,
        )
        pattern = KalmanFilterPattern(config)
        result = pattern.run()

        self.assertEqual(result["filter_type"], "ukf")
        # UKF should perform well on nonlinear system
        self.assertLess(result["performance_metrics"]["mean_error"], 1.0)

    def test_ekf_robot_localization(self):
        """Test EKF on robot localization"""
        config = KalmanFilterConfig(
            filter_type=FilterType.EKF,
            system_model=SystemModel.ROBOT_LOCALIZATION,
            simulation_steps=200,
            initial_state=np.array([1.0, 0.0, 0.0]),
        )
        pattern = KalmanFilterPattern(config)
        result = pattern.run()

        self.assertEqual(result["system_model"], "robot_localization")
        self.assertEqual(len(result["final_estimate"]), 3)

    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = KalmanFilterPattern.get_metadata()

        self.assertEqual(metadata["id"], "kalman_filter")
        self.assertEqual(metadata["category"], "EXTENDED")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2, exit=False)

    # Demo
    logging.basicConfig(level=logging.INFO)
    print("\n" + "=" * 60)
    print("Kalman Filter Pattern Demo")
    print("=" * 60)

    for filter_type in [FilterType.KF, FilterType.EKF, FilterType.UKF]:
        print(f"\n--- {filter_type.value.upper()} ---")

        if filter_type == FilterType.KF:
            model = SystemModel.CONSTANT_VELOCITY
        else:
            model = SystemModel.NONLINEAR_PENDULUM

        config = KalmanFilterConfig(
            filter_type=filter_type, system_model=model, simulation_steps=300
        )
        pattern = KalmanFilterPattern(config)
        result = pattern.run()

        print(f"System: {result['system_model']}")
        print(f"Mean Error: {result['performance_metrics']['mean_error']:.4f}")
        print(f"RMSE: {result['performance_metrics']['rmse']:.4f}")
        print(f"Final Error: {result['performance_metrics']['final_error']:.4f}")
