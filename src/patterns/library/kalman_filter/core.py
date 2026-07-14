"""
C4REQBER v6.0 - Kalman Filter Core
Core filter implementations: Standard KF, EKF, UKF.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import numpy as np


logger = logging.getLogger(__name__)


class KalmanFilterBase:
    """Base class for Kalman filters"""

    def __init__(self, state_dim: int, measurement_dim: int) -> None:
        self.state_dim = state_dim
        self.measurement_dim = measurement_dim

        # State estimate
        self.x = np.zeros(state_dim)
        self.P = np.eye(state_dim)

        # Matrices (set by subclasses or directly)
        self.F: np.ndarray | None = None
        self.H: np.ndarray | None = None
        self.Q: np.ndarray | None = None
        self.R: np.ndarray | None = None
        self.B: np.ndarray | None = None

        # History
        self.state_history = []  # type: ignore[var-annotated]
        self.covariance_history = []  # type: ignore[var-annotated]
        self.innovation_history = []  # type: ignore[var-annotated]

    def predict(self, u: np.ndarray | None = None) -> np.ndarray:
        """Predict step: x = F·x + B·u, P = F·P·F^T + Q"""
        if self.F is None:
            raise ValueError("State transition matrix F not set")
        self.x = self.F @ self.x
        if u is not None and self.B is not None:
            self.x += self.B @ u
        if self.Q is not None:
            self.P = self.F @ self.P @ self.F.T + self.Q
        else:
            self.P = self.F @ self.P @ self.F.T
        self.state_history.append(self.x.copy())
        self.covariance_history.append(self.P.copy())
        return self.x

    def update(self, z: np.ndarray) -> np.ndarray:
        """Update step: K = P·H^T·(H·P·H^T + R)^-1, x += K·(z - H·x)"""
        if self.H is None or self.R is None:
            raise ValueError("Measurement matrix H or noise R not set")
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        innovation = z - self.H @ self.x
        self.x = self.x + K @ innovation
        I_KH = np.eye(self.state_dim) - K @ self.H
        self.P = I_KH @ self.P @ I_KH.T + K @ self.R @ K.T
        self.innovation_history.append(innovation.copy())
        return self.x

    def reset(self, x0: np.ndarray, P0: np.ndarray) -> None:
        """Reset filter state"""
        self.x = x0.copy()
        self.P = P0.copy()

class StandardKF(KalmanFilterBase):
    """Standard Kalman Filter for linear systems"""

    def __init__(
        self, F: np.ndarray, H: np.ndarray, B: np.ndarray, Q: np.ndarray, R: np.ndarray
    ) -> None:
        super().__init__(F.shape[0], H.shape[0])
        self.F = F
        self.H = H
        self.B = B if B is not None else np.zeros((F.shape[0], 1))
        self.Q = Q
        self.R = R

    def predict(self, u: np.ndarray | None = None) -> np.ndarray:
        """Prediction step: x_pred = F*x + B*u, P_pred = F*P*F' + Q"""
        assert self.F is not None
        assert self.B is not None
        assert self.Q is not None
        if u is None:
            u = np.zeros(self.B.shape[1])

        self.x = self.F @ self.x + self.B @ u
        self.P = self.F @ self.P @ self.F.T + self.Q

        self.state_history.append(self.x.copy())
        self.covariance_history.append(self.P.copy())

        return self.x

    def update(self, z: np.ndarray) -> np.ndarray:
        """Update step with measurement"""
        assert self.H is not None
        assert self.R is not None
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
        f: Callable[..., Any],
        h: Callable[..., Any],
        F_jacobian: Callable[..., Any],
        H_jacobian: Callable[..., Any],
        Q: np.ndarray,
        R: np.ndarray,
    ) -> None:
        super().__init__(state_dim, measurement_dim)
        self.f = f  # Nonlinear state transition
        self.h = h  # Nonlinear measurement function
        self.F_jacobian = F_jacobian  # Jacobian of f
        self.H_jacobian = H_jacobian  # Jacobian of h
        self.Q = Q
        self.R = R

    def predict(self, u: np.ndarray | None = None) -> np.ndarray:
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
        f: Callable[..., Any],
        h: Callable[..., Any],
        Q: np.ndarray,
        R: np.ndarray,
        alpha: float = 1e-3,
        beta: float = 2.0,
        kappa: float = 0.0,
    ) -> None:
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
        except np.linalg.LinAlgError:
            logger.warning("Cholesky failed, using diagonal fallback for sigma points")
            # Fallback if not positive definite
            U = np.sqrt(n + self.lambda_) * np.eye(n)

        for i in range(n):
            sigma_points[i + 1] = x + U[i]
            sigma_points[n + i + 1] = x - U[i]

        return sigma_points

    def predict(self, u: np.ndarray | None = None) -> np.ndarray:
        """Prediction using unscented transform"""
        assert self.Q is not None
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
        assert self.R is not None
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
