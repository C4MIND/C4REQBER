"""Enhanced CDI Engine with LLM synthesis"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.cdi_engine import CDIEngine, CDISolution, PhysicalContradiction
from core.c4_state import C4State
from llm.client import LLMClient, MockLLMClient
from llm.synthesizer import HypothesisSynthesizer
from llm.falsifiability import FalsifiabilityGenerator


class EnhancedCDIEngine(CDIEngine):
    """CDI Engine with LLM-powered hypothesis synthesis."""

    def __init__(self, llm_client=None):
        super().__init__()
        self.llm = llm_client or MockLLMClient()
        self.synthesizer = HypothesisSynthesizer(self.llm)
        self.falsifiability = FalsifiabilityGenerator(self.llm)

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
        if self.llm and not isinstance(self.llm, MockLLMClient):
            hypothesis = self.synthesizer.synthesize(solution, domain)
            solution.hypothesis = hypothesis

            # Add falsifiability
            falsifiability = self.falsifiability.generate(hypothesis, domain)
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
