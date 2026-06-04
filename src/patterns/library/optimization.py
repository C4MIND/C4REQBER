"""
Linear Programming Pattern
Production-grade optimization using scipy.optimize and cvxpy

Based on:
- Simplex method (Dantzig)
- Interior point methods
- Operations research standard form
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
from scipy.optimize import linprog, minimize


try:
    import cvxpy as cp
    HAS_CVXPY = True
except ImportError:
    HAS_CVXPY = False

from ..core import (
    Hypothesis,
    SimulationParameter,
    SimulationPattern,
    SimulationResult,
    SimulationStatus,
    ValidationLevel,
    simulation_pattern,
)


logger = logging.getLogger(__name__)


class OptimizationType(Enum):
    """OptimizationType."""
    LP = "linear"           # Linear programming
    QP = "quadratic"        # Quadratic programming
    NLP = "nonlinear"       # Nonlinear optimization
    MILP = "mixed_integer"  # Mixed integer (if cvxpy available)


@simulation_pattern(
    id="optimization_lp",
    name="Linear Programming",
    category="optimization",
    description="Linear/quadratic programming for resource allocation and scheduling",
)
class LinearProgrammingPattern(SimulationPattern):
    """
    Optimization pattern for resource allocation, scheduling, planning

    Implements:
    - Linear programming (scipy.optimize.linprog)
    - Quadratic programming (if cvxpy available)
    - Nonlinear optimization fallback
    - Sensitivity analysis
    """

    parameters = [
        SimulationParameter(
            name="num_variables",
            type="int",
            default=3,
            min=1,
            max=1000,
            description="Number of decision variables",
        ),
        SimulationParameter(
            name="num_constraints",
            type="int",
            default=5,
            min=1,
            max=1000,
            description="Number of constraints",
        ),
        SimulationParameter(
            name="optimization_type",
            type="select",
            default="linear",
            options=["linear", "quadratic", "nonlinear"],
            description="Type of optimization problem",
        ),
        SimulationParameter(
            name="objective",
            type="select",
            default="minimize",
            options=["minimize", "maximize"],
            description="Optimization objective",
        ),
    ]

    def can_simulate(self, hypothesis: Hypothesis) -> bool:  # type: ignore[override]
        """Check if optimization can handle this hypothesis"""
        title = hypothesis.title.lower()
        desc = hypothesis.description.lower()

        keywords = [
            "optimize", "optimization",
            "allocate", "allocation",
            "schedule", "scheduling",
            "linear programming", "lp",
            "resource", "capacity",
            "minimize", "maximize",
            "cost", "profit", "revenue",
            "constraint", "feasible",
            "diet problem", "transportation",
            "assignment", "knapsack",
            "blending", "production planning",
        ]

        return any(kw in title or kw in desc for kw in keywords)

    async def run(  # type: ignore[override]
        self, hypothesis: Hypothesis, config: dict[str, Any]
    ) -> SimulationResult:
        """Execute optimization"""
        start_time = datetime.now()
        simulation_id = f"opt_{start_time.timestamp()}"

        logger.info(f"Starting optimization {simulation_id}")

        opt_type = config.get("optimization_type", "linear")

        try:
            if opt_type == "linear":
                results = await self._solve_linear(hypothesis, config)
            elif opt_type == "quadratic" and HAS_CVXPY:
                results = await self._solve_quadratic(hypothesis, config)
            else:
                results = await self._solve_nonlinear(hypothesis, config)

            end_time = datetime.now()

            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.COMPLETED,
                start_time=start_time,
                end_time=end_time,
                metrics=results["metrics"],
                logs=results["logs"],
                confidence_score=self._calculate_confidence(results),
                validation_level=ValidationLevel.MONTE_CARLO,
            )

        except Exception as e:
            logger.exception("Optimization failed")
            return SimulationResult(
                simulation_id=simulation_id,
                status=SimulationStatus.FAILED,
                start_time=start_time,
                end_time=datetime.now(),
                error_message=str(e),
            )

    async def _solve_linear(self, hypothesis: Hypothesis, config: dict[str, Any]) -> dict[str, Any]:
        """Solve linear programming problem"""

        params = hypothesis.parameters
        n_vars = config.get("num_variables", 3)
        n_constraints = config.get("num_constraints", 5)
        objective_dir = config.get("objective", "minimize")

        # Build problem from hypothesis or use defaults
        A_eq = None
        b_eq = None

        if "c" in params:
            # User provided objective coefficients
            c = np.array(params["c"])
            A_ub = np.array(params.get("A_ub", [])) if "A_ub" in params else None
            b_ub = np.array(params.get("b_ub", [])) if "b_ub" in params else None
            A_eq = np.array(params.get("A_eq", [])) if "A_eq" in params else None
            b_eq = np.array(params.get("b_eq", [])) if "b_eq" in params else None
            bounds = params.get("bounds", [(0, None)] * len(c))
        else:
            # Generate sample problem (diet-like)
            c, A_ub, b_ub, bounds = self._generate_diet_problem(n_vars, n_constraints)

        # Convert maximize to minimize
        if objective_dir == "maximize":
            c = -c

        # Solve using HiGHS (default in scipy >= 1.6)
        result = linprog(
            c,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            method='highs',
        )

        # Process results
        optimal_value = result.fun
        if objective_dir == "maximize":
            optimal_value = -optimal_value

        metrics = {
            "optimal_value": float(optimal_value),
            "success": result.success,
            "status": result.status,
            "num_iterations": result.nit,
            "slack": result.slack.tolist() if result.slack is not None else [],
        }

        if result.success:
            metrics["optimal_variables"] = result.x.tolist()

            # Sensitivity: how much can objective change?
            metrics["sensitivity"] = self._calculate_sensitivity(
                c, A_ub, b_ub, result.x
            )

        logs = [
            f"Optimization {'succeeded' if result.success else 'failed'}",
            f"Optimal value: {optimal_value:.4f}",
            f"Iterations: {result.nit}",
        ]

        if result.success:
            logs.append(f"Solution: {[f'{v:.3f}' for v in result.x]}")

        return {"metrics": metrics, "logs": logs}

    async def _solve_quadratic(self, hypothesis: Hypothesis, config: dict[str, Any]) -> dict[str, Any]:
        """Solve quadratic programming using cvxpy"""

        if not HAS_CVXPY:
            return await self._solve_nonlinear(hypothesis, config)

        n_vars = config.get("num_variables", 3)

        # Quadratic objective: minimize x'Px + q'x
        x = cp.Variable(n_vars)

        # Default problem: portfolio optimization
        P = np.random.randn(n_vars, n_vars)
        P = P.T @ P  # Positive semi-definite
        q = np.random.randn(n_vars)

        objective = cp.Minimize(0.5 * cp.quad_form(x, P) + q.T @ x)

        # Constraints
        constraints = [
            cp.sum(x) == 1,  # Budget constraint
            x >= 0,          # Non-negativity
        ]

        problem = cp.Problem(objective, constraints)
        result_value = problem.solve()

        metrics = {
            "optimal_value": float(result_value) if result_value is not None else None,
            "status": problem.status,
            "optimal_variables": x.value.tolist() if x.value is not None else None,
        }

        logs = [
            f"Quadratic optimization status: {problem.status}",
            f"Optimal value: {metrics['optimal_value']:.4f}" if metrics['optimal_value'] else "No solution",
        ]

        return {"metrics": metrics, "logs": logs}

    async def _solve_nonlinear(self, hypothesis: Hypothesis, config: dict[str, Any]) -> dict[str, Any]:
        """Solve nonlinear optimization"""

        n_vars = config.get("num_variables", 3)
        objective_dir = config.get("objective", "minimize")

        # Nonlinear objective (Rosenbrock-like)
        def objective(x: Any) -> Any:
            return sum(100 * (x[i+1] - x[i]**2)**2 + (1 - x[i])**2 for i in range(len(x)-1))

        # Initial guess
        x0 = np.zeros(n_vars)

        # Bounds
        bounds = [(0, 2) for _ in range(n_vars)]

        # Solve
        result = minimize(
            objective,
            x0,
            method='L-BFGS-B',
            bounds=bounds,
        )

        optimal_value = result.fun
        if objective_dir == "maximize":
            optimal_value = -optimal_value

        metrics = {
            "optimal_value": float(optimal_value),
            "success": result.success,
            "num_iterations": result.nit,
            "optimal_variables": result.x.tolist(),
        }

        logs = [
            f"Nonlinear optimization {'succeeded' if result.success else 'failed'}",
            f"Optimal value: {optimal_value:.4f}",
            f"Iterations: {result.nit}",
        ]

        return {"metrics": metrics, "logs": logs}

    def _generate_diet_problem(
        self, n_foods: int, n_nutrients: int
    ) -> tuple[Any, ...]:
        """Generate sample diet problem"""

        # Costs per food
        c = np.random.uniform(1, 10, n_foods)

        # Nutrient content (foods x nutrients)
        A = np.random.uniform(0, 5, (n_foods, n_nutrients))

        # Minimum nutrient requirements
        b = np.random.uniform(10, 50, n_nutrients)

        # Constraints: A^T x >= b  =>  -A^T x <= -b
        A_ub = -A.T
        b_ub = -b

        # Bounds: non-negative
        bounds = [(0, None) for _ in range(n_foods)]

        return c, A_ub, b_ub, bounds

    def _calculate_sensitivity(
        self, c: np.ndarray, A_ub: np.ndarray | None,
        b_ub: np.ndarray | None, x_opt: np.ndarray
    ) -> dict[str, Any]:
        """Calculate sensitivity analysis"""

        sensitivity = {}

        # Check which constraints are binding (active)
        if A_ub is not None and b_ub is not None:
            slack = b_ub - A_ub @ x_opt
            binding = np.abs(slack) < 1e-6
            sensitivity["binding_constraints"] = int(np.sum(binding))
            sensitivity["total_constraints"] = len(b_ub)

        # Variable sensitivity: how much can objective change?
        sensitivity["num_nonzero_variables"] = int(np.sum(x_opt > 1e-6))

        return sensitivity

    def _calculate_confidence(self, results: dict[str, Any]) -> float:
        """Calculate confidence score"""
        metrics = results["metrics"]
        factors = []

        # Successful optimization
        if metrics.get("success", False):
            factors.append(0.4)

        # Feasible solution
        if metrics.get("status") in [0, "optimal"]:
            factors.append(0.3)

        # Convergence information
        if metrics.get("num_iterations", 0) < 1000:
            factors.append(0.2)

        # Sensitivity analysis
        if "sensitivity" in metrics:
            factors.append(0.1)

        return min(0.95, sum(factors))

    def estimate_resources(self, hypothesis: Hypothesis) -> dict[str, Any]:  # type: ignore[override]
        """Estimate computational resources"""
        params = hypothesis.parameters
        n_vars = params.get("num_variables", 3)
        n_constraints = params.get("num_constraints", 5)

        # LP complexity is roughly O((n+m)^3)
        complexity = (n_vars + n_constraints) ** 3

        return {
            "cpu_cores": 1,
            "memory_gb": 0.5 + complexity / 1e6,
            "gpu_required": False,
            "estimated_time_seconds": complexity / 1e8,
        }
