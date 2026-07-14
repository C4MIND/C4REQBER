"""
C4REQBER: Pattern Result Formatter — Utilities
"""
from __future__ import annotations


__all__ = [
    "_detect_result_type",
    "_extract_agents",
    "_extract_behavior",
    "_extract_ci",
    "_extract_constraints",
    "_extract_flows",
    "_extract_metrics",
    "_extract_objective",
    "_extract_samples",
    "_extract_solution",
    "_extract_stocks",
    "_extract_steps",
    "_extract_variables",
    "_fmt_val",
    "_md_agent_based",
    "_md_monte_carlo",
    "_md_optimization",
    "_md_system_dynamics",
    "_pick_key_metrics",
]

from typing import Any


# ------------------------------------------------------------------ #
# Helpers: type detection
# ------------------------------------------------------------------ #

def _detect_result_type(result: dict[str, Any], pattern_type_map: dict[str, str]) -> str:
    pattern_id = result.get("pattern_id", "")
    mapped = pattern_type_map.get(pattern_id)
    if mapped:
        return mapped

    # Heuristic fallback based on metric keys
    data = result.get("result", {})
    metrics = _extract_metrics(data)
    keys = set(metrics.keys())

    if any(k in keys for k in ("final_mean_wealth", "gini_coefficient", "n_agents")):
        return "agent_based"
    if any(k in keys for k in ("mean", "ci_lower", "ci_upper", "ess")):
        return "monte_carlo"
    if any(k in keys for k in ("final_values", "is_stable", "chaos_indicator_k")):
        return "system_dynamics"
    if any(k in keys for k in ("optimal_value", "optimal_variables", "num_iterations")):
        return "optimization"

    return "generic"


# ------------------------------------------------------------------ #
# Helpers: metric extraction
# ------------------------------------------------------------------ #

def _extract_metrics(data: dict[str, Any]) -> dict[str, Any]:
    """Extract metrics dict from nested result data."""
    if "metrics" in data:
        return dict(data["metrics"])
    if "data" in data and isinstance(data["data"], dict) and "metrics" in data["data"]:
        return dict(data["data"]["metrics"])
    return {}


def _extract_agents(data: dict[str, Any]) -> dict[str, Any]:
    metrics = _extract_metrics(data)
    return {
        "count": metrics.get("n_agents", 0),
        "final_mean_wealth": metrics.get("final_mean_wealth"),
        "final_gini": metrics.get("final_gini"),
        "equilibrium_reached": metrics.get("equilibrium_reached"),
        "phase_transitions": metrics.get("phase_transitions"),
    }


def _extract_steps(data: dict[str, Any]) -> dict[str, Any]:
    metrics = _extract_metrics(data)
    return {
        "n_steps": metrics.get("n_steps", 0),
        "wealth_trend": metrics.get("wealth_trend"),
    }


def _extract_samples(data: dict[str, Any]) -> dict[str, Any]:
    metrics = _extract_metrics(data)
    return {
        "n_samples": metrics.get("n_samples", 0),
        "mean": metrics.get("mean"),
        "std": metrics.get("std"),
        "variance": metrics.get("variance"),
        "ess": metrics.get("ess"),
    }


def _extract_ci(data: dict[str, Any]) -> dict[str, Any]:
    metrics = _extract_metrics(data)
    return {
        "level": 0.95,
        "lower": metrics.get("ci_lower"),
        "upper": metrics.get("ci_upper"),
    }


def _extract_stocks(data: dict[str, Any]) -> dict[str, Any]:
    metrics = _extract_metrics(data)
    stocks: dict[str, Any] = {}
    for key in metrics:
        if key.endswith("_final"):
            name = key.replace("_final", "")
            stocks[name] = {
                "initial": metrics.get(f"{name}_initial"),
                "final": metrics[key],
                "mean": metrics.get(f"{name}_mean"),
                "std": metrics.get(f"{name}_std"),
                "min": metrics.get(f"{name}_min"),
                "max": metrics.get(f"{name}_max"),
            }
    return stocks


def _extract_flows(data: dict[str, Any]) -> list[dict[str, Any]]:
    raw = data.get("flows", [])
    if isinstance(raw, list):
        return [{"name": f.get("name", ""), "rate": f.get("rate_expression", "")} for f in raw]
    return []


def _extract_behavior(data: dict[str, Any]) -> dict[str, Any]:
    metrics = _extract_metrics(data)
    return {
        "stable": metrics.get("is_stable"),
        "chaotic": metrics.get("is_chaotic"),
        "chaos_indicator_k": metrics.get("chaos_indicator_k"),
        "n_equilibria": metrics.get("n_equilibria"),
    }


def _extract_objective(data: dict[str, Any]) -> dict[str, Any]:
    metrics = _extract_metrics(data)
    return {
        "value": metrics.get("optimal_value"),
        "direction": "minimize",  # default; could be inferred from config
    }


def _extract_variables(data: dict[str, Any]) -> list[float] | None:
    metrics = _extract_metrics(data)
    return metrics.get("optimal_variables")


def _extract_constraints(data: dict[str, Any]) -> dict[str, Any]:
    metrics = _extract_metrics(data)
    sensitivity = metrics.get("sensitivity", {})
    return {
        "binding": sensitivity.get("binding_constraints"),
        "total": sensitivity.get("total_constraints"),
    }


def _extract_solution(data: dict[str, Any]) -> dict[str, Any]:
    metrics = _extract_metrics(data)
    return {
        "optimal_value": metrics.get("optimal_value"),
        "variables": metrics.get("optimal_variables"),
        "success": metrics.get("success"),
        "iterations": metrics.get("num_iterations"),
    }


# ------------------------------------------------------------------ #
# Helpers: formatting
# ------------------------------------------------------------------ #

def _fmt_val(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}" if abs(value) < 1e6 else f"{value:.2e}"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if value is None:
        return "N/A"
    return str(value)


def _pick_key_metrics(metrics: dict[str, Any], max_items: int = 6) -> dict[str, Any]:
    """Select the most informative metrics for synthesis."""
    priority_keys = [
        "optimal_value", "mean", "final_mean_wealth", "success",
        "is_stable", "equilibrium_reached", "n_agents", "n_samples",
        "ci_lower", "ci_upper", "gini_coefficient", "phase_transitions",
    ]
    ordered: dict[str, Any] = {}
    for k in priority_keys:
        if k in metrics:
            ordered[k] = metrics[k]
    # Fill remaining slots with any other keys
    for k, v in metrics.items():
        if k not in ordered:
            ordered[k] = v
        if len(ordered) >= max_items:
            break
    return ordered


# ------------------------------------------------------------------ #
# Type-specific markdown sections
# ------------------------------------------------------------------ #

def _md_agent_based(data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    metrics = _extract_metrics(data)
    if "final_mean_wealth" in metrics:
        lines.append("### Agent Summary")
        lines.append("")
        lines.append(f"- Final mean wealth: {metrics['final_mean_wealth']:.2f}")
        lines.append(f"- Gini coefficient: {metrics.get('final_gini', 0):.4f}")
        lines.append(f"- Equilibrium reached: {metrics.get('equilibrium_reached', False)}")
        lines.append(f"- Phase transitions: {metrics.get('phase_transitions', 0)}")
        lines.append("")
    return lines


def _md_monte_carlo(data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    metrics = _extract_metrics(data)
    if "mean" in metrics:
        lines.append("### Statistical Summary")
        lines.append("")
        lines.append(f"- Mean: {metrics['mean']:.6f}")
        lines.append(f"- Std Dev: {metrics.get('std', 0):.6f}")
        ci_lower = metrics.get('ci_lower', 0)
        ci_upper = metrics.get('ci_upper', 0)
        lines.append(f"- 95% CI: [{ci_lower:.6f}, {ci_upper:.6f}]")
        lines.append(f"- Effective sample size: {metrics.get('ess', 0):.1f}")
        lines.append("")
    return lines


def _md_system_dynamics(data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    metrics = _extract_metrics(data)
    stocks = {k: v for k, v in metrics.items() if k.endswith("_final")}
    if stocks:
        lines.append("### Stock Trajectories")
        lines.append("")
        lines.append("| Stock | Initial | Final | Mean | Std |")
        lines.append("|-------|---------|-------|------|-----|")
        for key, final in stocks.items():
            name = key.replace("_final", "")
            initial = metrics.get(f"{name}_initial", 0)
            mean = metrics.get(f"{name}_mean", 0)
            std = metrics.get(f"{name}_std", 0)
            lines.append(f"| {name} | {initial:.2f} | {final:.2f} | {mean:.2f} | {std:.2f} |")
        lines.append("")

    if metrics.get("is_stable") is not None:
        stability = "stable" if metrics["is_stable"] else "unstable"
        lines.append(f"**System stability:** {stability}")
        lines.append("")

    if metrics.get("is_chaotic"):
        k_val = metrics.get('chaos_indicator_k', 0)
        lines.append(f"**Chaotic behavior detected** (K = {k_val:.4f})")
        lines.append("")
    return lines


def _md_optimization(data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    metrics = _extract_metrics(data)
    if "optimal_value" in metrics:
        lines.append("### Optimization Result")
        lines.append("")
        lines.append(f"- Optimal value: {metrics['optimal_value']:.4f}")
        lines.append(f"- Success: {metrics.get('success', False)}")
        lines.append(f"- Iterations: {metrics.get('num_iterations', 0)}")

        variables = metrics.get("optimal_variables")
        if variables:
            lines.append(f"- Optimal variables: {variables}")

        sensitivity = metrics.get("sensitivity")
        if sensitivity:
            lines.append(f"- Binding constraints: {sensitivity.get('binding_constraints', 0)}")

        lines.append("")
    return lines
