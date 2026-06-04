"""Optimization Plugin — gradient descent, grid search, Nelder-Mead simplex.

Does NOT duplicate: Monte Carlo (stochastic sampling), modular_math (exact math).
UNIQUE: Black-box optimization for parameter tuning in simulations.
"""
from __future__ import annotations

from typing import Any


def gradient_descent(
    loss_fn: str | None = None,
    initial_params: list[float] | None = None,
    learning_rate: float = 0.01,
    n_iterations: int = 100,
    data: list[float] | None = None,
) -> dict[str, Any]:
    """Gradient descent on a quadratic bowl: f(x) = Σ(x_i - target_i)^2.

    If data is provided, fits a quadratic model to the data.
    Otherwise minimizes |x|^2.
    """
    params = initial_params or [1.0, 1.0]
    data = data or []

    history = []
    for _it in range(n_iterations):
        loss = sum((p - (d if d else 0)) ** 2 for p, d in zip(params, data, strict=False)) if data else sum(p * p for p in params)
        history.append(round(loss, 6))

        # Gradient: 2*(params[i] - data[i]) or 2*params[i]
        grad = [2 * (params[i] - data[i]) if i < len(data) else 2 * params[i] for i in range(len(params))]
        params = [params[i] - learning_rate * grad[i] for i in range(len(params))]

        # Early stop if converged
        if len(history) >= 2 and abs(history[-1] - history[-2]) < 1e-10:
            break

    return {
        "final_params": [round(p, 6) for p in params],
        "final_loss": history[-1] if history else 0.0,
        "iterations": len(history),
        "converged": len(history) < n_iterations,
        "loss_history": history[::max(1, len(history) // 10)],  # ~10 points
    }


def grid_search(
    loss_fn: str | None = None,
    param_grid: dict[str, list[float]] | None = None,
    data: list[float] | None = None,
) -> dict[str, Any]:
    """Grid search over parameter space.

    Minimizes sum of squared errors against target data.
    """
    param_grid = param_grid or {}
    data = data or []

    if not param_grid:
        return {"error": "Need param_grid"}

    # Generate all combinations
    keys = list(param_grid.keys())
    values = list(param_grid.values())
    combinations = _cartesian_product(values)

    best_params = None
    best_loss = float("inf")

    for combo in combinations:
        params = list(combo)
        loss = sum((p - d) ** 2 for p, d in zip(params, data, strict=False)) if len(data) == len(params) else sum(p * p for p in params)
        if loss < best_loss:
            best_loss = loss
            best_params = params

    result = {keys[i]: round(best_params[i], 6) for i in range(len(keys))} if best_params else {}

    return {
        "best_params": result,
        "best_loss": round(best_loss, 6) if best_loss != float("inf") else 0.0,
        "total_combinations": len(combinations),
    }


def nelder_mead(
    loss_fn: str | None = None,
    initial_simplex: list[list[float]] | None = None,
    n_iterations: int = 50,
    data: list[float] | None = None,
) -> dict[str, Any]:
    """Nelder-Mead simplex optimization.

    Minimizes f(x) = Σ(x_i - data_i)^2.
    """
    data = data or []
    simplex = initial_simplex or [[1.0, 0.0], [1.1, 0.0], [1.0, 1.0]]

    def f(x: list[float]) -> float:
        """F."""
        if len(data) == len(x):
            return sum((x[i] - data[i]) ** 2 for i in range(len(x)))
        return sum(v * v for v in x)

    n = len(simplex[0])
    alpha = 1.0      # reflection
    gamma = 2.0      # expansion
    rho = 0.5        # contraction
    sigma = 0.5      # shrink

    history = []

    for _it in range(n_iterations):
        # Sort simplex by function value
        simplex.sort(key=lambda s: f(s))
        centroid = [sum(simplex[j][i] for j in range(n)) / n for i in range(n)]

        best_f = f(simplex[0])
        history.append(round(best_f, 8))

        # Reflect
        reflected = [centroid[i] + alpha * (centroid[i] - simplex[n][i]) for i in range(n)]
        f_reflected = f(reflected)

        if f_reflected < f(simplex[0]):
            # Expand
            expanded = [centroid[i] + gamma * (reflected[i] - centroid[i]) for i in range(n)]
            simplex[n] = expanded if f(expanded) < f_reflected else reflected
        elif f_reflected < f(simplex[n - 1]):
            simplex[n] = reflected
        else:
            # Contract
            contracted = [centroid[i] + rho * (simplex[n][i] - centroid[i]) for i in range(n)]
            if f(contracted) < f(simplex[n]):
                simplex[n] = contracted
            else:
                # Shrink
                for i in range(1, n + 1):
                    for j in range(n):
                        simplex[i][j] = simplex[0][j] + sigma * (simplex[i][j] - simplex[0][j])

        # Converged?
        if len(history) >= 3 and abs(history[-1] - history[-2]) < 1e-12:
            break

    return {
        "optimal_params": [round(v, 6) for v in simplex[0]],
        "optimal_value": round(f(simplex[0]), 8),
        "iterations": len(history),
        "converged": len(history) < n_iterations,
    }


def _cartesian_product(lists: list[list[float]]) -> list[list[float]]:
    """Cartesian product of lists."""
    if not lists:
        return [[]]
    result: list[list[float]] = [[]]
    for lst in lists:
        result = [r + [x] for r in result for x in lst]
    return result


# ── Pipeline interface ─────────────────────────────────────────────────

def execute(problem: str = "", hypothesis_text: str = "", **kwargs: Any) -> dict[str, Any]:
    """Run optimization on provided data.

    method: "gradient_descent" | "grid_search" | "nelder_mead"
    data: target values to fit
    param_grid: grid for grid search
    initial_params: starting point for gradient descent
    """
    method = kwargs.get("method", "gradient_descent")
    data = kwargs.get("data", [])

    try:
        if method == "grid_search":
            p = kwargs.get("param_grid") or {"a": [0.0, 0.5, 1.0, 1.5, 2.0], "b": [-1.0, 0.0, 1.0]}
            return grid_search(param_grid=p, data=data)
        elif method == "nelder_mead":
            return nelder_mead(initial_simplex=kwargs.get("simplex"), data=data, n_iterations=kwargs.get("n_iterations", 50))
        else:
            return gradient_descent(
                initial_params=kwargs.get("initial_params"),
                learning_rate=kwargs.get("learning_rate", 0.01),
                n_iterations=kwargs.get("n_iterations", 100),
                data=data,
            )
    except Exception as e:
        return {"error": str(e), "method": method}
