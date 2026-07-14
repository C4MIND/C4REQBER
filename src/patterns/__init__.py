"""
c4-cdi-turbo: Pattern Result Formatter
"""
from __future__ import annotations

from src.patterns.format.core import PatternResultFormatter
from src.patterns.format.utils import (
    _detect_result_type,
    _extract_agents,
    _extract_behavior,
    _extract_ci,
    _extract_constraints,
    _extract_flows,
    _extract_metrics,
    _extract_objective,
    _extract_samples,
    _extract_solution,
    _extract_steps,
    _extract_stocks,
    _extract_variables,
    _fmt_val,
    _md_agent_based,
    _md_monte_carlo,
    _md_optimization,
    _md_system_dynamics,
    _pick_key_metrics,
)


__all__ = [
    "PatternResultFormatter",
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
