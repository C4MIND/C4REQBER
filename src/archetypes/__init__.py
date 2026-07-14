"""
C4 Archetypes — 27 Cognitive State Agents
Z₃³ hypercube: Time × Scale × Agency
"""
from __future__ import annotations

from .data import ARCHETYPE_MAP, C4Archetype, get_all_archetypes, get_archetype
from .engine import (
    build_agent_prompt,
    build_synergy_matrix,
    get_neighbors,
    get_optimal_team,
    get_synergy_coefficient,
    select_agents_for_task,
)


__all__ = [
    "ARCHETYPE_MAP",
    "C4Archetype",
    "get_archetype",
    "get_all_archetypes",
    "get_synergy_coefficient",
    "build_synergy_matrix",
    "get_optimal_team",
    "get_neighbors",
    "select_agents_for_task",
    "build_agent_prompt",
]
