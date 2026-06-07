"""Shared pipeline types — no implementation, no imports from src.*"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


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
