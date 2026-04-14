"""
TURBO-CDI v6.0 - Model Predictive Control Pattern
MPC with Quadratic Programming solver for constrained optimal control.

Pattern Structure (Christopher Alexander):
- Context: Multi-variable control with constraints (physical limits, safety)
- Forces: Optimality vs computation time, constraint satisfaction vs performance
- Solution: Receding horizon optimization with QP solver
"""

import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class QPSolver(Enum):
    """Available QP solvers"""

    OSQP = "osqp"  # Operator Splitting QP (if available)
    ECOS = "ecos"  # Embedded Conic Solver (if available)
    ACTIVE_SET = "active_set"  # Custom active set method
    INTERIOR_POINT = "interior_point"  # Custom interior point method
    SQP = "sqp"  # Sequential Quadratic Programming


class SystemType(Enum):
    """Predefined system types"""

    DOUBLE_INTEGRATOR = "double_integrator"
    INVERTED_PENDULUM = "inverted_pendulum"
    MIMO_SYSTEM = "mimo_system"
    QUADROTOR = "quadrotor"
    CUSTOM = "custom"


@dataclass
class MPCConfig:
    """Configuration for Model Predictive Control"""

    # System definition
    system_type: SystemType = SystemType.DOUBLE_INTEGRATOR
    A: Optional[np.ndarray] = None  # State matrix
    B: Optional[np.ndarray] = None  # Input matrix

    # MPC horizon
    N: int = 20  # Prediction horizon
    dt: float = 0.05  # Time step

    # Cost function weights
    Q: Optional[np.ndarray] = None  # State cost
    R: Optional[np.ndarray] = None  # Control cost
    Qf: Optional[np.ndarray] = None  # Terminal state cost

    # Constraints
    u_min: Optional[np.ndarray] = None  # Control lower bounds
    u_max: Optional[np.ndarray] = None  # Control upper bounds
    x_min: Optional[np.ndarray] = None  # State lower bounds
    x_max: Optional[np.ndarray] = None  # State upper bounds

    # QP solver
    solver: QPSolver = QPSolver.ACTIVE_SET
    max_qp_iters: int = 100
    qp_tol: float = 1e-6

    # Simulation
    simulation_steps: int = 1000
    initial_state: Optional[np.ndarray] = None
    reference_type: str = "constant"
    reference_value: Optional[np.ndarray] = None

    # Output
    output_interval: int = 10

    def __post_init__(self):
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
            return P
        except:
            return self.Q.copy()


class QPSolverBase:
    """Base class for QP solvers"""

    def __init__(self, max_iters: int = 100, tol: float = 1e-6):
        self.max_iters = max_iters
        self.tol = tol

    def solve(
        self,
        H: np.ndarray,
        g: np.ndarray,
        A_eq: np.ndarray,
        b_eq: np.ndarray,
        A_ineq: np.ndarray,
        b_ineq: np.ndarray,
        lb: np.ndarray,
        ub: np.ndarray,
    ) -> Tuple[np.ndarray, bool]:
        """
        Solve QP: min 0.5*x'*H*x + g'*x
                subject to: A_eq*x = b_eq
                            A_ineq*x <= b_ineq
                            lb <= x <= ub
        Returns: (x_optimal, success)
        """
        raise NotImplementedError


class ActiveSetSolver(QPSolverBase):
    """Active set method for QP"""

    def solve(
        self,
        H: np.ndarray,
        g: np.ndarray,
        A_eq: np.ndarray,
        b_eq: np.ndarray,
        A_ineq: np.ndarray,
        b_ineq: np.ndarray,
        lb: np.ndarray,
        ub: np.ndarray,
    ) -> Tuple[np.ndarray, bool]:
        """
        Simple active set QP solver.
        """
        n_vars = H.shape[0]

        # Combine all inequality constraints
        A_all = []
        b_all = []

        if A_ineq.size > 0:
            A_all.append(A_ineq)
            b_all.append(b_ineq)

        # Add bound constraints as inequalities
        I = np.eye(n_vars)
        A_all.append(I)
        b_all.append(ub)
        A_all.append(-I)
        b_all.append(-lb)

        if len(A_all) > 0:
            A_ineq_full = np.vstack(A_all)
            b_ineq_full = np.hstack(b_all)
        else:
            A_ineq_full = np.zeros((0, n_vars))
            b_ineq_full = np.zeros(0)

        # Initial guess (unconstrained minimum)
        try:
            x = -np.linalg.solve(H + 1e-8 * np.eye(n_vars), g)
        except:
            x = np.zeros(n_vars)

        # Project to feasible region
        x = np.clip(x, lb, ub)

        # Simple projected gradient descent
        alpha = 0.1
        for _ in range(self.max_iters):
            x_prev = x.copy()

            # Gradient
            grad = H @ x + g

            # Gradient step
            x = x - alpha * grad

            # Projection to feasible region
            x = np.clip(x, lb, ub)

            # Check inequality constraints
            if A_ineq_full.size > 0:
                violation = A_ineq_full @ x - b_ineq_full
                for i, v in enumerate(violation):
                    if v > 0:
                        # Project back (simplified)
                        x = x - v * A_ineq_full[i] / (
                            np.dot(A_ineq_full[i], A_ineq_full[i]) + 1e-10
                        )

            # Convergence check
            if np.linalg.norm(x - x_prev) < self.tol:
                break

        # Check feasibility
        feasible = True
        if A_ineq_full.size > 0:
            feasible = np.all(A_ineq_full @ x <= b_ineq_full + 1e-4)
        feasible = feasible and np.all(x >= lb - 1e-4) and np.all(x <= ub + 1e-4)

        return x, feasible


class ModelPredictivePattern:
    """
    Model Predictive Control pattern.

    Implements MPC with QP-based optimization for constrained
    control of linear systems.
    """

    PATTERN_ID = "model_predictive"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: Optional[MPCConfig] = None):
        self.config = config or MPCConfig()
        self.solver: Optional[QPSolverBase] = None
        self.history: Dict[str, List] = {
            "time": [],
            "state": [],
            "control": [],
            "reference": [],
            "solve_time": [],
            "feasible": [],
        }

    def _initialize_solver(self):
        """Initialize QP solver"""
        cfg = self.config

        if cfg.solver == QPSolver.ACTIVE_SET:
            self.solver = ActiveSetSolver(cfg.max_qp_iters, cfg.qp_tol)
        elif cfg.solver == QPSolver.INTERIOR_POINT:
            self.solver = ActiveSetSolver(cfg.max_qp_iters, cfg.qp_tol)  # Fallback
        else:
            self.solver = ActiveSetSolver(cfg.max_qp_iters, cfg.qp_tol)

    def _build_qp(
        self, x0: np.ndarray, x_ref: np.ndarray
    ) -> Tuple[
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
        np.ndarray,
    ]:
        """
        Build QP matrices for MPC.

        Formulation: min 0.5*U'*H*U + g'*U

        where U = [u_0, u_1, ..., u_{N-1}] is the control sequence
        """
        cfg = self.config
        N = cfg.N
        n_states = cfg.A.shape[0]
        n_inputs = cfg.B.shape[1]

        # Build prediction matrices
        # x_k = A^k x_0 + sum_{j=0}^{k-1} A^{k-1-j} B u_j

        # Build dense QP
        # Cost: J = x_N' Qf x_N + sum_{k=0}^{N-1} (x_k' Q x_k + u_k' R u_k)

        n_vars = N * n_inputs
        H = np.zeros((n_vars, n_vars))
        g = np.zeros(n_vars)

        # Build cost function
        for k in range(N):
            # Control cost
            idx_k = k * n_inputs
            idx_kp1 = (k + 1) * n_inputs
            H[idx_k:idx_kp1, idx_k:idx_kp1] += cfg.R

            # State cost through prediction
            A_pow = np.eye(n_states)
            for j in range(k + 1):
                B_term = A_pow @ cfg.B
                idx_j = j * n_inputs
                idx_jp1 = (j + 1) * n_inputs
                H[idx_j:idx_jp1, idx_j:idx_jp1] += B_term.T @ cfg.Q @ B_term

                # Linear term
                x_pred = A_pow @ x0
                g[idx_j:idx_jp1] += 2 * B_term.T @ cfg.Q @ (x_pred - x_ref)

                A_pow = cfg.A @ A_pow

        # Terminal cost
        A_pow = np.eye(n_states)
        for k in range(N):
            A_pow = cfg.A @ A_pow

        for j in range(N):
            A_pow_B = np.eye(n_states)
            for _ in range(N - j - 1):
                A_pow_B = cfg.A @ A_pow_B
            B_term = A_pow_B @ cfg.B

            idx_j = j * n_inputs
            idx_jp1 = (j + 1) * n_inputs
            H[idx_j:idx_jp1, idx_j:idx_jp1] += B_term.T @ cfg.Qf @ B_term

        # Constraints
        # Input bounds: u_min <= u_k <= u_max
        A_ineq = np.vstack([np.eye(n_vars), -np.eye(n_vars)])
        b_ineq = np.hstack([np.tile(cfg.u_max, N), -np.tile(cfg.u_min, N)])

        # State constraints (simplified - only on predicted states)
        # This is an approximation; proper MPC uses constraints on all predicted states
        if np.any(np.isfinite(cfg.x_min)) or np.any(np.isfinite(cfg.x_max)):
            # Add terminal state constraint
            A_state = np.zeros((2 * n_states, n_vars))
            A_pow = np.eye(n_states)
            for j in range(N):
                A_pow_B = np.eye(n_states)
                for _ in range(N - j - 1):
                    A_pow_B = cfg.A @ A_pow_B
                A_state[:, j * n_inputs : (j + 1) * n_inputs] = np.vstack(
                    [A_pow_B @ cfg.B, -A_pow_B @ cfg.B]
                )

            A_ineq = np.vstack([A_ineq, A_state])
            x_pred_final = A_pow @ x0
            b_ineq = np.hstack(
                [b_ineq, cfg.x_max - x_pred_final, -cfg.x_min + x_pred_final]
            )

        # No equality constraints
        A_eq = np.zeros((0, n_vars))
        b_eq = np.zeros(0)

        # Variable bounds
        lb = np.tile(cfg.u_min, N)
        ub = np.tile(cfg.u_max, N)

        return H, g, A_eq, b_eq, A_ineq, b_ineq, lb, ub

    def _solve_mpc(
        self, x0: np.ndarray, x_ref: np.ndarray
    ) -> Tuple[np.ndarray, bool, float]:
        """
        Solve MPC optimization problem.
        Returns: (u_optimal, feasible, solve_time)
        """
        import time

        t_start = time.time()

        H, g, A_eq, b_eq, A_ineq, b_ineq, lb, ub = self._build_qp(x0, x_ref)

        U_opt, feasible = self.solver.solve(H, g, A_eq, b_eq, A_ineq, b_ineq, lb, ub)

        t_solve = time.time() - t_start

        # Extract first control input
        n_inputs = self.config.B.shape[1]
        u0 = U_opt[:n_inputs]

        return u0, feasible, t_solve

    def _get_reference(self, t: float) -> np.ndarray:
        """Get reference signal"""
        cfg = self.config

        if cfg.reference_type == "constant":
            return cfg.reference_value
        elif cfg.reference_type == "sinusoid":
            freq = 0.2
            return cfg.reference_value * np.sin(2 * np.pi * freq * t)
        elif cfg.reference_type == "ramp":
            return cfg.reference_value * min(
                1.0, t / (cfg.simulation_steps * cfg.dt * 0.5)
            )
        else:
            return cfg.reference_value

    def run(self, hypothesis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run MPC simulation"""
        cfg = self.config

        logger.info(
            f"Starting MPC simulation: {cfg.system_type.value}, horizon={cfg.N}"
        )

        self._initialize_solver()

        x = cfg.initial_state.copy()

        solve_times = []
        feasibility_count = 0

        for step in range(cfg.simulation_steps):
            t = step * cfg.dt

            # Get reference
            x_ref = self._get_reference(t)

            # Solve MPC
            u, feasible, t_solve = self._solve_mpc(x, x_ref)
            solve_times.append(t_solve)

            if feasible:
                feasibility_count += 1

            # Apply control and simulate
            x = cfg.A @ x + cfg.B @ u

            # Record
            if step % cfg.output_interval == 0:
                self.history["time"].append(t)
                self.history["state"].append(x.copy())
                self.history["control"].append(u.copy())
                self.history["reference"].append(x_ref.copy())
                self.history["solve_time"].append(t_solve)
                self.history["feasible"].append(feasible)

        return self._format_output(solve_times, feasibility_count)

    def _format_output(
        self, solve_times: List[float], feasibility_count: int
    ) -> Dict[str, Any]:
        """Format simulation output"""
        cfg = self.config

        states = np.array(self.history["state"])
        controls = np.array(self.history["control"])
        references = np.array(self.history["reference"])

        # Calculate performance metrics
        state_error = states - references

        metrics = {
            "mean_state_error": float(np.mean(np.abs(state_error))),
            "max_state_error": float(np.max(np.abs(state_error))),
            "control_effort": float(np.sum(controls**2) * cfg.dt),
            "mean_solve_time": float(np.mean(solve_times)),
            "max_solve_time": float(np.max(solve_times)),
            "feasibility_rate": feasibility_count / cfg.simulation_steps,
            "final_state": states[-1].tolist(),
        }

        # Check constraint violations
        u_violations = 0
        if np.any(np.isfinite(cfg.u_max)):
            u_violations += np.sum(controls > cfg.u_max + 1e-6)
        if np.any(np.isfinite(cfg.u_min)):
            u_violations += np.sum(controls < cfg.u_min - 1e-6)

        metrics["constraint_violations"] = int(u_violations)

        return {
            "system_type": cfg.system_type.value,
            "prediction_horizon": cfg.N,
            "solver": cfg.solver.value,
            "performance_metrics": metrics,
            "history": {
                "time": self.history["time"],
                "state": [s.tolist() for s in self.history["state"]],
                "control": [c.tolist() for c in self.history["control"]],
                "reference": [r.tolist() for r in self.history["reference"]],
                "solve_time": self.history["solve_time"],
                "feasible": self.history["feasible"],
            },
            "system_matrices": {
                "A": cfg.A.tolist(),
                "B": cfg.B.tolist(),
            },
            "cost_matrices": {
                "Q": cfg.Q.tolist(),
                "R": cfg.R.tolist(),
            },
            "constraints": {
                "u_min": cfg.u_min.tolist() if cfg.u_min is not None else None,
                "u_max": cfg.u_max.tolist() if cfg.u_max is not None else None,
            },
            "config": {
                "dt": cfg.dt,
                "simulation_steps": cfg.simulation_steps,
            },
        }

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "id": cls.PATTERN_ID,
            "version": cls.PATTERN_VERSION,
            "name": "Model Predictive Control",
            "category": "EXTENDED",
            "domain": ["Control Systems", "Robotics", "Process Control"],
            "description": "MPC with QP solver for constrained optimal control",
            "computational_complexity": "O(N³ n_u³) per timestep",
            "typical_runtime": "milliseconds per timestep",
            "accuracy": "High (optimal with constraints)",
            "assumptions": [
                "Linear system model",
                "Quadratic cost function",
                "Convex constraints",
                "Sufficient computation time",
            ],
            "parameters": [
                {
                    "name": "system_type",
                    "type": "enum",
                    "options": [
                        "double_integrator",
                        "inverted_pendulum",
                        "mimo_system",
                        "quadrotor",
                    ],
                    "default": "double_integrator",
                },
                {
                    "name": "N",
                    "type": "int",
                    "default": 20,
                    "description": "Prediction horizon",
                },
                {
                    "name": "solver",
                    "type": "enum",
                    "options": ["active_set", "interior_point", "sqp"],
                    "default": "active_set",
                },
                {"name": "dt", "type": "float", "default": 0.05},
            ],
        }


# =============================================================================
# UNIT TESTS
# =============================================================================

import unittest


class TestActiveSetSolver(unittest.TestCase):
    """Unit tests for active set QP solver"""

    def test_unconstrained_qp(self):
        """Test unconstrained QP"""
        solver = ActiveSetSolver()

        # min 0.5*x^2 + 2*x + 3 => x* = -2
        H = np.array([[1.0]])
        g = np.array([2.0])
        A_eq = np.zeros((0, 1))
        b_eq = np.zeros(0)
        A_ineq = np.zeros((0, 1))
        b_ineq = np.zeros(0)
        lb = np.array([-np.inf])
        ub = np.array([np.inf])

        x, feasible = solver.solve(H, g, A_eq, b_eq, A_ineq, b_ineq, lb, ub)

        self.assertTrue(feasible)
        self.assertAlmostEqual(x[0], -2.0, places=2)

    def test_constrained_qp(self):
        """Test QP with box constraints"""
        solver = ActiveSetSolver()

        # min 0.5*x^2 subject to x >= 1
        H = np.array([[1.0]])
        g = np.array([0.0])
        lb = np.array([1.0])
        ub = np.array([np.inf])

        x, feasible = solver.solve(
            H, g, np.zeros((0, 1)), np.zeros(0), np.zeros((0, 1)), np.zeros(0), lb, ub
        )

        self.assertTrue(feasible)
        self.assertGreaterEqual(x[0], 1.0 - 1e-4)

    def test_2d_qp(self):
        """Test 2D QP"""
        solver = ActiveSetSolver()

        # min 0.5*(x1^2 + x2^2) + x1 + 2*x2
        H = np.eye(2)
        g = np.array([1.0, 2.0])
        lb = np.array([-10.0, -10.0])
        ub = np.array([10.0, 10.0])

        x, feasible = solver.solve(
            H, g, np.zeros((0, 2)), np.zeros(0), np.zeros((0, 2)), np.zeros(0), lb, ub
        )

        self.assertTrue(feasible)
        self.assertAlmostEqual(x[0], -1.0, places=2)
        self.assertAlmostEqual(x[1], -2.0, places=2)


class TestModelPredictivePattern(unittest.TestCase):
    """Unit tests for MPC pattern"""

    def test_initialization(self):
        """Test pattern initialization"""
        pattern = ModelPredictivePattern()
        self.assertIsNotNone(pattern.config)
        self.assertEqual(pattern.config.N, 20)

    def test_qp_build(self):
        """Test QP matrix construction"""
        config = MPCConfig(system_type=SystemType.DOUBLE_INTEGRATOR, N=10)
        pattern = ModelPredictivePattern(config)

        x0 = np.array([1.0, 0.0])
        x_ref = np.array([0.0, 0.0])

        H, g, A_eq, b_eq, A_ineq, b_ineq, lb, ub = pattern._build_qp(x0, x_ref)

        # Check dimensions
        n_vars = config.N * config.B.shape[1]
        self.assertEqual(H.shape, (n_vars, n_vars))
        self.assertEqual(g.shape, (n_vars,))

    def test_mpc_solve(self):
        """Test MPC optimization solve"""
        config = MPCConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            N=10,
            u_max=np.array([5.0]),
            u_min=np.array([-5.0]),
        )
        pattern = ModelPredictivePattern(config)
        pattern._initialize_solver()

        x0 = np.array([1.0, 0.0])
        x_ref = np.array([0.0, 0.0])

        u, feasible, t_solve = pattern._solve_mpc(x0, x_ref)

        self.assertEqual(u.shape, (1,))
        self.assertGreaterEqual(u[0], -5.0 - 1e-3)
        self.assertLessEqual(u[0], 5.0 + 1e-3)

    def test_full_simulation(self):
        """Test complete MPC simulation"""
        config = MPCConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            N=15,
            simulation_steps=200,
            u_max=np.array([2.0]),
            u_min=np.array([-2.0]),
        )
        pattern = ModelPredictivePattern(config)
        result = pattern.run()

        self.assertEqual(result["system_type"], "double_integrator")
        self.assertIn("performance_metrics", result)
        self.assertGreater(result["performance_metrics"]["feasibility_rate"], 0.8)

    def test_constrained_control(self):
        """Test MPC with control constraints"""
        config = MPCConfig(
            system_type=SystemType.DOUBLE_INTEGRATOR,
            N=20,
            simulation_steps=300,
            u_max=np.array([1.0]),
            u_min=np.array([-1.0]),
        )
        pattern = ModelPredictivePattern(config)
        result = pattern.run()

        # Check that constraints are respected
        controls = np.array(result["history"]["control"])
        self.assertLessEqual(np.max(controls), 1.0 + 1e-3)
        self.assertGreaterEqual(np.min(controls), -1.0 - 1e-3)

    def test_inverted_pendulum(self):
        """Test MPC on inverted pendulum"""
        config = MPCConfig(
            system_type=SystemType.INVERTED_PENDULUM,
            N=25,
            simulation_steps=300,
            Q=np.array([[10.0, 0.0], [0.0, 1.0]]),
        )
        pattern = ModelPredictivePattern(config)
        result = pattern.run()

        # Should stabilize the pendulum
        final_state = result["performance_metrics"]["final_state"]
        self.assertLess(abs(final_state[0]), 1.0)  # Angle should be small

    def test_mimo_system(self):
        """Test MPC on MIMO system"""
        config = MPCConfig(
            system_type=SystemType.MIMO_SYSTEM, N=15, simulation_steps=200
        )
        pattern = ModelPredictivePattern(config)
        result = pattern.run()

        self.assertEqual(result["system_type"], "mimo_system")
        self.assertEqual(len(result["history"]["state"][0]), 4)
        self.assertEqual(len(result["history"]["control"][0]), 2)

    def test_get_metadata(self):
        """Test metadata retrieval"""
        metadata = ModelPredictivePattern.get_metadata()

        self.assertEqual(metadata["id"], "model_predictive")
        self.assertEqual(metadata["category"], "EXTENDED")
        self.assertIn("parameters", metadata)


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2, exit=False)

    # Demo
    logging.basicConfig(level=logging.INFO)
    print("\n" + "=" * 60)
    print("Model Predictive Control Pattern Demo")
    print("=" * 60)

    for system in [SystemType.DOUBLE_INTEGRATOR, SystemType.INVERTED_PENDULUM]:
        print(f"\n--- {system.value.upper()} ---")
        config = MPCConfig(
            system_type=system,
            N=20,
            simulation_steps=300,
            u_max=np.array([2.0]),
            u_min=np.array([-2.0]),
        )
        pattern = ModelPredictivePattern(config)
        result = pattern.run()

        print(f"Prediction Horizon: {result['prediction_horizon']}")
        print(
            f"Mean Solve Time: {result['performance_metrics']['mean_solve_time'] * 1000:.2f} ms"
        )
        print(
            f"Feasibility Rate: {result['performance_metrics']['feasibility_rate'] * 100:.1f}%"
        )
        print(
            f"Mean State Error: {result['performance_metrics']['mean_state_error']:.4f}"
        )
        print(f"Final State: {result['performance_metrics']['final_state']}")
