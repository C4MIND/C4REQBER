"""
c4reqber: Convergence Checker

Determines when enough evidence has been gathered.
"""
from __future__ import annotations

from typing import Any

from src.discovery.closed_loop.bayesian_tracker import BayesianHypothesisTracker


class ConvergenceChecker:
    """Check if closed-loop has converged."""

    def __init__(
        self,
        accept_threshold: float = 10.0,
        reject_threshold: float = 0.1,
        max_iterations: int = 5,
    ) -> None:
        self.accept_threshold = accept_threshold
        self.reject_threshold = reject_threshold
        self.max_iterations = max_iterations

    def check(self, tracker: BayesianHypothesisTracker, iteration: int) -> str:
        """Check convergence status.

        Returns: 'accept', 'reject', 'inconclusive', or 'continue'.
        """
        bf = tracker.bayes_factor

        if bf > self.accept_threshold:
            return "accept"
        if bf < self.reject_threshold:
            return "reject"
        if iteration >= self.max_iterations - 1:
            return "inconclusive"
        return "continue"

    def to_dict(self) -> dict[str, Any]:
        return {
            "accept_threshold": self.accept_threshold,
            "reject_threshold": self.reject_threshold,
            "max_iterations": self.max_iterations,
        }
