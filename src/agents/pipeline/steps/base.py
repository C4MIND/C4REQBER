"""
C4REQBER: Pipeline Base Types
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PipelineStage(Enum):
    """PipelineStage."""
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
class PipelineStepResult:
    """PipelineStepResult."""
    stage: PipelineStage
    status: str = "pending"
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    error: str | None = None


class PipelineStep(ABC):
    """Abstract base class for pipeline steps."""

    @property
    @abstractmethod
    def stage(self) -> PipelineStage:
        """Return the pipeline stage this step handles."""

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute the step with given context.

        Args:
            context: Shared pipeline context with data from previous steps.

        Returns:
            PipelineStepResult with execution results.
        """

    def get_required_context(self) -> list[str]:
        """Return list of required context keys. Override if needed."""
        return []

    def get_optional_context(self) -> list[str]:
        """Return list of optional context keys. Override if needed."""
        return []
