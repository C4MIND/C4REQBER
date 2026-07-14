"""
c4reqber: Closed-Loop Orchestrator

Runs the full closed-loop: design → simulate → update → check → refine.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.discovery.closed_loop.bayesian_tracker import BayesianHypothesisTracker
from src.discovery.closed_loop.convergence import ConvergenceChecker
from src.discovery.closed_loop.ensemble_runner import EnsembleRunner
from src.discovery.closed_loop.experiment_designer import ExperimentDesigner
from src.discovery.closed_loop.refiner import HypothesisRefiner


logger = logging.getLogger("c4reqber.discovery.closed_loop")


@dataclass
class ClosedLoopResult:
    action: str  # 'accept', 'reject', 'inconclusive'
    tracker: BayesianHypothesisTracker
    iterations: int = 0
    refined_hypothesis: str | None = None
    design_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "tracker": self.tracker.to_dict(),
            "iterations": self.iterations,
            "refined_hypothesis": self.refined_hypothesis,
            "design_history": self.design_history,
        }


class ClosedLoopOrchestrator:
    """Orchestrate closed-loop hypothesis testing."""

    def __init__(
        self,
        max_iterations: int = 5,
        accept_threshold: float = 10.0,
        reject_threshold: float = 0.1,
    ) -> None:
        self.max_iterations = max_iterations
        self.designer = ExperimentDesigner()
        self.runner = EnsembleRunner()
        self.checker = ConvergenceChecker(
            accept_threshold=accept_threshold,
            reject_threshold=reject_threshold,
            max_iterations=max_iterations,
        )
        self.refiner = HypothesisRefiner()

    async def run(
        self,
        hypothesis: dict[str, Any],
        available_simulators: list[str] | None = None,
    ) -> ClosedLoopResult:
        """Run closed-loop simulation for a hypothesis.

        Args:
            hypothesis: Hypothesis dict with at least "text" key.
            available_simulators: List of simulator names.

        Returns:
            ClosedLoopResult with final action and tracker.
        """
        hyp_text = hypothesis.get("text", "")
        tracker = BayesianHypothesisTracker(hyp_text)
        design_history: list[dict[str, Any]] = []

        for i in range(self.max_iterations):
            design = self.designer.design(tracker, i, available_simulators)
            design_history.append({
                "iteration": i,
                "simulator": design.simulator,
                "params": design.params,
                "n_runs": design.n_runs,
            })

            results = await self.runner.run_ensemble(design)
            tracker.update(results, design.simulator)

            action = self.checker.check(tracker, i)
            if action in ("accept", "reject", "inconclusive"):
                refined = await self.refiner.refine(hyp_text, tracker)
                return ClosedLoopResult(
                    action=action,
                    tracker=tracker,
                    iterations=i + 1,
                    refined_hypothesis=refined,
                    design_history=design_history,
                )

        # Max iterations reached
        refined = await self.refiner.refine(hyp_text, tracker)
        return ClosedLoopResult(
            action="inconclusive",
            tracker=tracker,
            iterations=self.max_iterations,
            refined_hypothesis=refined,
            design_history=design_history,
        )
