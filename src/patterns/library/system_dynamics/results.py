"""
Results compilation and confidence calculation for System Dynamics
"""

from typing import Any

import numpy as np

from .types import SystemDynamicsConfig


def compile_results(
    solution: Any,
    stock_names: list[str],
    sensitivity: dict[str, Any],
    stability: dict[str, Any],
    chaos: dict[str, Any],
    events_detected: list[dict[str, Any]],
    config: SystemDynamicsConfig,
) -> dict[str, Any]:
    """Compile all results"""

    # Basic trajectory metrics
    final_state = solution.y[:, -1]
    initial_state = solution.y[:, 0]

    metrics = {
        "final_values": {name: float(final_state[i]) for i, name in enumerate(stock_names)},
        "initial_values": {name: float(initial_state[i]) for i, name in enumerate(stock_names)},
        "n_steps": len(solution.t),
        "integration_success": solution.success,
        "n_function_evals": solution.nfev if hasattr(solution, 'nfev') else 0,
    }

    # Add time series statistics
    for i, name in enumerate(stock_names):
        traj = solution.y[i, :]
        metrics[f"{name}_mean"] = float(np.mean(traj))
        metrics[f"{name}_std"] = float(np.std(traj))
        metrics[f"{name}_min"] = float(np.min(traj))
        metrics[f"{name}_max"] = float(np.max(traj))
        metrics[f"{name}_initial"] = float(traj[0])
        metrics[f"{name}_final"] = float(traj[-1])

        # Oscillation frequency
        if len(traj) > 10:
            zero_crossings = np.sum(np.diff(np.signbit(traj - np.mean(traj))))
            metrics[f"{name}_oscillations"] = int(zero_crossings // 2)

    # Add sensitivity results
    metrics.update(sensitivity)

    # Add stability results
    metrics.update(stability)

    # Add chaos results
    metrics.update(chaos)

    # Event detection
    metrics["n_events"] = len(events_detected)

    # Build logs
    logs = [
        f"Simulation completed: {len(solution.t)} time points",
        f"Integration {'successful' if solution.success else 'may have issues'}",
        f"Stocks analyzed: {stock_names}",
    ]

    for name in stock_names:
        logs.append(
            f"  {name}: {metrics[f'{name}_initial']:.2f} → {metrics[f'{name}_final']:.2f}"
        )

    if stability.get("is_stable"):
        logs.append(f"System is STABLE (max eigenvalue: {stability.get('max_eigenvalue_real', 0):.4f})")
    elif stability.get("max_eigenvalue_real"):
        logs.append(f"System is UNSTABLE (max eigenvalue: {stability.get('max_eigenvalue_real', 0):.4f})")

    if chaos.get("is_chaotic"):
        logs.append(f"CHAOTIC behavior detected (K = {chaos.get('chaos_indicator_k', 0):.4f})")

    if events_detected:
        logs.append(f"Detected {len(events_detected)} threshold crossing events")

    return {"metrics": metrics, "logs": logs}

def calculate_confidence(
    results: dict[str, Any],
    config: SystemDynamicsConfig,
) -> float:
    """Calculate confidence score"""
    metrics = results["metrics"]
    factors = []

    # 1. Successful integration
    if metrics.get("integration_success", False):
        factors.append(0.2)

    # 2. Stability analysis performed
    if "is_stable" in metrics:
        factors.append(0.15)

    # 3. Sensitivity analysis performed
    if any("sensitivity" in k for k in metrics.keys()):
        factors.append(0.15)

    # 4. Sufficient time points
    if metrics.get("n_steps", 0) > 100:
        factors.append(0.15)

    # 5. No chaos (deterministic systems more confident)
    if not metrics.get("is_chaotic", False):
        factors.append(0.15)

    # 6. Events detected or explicitly searched for
    if metrics.get("n_events", 0) > 0 or not config.detect_events:
        factors.append(0.1)

    return min(0.95, sum(factors))
