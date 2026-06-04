"""
c4reqber: Hypothesis Ranking Orchestrator

Integrates PriorScorer, EIGEstimator, CostModel, and MCDMRanker.
"""
from __future__ import annotations

import logging
from typing import Any

from src.discovery.ranking.cost_model import CostModel
from src.discovery.ranking.eig_estimator import EIGEstimator
from src.discovery.ranking.mcdm_ranker import MCDMRanker, RankedHypothesis
from src.discovery.ranking.prior_scorer import PriorScorer

logger = logging.getLogger("c4reqber.discovery.ranking")


async def rank_hypotheses(
    hypotheses: list[dict[str, Any]],
    context: dict[str, Any],
    max_simulations: int = 3,
) -> list[RankedHypothesis]:
    """Rank hypotheses by expected information gain, novelty, plausibility, cost.

    Args:
        hypotheses: List of hypothesis dicts.
        context: Dict with "literature" (list of papers), "domain" (str), etc.
        max_simulations: Number of top hypotheses to return.

    Returns:
        Ranked hypotheses.
    """
    if not hypotheses:
        return []

    literature = context.get("literature", [])
    domain = context.get("domain", "general")

    prior_scorer = PriorScorer()
    eig_estimator = EIGEstimator()
    cost_model = CostModel()

    # Score all hypotheses
    prior_scores: list[dict[str, float]] = []
    eig_scores: list[float] = []
    costs: list[dict[str, float]] = []

    for hyp in hypotheses:
        prior = prior_scorer.score(hyp, literature)
        prior_scores.append(prior)

        eig = eig_estimator.estimate(hyp, domain)
        eig_scores.append(eig)

        cost = cost_model.estimate(hyp)
        costs.append(cost)

    # Build criteria matrix
    criteria = {
        "eig": eig_scores,
        "novelty": [p["novelty"] for p in prior_scores],
        "plausibility": [p["plausibility"] for p in prior_scores],
        "falsifiability": [p["falsifiability"] for p in prior_scores],
    }

    ranker = MCDMRanker()
    ranked = ranker.rank(hypotheses, criteria=criteria, costs=costs)

    logger.info(
        "Ranked %d hypotheses. Top: %s (score=%.3f)",
        len(ranked),
        ranked[0].hypothesis.get("text", "")[:50] if ranked else "N/A",
        ranked[0].total_score if ranked else 0.0,
    )

    return ranked[:max_simulations]
