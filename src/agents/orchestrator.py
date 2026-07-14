"""
C4REQBER: Enhanced Agent System
Multi-agent orchestrator with MP rotation and C4 state tracking.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from src.agents.pipeline import UniversalSolvePipeline
from src.c4.engine import C4Space
from src.c4.observer import ObserverController, ObserverPosition
from src.c4.state import C4State
from src.metamodels.mp.library import MPLibrary, MPProfile
from src.metamodels.mp.profiles import MPRotationEngine, RotationResult
from src.metamodels.qzrf.operators import QzrfLibrary


class AgentRole(Enum):
    """AgentRole."""

    ORCHESTRATOR = "orchestrator"
    DOMAIN = "domain"
    CRITIC = "critic"
    SYNTHESIZER = "synthesizer"
    EXPLORER = "explorer"


@dataclass
class AgentConfig:
    """Configuration for a single agent."""

    role: AgentRole
    domain: str
    mp_profile: MPProfile
    c4_state: C4State
    observer_position: ObserverPosition = ObserverPosition.OBSERVING
    max_iterations: int = 10


@dataclass
class AgentStep:
    """A step taken by an agent."""

    agent_id: str
    role: str
    action: str
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    c4_state_before: C4State | None = None
    c4_state_after: C4State | None = None
    duration_ms: float = 0.0


@dataclass
class AgentSessionResult:
    """Result of a full multi-agent session."""

    session_id: str
    problem: str
    mode: str  # manual, copilot, autopilot
    steps: list[AgentStep] = field(default_factory=list)
    final_solution: str = ""
    confidence: float = 0.0
    c4_path: list[str] = field(default_factory=list)
    mp_rotation: RotationResult | None = None
    total_duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "problem": self.problem,
            "mode": self.mode,
            "final_solution": self.final_solution,
            "confidence": self.confidence,
            "c4_path": self.c4_path,
            "total_duration_ms": self.total_duration_ms,
            "step_count": len(self.steps),
            "mp_rotation": self.mp_rotation.to_dict() if self.mp_rotation else None,
        }


class AgentOrchestrator:
    """
    Multi-agent orchestrator with:
    - MP profile rotation
    - C4 state tracking per agent
    - Observer position shifts
    - QZRF operator recommendations
    """

    def __init__(self) -> None:
        self.c4_space = C4Space()
        self.observer = ObserverController(self.c4_space)
        self.mp_engine = MPRotationEngine()
        self.qzrf = QzrfLibrary()
        self.mp_lib = MPLibrary()
        self._sessions: dict[str, AgentSessionResult] = {}
        self._session_timestamps: dict[str, float] = {}
        self._session_ttl_seconds = 3600  # 1 hour TTL

    def _cleanup_expired_sessions(self) -> None:
        now = time.time()
        expired = [
            sid
            for sid, ts in self._session_timestamps.items()
            if now - ts > self._session_ttl_seconds
        ]
        for sid in expired:
            self._sessions.pop(sid, None)
            self._session_timestamps.pop(sid, None)

    async def solve(
        self,
        problem: str,
        mode: str = "autopilot",
        domain_hint: str | None = None,
        max_depth: int = 6,
    ) -> AgentSessionResult:
        """
        Execute multi-agent problem-solving session via Universal Solve Pipeline.

        Modes:
        - manual: user drives every step
        - copilot: system suggests, user approves
        - autopilot: full automatic execution
        """
        self._cleanup_expired_sessions()
        pipeline = UniversalSolvePipeline()
        pipeline_result = await pipeline.solve(problem, mode, domain_hint, max_depth)

        # Convert pipeline result to AgentSessionResult for API compatibility
        session_id = f"sess_{hashlib.sha256(problem.encode()).hexdigest()[:8]}_{int(time.time())}"

        result = AgentSessionResult(
            session_id=session_id,
            problem=problem,
            mode=mode,
            final_solution=pipeline_result.final_solution,
            confidence=pipeline_result.confidence,
            c4_path=pipeline_result.c4_path,
            total_duration_ms=pipeline_result.total_duration_ms,
        )

        # Map pipeline perspectives to MP rotation result
        mp_result = RotationResult(
            problem=problem,
            perspectives=pipeline_result.mp_perspectives,
            synthesized_view=pipeline_result.final_solution,
            consensus_score=pipeline_result.confidence,
            total_duration_ms=pipeline_result.total_duration_ms,
        )
        result.mp_rotation = mp_result

        self._sessions[session_id] = result
        self._session_timestamps[session_id] = time.time()
        return result

    def get_session(self, session_id: str) -> AgentSessionResult | None:
        """Get session."""
        self._cleanup_expired_sessions()
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[dict[str, Any]]:
        """List sessions."""
        self._cleanup_expired_sessions()
        return [s.to_dict() for s in self._sessions.values()]

    def recommend_qzrf(self, current_state: C4State) -> list[dict[str, Any]]:
        """Recommend QZRF operators for current C4 state."""
        operators = self.qzrf.applicable_to(current_state)
        return [
            {
                "id": op.id,
                "name": op.name,
                "name_ru": op.name_ru,
                "phase": op.phase.value,
                "description": op.description,
                "c4_target": op.c4_target.to_tuple(),
            }
            for op in operators
        ]
