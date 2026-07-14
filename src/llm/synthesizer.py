"""Hypothesis Synthesizer.

Generate scientific hypotheses using CDI path + LLM.
"""
from __future__ import annotations

from .client import LLMClient


try:
    from ..core.cdi_engine import CDISolution
except ImportError:
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.cdi_engine import CDISolution  # type: ignore[no-redef]


class HypothesisSynthesizer:
    """
    Synthesize scientific hypotheses from CDI navigation path.

    Uses LLM to transform C4 path + contradiction into concrete hypothesis.
    """

    SYSTEM_PROMPT = """You are C4REQBER, a scientific hypothesis generation engine.

Your task: Transform a physical contradiction into a novel scientific hypothesis using C4 cognitive navigation.

PRINCIPLES:
1. Be specific and concrete, not vague
2. Ground in existing science but propose something new
3. The hypothesis should resolve the stated contradiction
4. Explain the mechanism, not just the outcome
5. Use precise scientific terminology

C4 COGNITIVE OPERATORS REFERENCE:
- τ (tau): Time shifts (past/present/future)
- σ (sigma): Integration/connection
- δ (delta): Differentiation/separation
- ρ (rho): Pattern recognition
- ι (iota): Inversion/perspective flip
- λ (lambda): Abstraction/generalization
- κ (kappa): Concretization/perspective expansion
- μ (mu): Meta-reflection

RESPOND ONLY with the hypothesis statement. Be concise (2-4 sentences)."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        if llm_client is None:
            raise RuntimeError("LLMClient required for HypothesisSynthesizer")
        self.llm = llm_client

    def synthesize(
        self,
        solution: CDISolution,
        domain: str = "general",
        detail_level: str = "medium",
    ) -> str:
        """
        Generate hypothesis from CDI solution.

        Args:
            solution: CDI solution with path and contradiction
            domain: Scientific domain (physics, biology, materials, etc.)
            detail_level: "brief", "medium", or "detailed"

        Returns:
            Hypothesis text
        """
        # Build prompt from CDI path
        prompt = self._build_prompt(solution, domain, detail_level)

        # Generate with LLM
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=500 if detail_level == "brief" else 1000,
        )

        return response.content.strip()

    def _build_prompt(
        self, solution: CDISolution, domain: str, detail_level: str
    ) -> str:
        """Build synthesis prompt from CDI solution."""

        # Format C4 path
        path_description = (
            " → ".join([f"{t.operator} ({t.to_state})" for t in solution.c4_path])
            if solution.c4_path
            else "Direct (no transitions)"
        )

        operators_used = [t.operator for t in solution.c4_path]

        prompt = f"""DOMAIN: {domain}

PHYSICAL CONTRACTION TO RESOLVE:
{solution.contradiction}

C4 COGNITIVE NAVIGATION PATH:
{path_description}

OPERATORS APPLIED: {", ".join(operators_used) if operators_used else "None (identity)"}

FINAL STATE: {solution.c4_path[-1].to_state if solution.c4_path else "Initial"}

TASK: Generate a specific scientific hypothesis that resolves this contradiction by applying the cognitive transformations above.

The hypothesis should:
1. Propose a mechanism that satisfies BOTH requirements of the contradiction
2. Be grounded in {domain} science
3. Be specific enough to test experimentally
4. Reflect the cognitive path taken (time shifts, abstraction, perspective changes, etc.)

HYPOTHESIS:"""

        return prompt

    def synthesize_batch(
        self, solutions: list[CDISolution], domain: str = "general"
    ) -> list[str]:
        """Synthesize hypotheses for multiple solutions."""
        return [self.synthesize(sol, domain) for sol in solutions]

    def explain_path(self, solution: CDISolution) -> str:
        """Generate human-readable explanation of C4 path."""

        prompt = f"""Explain this cognitive navigation path in plain English:

Contradiction: {solution.contradiction}

Path: {" → ".join([t.operator for t in solution.c4_path])}

Explain how each operator transforms the thinking to move toward a solution.
Use metaphors where helpful."""

        response = self.llm.generate(prompt=prompt, temperature=0.5, max_tokens=800)

        return response.content.strip()


class ResearchContextEnricher:
    """
    Enrich hypothesis with research context from literature.
    """

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        if llm_client is not None:
            self.llm = llm_client
        else:
            from src.llm.multi_provider import OpenRouterClient
            self.llm = OpenRouterClient()  # type: ignore[assignment]

    def enrich(
        self, hypothesis: str, domain: str, key_papers: list[str] | None = None
    ) -> dict[str, str]:
        """
        Enrich hypothesis with research context.

        Returns:
            Dict with keys: theoretical_basis, related_work, gaps_addressed
        """

        prompt = f"""DOMAIN: {domain}
HYPOTHESIS: {hypothesis}

Provide:
1. Theoretical basis: What established theories support this approach?
2. Related work: What similar research exists?
3. Novel contribution: What's new about this hypothesis?
4. Key assumptions: What must be true for this to work?

Respond in JSON format with keys: theoretical_basis, related_work, novel_contribution, key_assumptions"""

        schema = {
            "type": "object",
            "properties": {
                "theoretical_basis": {"type": "string"},
                "related_work": {"type": "string"},
                "novel_contribution": {"type": "string"},
                "key_assumptions": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["theoretical_basis", "related_work", "novel_contribution"],
        }

        return self.llm.generate_structured(prompt, schema)
