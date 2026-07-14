"""
c4-cdi-turbo: Multi-Agent System (Legacy Compatibility)
Re-exports all symbols from the new modular structure.
"""
from __future__ import annotations

from src.agents.multi.agents import (
    AnalystAgent,
    CriticAgent,
    ScientistAgent,
    SynthesizerAgent,
)
from src.agents.multi.core import AgentMessage, AgentOutput, AgentRole, BaseAgent
from src.agents.multi.orchestrator import MultiAgentSystem, get_multi_agent_system


__all__ = [
    "AgentRole",
    "AgentMessage",
    "AgentOutput",
    "BaseAgent",
    "AnalystAgent",
    "ScientistAgent",
    "CriticAgent",
    "SynthesizerAgent",
    "MultiAgentSystem",
    "get_multi_agent_system",
]
