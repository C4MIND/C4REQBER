"""
C4REQBER: MP Profile Rotation System
Agent system with rotating Metaprogram profiles for multi-perspective analysis.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from src.c4.state import C4State
from src.metamodels.mp.library import MPLibrary, MPProfile


@dataclass
class AgentPerspective:
    """A single perspective from an agent with a specific MP profile."""

    agent_id: str
    profile_name: str
    profile_name_ru: str
    c4_state: C4State
    analysis: str = ""
    confidence: float = 0.0
    key_insights: list[str] = field(default_factory=list)
    blind_spots: list[str] = field(default_factory=list)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "profile_name": self.profile_name,
            "profile_name_ru": self.profile_name_ru,
            "c4_state": self.c4_state.to_tuple(),
            "c4_state_label": str(self.c4_state),
            "analysis": self.analysis,
            "confidence": self.confidence,
            "key_insights": self.key_insights,
            "blind_spots": self.blind_spots,
            "duration_ms": self.duration_ms,
        }


@dataclass
class RotationResult:
    """Result of running MP profile rotation on a problem."""

    problem: str
    perspectives: list[AgentPerspective] = field(default_factory=list)
    synthesized_view: str = ""
    consensus_score: float = 0.0
    total_duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem": self.problem,
            "perspectives": [p.to_dict() for p in self.perspectives],
            "synthesized_view": self.synthesized_view,
            "consensus_score": self.consensus_score,
            "total_duration_ms": self.total_duration_ms,
        }


class MPRotationEngine:
    """
    MP Rotation Engine.

    For any problem, runs multiple agents with different MP profiles
    and synthesizes their perspectives.
    """

    def __init__(self, mp_library: MPLibrary | None = None) -> None:
        self.mp = mp_library or MPLibrary()

    def analyze(
        self, problem: str, n_profiles: int = 3, c4_state: C4State | None = None
    ) -> RotationResult:
        """
        Analyze a problem through n different MP profiles.

        Rotates MP profiles to generate multi-perspective analysis.
        For standalone lens-based analysis, use MPProfiler.analyze().
        """
        start_time = time.time()
        profiles = self.mp.rotate_profiles(problem, n_profiles)
        result = RotationResult(problem=problem)

        for i, profile in enumerate(profiles):
            perspective = self._generate_perspective(
                agent_id=f"agent_{i + 1}",
                profile=profile,
                problem=problem,
                c4_state=c4_state or C4State(T=1, S=1, A=1),
            )
            result.perspectives.append(perspective)

        result.synthesized_view = self._synthesize(profiles, result.perspectives)
        result.consensus_score = self._compute_consensus(result.perspectives)
        result.total_duration_ms = (time.time() - start_time) * 1000
        return result

    def _generate_perspective(
        self, agent_id: str, profile: MPProfile, problem: str, c4_state: C4State
    ) -> AgentPerspective:
        """Generate a perspective from a specific MP profile."""
        start = time.time()

        # Adjust C4 state based on profile biases
        adjusted_state = self._adjust_state_for_profile(c4_state, profile)

        # Generate insights based on profile's dominant MPs
        insights = self._generate_insights_for_profile(profile, problem)
        blind_spots = self._generate_blind_spots_for_profile(profile)

        perspective = AgentPerspective(
            agent_id=agent_id,
            profile_name=profile.name,
            profile_name_ru=profile.name_ru,
            c4_state=adjusted_state,
            analysis=f"Analysis from {profile.name} perspective on: {problem[:100]}...",
            confidence=0.7 + (0.2 * (hash(profile.name) % 100) / 100),
            key_insights=insights,
            blind_spots=blind_spots,
            duration_ms=(time.time() - start) * 1000,
        )
        return perspective

    def _adjust_state_for_profile(self, state: C4State, profile: MPProfile) -> C4State:
        """Adjust C4 state based on profile biases."""
        T, S, A = state.T, state.S, state.A

        # Systems thinker → Meta, System
        if profile.name == "Systems Thinker":
            S = min(S + 1, 2)
            A = min(A + 1, 2)
        # Pragmatic → Concrete, Self
        elif profile.name == "Pragmatic Executor":
            S = max(S - 1, 0)
            A = max(A - 1, 0)
        # Creative → Future, Abstract
        elif profile.name == "Creative Explorer":
            T = min(T + 1, 2)
            S = min(S + 1, 2)
        # Critical → Present, System
        elif profile.name == "Critical Analyst":
            T = 1
            A = min(A + 1, 2)
        # Intuitive → Present, Other
        elif profile.name == "Intuitive Synthesizer":
            T = 1
            A = 1

        return C4State(T=T, S=S, A=A)

    def _generate_insights_for_profile(
        self, profile: MPProfile, problem: str
    ) -> list[str]:
        """Generate characteristic insights for a profile."""
        insights_map = {
            "Systems Thinker": [
                "Identify feedback loops and emergent properties",
                "Map the full system boundary",
                "Look for leverage points with disproportionate effect",
            ],
            "Pragmatic Executor": [
                "Break into actionable steps with clear owners",
                "Identify quick wins for momentum",
                "Check resource constraints early",
            ],
            "Creative Explorer": [
                "Consider radical alternatives to current approach",
                "What would this look like in an entirely different domain?",
                "Find patterns that suggest unexpected connections",
            ],
            "Critical Analyst": [
                "Identify hidden assumptions that could fail",
                "What evidence would falsify each proposed solution?",
                "Check for survivorship bias in analogies",
            ],
            "Intuitive Synthesizer": [
                "What feels 'off' about the current framing?",
                "Find the underlying rhythm or pattern",
                "Trust the gestalt that emerges from partial data",
            ],
        }
        return insights_map.get(profile.name, ["Analyze from multiple angles"])

    def _generate_blind_spots_for_profile(self, profile: MPProfile) -> list[str]:
        """Identify typical blind spots for a profile."""
        blind_spots_map = {
            "Systems Thinker": [
                "May miss urgent tactical details",
                "Can overcomplicate simple problems",
            ],
            "Pragmatic Executor": [
                "May miss paradigm-shifting alternatives",
                "Can optimize locally while harming globally",
            ],
            "Creative Explorer": [
                "May propose impractical solutions",
                "Can ignore critical constraints",
            ],
            "Critical Analyst": [
                "May paralyze action with excessive caution",
                "Can miss opportunities due to risk aversion",
            ],
            "Intuitive Synthesizer": [
                "May lack rigorous validation",
                "Can be wrong with high confidence",
            ],
        }
        return blind_spots_map.get(profile.name, ["Unknown blind spots"])

    def _synthesize(
        self, profiles: list[MPProfile], perspectives: list[AgentPerspective]
    ) -> str:
        """Synthesize multiple perspectives into unified view."""
        # Placeholder: in production, use LLM synthesis
        return (
            f"Synthesized view from {len(perspectives)} perspectives: "
            f"{'; '.join(p.profile_name for p in perspectives)}. "
            f"Key convergence: {len([p for p in perspectives if p.confidence > 0.8])} agents "
            f"show high confidence."
        )

    def _compute_consensus(self, perspectives: list[AgentPerspective]) -> float:
        """Compute consensus score across perspectives (0-1)."""
        if len(perspectives) < 2:
            return 1.0
        confidences = [p.confidence for p in perspectives]
        avg = sum(confidences) / len(confidences)
        variance = sum((c - avg) ** 2 for c in confidences) / len(confidences)
        # High consensus = high average confidence + low variance
        return round(avg * (1 - variance), 2)


class MPProfiler:
    """
    Real multi-perspective analysis engine with 12 perceptive lenses.

    Replaces placeholder perspective generation in the MP Rotation step.
    Scores lenses against problem text via keyword relevance and produces
    structured multi-perspective analyses for downstream synthesis.

    Usage:
        profiler = MPProfiler()
        result = profiler.analyze('Design a new rocket engine', 'engineering')
        print(f"Got {len(result['perspectives'])} perspectives")
    """

    def analyze(self, problem: str, domain: str = "general") -> dict[str, Any]:
        """Generate multi-perspective analysis using real heuristics"""
        lenses = [
            # Temporal
            {"name": "Historical Analysis", "category": "temporal",
             "question": "What does history tell us about similar problems?"},
            {"name": "Future Projection", "category": "temporal",
             "question": "What will this problem look like in 5 years?"},
            {"name": "Trend Analysis", "category": "temporal",
             "question": "What trends are driving this problem?"},
            # Structural
            {"name": "Systems Analysis", "category": "structural",
             "question": "What system does this problem exist within?"},
            {"name": "Decomposition", "category": "structural",
             "question": "What are the component parts of this problem?"},
            {"name": "Relationship Mapping", "category": "structural",
             "question": "How are the parts connected?"},
            # Functional
            {"name": "Utility Analysis", "category": "functional",
             "question": "Who benefits from solving this? Who loses?"},
            {"name": "Resource Analysis", "category": "functional",
             "question": "What resources are needed? What's available?"},
            {"name": "Constraint Analysis", "category": "functional",
             "question": "What constraints limit possible solutions?"},
            # Analogical
            {"name": "Biological Analogy", "category": "analogical",
             "question": "How does nature solve similar problems?"},
            {"name": "Engineering Analogy", "category": "analogical",
             "question": "How would an engineer approach this?"},
            {"name": "Mathematical Analogy", "category": "analogical",
             "question": "What mathematical structure maps to this problem?"},
        ]

        analyses = []
        for lens in lenses:
            keywords = lens["category"].split() + lens["name"].lower().split()
            relevance = 0.0
            for kw in keywords:
                if kw in problem.lower():
                    relevance += 1
            for kw in keywords:
                if kw in domain.lower():
                    relevance += 0.5

            if relevance > 0:
                analyses.append({
                    "lens": lens["name"],
                    "category": lens["category"],
                    "question": lens["question"],
                    "relevance_score": min(1.0, relevance * 0.3),
                    "insight": (
                        f"From {lens['name']} perspective: {lens['question']} "
                        f"Applied to: {problem[:80]}"
                    ),
                })

        analyses.sort(key=lambda x: float(x["relevance_score"]), reverse=True)  # type: ignore[arg-type]

        return {
            "perspectives": analyses[:8],
            "total_lenses_available": len(lenses),
            "selected_lenses": len(analyses[:8]),
            "recommended_view": analyses[0]["category"] if analyses else "general",
        }
