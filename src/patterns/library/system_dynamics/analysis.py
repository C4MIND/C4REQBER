"""
Analysis methods for System Dynamics simulation
- Sensitivity analysis
- Stability analysis
- Chaos detection
"""

import asyncio
import logging
from typing import Any

import numpy as np

from .models import create_ode_function
from .solver import run_simulation
from .types import Flow, Stock, SystemDynamicsConfig


logger = logging.getLogger(__name__)

async def run_sensitivity_analysis(
    config: SystemDynamicsConfig,
    stocks: dict[str, Stock],
    flows: list[Flow],
    events_detected: list[dict[str, Any]],
    rng: np.random.Generator,
) -> dict[str, Any]:
    """Run Monte Carlo sensitivity analysis"""
    logger.info(f"Running sensitivity analysis ({config.n_sensitivity_runs} runs)")

    # Store original parameters
    original_stocks = {name: stock.initial_value for name, stock in stocks.items()}

    # Collect final values across runs
    final_values: dict[str, Any] = {name: [] for name in stocks.keys()}

    for i in range(config.n_sensitivity_runs):
        # Perturb initial conditions
        for name, stock in stocks.items():
            variation = rng.normal(1.0, config.parameter_variation)
            stock.initial_value = original_stocks[name] * variation

        # Run simulation
        try:
            solution, _ = await run_simulation(config, stocks, flows, events_detected)

            # Record final values
            for j, name in enumerate(stocks.keys()):
                final_values[name].append(solution.y[j, -1])

        except Exception as e:
            logger.warning(f"Sensitivity run {i} failed: {e}")

        # Yield control
        if i % 10 == 0:
            await asyncio.sleep(0)

    # Restore original parameters
    for name, value in original_stocks.items():
        stocks[name].initial_value = value

    # Calculate sensitivity metrics
    sensitivity_metrics = {}
    for name, values in final_values.items():
        if values:
            sensitivity_metrics[f"{name}_sensitivity_mean"] = float(np.mean(values))
            sensitivity_metrics[f"{name}_sensitivity_std"] = float(np.std(values))
            sensitivity_metrics[f"{name}_cv"] = float(np.std(values) / np.mean(values)) if np.mean(values) != 0 else 0

    return sensitivity_metrics

def analyze_stability(
    config: SystemDynamicsConfig,
    stocks: dict[str, Stock],
    flows: list[Flow],
    time_history: np.ndarray,
    state_history: np.ndarray,
) -> dict[str, Any]:
    """Analyze system stability using Jacobian eigenvalues"""
    if state_history is None or state_history.size == 0:
        return {}

    # Compute Jacobian numerically at final state
    stock_names = list(stocks.keys())
    n = len(stock_names)

    # Use finite differences to approximate Jacobian
    epsilon = 1e-8
    jacobian = np.zeros((n, n))

    y_final = state_history[:, -1]
    t_final = time_history[-1]
    ode_func = create_ode_function(stocks, flows)

    for i in range(n):
        y_plus = y_final.copy()
        y_plus[i] += epsilon
        y_minus = y_final.copy()
        y_minus[i] -= epsilon

        f_plus = ode_func(t_final, y_plus)
        f_minus = ode_func(t_final, y_minus)

        jacobian[:, i] = (f_plus - f_minus) / (2 * epsilon)

    # Compute eigenvalues
    eigenvalues = np.linalg.eigvals(jacobian)

    # Analyze stability
    max_real = np.max(np.real(eigenvalues))
    is_stable = max_real < 0

    # Find equilibria (where derivatives are near zero)
    equilibria = []
    if config.find_equilibria:
        for i in range(len(time_history)):
            y = state_history[:, i]
            dy = ode_func(time_history[i], y)
            if np.all(np.abs(dy) < 0.01):
                equilibria.append({
                    "time": float(time_history[i]),
                    "state": y.tolist(),
                })

    return {
        "jacobian_eigenvalues_real": [float(np.real(ev)) for ev in eigenvalues],
        "jacobian_eigenvalues_imag": [float(np.imag(ev)) for ev in eigenvalues],
        "max_eigenvalue_real": float(max_real),
        "is_stable": bool(is_stable),
        "damped_frequency": float(np.max(np.imag(eigenvalues))) if any(np.imag(eigenvalues) != 0) else 0.0,
        "n_equilibria": len(equilibria),
    }

def detect_chaos(
    config: SystemDynamicsConfig,
    state_history: np.ndarray,
    rng: np.random.Generator,
) -> dict[str, Any]:
    """Detect chaotic behavior using 0-1 test"""
    if state_history is None or state_history.shape[1] < 100:
        return {}

    # Use 0-1 test for chaos
    # K ≈ 0: regular dynamics, K ≈ 1: chaotic dynamics

    # Select primary variable (usually first stock)
    x = state_history[0, :]

    # 0-1 test
    c = rng.uniform(0, 2 * np.pi)
    n = len(x)

    p = np.zeros(n)
    q = np.zeros(n)

    for i in range(n):
        p[i] = np.sum(x[:i+1] * np.cos(np.arange(i+1) * c))
        q[i] = np.sum(x[:i+1] * np.sin(np.arange(i+1) * c))

    # Compute mean square displacement
    M = np.zeros(n // 10)
    for j in range(1, n // 10):
        M[j] = np.mean((p[j:] - p[:-j])**2 + (q[j:] - q[:-j])**2)

    # Compute K
    log_M = np.log(M[1:])
    log_n = np.log(np.arange(1, len(M)))

    K = np.polyfit(log_n, log_M, 1)[0]

    # Alternative: Check for sensitivity to initial conditions
    # by looking at phase space expansion
    phase_volume = _estimate_phase_volume_expansion(state_history)

    return {
        "chaos_indicator_k": float(K),
        "is_chaotic": bool(K > 0.8),
        "phase_volume_expansion": float(phase_volume),
        "lyapunov_estimate": float(K),  # K approximates largest Lyapunov exponent
    }

def _estimate_phase_volume_expansion(state_history: np.ndarray) -> float:
    """Estimate phase space volume expansion rate"""
    if state_history is None or state_history.shape[1] < 10:
        return 0.0

    # Compute distance between trajectories at different times
    n_points = min(100, state_history.shape[1] // 2)

    distances_early = []
    distances_late = []

    for i in range(n_points):
        for j in range(i + 1, n_points):
            d_early = np.linalg.norm(
                state_history[:, i] - state_history[:, j]
            )
            d_late = np.linalg.norm(
                state_history[:, -(i+1)] - state_history[:, -(j+1)]
            )
            if d_early > 1e-6:
                distances_early.append(d_early)
                distances_late.append(d_late)

    if distances_early and distances_late:
        expansion = np.mean(distances_late) / np.mean(distances_early)
        return float(np.log(expansion))

    return 0.0
