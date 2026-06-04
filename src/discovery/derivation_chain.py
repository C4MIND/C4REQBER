# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
from typing import Any

from src.pipeline.parsimony import ParsimonyScorer
from src.pipeline.recursive_validation import RecursiveValidationLoop


logger = logging.getLogger(__name__)


class MultiStepChain:
    """Orchestrate multi-step discovery chain with self-validation.

    Chains together: hypothesis → test → refine → repeat.
    Tracks: quality trajectory, hypothesis evolution, discovery score.
    """

    def __init__(self, max_steps: int = 5) -> None:
        self.max_steps = max_steps
        self.validator = RecursiveValidationLoop(max_iterations=max_steps)
        self.parsimony = ParsimonyScorer()
        self.chain: list[dict[str, Any]] = []

    def run(
        self,
        initial_hypothesis: str,
        quality_report: Any | None = None,
        simulation: dict[str, Any] | None = None,
        verification: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute multi-step chain starting from initial hypothesis.

        Returns: final_hypothesis, steps, quality_trajectory, total_score.
        """
        current = initial_hypothesis
        self.chain = []

        for step in range(self.max_steps):
            step_data: dict[str, Any] = {
                "step": step + 1,
                "hypothesis": current[:500],
                "quality_score": getattr(quality_report, "overall_score", 0) if quality_report else 0,
            }

            # Check termination
            if quality_report and not self.validator.should_reformulate(quality_report):
                step_data["terminated"] = "quality_sufficient"
                self.chain.append(step_data)
                break

            if self.validator.is_converged():
                step_data["terminated"] = "converged"
                self.chain.append(step_data)
                break

            # Refine
            if quality_report:
                prompt = self.validator.generate_reformulation_prompt(
                    current, quality_report, step,
                )
                step_data["reformulation_prompt"] = prompt[:300]
                # In production: call LLM with prompt → new hypothesis
                # For now: return prompt for pipeline to use

            # Record
            if quality_report:
                self.validator.record_attempt(getattr(quality_report, "overall_score", 0))

            # Switch hypothesis (simulated — in real pipeline, LLM generates new)
            step_data["next_ready"] = quality_report is not None
            self.chain.append(step_data)

        # Compute trajectory
        trajectory = [s.get("quality_score", 0) for s in self.chain]
        improving = len(trajectory) >= 2 and trajectory[-1] >= trajectory[0]

        parsimony_score = self.parsimony.score(current)

        return {
            "final_hypothesis": current[:500],
            "steps_taken": len(self.chain),
            "max_steps": self.max_steps,
            "quality_trajectory": trajectory,
            "improving": improving,
            "improvement_rate": self.validator.improvement_trajectory(),
            "converged": self.validator.is_converged(),
            "parsimony": parsimony_score,
            "chain": self.chain,
        }


__all__ = ["MultiStepChain"]
