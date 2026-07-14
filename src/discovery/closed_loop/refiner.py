"""
c4reqber: Hypothesis Refiner

LLM-based refinement of hypothesis given simulation results.
"""
from __future__ import annotations

import logging

from src.discovery.closed_loop.bayesian_tracker import BayesianHypothesisTracker
from src.llm.gateway import DefaultGateway


logger = logging.getLogger("c4reqber.discovery.closed_loop")

REFINER_PROMPT = """You are a scientific hypothesis refiner.

ORIGINAL HYPOTHESIS:
{hypothesis}

SIMULATION RESULTS:
{results}

BAYESIAN TRACKER:
- Prior belief: {prior}
- Posterior belief: {posterior}
- Bayes factor: {bayes_factor}

INSTRUCTIONS:
If the evidence strongly supports or refutes the hypothesis, propose a refined version that:
1. Incorporates the new evidence
2. Specifies tighter constraints or boundary conditions
3. Makes the claim more precise or more falsifiable

If no refinement is possible or useful, respond with "NO_REFINEMENT_NEEDED".

Otherwise, respond with ONLY the refined hypothesis text (1-2 sentences)."""


class HypothesisRefiner:
    """Refine hypothesis based on simulation evidence."""

    def __init__(self) -> None:
        self._router = DefaultGateway()

    async def refine(
        self,
        original_hypothesis: str,
        tracker: BayesianHypothesisTracker,
    ) -> str | None:
        """Propose refined hypothesis or None if no improvement possible."""
        if len(tracker.evidence_log) < 1:
            return None

        latest = tracker.evidence_log[-1]
        results_text = f"Simulator: {latest.simulator}\nPredicted: {latest.predicted:.4f}\nObserved: {latest.observed:.4f}"

        prompt = REFINER_PROMPT.format(
            hypothesis=original_hypothesis[:1000],
            results=results_text,
            prior=round(tracker.prior, 3),
            posterior=round(tracker.posterior, 3),
            bayes_factor=round(tracker.bayes_factor, 3) if tracker.bayes_factor != float("inf") else "inf",
        )

        try:
            response = await self._router.generate_for_stage(
                stage_name="hypothesis_refinement",
                prompt=prompt,
                system_prompt="You are a precise scientific editor. Be concise.",
            )
            content = response.content if hasattr(response, "content") else str(response)
            content = content.strip()
            if "NO_REFINEMENT_NEEDED" in content:
                return None
            if len(content) < 10:
                return None
            return content
        except Exception as e:
            logger.warning("HypothesisRefiner error: %s", e)
            return None
