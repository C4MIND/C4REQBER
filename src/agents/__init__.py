"""
TURBO-CDI: Agents Module
Multi-agent scientific discovery system
"""

from src.agents.multi_agent import (
    MultiAgentSystem,
    AnalystAgent,
    ScientistAgent,
    CriticAgent,
    SynthesizerAgent,
    AgentRole,
    AgentOutput,
    get_multi_agent_system,
)

__all__ = [
    "MultiAgentSystem",
    "AnalystAgent",
    "ScientistAgent",
    "CriticAgent",
    "SynthesizerAgent",
    "AgentRole",
    "AgentOutput",
    "get_multi_agent_system",
]
