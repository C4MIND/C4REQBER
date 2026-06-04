"""
C4REQBER: First Principles Plugin
Decompose problem into fundamental truths and rebuild from scratch.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FirstPrinciplesResult:
    """Result of first principles analysis."""

    original_problem: str
    assumptions: list[str] = field(default_factory=list)
    fundamental_truths: list[str] = field(default_factory=list)
    deconstructed_elements: list[str] = field(default_factory=list)
    rebuilt_solution: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_problem": self.original_problem,
            "assumptions": self.assumptions,
            "fundamental_truths": self.fundamental_truths,
            "deconstructed_elements": self.deconstructed_elements,
            "rebuilt_solution": self.rebuilt_solution,
            "confidence": self.confidence,
        }


def analyze(problem: str) -> FirstPrinciplesResult:
    """Apply first principles thinking."""
    result = FirstPrinciplesResult(original_problem=problem)

    # Extract assumptions (heuristic: sentences with "must", "should", "always")
    sentences = problem.replace("?", ".").replace("!", ".").split(".")
    for s in sentences:
        s = s.strip()
        if any(
            w in s.lower() for w in ["must", "should", "always", "never", "impossible", "can't"]
        ):
            result.assumptions.append(s)

    if not result.assumptions:
        result.assumptions = [
            "Assumed current approach is optimal",
            "Assumed constraints are fixed",
            "Assumed problem definition is correct",
        ]

    # Generate fundamental truths
    result.fundamental_truths = [
        f"What is physically possible? → {problem[:40]}...",
        "What are the economic constraints?",
        "What do we know with certainty?",
        "What has nature already solved?",
    ]

    # Deconstruct
    result.deconstructed_elements = [
        "Break into smallest independent components",
        "Identify dependencies between components",
        "Find irreducible elements",
        "Map cause-effect chains",
    ]

    # Rebuild
    result.rebuilt_solution = (
        f"From first principles: Rebuild {problem[:50]}... "
        "by identifying fundamental constraints, removing artificial limitations, "
        "and constructing solution from verified truths."
    )
    result.confidence = 0.75

    return result


def execute(problem: str, **kwargs: Any) -> dict[str, Any]:
    return analyze(problem).to_dict()
