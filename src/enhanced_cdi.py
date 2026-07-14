from __future__ import annotations


"""Enhanced CDI Engine with LLM synthesis"""

import os
import sys
from typing import Any


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.c4_state import C4State
from core.cdi_engine import CDIEngine, CDISolution, PhysicalContradiction
from llm.falsifiability import FalsifiabilityGenerator
from llm.synthesizer import HypothesisSynthesizer


class EnhancedCDIEngine(CDIEngine):  # type: ignore[misc]
    """CDI Engine with LLM-powered hypothesis synthesis."""

    def __init__(self, llm_client: Any = None) -> None:
        super().__init__()
        self.llm = llm_client
        self._synthesizer = None
        self._falsifiability = None

    def _ensure_synthesizer(self) -> HypothesisSynthesizer:
        if self.llm is None:
            from llm.fallback import get_real_sync_client_or_raise
            self.llm = get_real_sync_client_or_raise()
        if self._synthesizer is None:
            self._synthesizer = HypothesisSynthesizer(self.llm)
        return self._synthesizer

    def _ensure_falsifiability(self) -> FalsifiabilityGenerator:
        if self.llm is None:
            from llm.fallback import get_real_sync_client_or_raise
            self.llm = get_real_sync_client_or_raise()
        if self._falsifiability is None:
            self._falsifiability = FalsifiabilityGenerator(self.llm)
        return self._falsifiability

    def solve_enhanced(
        self,
        contradiction: PhysicalContradiction,
        domain: str = "general",
        current_state: C4State = None,
    ) -> CDISolution:
        """
        Solve with LLM-enhanced hypothesis generation.

        Returns solution with:
        - Generated hypothesis (via LLM)
        - Falsifiability criteria
        - Confidence breakdown
        """
        # Run base CDI
        solution = self.solve(contradiction, current_state)

        # Enhance with LLM synthesis
        if self.llm:
            hypothesis = self._ensure_synthesizer().synthesize(solution, domain)
            solution.hypothesis = hypothesis

            # Add falsifiability
            falsifiability = self._ensure_falsifiability().generate(hypothesis, domain)
            solution.falsifiability_criteria = falsifiability.criteria

        return solution


if __name__ == "__main__":
    # Test enhanced engine
    from core.cdi_engine import ContradictionType

    print("Testing Enhanced CDI Engine...")

    engine = EnhancedCDIEngine()

    contradiction = PhysicalContradiction(
        parameter="Battery charging",
        value_a="FAST (<10 min)",
        value_not_a="SLOW (preserve capacity)",
        requirement_y="User convenience",
        requirement_z="Cycle life >1000",
        contradiction_type=ContradictionType.TRADE_OFF,
    )

    solution = engine.solve_enhanced(contradiction, domain="materials_science")

    print(f"\nHypothesis: {solution.hypothesis}")
    print(f"Steps: {solution.steps_taken}")
    print(f"Confidence: {solution.confidence_score}")
