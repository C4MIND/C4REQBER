"""
c4-cdi-turbo v6.0 - Kalman Filter Pattern[str]
Extended Kalman Filter (EKF) and Unscented Kalman Filter (UKF) for state estimation.

Pattern[str] Structure (Christopher Alexander):
- Context: State estimation with noisy measurements and uncertain dynamics
- Forces: Linearity assumptions vs accuracy, computational cost vs robustness
- Solution: Gaussian filter with linearization or sigma-point transformation
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .config import FilterType, KalmanFilterConfig, SystemModel
from .core import ExtendedKF, KalmanFilterBase, StandardKF, UnscentedKF
from .utils import format_simulation_results, get_default_metadata


logger = logging.getLogger(__name__)

__all__ = [
    "KalmanFilterPattern",
    "KalmanFilterConfig",
    "FilterType",
    "SystemModel",
    "KalmanFilterBase",
    "StandardKF",
    "ExtendedKF",
    "UnscentedKF",
]

class KalmanFilterPattern:
    """
    Kalman Filter pattern with EKF and UKF variants.

    Implements state estimation for linear and nonlinear
    systems with Gaussian noise assumptions.
    """

    PATTERN_ID = "kalman_filter"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: KalmanFilterConfig | None = None) -> None:
        self.config = config or KalmanFilterConfig()
        self.filter: KalmanFilterBase | None = None
        self.history: dict[str, list[Any]] = {
            "time": [],
            "true_state": [],
            "estimated_state": [],
            "measurement": [],
            "covariance_trace": [],
            "error": [],
        }

    def _initialize_filter(self) -> None:
        """Initialize appropriate filter"""
        cfg = self.config

        if cfg.filter_type == FilterType.KF:
            self.filter = StandardKF(cfg.F, cfg.H, cfg.B, cfg.Q, cfg.R)  # type: ignore[arg-type]

        elif cfg.filter_type == FilterType.EKF:
            # Define nonlinear functions based on system model
            if cfg.system_model == SystemModel.NONLINEAR_PENDULUM:
                # Pendulum: [theta, theta_dot]
                g, L = 9.81, 1.0
                dt = cfg.dt

                def f(x: Any, u: Any) -> Any:
                    """F."""
                    theta, theta_dot = x
                    if u is None:
                        u = 0.0
                    theta_ddot = -g / L * np.sin(theta) + u
                    return np.array(
                        [theta + theta_dot * dt, theta_dot + theta_ddot * dt]
                    )

                def h(x: Any) -> Any:
                    return np.array([x[0]])  # Measure angle

                def F_jacobian(x: Any, u: Any) -> Any:
                    """F jacobian."""
                    theta = x[0]
                    return np.array([[1.0, dt], [-g / L * np.cos(theta) * dt, 1.0]])

                def H_jacobian(x: Any) -> Any:
                    return np.array([[1.0, 0.0]])

                self.filter = ExtendedKF(
                    cfg.state_dim,
                    cfg.measurement_dim,
                    f,
                    h,
                    F_jacobian,
                    H_jacobian,
                    cfg.Q,  # type: ignore[arg-type]
                    cfg.R,  # type: ignore[arg-type]
                )

            elif cfg.system_model == SystemModel.ROBOT_LOCALIZATION:
                # Robot: [x, y, theta]
                dt = cfg.dt

                def f(x: Any, u: Any) -> Any:
                    """F."""
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

                def h(x: Any) -> Any:
                    # Range and bearing to landmark at origin
                    """H."""
                    r = np.sqrt(x[0] ** 2 + x[1] ** 2)
                    bearing = np.arctan2(x[1], x[0]) - x[2]
                    return np.array([r, bearing])

                def F_jacobian(x: Any, u: Any) -> Any:
                    """F jacobian."""
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

                def H_jacobian(x: Any) -> Any:
                    """H jacobian."""
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
                    cfg.Q,  # type: ignore[arg-type]
                    cfg.R,  # type: ignore[arg-type]
                )
            else:
                # Default to linear
                self.filter = StandardKF(cfg.F, cfg.H, cfg.B, cfg.Q, cfg.R)  # type: ignore[arg-type]

        elif cfg.filter_type == FilterType.UKF:
            # UKF uses the same nonlinear functions as EKF
            if cfg.system_model == SystemModel.NONLINEAR_PENDULUM:
                g, L = 9.81, 1.0
                dt = cfg.dt

                def f(x: Any, u: Any) -> Any:
                    """F."""
                    theta, theta_dot = x
                    if u is None:
                        u = 0.0
                    theta_ddot = -g / L * np.sin(theta) + u
                    return np.array(
                        [theta + theta_dot * dt, theta_dot + theta_ddot * dt]
                    )

                def h(x: Any) -> Any:
                    return np.array([x[0]])

                self.filter = UnscentedKF(
                    cfg.state_dim,
                    cfg.measurement_dim,
                    f,
                    h,
                    cfg.Q,  # type: ignore[arg-type]
                    cfg.R,  # type: ignore[arg-type]
                    cfg.ukf_alpha,
                    cfg.ukf_beta,
                    cfg.ukf_kappa,
                )
            else:
                # Linear system for UKF
                def f(x: Any, u: Any) -> Any:
                    return cfg.F @ x + (cfg.B @ u if u is not None else 0)

                def h(x: Any) -> Any:
                    return cfg.H @ x

                self.filter = UnscentedKF(
                    cfg.state_dim,
                    cfg.measurement_dim,
                    f,
                    h,
                    cfg.Q,  # type: ignore[arg-type]
                    cfg.R,  # type: ignore[arg-type]
                    cfg.ukf_alpha,
                    cfg.ukf_beta,
                    cfg.ukf_kappa,
                )

        # Initialize state
        self.filter.reset(cfg.initial_state, cfg.P0)  # type: ignore[arg-type, union-attr]

    def _simulate_true_system(
        self, x: np.ndarray, u: np.ndarray | None = None
    ) -> tuple[np.ndarray, np.ndarray]:
        """Simulate true system with noise"""
        cfg = self.config

        if cfg.system_model == SystemModel.NONLINEAR_PENDULUM:
            g, L = 9.81, 1.0
            dt = cfg.dt
            theta, theta_dot = x
            if u is None:
                u = 0.0  # type: ignore[assignment]
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
                u = np.zeros(cfg.B.shape[1])  # type: ignore[union-attr]
            x_next = cfg.F @ x + cfg.B @ u  # type: ignore[operator]
            z = cfg.H @ x_next

        # Add process noise
        w = np.random.multivariate_normal(np.zeros(cfg.state_dim), cfg.Q)  # type: ignore[arg-type]
        x_next = x_next + w

        # Add measurement noise
        v = np.random.multivariate_normal(np.zeros(cfg.measurement_dim), cfg.R)  # type: ignore[arg-type]
        z = z + v

        return x_next, z

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run Kalman filter simulation"""
        cfg = self.config

        logger.info(
            f"Starting Kalman filter: {cfg.filter_type.value}, {cfg.system_model.value}"
        )

        self._initialize_filter()

        # True state (unknown to filter)
        x_true = cfg.initial_state.copy()  # type: ignore[union-attr]

        for step in range(cfg.simulation_steps):
            t = step * cfg.dt

            # Simulate true system
            x_true, z = self._simulate_true_system(x_true)

            # Filter prediction and update
            self.filter.predict()  # type: ignore[union-attr]
            self.filter.update(z)  # type: ignore[union-attr]

            # Record
            if step % cfg.output_interval == 0:
                self.history["time"].append(t)
                self.history["true_state"].append(x_true.copy())
                self.history["estimated_state"].append(self.filter.x.copy())  # type: ignore[union-attr]
                self.history["measurement"].append(z.copy())
                self.history["covariance_trace"].append(np.trace(self.filter.P))  # type: ignore[union-attr]
                self.history["error"].append(np.linalg.norm(x_true - self.filter.x))  # type: ignore[union-attr]

        return self._format_output()

    def _format_output(self) -> dict[str, Any]:
        """Format output"""
        errors = np.array(self.history["error"])
        cov_traces = np.array(self.history["covariance_trace"])

        return format_simulation_results(
            self.config,
            self.filter,
            self.history,
            errors,
            cov_traces,
        )

    @classmethod
    def get_metadata(cls) -> dict[str, Any]:
        return get_default_metadata()

# =============================================================================
# UNIT TESTS
# =============================================================================

import unittest


class TestStandardKF(unittest.TestCase):
    """Unit tests for standard Kalman filter"""

    def test_kf_prediction(self) -> None:
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

    def test_kf_update(self) -> None:
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

class TestExtendedKF(unittest.TestCase):
    """Unit tests for Extended Kalman Filter"""

    def test_ekf_initialization(self) -> None:
        """Test EKF initialization"""

        def f(x: Any, u: Any) -> Any:
            return x

        def h(x: Any) -> Any:
            return x[:1]

        def F_jac(x: Any, u: Any) -> Any:
            return np.eye(2)

        def H_jac(x: Any) -> Any:
            return np.array([[1.0, 0.0]])

        ekf = ExtendedKF(2, 1, f, h, F_jac, H_jac, 0.01 * np.eye(2), np.array([[0.1]]))

        self.assertEqual(ekf.state_dim, 2)
        self.assertEqual(ekf.measurement_dim, 1)

class TestKalmanFilterPattern(unittest.TestCase):
    """Unit tests for Kalman filter pattern"""

    def test_initialization(self) -> None:
        """Test pattern initialization"""
        pattern = KalmanFilterPattern()
        self.assertIsNotNone(pattern.config)

    def test_kf_simulation(self) -> None:
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

    def test_get_metadata(self) -> None:
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
    print("Kalman Filter Pattern[str] Demo")
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
