"""Falsifiability Criteria Generator.

Generate testable criteria for hypothesis falsification (Popper-style).
"""
from __future__ import annotations

from dataclasses import dataclass

from .client import LLMClient


@dataclass
class FalsifiabilityCriterion:
    """Single falsifiability criterion."""

    statement: str  # "If X, then hypothesis is false"
    measurement: str  # How to measure X
    threshold: str  # Specific threshold value
    experiment_type: str  # Type of experiment needed
    difficulty: str  # "easy", "medium", "hard"


@dataclass
class FalsifiabilityReport:
    """Complete falsifiability analysis."""

    hypothesis: str
    criteria: list[FalsifiabilityCriterion]
    confidence_if_passed: float  # Confidence increase if all criteria pass
    summary: str


class FalsifiabilityGenerator:
    """
    Generate falsifiability criteria for scientific hypotheses.

    Based on Karl Popper's philosophy of science: a hypothesis is scientific
    only if it can be falsified by observable evidence.
    """

    SYSTEM_PROMPT = """You are a scientific methodology expert specializing in falsifiability (Karl Popper's philosophy).

Your task: Generate specific experimental outcomes that would FALSIFY (prove wrong) the given hypothesis.

CRITERIA FOR GOOD FALSIFIABILITY:
1. Observable: Must be measurable in principle
2. Specific: Include concrete numbers/thresholds
3. Decisive: Clear yes/no outcome
4. Feasible: Can be tested with current/reasonable technology

FORMAT:
For each criterion provide:
- Statement: "If [observation], then hypothesis is false"
- Measurement: How to measure it
- Threshold: Specific numeric threshold
- Experiment: Type of experiment needed
- Difficulty: easy/medium/hard

Generate 3-5 falsifiability criteria. Be harsh - think like a skeptical reviewer trying to disprove the hypothesis."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        if llm_client is None:
            raise RuntimeError("LLMClient required for FalsifiabilityGenerator")
        self.llm = llm_client

    def generate(
        self, hypothesis: str, domain: str = "general", num_criteria: int = 3
    ) -> FalsifiabilityReport:
        """
        Generate falsifiability criteria for a hypothesis.

        Args:
            hypothesis: The hypothesis to evaluate
            domain: Scientific domain
            num_criteria: Number of criteria to generate

        Returns:
            FalsifiabilityReport with criteria and analysis
        """
        prompt = f"""DOMAIN: {domain}

HYPOTHESIS TO FALSIFY:
{hypothesis}

Generate {num_criteria} specific falsifiability criteria.

For each criterion, provide:
1. Statement: "If [observation], then hypothesis is false"
2. Measurement: Specific measurement method
3. Threshold: Concrete numeric threshold with units
4. Experiment: Brief description of experiment type
5. Difficulty: easy/medium/hard based on current technology

Also provide a brief summary of what passing all these criteria would mean for the hypothesis."""

        schema = {
            "type": "object",
            "properties": {
                "criteria": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "statement": {"type": "string"},
                            "measurement": {"type": "string"},
                            "threshold": {"type": "string"},
                            "experiment_type": {"type": "string"},
                            "difficulty": {
                                "type": "string",
                                "enum": ["easy", "medium", "hard"],
                            },
                        },
                        "required": [
                            "statement",
                            "measurement",
                            "threshold",
                            "difficulty",
                        ],
                    },
                },
                "confidence_if_passed": {"type": "number"},
                "summary": {"type": "string"},
            },
            "required": ["criteria", "summary"],
        }

        response = self.llm.generate_structured(  # type: ignore[call-arg]
            prompt=prompt,
            schema=schema,
            temperature=0.4,  # More deterministic for criteria
        )

        criteria = [
            FalsifiabilityCriterion(
                statement=c["statement"],
                measurement=c["measurement"],
                threshold=c["threshold"],
                experiment_type=c.get("experiment_type", "Not specified"),
                difficulty=c["difficulty"],
            )
            for c in response.get("criteria", [])
        ]

        return FalsifiabilityReport(
            hypothesis=hypothesis,
            criteria=criteria,
            confidence_if_passed=response.get("confidence_if_passed", 0.7),
            summary=response.get("summary", ""),
        )

    def generate_quick(self, hypothesis: str) -> list[str]:
        """
        Generate simple falsifiability statements (strings only).

        Fast version for CLI display.
        """
        prompt = f"""HYPOTHESIS: {hypothesis}

Generate 3 "This hypothesis is wrong if..." statements.
Be specific with numbers. One sentence each."""

        response = self.llm.generate(prompt=prompt, temperature=0.3, max_tokens=300)

        lines = [line.strip() for line in response.content.split("\n") if line.strip()]
        criteria = [line for line in lines if line.startswith(("-", "•", "*", "If"))]

        return criteria if criteria else ["Could not generate falsifiability criteria"]

    def evaluate_testability(self, hypothesis: str) -> dict[str, any]:  # type: ignore[valid-type]
        """
        Evaluate how testable a hypothesis is.

        Returns metrics on falsifiability strength.
        """
        prompt = f"""Evaluate the testability of this hypothesis:

{hypothesis}

Provide analysis in JSON:
- falsifiability_score: 0-1 (how easy to falsify)
- specificity_score: 0-1 (how specific are predictions)
- feasibility_score: 0-1 (can be tested with current tech)
- time_to_test: estimated time to validate/falsify
- key_challenges: main obstacles to testing"""

        schema = {
            "type": "object",
            "properties": {
                "falsifiability_score": {"type": "number"},
                "specificity_score": {"type": "number"},
                "feasibility_score": {"type": "number"},
                "time_to_test": {"type": "string"},
                "key_challenges": {"type": "array", "items": {"type": "string"}},
            },
        }

        return self.llm.generate_structured(prompt, schema)


class ExperimentDesigner:
    """
    Design experiments to test falsifiability criteria.
    """

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        if llm_client is not None:
            self.llm = llm_client
        else:
            from src.llm.multi_provider import OpenRouterClient
            self.llm = OpenRouterClient()  # type: ignore[assignment]

    def design_experiment(
        self,
        criterion: FalsifiabilityCriterion,
        budget_level: str = "medium",  # "low", "medium", "high", "unlimited"
    ) -> dict[str, any]:  # type: ignore[valid-type]
        """
        Design experiment to test a falsifiability criterion.

        Returns:
            Dict with experimental design details
        """
        prompt = f"""Design an experiment to test this falsifiability criterion:

CRITERION: {criterion.statement}
MEASUREMENT: {criterion.measurement}
THRESHOLD: {criterion.threshold}
BUDGET LEVEL: {budget_level}

Provide experimental design including:
1. Apparatus/methods needed
2. Sample size and controls
3. Data collection procedure
4. Statistical analysis approach
5. Timeline
6. Estimated cost"""

        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "apparatus": {"type": "array", "items": {"type": "string"}},
                "method": {"type": "string"},
                "sample_size": {"type": "string"},
                "controls": {"type": "array", "items": {"type": "string"}},
                "procedure": {"type": "array", "items": {"type": "string"}},
                "analysis": {"type": "string"},
                "timeline": {"type": "string"},
                "estimated_cost": {"type": "string"},
            },
        }

        return self.llm.generate_structured(prompt, schema)
