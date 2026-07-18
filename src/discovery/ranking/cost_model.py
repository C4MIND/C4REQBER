"""
c4reqber: Cost Model

Estimates computational and financial cost of verifying a hypothesis.
"""

from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger("c4reqber.discovery.ranking")


class CostModel:
    """Estimate cost of hypothesis verification."""

    # Rough cost constants (USD)
    LLM_COST_PER_1K_TOKENS = 0.002  # DeepSeek V4 Flash blended rate
    PROOF_COST_PER_LANGUAGE = 0.012  # From ConsensusEngine
    SIM_COST_PER_MINUTE = 0.01  # Compute cost estimate
    DATA_API_COST_PER_CALL = 0.001  # External API call

    def estimate(
        self, hypothesis: dict[str, Any], plan: dict[str, Any] | None = None
    ) -> dict[str, float]:
        """Estimate costs for verifying a hypothesis.

        Returns dict with: llm_cost_usd, sim_cpu_seconds, data_api_calls, total_usd.
        """
        plan = plan or {}
        hyp_text = hypothesis.get("text", "")

        # LLM cost: proportional to text length and proof languages
        token_estimate = len(hyp_text) // 4 + 500  # rough tokens
        n_languages = plan.get("languages", 3)
        llm_cost = (token_estimate / 1000) * self.LLM_COST_PER_1K_TOKENS
        llm_cost += n_languages * self.PROOF_COST_PER_LANGUAGE

        # Simulation cost
        n_simulations = plan.get("simulations", 1)
        sim_minutes = plan.get("sim_minutes", 1.0)
        sim_cost = n_simulations * sim_minutes * self.SIM_COST_PER_MINUTE

        # Data API calls
        n_sources = plan.get("sources", 5)
        data_cost = n_sources * self.DATA_API_COST_PER_CALL

        return {
            "llm_cost_usd": round(llm_cost, 4),
            "sim_cost_usd": round(sim_cost, 4),
            "data_cost_usd": round(data_cost, 4),
            "total_usd": round(llm_cost + sim_cost + data_cost, 4),
            "heuristic": True,
            "note": "Costs derived from text length / constants — not metered spend",
        }
