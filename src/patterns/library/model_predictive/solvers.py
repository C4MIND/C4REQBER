"""QP solver implementations for Model Predictive Control."""


import numpy as np


class QPSolverBase:
    """Base class for QP solvers"""

    def __init__(self, max_iters: int = 100, tol: float = 1e-6) -> None:
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
    ) -> tuple[np.ndarray, bool]:
        """
        Solve QP: min 0.5·x'·H·x + g'·x s.t. constraints
        Returns: (x_optimal, success)
        """
        n = len(g)
        H_reg = H + np.eye(n) * 1e-6

        try:
            x = -np.linalg.solve(H_reg, g)
        except np.linalg.LinAlgError:
            x, _, _, _ = np.linalg.lstsq(H_reg, -g, rcond=None)

        if lb is not None:
            x = np.maximum(x, lb)
        if ub is not None:
            x = np.minimum(x, ub)

        if A_eq.size > 0 and b_eq.size > 0:
            x = self._project_equality(x, A_eq, b_eq)

        if A_ineq.size > 0 and b_ineq.size > 0:
            for _ in range(min(10, self.max_iters)):
                violation = A_ineq @ x - b_ineq
                if not np.any(violation > 1e-8):
                    break
                i = np.argmax(violation)
                a_i = A_ineq[i:i + 1]
                denom = a_i @ a_i.T
                if denom > 1e-12:
                    x = x - a_i.T * (float(violation[i]) / float(denom))

        feasible = True
        if A_ineq.size > 0:
            feasible = bool(np.all(A_ineq @ x <= b_ineq + 1e-4))
        if lb is not None:
            feasible = feasible and bool(np.all(x >= lb - 1e-4))
        if ub is not None:
            feasible = feasible and bool(np.all(x <= ub + 1e-4))

        return x, feasible

    def _project_equality(
        self, x: np.ndarray, A_eq: np.ndarray, b_eq: np.ndarray
    ) -> np.ndarray:
        """Project x onto A_eq·x = b_eq."""
        AAT = A_eq @ A_eq.T
        try:
            lam = np.linalg.solve(AAT, A_eq @ x - b_eq)
        except np.linalg.LinAlgError:
            lam = np.linalg.lstsq(AAT, A_eq @ x - b_eq, rcond=None)[0]
        return x - A_eq.T @ lam

class ActiveSetSolver(QPSolverBase):
    """Active set[Any] method for QP"""

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
    ) -> tuple[np.ndarray, bool]:
        """
        Simple active set[Any] QP solver.
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
        except np.linalg.LinAlgError:
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
            feasible = np.all(A_ineq_full @ x <= b_ineq_full + 1e-4)  # type: ignore[assignment]
        feasible = feasible and np.all(x >= lb - 1e-4) and np.all(x <= ub + 1e-4)  # type: ignore[assignment]

        return x, feasible
