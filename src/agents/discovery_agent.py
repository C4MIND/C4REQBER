"""
C4REQBER: Agent Mode v4.1
Autonomous scientific discovery agent

DEPRECATED: This module has been split. Use src.agents.discovery.core and src.agents.discovery.strategies instead.
This file remains as a backward-compatibility wrapper.
"""
from __future__ import annotations


__all__ = [
    "AgentHypothesis",
    "AgentReport",
    "ScientificDiscoveryAgent",
    "get_agent",
]

from src.agents.discovery.core import (
    AgentHypothesis,
    AgentReport,
    ScientificDiscoveryAgent,
    get_agent,
)
from src.agents.discovery.strategies import (  # type: ignore[attr-defined]
    estimate_cost,
    estimate_time,
    generate_analogies,
    generate_c4_triz,
    generate_falsifiability,
    generate_hybrid,
    generate_recommendations,
    generate_summary,
    parse_time,
    rank_hypotheses,
)
