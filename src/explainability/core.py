"""
C4REQBER: Explainability Engine - Core data structures and engine
Explains WHY each C4 step works
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ExplanationLevel(Enum):
    """Level of explanation detail."""

    SIMPLE = "simple"  # For non-experts
    TECHNICAL = "technical"  # For scientists
    MATHEMATICAL = "math"  # Full formalism


@dataclass
class StepExplanation:
    """Explanation for a single C4 step."""

    step_number: int
    operator: str
    from_state: str
    to_state: str

    # Explanation content
    what: str  # What happens
    why: str  # Why this helps
    how: str  # How to apply
    example: str  # Concrete example

    # Confidence
    confidence: float  # How well this applies

    # References
    related_principles: list[str]  # Related TRIZ, analogies, etc.


@dataclass
class PathExplanation:
    """Complete explanation for a C4 path."""

    problem: str
    hypothesis: str
    c4_path: list[str]

    # Overall explanation
    summary: str
    intuition: str
    key_insight: str

    # Step-by-step
    steps: list[StepExplanation]

    # Validation
    expected_outcomes: list[str]
    warning_signs: list[str]

    # Alternatives
    alternative_paths: list[list[str]]


class ExplainabilityEngine:
    """
    Explainability Engine for C4 Cognitive Geometry.

    Answers the question: "WHY does this C4 path work?"

    Provides explanations at multiple levels:
    - Simple: For non-experts
    - Technical: For scientists
    - Mathematical: Full Z₃³ formalism
    """

    # Operator explanations database
    OPERATOR_EXPLANATIONS = {
        "tau+": {
            "simple": {
                "what": "Shift from past/present to future perspective",
                "why": "Future focus reveals new possibilities not visible now",
                "how": "Ask 'What will this look like in 5 years?'",
                "example": "Instead of 'battery is slow', think 'future batteries charge in 1 min'",
            },
            "technical": {
                "what": "Temporal operator advancing T-axis from Past(0) or Present(1) to Future(2)",
                "why": "Removes anchoring bias to current limitations; enables aspirational thinking",
                "how": "Apply τ⁺: F⟨T,S,A⟩ → F⟨T+1,S,A⟩ within Z₃³",
                "example": "In battery design: τ⁺ transforms 'current Li-ion limits' → 'solid-state potential'",
            },
            "math": {
                "what": "τ⁺: (t,s,a) ↦ (t+1 mod 3, s, a)",
                "why": "Time translation symmetry in cognitive space; Theorem 11 guarantees reachability",
                "how": "Compute τ⁺(s) = s ⊕ (1,0,0) in Z₃³",
                "example": "τ⁺(0,0,0) = (1,0,0) ; τ⁺(1,1,0) = (2,1,0)",
            },
            "related": [
                "TRIZ Principle 35: Parameter Changes",
                "Counterfactual reasoning",
            ],
        },
        "sigma": {
            "simple": {
                "what": "Move from concrete details to abstract concepts",
                "why": "Abstraction reveals patterns hidden in specifics",
                "how": "Ask 'What is the general principle here?'",
                "example": "Instead of 'battery overheats', think 'thermal management problem'",
            },
            "technical": {
                "what": "Scale operator advancing S-axis from Concrete(0) to Abstract(1) or Meta(2)",
                "why": "Abstraction enables transfer across domains; reduces problem complexity",
                "how": "Apply σ: F⟨T,S,A⟩ → F⟨T,S+1,A⟩ within Z₃³",
                "example": "Battery overheating → thermal dissipation → entropy flow management",
            },
            "math": {
                "what": "σ: (t,s,a) ↦ (t, s+1 mod 3, a)",
                "why": "Scale invariance; functorial mapping across abstraction levels",
                "how": "Compute σ(s) = s ⊕ (0,1,0) in Z₃³",
                "example": "σ(1,0,1) = (1,1,1) ; σ(2,1,0) = (2,2,0)",
            },
            "related": ["TRIZ Principle 1: Segmentation", "Category theory"],
        },
        "delta": {
            "simple": {
                "what": "Connect past, present, and future in one view",
                "why": "Time connections reveal trends and trajectories",
                "how": "Ask 'How did we get here and where are we going?'",
                "example": "Battery evolution: lead-acid → Li-ion → solid-state → ?",
            },
            "technical": {
                "what": "Temporal differential operator across all time scales",
                "why": "Reveals S-curves and evolutionary trends; identifies inflection points",
                "how": "Apply δ to trace trajectory through temporal manifold",
                "example": "Map battery technology S-curve to predict next paradigm",
            },
            "math": {
                "what": "δ = τ⁺ ∘ τ⁻ : temporal difference operator",
                "why": "Discrete derivative in time dimension; captures rate of cognitive change",
                "how": "δ(s) = ∇ₜF(s)",
                "example": "δ measures innovation velocity across technology generations",
            },
            "related": ["TRIZ Trends of Evolution", "Technology forecasting"],
        },
        "lambda+": {
            "simple": {
                "what": "Create higher-level synthesis of all perspectives",
                "why": "Synthesis combines insights from all previous steps",
                "how": "Ask 'What emerges from combining all these views?'",
                "example": "Combine speed + safety + cost → adaptive battery management",
            },
            "technical": {
                "what": "Meta-synthesis operator at highest abstraction level",
                "why": "Emergent properties arise from integration; resolves contradictions",
                "how": "Apply λ⁺ at (2,2,2) to synthesize complete solution space",
                "example": "λ⁺ transforms trade-offs into synergies",
            },
            "math": {
                "what": "λ⁺: meta-functor (F → F²)",
                "why": "Fixed point operator in cognitive space; achieves closure",
                "how": "λ⁺(s) = ⨆ᵢ φᵢ(s) where φᵢ are component operators",
                "example": "λ⁺(2,2,2) = complete design framework",
            },
            "related": [
                "Dialectical synthesis",
                "TRIZ Principle 40: Composite Materials",
            ],
        },
        "iota": {
            "simple": {
                "what": "Connect different domains or perspectives",
                "why": "Cross-domain connections spark creative solutions",
                "how": "Ask 'Where else does this problem occur?'",
                "example": "Battery heat management ↔ biological thermoregulation",
            },
            "technical": {
                "what": "Integration operator combining multiple viewpoints",
                "why": "Cross-domain analogy; bisociative thinking",
                "how": "Apply ι to merge cognitive spaces",
                "example": "Integrate physics and biology models for thermal management",
            },
            "math": {
                "what": "ι: A × B → C (bifunctor)",
                "why": "Universal property of products in category theory",
                "how": "ι(a,b) = a ⊗ b",
                "example": "ι(physics, biology) = bio-inspired engineering",
            },
            "related": ["Bisociation", "Analogical reasoning"],
        },
        "rho+": {
            "simple": {
                "what": "Expand from individual to system-level thinking",
                "why": "System view reveals emergent behaviors",
                "how": "Ask 'How does this fit into the bigger system?'",
                "example": "Battery cell → battery pack → grid storage system",
            },
            "technical": {
                "what": "Agency operator advancing A-axis from Self(0) to Other(1) or System(2)",
                "why": "System thinking reveals interactions and feedback loops",
                "how": "Apply ρ⁺: F⟨T,S,A⟩ → F⟨T,S,A+1⟩",
                "example": "Component optimization → system-level efficiency",
            },
            "math": {
                "what": "ρ⁺: (t,s,a) ↦ (t,s, a+1 mod 3)",
                "why": "Agency expansion; from local to global optimization",
                "how": "Compute ρ⁺(s) = s ⊕ (0,0,1)",
                "example": "ρ⁺(1,1,0) = (1,1,1) expands self to other",
            },
            "related": ["Systems thinking", "Holism"],
        },
    }

    def explain_path(
        self,
        problem: str,
        c4_path: list[str],
        hypothesis: str,
        level: ExplanationLevel = ExplanationLevel.TECHNICAL,
    ) -> PathExplanation:
        """
        Generate complete explanation for a C4 path.

        Args:
            problem: Original problem statement
            c4_path: List of C4 operators used
            hypothesis: Generated hypothesis
            level: Explanation detail level

        Returns:
            PathExplanation with complete breakdown
        """
        # Generate step explanations
        steps = []
        for i, operator in enumerate(c4_path):
            step = self._explain_step(i + 1, operator, level)
            steps.append(step)

        # Generate overall explanation
        summary = self._generate_summary(problem, c4_path, hypothesis)
        intuition = self._generate_intuition(c4_path)
        key_insight = self._generate_key_insight(problem, c4_path)

        # Generate validation guidance
        expected_outcomes = self._generate_expected_outcomes(c4_path)
        warning_signs = self._generate_warning_signs(c4_path)

        # Find alternatives
        alternatives = self._find_alternative_paths(c4_path)

        return PathExplanation(
            problem=problem,
            hypothesis=hypothesis,
            c4_path=c4_path,
            summary=summary,
            intuition=intuition,
            key_insight=key_insight,
            steps=steps,
            expected_outcomes=expected_outcomes,
            warning_signs=warning_signs,
            alternative_paths=alternatives,
        )

    def _explain_step(
        self, step_num: int, operator: str, level: ExplanationLevel
    ) -> StepExplanation:
        """Explain a single C4 step."""
        level_key = level.value

        # Get explanation for this operator
        op_data = self.OPERATOR_EXPLANATIONS.get(operator, {})
        exp_data = op_data.get(level_key, {})

        # Determine state transition
        from_state, to_state = self._determine_states(operator)

        return StepExplanation(
            step_number=step_num,
            operator=operator,
            from_state=from_state,
            to_state=to_state,
            what=exp_data.get("what", f"Apply {operator}"),  # type: ignore[attr-defined]
            why=exp_data.get("why", "Transforms the problem"),  # type: ignore[attr-defined]
            how=exp_data.get("how", f"Execute {operator}"),  # type: ignore[attr-defined]
            example=exp_data.get("example", ""),  # type: ignore[attr-defined]
            confidence=0.8,
            related_principles=op_data.get("related", []),  # type: ignore[arg-type]
        )

    def _determine_states(self, operator: str) -> tuple[Any, ...]:
        """Determine state transition for operator."""
        transitions = {
            "tau+": ("F⟨Past/Present, *, *⟩", "F⟨Future, *, *⟩"),
            "sigma": ("F⟨*, Concrete, *⟩", "F⟨*, Abstract, *⟩"),
            "delta": ("F⟨t, s, a⟩", "F⟨t+1, s, a⟩"),
            "lambda+": ("F⟨*, *, *⟩", "F⟨Meta, Meta, System⟩"),
            "iota": ("Multiple spaces", "Integrated space"),
            "rho+": ("F⟨*, *, Self⟩", "F⟨*, *, System⟩"),
        }
        return transitions.get(operator, ("Unknown", "Unknown"))

    def _generate_summary(self, problem: str, path: list[str], hypothesis: str) -> str:
        """Generate high-level summary."""
        return (
            f"This C4 path transforms the problem through {len(path)} cognitive steps. "
            f"Starting from the problem as given, we apply {', '.join(path)} to reach "
            f"a novel hypothesis: {hypothesis[:80]}..."
        )

    def _generate_intuition(self, path: list[str]) -> str:
        """Generate intuitive explanation."""
        intuitions = {
            "tau+": "Think forward in time",
            "sigma": "Think more abstractly",
            "delta": "Connect past to future",
            "lambda+": "Synthesize everything",
            "iota": "Connect different fields",
            "rho+": "See the bigger picture",
        }

        parts = [intuitions.get(op, f"Apply {op}") for op in path]
        return " → ".join(parts)

    def _generate_key_insight(self, problem: str, path: list[str]) -> str:
        """Generate key insight."""
        if "tau+" in path and "sigma" in path:
            return "The solution lies in abstracting the problem and projecting it into the future."
        elif "iota" in path:
            return "Cross-domain thinking reveals non-obvious solutions."
        elif "lambda+" in path:
            return "Meta-level synthesis resolves apparent contradictions."
        else:
            return "Systematic cognitive transformation reveals hidden solution paths."

    def _generate_expected_outcomes(self, path: list[str]) -> list[str]:
        """Generate expected validation outcomes."""
        outcomes = [
            "Solution addresses root cause, not just symptoms",
            "Approach is novel compared to existing methods",
            "Trade-offs are minimized or eliminated",
        ]

        if "sigma" in path:
            outcomes.append("Abstract principles enable domain transfer")
        if "tau+" in path:
            outcomes.append("Future-oriented design anticipates evolution")

        return outcomes

    def _generate_warning_signs(self, path: list[str]) -> list[str]:
        """Generate warning signs to watch for."""
        warnings = [
            "Solution too abstract to implement",
            "Future projection too speculative",
            "Cross-domain analogy breaks down",
        ]
        return warnings

    def _find_alternative_paths(self, current_path: list[str]) -> list[list[str]]:
        """Find alternative C4 paths."""
        # Common alternatives
        alternatives = [
            ["sigma", "tau+", "iota", "lambda+"],
            ["rho+", "sigma", "delta", "lambda+"],
            ["iota", "sigma", "tau+", "lambda+"],
        ]

        # Filter out current path
        return [p for p in alternatives if p != current_path][:2]


def get_explainability_engine() -> ExplainabilityEngine:
    """Get singleton explainability engine (backed by DI container)."""
    from src.di.container import get_container
    return get_container().get_or_register("explainability_engine", ExplainabilityEngine)
