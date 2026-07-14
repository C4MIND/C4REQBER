"""Core Model Predictive Control implementation."""

from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np

from .config import MPCConfig
from .solvers import ActiveSetSolver, QPSolverBase
from .types import QPSolver


logger = logging.getLogger(__name__)

class ModelPredictivePattern:
    """
    Model Predictive Control pattern.

    Implements MPC with QP-based optimization for constrained
    control of linear systems.
    """

    PATTERN_ID = "model_predictive"
    PATTERN_VERSION = "6.0.0"

    def __init__(self, config: MPCConfig | None = None) -> None:
        self.config = config or MPCConfig()
        self.solver: QPSolverBase | None = None
        self.history: dict[str, list[Any]] = {
            "time": [],
            "state": [],
            "control": [],
            "reference": [],
            "solve_time": [],
            "feasible": [],
        }

    def _initialize_solver(self) -> None:
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
    ) -> tuple[
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
        n_states = cfg.A.shape[0]  # type: ignore[union-attr]
        n_inputs = cfg.B.shape[1]  # type: ignore[union-attr]

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
            H[idx_k:idx_kp1, idx_k:idx_kp1] += cfg.R  # type: ignore[arg-type]

            # State cost through prediction
            A_pow = np.eye(n_states)
            for j in range(k + 1):
                B_term = A_pow @ cfg.B  # type: ignore[operator]
                idx_j = j * n_inputs
                idx_jp1 = (j + 1) * n_inputs
                H[idx_j:idx_jp1, idx_j:idx_jp1] += B_term.T @ cfg.Q @ B_term

                # Linear term
                x_pred = A_pow @ x0
                g[idx_j:idx_jp1] += 2 * B_term.T @ cfg.Q @ (x_pred - x_ref)

                A_pow = cfg.A @ A_pow  # type: ignore[operator]

        # Terminal cost
        A_pow = np.eye(n_states)
        for _ in range(N):
            A_pow = cfg.A @ A_pow  # type: ignore[operator]

        for j in range(N):
            A_pow_B = np.eye(n_states)
            for _ in range(N - j - 1):
                A_pow_B = cfg.A @ A_pow_B  # type: ignore[operator]
            B_term = A_pow_B @ cfg.B  # type: ignore[operator]

            idx_j = j * n_inputs
            idx_jp1 = (j + 1) * n_inputs
            H[idx_j:idx_jp1, idx_j:idx_jp1] += B_term.T @ cfg.Qf @ B_term

        # Constraints
        # Input bounds: u_min <= u_k <= u_max
        A_ineq = np.vstack([np.eye(n_vars), -np.eye(n_vars)])
        b_ineq = np.hstack([np.tile(cfg.u_max, N), -np.tile(cfg.u_min, N)])  # type: ignore[arg-type]

        # State constraints (simplified - only on predicted states)
        # This is an approximation; proper MPC uses constraints on all predicted states
        if np.any(np.isfinite(cfg.x_min)) or np.any(np.isfinite(cfg.x_max)):  # type: ignore[arg-type]
            # Add terminal state constraint
            A_state = np.zeros((2 * n_states, n_vars))
            A_pow = np.eye(n_states)
            for j in range(N):
                A_pow_B = np.eye(n_states)
                for _ in range(N - j - 1):
                    A_pow_B = cfg.A @ A_pow_B  # type: ignore[operator]
                A_state[:, j * n_inputs : (j + 1) * n_inputs] = np.vstack(
                    [A_pow_B @ cfg.B, -A_pow_B @ cfg.B]  # type: ignore[operator]
                )

            A_ineq = np.vstack([A_ineq, A_state])
            x_pred_final = A_pow @ x0
            b_ineq = np.hstack(
                [b_ineq, cfg.x_max - x_pred_final, -cfg.x_min + x_pred_final]  # type: ignore[operator]
            )

        # No equality constraints
        A_eq = np.zeros((0, n_vars))
        b_eq = np.zeros(0)

        # Variable bounds
        lb = np.tile(cfg.u_min, N)  # type: ignore[arg-type]
        ub = np.tile(cfg.u_max, N)  # type: ignore[arg-type]

        return H, g, A_eq, b_eq, A_ineq, b_ineq, lb, ub

    def _solve_mpc(
        self, x0: np.ndarray, x_ref: np.ndarray
    ) -> tuple[np.ndarray, bool, float]:
        """
        Solve MPC optimization problem.
        Returns: (u_optimal, feasible, solve_time)
        """
        t_start = time.time()

        H, g, A_eq, b_eq, A_ineq, b_ineq, lb, ub = self._build_qp(x0, x_ref)

        U_opt, feasible = self.solver.solve(H, g, A_eq, b_eq, A_ineq, b_ineq, lb, ub)  # type: ignore[union-attr]

        t_solve = time.time() - t_start

        # Extract first control input
        n_inputs = self.config.B.shape[1]  # type: ignore[union-attr]
        u0 = U_opt[:n_inputs]

        return u0, feasible, t_solve

    def _get_reference(self, t: float) -> np.ndarray:
        """Get reference signal"""
        cfg = self.config

        if cfg.reference_type == "constant":
            return cfg.reference_value  # type: ignore[return-value]
        elif cfg.reference_type == "sinusoid":
            freq = 0.2
            return cfg.reference_value * np.sin(2 * np.pi * freq * t)  # type: ignore[no-any-return]
        elif cfg.reference_type == "ramp":
            return cfg.reference_value * min(  # type: ignore[operator, return-value]
                1.0, t / (cfg.simulation_steps * cfg.dt * 0.5)
            )
        else:
            return cfg.reference_value  # type: ignore[return-value]

    def run(self, hypothesis: dict[str, Any] = None) -> dict[str, Any]:  # type: ignore[assignment]
        """Run MPC simulation"""
        cfg = self.config

        logger.info(
            f"Starting MPC simulation: {cfg.system_type.value}, horizon={cfg.N}"
        )

        self._initialize_solver()

        x = cfg.initial_state.copy()  # type: ignore[union-attr]

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
        self, solve_times: list[float], feasibility_count: int
    ) -> dict[str, Any]:
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
        if np.any(np.isfinite(cfg.u_max)):  # type: ignore[arg-type]
            u_violations += np.sum(controls > cfg.u_max + 1e-6)  # type: ignore[assignment, operator]
        if np.any(np.isfinite(cfg.u_min)):  # type: ignore[arg-type]
            u_violations += np.sum(controls < cfg.u_min - 1e-6)  # type: ignore[assignment, operator]

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
                "A": cfg.A.tolist(),  # type: ignore[union-attr]
                "B": cfg.B.tolist(),  # type: ignore[union-attr]
            },
            "cost_matrices": {
                "Q": cfg.Q.tolist(),  # type: ignore[union-attr]
                "R": cfg.R.tolist(),  # type: ignore[union-attr]
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
    def get_metadata(cls) -> dict[str, Any]:
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
