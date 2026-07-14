"""c4-cdi-turbo: Agent Discovery Module"""
from __future__ import annotations

from .core import (
    AgentHypothesis,
    AgentReport,
    ScientificDiscoveryAgent,
    get_agent,
)
from .strategies import (
    _estimate_cost,
    _estimate_time,
    _generate_analogies,
    _generate_c4_triz,
    _generate_falsifiability,
    _generate_hybrid,
    _generate_recommendations,
    _generate_summary,
    _parse_time,
    _rank_hypotheses,
)


__all__ = [
    "AgentHypothesis",
    "AgentReport",
    "ScientificDiscoveryAgent",
    "get_agent",
    "_generate_c4_triz",
    "_generate_analogies",
    "_generate_hybrid",
    "_generate_falsifiability",
    "_rank_hypotheses",
    "_estimate_cost",
    "_estimate_time",
    "_parse_time",
    "_generate_summary",
    "_generate_recommendations",
]
