"""
C4REQBER: Pre-Mortem Plugin
Imagine project failed and work backwards to identify causes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PreMortemResult:
    """Result of pre-mortem analysis."""

    project: str
    hypothetical_failure: str = ""
    root_causes: list[str] = field(default_factory=list)
    warning_signs: list[str] = field(default_factory=list)
    preventive_actions: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "hypothetical_failure": self.hypothetical_failure,
            "root_causes": self.root_causes,
            "warning_signs": self.warning_signs,
            "preventive_actions": self.preventive_actions,
            "confidence": self.confidence,
        }


def analyze(project: str) -> PreMortemResult:
    """Apply pre-mortem analysis."""
    result = PreMortemResult(project=project)

    result.hypothetical_failure = (
        f"It is 1 year later. The project '{project[:50]}...' has failed completely. "
        "We are analyzing why."
    )

    result.root_causes = [
        "Insufficient stakeholder buy-in from start",
        "Key technical assumptions proved invalid",
        "Resource constraints emerged mid-project",
        "External market conditions changed",
        "Team lacked critical expertise",
    ]

    result.warning_signs = [
        "Missed early milestones without escalation",
        "Declining team morale and engagement",
        "Increasing technical debt accumulation",
        "Stakeholder feedback ignored",
        "Budget overruns without review",
    ]

    result.preventive_actions = [
        "Validate core assumptions within first 2 weeks",
        "Establish clear success metrics and checkpoints",
        "Build in 20% buffer for resources and time",
        "Create escalation protocol for risks",
        "Conduct monthly stakeholder alignment reviews",
    ]

    result.confidence = 0.7
    return result


def execute(project: str, **kwargs: Any) -> dict[str, Any]:
    return analyze(project).to_dict()
