"""Configuration classes for Model Predictive Control."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .types import QPSolver, SystemType


@dataclass
class MPCConfig:
    """Configuration for Model Predictive Control"""

    # System definition
    system_type: SystemType = SystemType.DOUBLE_INTEGRATOR
    A: np.ndarray | None = None  # State matrix
    B: np.ndarray | None = None  # Input matrix

    # MPC horizon
    N: int = 20  # Prediction horizon
    dt: float = 0.05  # Time step

    # Cost function weights
    Q: np.ndarray | None = None  # State cost
    R: np.ndarray | None = None  # Control cost
    Qf: np.ndarray | None = None  # Terminal state cost

    # Constraints
    u_min: np.ndarray | None = None  # Control lower bounds
    u_max: np.ndarray | None = None  # Control upper bounds
    x_min: np.ndarray | None = None  # State lower bounds
    x_max: np.ndarray | None = None  # State upper bounds

    # QP solver
    solver: QPSolver = QPSolver.ACTIVE_SET
    max_qp_iters: int = 100
    qp_tol: float = 1e-6

    # Simulation
    simulation_steps: int = 1000
    initial_state: np.ndarray | None = None
    reference_type: str = "constant"
    reference_value: np.ndarray | None = None

    # Output
    output_interval: int = 10

    def __post_init__(self) -> None:
        """Initialize default matrices"""
        if self.system_type == SystemType.DOUBLE_INTEGRATOR:
            self.A = np.array([[1.0, self.dt], [0.0, 1.0]])
            self.B = np.array([[0.5 * self.dt**2], [self.dt]])
            n_states, n_inputs = 2, 1

        elif self.system_type == SystemType.INVERTED_PENDULUM:
            # Discrete-time inverted pendulum
            g, L = 9.81, 1.0
            self.A = np.array([[1.0, self.dt], [g / L * self.dt, 1.0]])
            self.B = np.array([[0.0], [self.dt / L]])
            n_states, n_inputs = 2, 1

        elif self.system_type == SystemType.MIMO_SYSTEM:
            # 4-state, 2-input MIMO system
            self.A = np.array(
                [
                    [0.95, 0.05, 0.0, 0.0],
                    [0.0, 0.9, 0.1, 0.0],
                    [0.0, 0.0, 0.92, 0.08],
                    [0.05, 0.0, 0.0, 0.88],
                ]
            )
            self.B = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.5], [0.5, 1.0]])
            n_states, n_inputs = 4, 2

        elif self.system_type == SystemType.QUADROTOR:
            # Simplified quadrotor altitude control
            self.A = np.array([[1.0, self.dt], [0.0, 1.0]])
            self.B = np.array([[0.0], [self.dt / 0.5]])  # mass = 0.5kg
            n_states, n_inputs = 2, 1
        else:
            n_states = self.A.shape[0] if self.A is not None else 2
            n_inputs = self.B.shape[1] if self.B is not None else 1

        # Default cost matrices
        if self.Q is None:
            self.Q = np.eye(n_states)
        if self.R is None:
            self.R = 0.1 * np.eye(n_inputs)
        if self.Qf is None:
            # Terminal cost as solution to DARE
            self.Qf = self._solve_dare()

        # Default constraints
        if self.u_min is None:
            self.u_min = -np.ones(n_inputs) * np.inf
        if self.u_max is None:
            self.u_max = np.ones(n_inputs) * np.inf
        if self.x_min is None:
            self.x_min = -np.ones(n_states) * np.inf
        if self.x_max is None:
            self.x_max = np.ones(n_states) * np.inf

        # Default initial state and reference
        if self.initial_state is None:
            self.initial_state = np.zeros(n_states)
        if self.reference_value is None:
            self.reference_value = np.ones(n_states)

    def _solve_dare(self) -> np.ndarray:
        """Solve discrete-time algebraic Riccati equation for terminal cost"""
        from scipy.linalg import solve_discrete_are

        try:
            P = solve_discrete_are(self.A, self.B, self.Q, self.R)
            return P  # type: ignore[no-any-return]
        except (ValueError, np.linalg.LinAlgError):
            return self.Q.copy()  # type: ignore[union-attr]
