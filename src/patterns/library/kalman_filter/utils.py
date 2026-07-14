"""
C4REQBER v6.0 - Kalman Filter Utilities
Helper functions for system simulation and metrics calculation.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def calculate_nees(
    true_states: list[np.ndarray],
    estimated_states: list[np.ndarray],
    covariances: list[np.ndarray],
    state_dim: int,
) -> list[float]:
    """
    Calculate Normalized Estimation Error Squared (NEES).

    NEES = error' * P^-1 * error
    Should be close to state_dim for well-tuned filter.
    """
    nees_values = []
    for i, (x_true, x_est) in enumerate(zip(true_states, estimated_states, strict=False)):
        if i < len(covariances):
            P = (
                covariances[i]
                if i < len(covariances)
                else np.eye(state_dim)
            )
            error = x_true - x_est
            try:
                nees = (
                    error @ np.linalg.inv(P + 1e-6 * np.eye(state_dim)) @ error
                )
                nees_values.append(nees)
            except (np.linalg.LinAlgError, ValueError):
                pass
    return nees_values

def calculate_rmse(errors: np.ndarray) -> float:
    """Calculate Root Mean Square Error"""
    return float(np.sqrt(np.mean(errors**2)))

def format_simulation_results(
    cfg: Any,
    filter_obj: Any,
    history: dict[str, list[Any]],
    errors: np.ndarray,
    cov_traces: np.ndarray,
) -> dict[str, Any]:
    """Format simulation output into standard result structure"""
    metrics = {
        "mean_error": float(np.mean(errors)),
        "max_error": float(np.max(errors)),
        "final_error": float(errors[-1]),
        "mean_covariance_trace": float(np.mean(cov_traces)),
        "final_covariance_trace": float(cov_traces[-1]),
        "rmse": float(np.sqrt(np.mean(errors**2))),
    }

    # Calculate NEES
    nees_values = calculate_nees(
        [np.array(s) for s in history["true_state"]],
        [np.array(s) for s in history["estimated_state"]],
        filter_obj.covariance_history,
        cfg.state_dim,
    )

    if nees_values:
        metrics["mean_nees"] = float(np.mean(nees_values))

    return {
        "filter_type": cfg.filter_type.value,
        "system_model": cfg.system_model.value,
        "performance_metrics": metrics,
        "history": {
            "time": history["time"],
            "true_state": [s.tolist() for s in history["true_state"]],
            "estimated_state": [
                s.tolist() for s in history["estimated_state"]
            ],
            "measurement": [m.tolist() for m in history["measurement"]],
            "covariance_trace": history["covariance_trace"],
            "error": history["error"],
        },
        "final_estimate": filter_obj.x.tolist(),
        "final_covariance": filter_obj.P.tolist(),
        "noise_parameters": {
            "Q": cfg.Q.tolist(),
            "R": cfg.R.tolist(),
        },
        "config": {
            "state_dim": cfg.state_dim,
            "measurement_dim": cfg.measurement_dim,
            "dt": cfg.dt,
            "simulation_steps": cfg.simulation_steps,
        },
    }

def get_default_metadata() -> dict[str, Any]:
    """Get default metadata for KalmanFilterPattern"""
    return {
        "id": "kalman_filter",
        "version": "6.0.0",
        "name": "Kalman Filter",
        "category": "EXTENDED",
        "domain": [
            "State Estimation",
            "Navigation",
            "Robotics",
            "Signal Processing",
        ],
        "description": "EKF and UKF for state estimation in linear and nonlinear systems",
        "computational_complexity": "O(n³) per update",
        "typical_runtime": "microseconds to milliseconds",
        "accuracy": "High (optimal for linear-Gaussian)",
        "assumptions": [
            "Gaussian noise",
            "Known system model",
            "Linear or mildly nonlinear dynamics",
        ],
        "parameters": [
            {
                "name": "filter_type",
                "type": "enum",
                "options": ["kf", "ekf", "ukf"],
                "default": "ekf",
            },
            {
                "name": "system_model",
                "type": "enum",
                "options": [
                    "constant_velocity",
                    "constant_acceleration",
                    "nonlinear_pendulum",
                ],
                "default": "constant_velocity",
            },
            {"name": "state_dim", "type": "int", "default": 2},
            {"name": "dt", "type": "float", "default": 0.01},
        ],
    }
