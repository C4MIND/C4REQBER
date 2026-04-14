"""TURBO-CDI Agent Module"""

from .discovery_agent import (
    ScientificDiscoveryAgent,
    get_agent,
    AgentHypothesis,
    AgentReport,
)

__all__ = [
    "ScientificDiscoveryAgent",
    "get_agent",
    "AgentHypothesis",
    "AgentReport",
]
