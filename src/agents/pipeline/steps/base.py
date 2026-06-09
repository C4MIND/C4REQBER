"""
C4REQBER: Pipeline Base Types
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

# PipelineStage moved to the foundational contracts layer; re-exported here so
# existing `agents.pipeline.steps.base` imports keep working.
from src.contracts.pipeline_types import PipelineStage


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
