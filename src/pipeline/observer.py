from __future__ import annotations

import hashlib
import logging
from typing import Any


class PipelineObserver:
    """Meta-observer: watches pipeline state transitions and detects quality degradation.

    Phase 1.7 (von Neumann audit): No mechanism existed to detect that refinements
    produce semantically identical output. The observer tracks novelty, gap_potential,
    and hypothesis similarity across iterations and HALTS the loop on stagnation.
    """

    def __init__(self, stagnation_threshold: float = 0.05, max_stagnant_iterations: int = 3) -> None:
        self._logger = logging.getLogger("c44tcdi.pipeline.observer")
        self.stagnation_threshold = stagnation_threshold
        self.max_stagnant_iterations = max_stagnant_iterations
        self.history: list[Observation] = []

    def observe(self, iteration: int, metrics: dict[str, Any]) -> Observation:
        """Observe."""
        obs = Observation(
            iteration=iteration,
            novelty_score=metrics.get("novelty_score", 0),
            gap_potential=metrics.get("gap_potential", 0),
            hypothesis_hash=self._hash_hypothesis(metrics.get("hypothesis_text", "")),
            abort_reasons=metrics.get("abort_reasons", []),
        )
        self.history.append(obs)
        return obs

    def should_halt(self) -> bool:
        """Determine if should halt."""
        if len(self.history) < self.max_stagnant_iterations:
            return False
        recent = self.history[-self.max_stagnant_iterations:]
        if all(o.hypothesis_hash == recent[0].hypothesis_hash for o in recent):
            self._logger.warning("HALT_STAGNATION: %d consecutive iterations with identical hypothesis", self.max_stagnant_iterations)
            return True
        if all(o.gap_potential >= recent[0].gap_potential * 0.95 for o in recent) and all(o.gap_potential <= recent[0].gap_potential * 1.05 for o in recent):
            self._logger.warning("HALT_PLATEAU: gap_potential unchanged across %d iterations", self.max_stagnant_iterations)
            return True
        if all(o.novelty_score <= self.stagnation_threshold for o in recent):
            self._logger.warning("HALT_LOW_NOVELTY: novelty_score ≤ %.3f across %d iterations", self.stagnation_threshold, self.max_stagnant_iterations)
            return True
        return False

    @staticmethod
    def _hash_hypothesis(text: str) -> str:
        return hashlib.sha256(text[:200].lower().strip().encode()).hexdigest()


class Observation:
    """Observation."""
    def __init__(self, iteration: int, novelty_score: float, gap_potential: float, hypothesis_hash: str, abort_reasons: list[str]) -> None:
        self.iteration = iteration
        self.novelty_score = novelty_score
        self.gap_potential = gap_potential
        self.hypothesis_hash = hypothesis_hash
        self.abort_reasons = abort_reasons
