"""Shared pipeline types — no implementation, no imports from src.*"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class PipelineStage(Enum):
    """Canonical pipeline stage identifiers (shared foundational type).

    Lives here so both the generic pipeline engine (src/pipeline) and the agent
    solve pipeline (src/agents/pipeline) can reference stages without one having
    to import the other.
    """
    IMPACT_IDENTIFY = "impact_identify"
    PRIOR_ART = "prior_art"
    GAP_ANALYSIS = "gap_analysis"
    QUALITY_GATE = "quality_gate"
    REALITY_CHECK = "reality_check"
    C4_FINGERPRINT = "c4_fingerprint"
    CROSS_DOMAIN_TRANSFER = "cross_domain_transfer"
    MP_ROTATION = "mp_rotation"
    QZRF_SELECT = "qzrf_select"
    ISOMORPHISM_SEARCH = "isomorphism_search"
    PLUGIN_EXECUTION = "plugin_execution"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    SIMULATION = "simulation"
    FORMAL_VERIFICATION = "formal_verification"


@dataclass
class PipelineResult:
    """Generic pipeline execution result."""
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    execution_time_ms: int = 0


class PipelineConfig(Protocol):
    """Protocol for pipeline configuration."""

    name: str
    description: str
    version: str

    def validate(self) -> list[str]:
        """Return list of validation error messages."""
        ...

    def to_dict(self) -> dict[str, Any]:
        ...


class SolvePipeline(Protocol):
    """Structural interface for a solve pipeline (e.g. agents.UniversalSolvePipeline).

    Lets lower layers (e.g. validation's benchmark harness) depend on the
    capability without importing the concrete pipeline from the agents package.
    The concrete pipeline is injected by the caller.
    """

    async def solve(self, problem: str, mode: str = ...) -> Any:
        ...
