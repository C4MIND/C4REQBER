# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


class RecursiveValidationLoop:
    """Feedback loop: Quality Gates → Hypothesis Refinement.

    Max 3 iterations. Tracks improvement trajectory.
    """

    def __init__(self, max_iterations: int = 3, quality_threshold: float = 60.0) -> None:
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.history: list[dict[str, float]] = []

    def should_reformulate(self, quality_report: Any) -> bool:
        """Check if hypothesis needs reformulation based on quality score."""
        if not quality_report:
            return False
        score = getattr(quality_report, "overall_score", 0)
        return score < self.quality_threshold and len(self.history) < self.max_iterations

    def generate_reformulation_prompt(
        self,
        hypothesis: str,
        quality_report: Any,
        iteration: int,
    ) -> str:
        """Generate a prompt that reformulates the hypothesis based on quality feedback."""
        recommendations = getattr(quality_report, "recommendations", []) or []
        score = getattr(quality_report, "overall_score", 0)
        grade = getattr(quality_report, "grade", "N/A")

        feedback = "\n".join(f"  - {r}" for r in recommendations[:5]) if recommendations else "  No specific recommendations."

        return f"""REFORMULATE this hypothesis based on quality assessment feedback.

ORIGINAL HYPOTHESIS: {hypothesis[:500]}

QUALITY SCORE: {score}/100 (Grade: {grade})
FEEDBACK:
{feedback}

ATTEMPT: {iteration + 1}/{self.max_iterations}

Reformulate the hypothesis addressing ALL feedback points above. Be specific, concrete, and scientifically rigorous."""

    def record_attempt(self, score: float) -> None:
        self.history.append({"score": score, "iteration": len(self.history) + 1})

    def improvement_trajectory(self) -> float:
        """Calculate improvement rate (Δ per iteration)."""
        if len(self.history) < 2:
            return 0.0
        scores = [h["score"] for h in self.history]
        return (scores[-1] - scores[0]) / (len(scores) - 1)

    def is_improving(self) -> bool:
        """Check if quality is trending upward."""
        if len(self.history) < 2:
            return True
        return self.history[-1]["score"] >= self.history[-2]["score"] - 2  # 2pt tolerance

    def is_converged(self) -> bool:
        """Check if score has plateaued."""
        if len(self.history) < 2:
            return False
        return abs(self.history[-1]["score"] - self.history[-2]["score"]) < 1.0


__all__ = ["RecursiveValidationLoop"]
