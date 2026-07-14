"""
C4REQBER: Multi-Agent System — Core Types and Base Classes
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgentRole(Enum):
    """Specialized agent roles."""

    ANALYST = "analyst"
    SCIENTIST = "scientist"
    CRITIC = "critic"
    SYNTHESIZER = "synthesizer"
    VALIDATOR = "validator"


@dataclass
class AgentMessage:
    """Message between agents."""

    from_agent: str
    to_agent: str
    message_type: str
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentOutput:
    """Output from an agent."""

    agent_role: str
    agent_name: str
    output_type: str
    content: Any
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)


class BaseAgent:
    """Base class for all agents."""

    def __init__(self, role: AgentRole, name: str) -> None:
        self.role = role
        self.name = name
        self.memory: list[AgentMessage] = []
        self.confidence_threshold = 0.6

    def receive_message(self, message: AgentMessage) -> None:
        """Receive message from another agent."""
        self.memory.append(message)

    async def process(self, context: dict[str, Any]) -> AgentOutput:
        """Process input and produce output. Override in subclasses."""
        raise NotImplementedError

    def get_relevant_memory(
        self, message_type: str | None = None
    ) -> list[AgentMessage]:
        """Get relevant messages from memory."""
        if message_type:
            return [m for m in self.memory if m.message_type == message_type]
        return self.memory


class Agent:
    """Concrete agent with message-type routing — sync interface for direct usage."""

    def __init__(self, name: str = "agent", expertise: str = "general", domain: str = "general") -> None:
        self.name = name
        self.expertise = expertise
        self.domain = domain

    def process(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        """Process an incoming message and optionally return a response"""
        msg_type = msg.get("type", "unknown")

        if msg_type == "query":
            return self._handle_query(msg)
        elif msg_type == "proposal":
            return self._handle_proposal(msg)
        elif msg_type == "critique":
            return self._handle_critique(msg)
        elif msg_type == "data":
            return self._handle_data(msg)
        else:
            return self._handle_unknown(msg)

    def _handle_query(self, msg: dict[str, Any]) -> dict[str, Any]:
        """Handle a query message — analyze and respond"""
        query = msg.get("content", "")
        keywords = self.expertise.lower().split("_") if self.expertise != "general" else self.name.lower().split("_")

        relevance = sum(1 for kw in keywords if kw in query.lower()) / max(len(keywords), 1)

        if relevance > 0.1:
            return {
                "type": "response",
                "agent": self.name,
                "relevance": relevance,
                "content": f"({self.__class__.__name__}) Analysis: {query[:100]}... [confidence: {relevance:.2f}]",
                "confidence": min(1.0, relevance * 1.5),
            }

        return {"type": "ack", "agent": self.name, "content": "Out of scope"}

    def _handle_proposal(self, msg: dict[str, Any]) -> dict[str, Any]:
        return {"type": "vote", "agent": self.name, "approval": 0.5}

    def _handle_critique(self, msg: dict[str, Any]) -> dict[str, Any]:
        return {"type": "revision", "agent": self.name, "suggestions": ["Consider alternative approach"]}

    def _handle_data(self, msg: dict[str, Any]) -> dict[str, Any]:
        return {"type": "analysis", "agent": self.name, "insights": ["Data received and processed"]}

    def _handle_unknown(self, msg: dict[str, Any]) -> dict[str, Any]:
        return {"type": "ack", "agent": self.name, "content": "Message received"}
