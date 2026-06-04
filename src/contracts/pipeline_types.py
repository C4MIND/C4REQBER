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
