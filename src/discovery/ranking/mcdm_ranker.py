"""
c4reqber: Multi-Criteria Decision Making Ranker

Ranks hypotheses using weighted aggregation of criteria.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class RankedHypothesis:
    """A hypothesis with its ranking scores."""

    hypothesis: dict[str, Any]
    rank: int
    total_score: float
    criteria_scores: dict[str, float]
    cost_estimate: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_text": self.hypothesis.get("text", "")[:200],
            "rank": self.rank,
            "total_score": round(self.total_score, 4),
            "criteria_scores": {k: round(v, 4) for k, v in self.criteria_scores.items()},
            "cost_estimate": self.cost_estimate,
        }


DEFAULT_WEIGHTS = {
    "eig": 0.35,
    "novelty": 0.20,
    "plausibility": 0.20,
    "falsifiability": 0.15,
    "cost_inverse": 0.10,
}


class MCDMRanker:
    """Rank hypotheses using weighted sum MCDM."""

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self.weights = weights or DEFAULT_WEIGHTS
        self._validate_weights()

    def _validate_weights(self) -> None:
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):
            # Normalize
            self.weights = {k: v / total for k, v in self.weights.items()}

    def rank(
        self,
        hypotheses: list[dict[str, Any]],
        criteria: dict[str, list[float]] | None = None,
        costs: list[dict[str, float]] | None = None,
    ) -> list[RankedHypothesis]:
        """Rank hypotheses by weighted criteria.

        Args:
            hypotheses: List of hypothesis dicts.
            criteria: Dict mapping criterion name to list of scores (per hypothesis).
            costs: List of cost estimate dicts (per hypothesis).

        Returns:
            List of RankedHypothesis, sorted by total_score descending.
        """
        if not hypotheses:
            return []

        n = len(hypotheses)
        criteria = criteria or {}
        costs = costs or [{} for _ in range(n)]

        # Build score matrix
        score_matrix = np.zeros((n, len(self.weights)))
        criterion_names = list(self.weights.keys())

        for j, crit_name in enumerate(criterion_names):
            if crit_name == "cost_inverse":
                # Lower cost = higher score
                total_costs = [c.get("total_usd", 0.0) for c in costs]
                max_cost = max(total_costs) if total_costs else 1.0
                scores = [1.0 - (c / max_cost) if max_cost > 0 else 1.0 for c in total_costs]
            else:
                scores = criteria.get(crit_name, [0.5] * n)
                # Normalize to 0-1
                min_s, max_s = min(scores), max(scores)
                if max_s > min_s:
                    scores = [(s - min_s) / (max_s - min_s) for s in scores]
                else:
                    scores = [0.5] * n

            for i in range(n):
                score_matrix[i, j] = scores[i]

        # Weighted sum
        weights_vec = np.array([self.weights[c] for c in criterion_names])
        total_scores = score_matrix @ weights_vec

        # Sort by total score descending
        indexed = list(enumerate(total_scores))
        indexed.sort(key=lambda x: x[1], reverse=True)

        ranked = []
        for rank, (orig_idx, score) in enumerate(indexed, 1):
            crit_scores = {
                name: float(score_matrix[orig_idx, j])
                for j, name in enumerate(criterion_names)
            }
            ranked.append(RankedHypothesis(
                hypothesis=hypotheses[orig_idx],
                rank=rank,
                total_score=float(score),
                criteria_scores=crit_scores,
                cost_estimate=costs[orig_idx],
            ))

        return ranked
