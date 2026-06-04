"""
C4REQBER: Second-Order Thinking Plugin
Consider consequences of consequences.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SecondOrderResult:
    """Result of second-order thinking."""

    decision: str
    first_order: list[str] = field(default_factory=list)
    second_order: list[str] = field(default_factory=list)
    third_order: list[str] = field(default_factory=list)
    unintended_consequences: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "first_order": self.first_order,
            "second_order": self.second_order,
            "third_order": self.third_order,
            "unintended_consequences": self.unintended_consequences,
            "recommendations": self.recommendations,
        }


def analyze(decision: str) -> SecondOrderResult:
    """Apply second-order thinking."""
    result = SecondOrderResult(decision=decision)

    result.first_order = [
        "Immediate expected outcome",
        "Direct cost/benefit",
        "Short-term stakeholder reaction",
    ]

    result.second_order = [
        "How do competitors respond?",
        "What market dynamics shift?",
        "How does behavior change over time?",
        "What incentives are created?",
    ]

    result.third_order = [
        "System-level equilibrium shifts",
        "Long-term cultural changes",
        "Emergent properties from scale",
        "Feedback loop amplification",
    ]

    result.unintended_consequences = [
        "Resource reallocation effects",
        "Moral hazard creation",
        "Dependency formation",
        "Loss of optionality",
    ]

    result.recommendations = [
        "Map at least 3 levels of consequences",
        "Identify feedback loops",
        "Consider time delays in effects",
        "Plan for unintended consequences",
        "Build in reversibility where possible",
    ]

    return result


def execute(decision: str, **kwargs: Any) -> dict[str, Any]:
    return analyze(decision).to_dict()
