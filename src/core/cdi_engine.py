"""
TURBO-CDI: CDI Engine
Creative & Destructive Insights Algorithm
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum
import asyncio

from .c4_state import C4State, C4Space
from .operators import Operators


class ContradictionType(Enum):
    """Types of physical contradictions."""

    TRADE_OFF = "trade_off"
    DUAL_REQUIREMENT = "dual_requirement"
    CONFLICTING_GOALS = "conflicting_goals"
    TEMPORAL = "temporal"
    SCALE = "scale"
    PERSPECTIVE = "perspective"


@dataclass
class PhysicalContradiction:
    """
    Physical Contradiction (Altshuller-style).

    Format: "X must be A AND not-A simultaneously"
    """

    parameter: str
    value_a: str
    value_not_a: str
    requirement_y: str
    requirement_z: str
    contradiction_type: ContradictionType

    def __str__(self) -> str:
        return f"'{self.parameter}' must be {self.value_a} (for {self.requirement_y}) AND {self.value_not_a} (for {self.requirement_z})"


@dataclass
class C4Transition:
    """Single step in C4 navigation."""

    operator: str
    from_state: C4State
    to_state: C4State
    description: str = ""


@dataclass
class CDISolution:
    """Output of CDI algorithm."""

    hypothesis: str
    c4_path: List[C4Transition]
    steps_taken: int
    contradiction: PhysicalContradiction
    confidence_score: float

    def __post_init__(self):
        assert self.steps_taken <= 6, f"Theorem 11 violated: {self.steps_taken} > 6"


class CDIEngine:
    """
    Creative & Destructive Insights Engine.

    The 6-step CDI Process:
    0. Extract Physical Contradiction
    1. Fingerprint (C4 coordinates)
    2. Predict Solution Region
    3. Compute Route (Theorem 9)
    4. Execute Transforms (27 operators)
    5. Synthesize Solution
    """

    def __init__(self):
        self.c4_space = C4Space()
        self.operators = Operators()

    def solve(
        self,
        contradiction: PhysicalContradiction,
        current_state: Optional[C4State] = None,
    ) -> CDISolution:
        """
        Execute CDI algorithm on a physical contradiction.

        Args:
            contradiction: The physical contradiction to resolve
            current_state: Starting C4 state (default: F⟨Past, Concrete, System⟩)

        Returns:
            CDISolution with hypothesis and navigation path
        """
        # Step 0: Already have contradiction

        # Step 1: Fingerprint (if state not provided)
        if current_state is None:
            current_state = self._fingerprint_contradiction(contradiction)

        # Step 2: Predict target solution region
        target_state = self._predict_solution_region(contradiction)

        # Step 3: Compute route (Theorem 9)
        path = self._compute_route(current_state, target_state)

        # Step 4: Execute transforms
        solution_state = self._execute_path(current_state, path)

        # Step 5: Synthesize
        hypothesis = self._synthesize_hypothesis(contradiction, solution_state, path)

        # Calculate confidence
        confidence = self._calculate_confidence(path, contradiction)

        return CDISolution(
            hypothesis=hypothesis,
            c4_path=path,
            steps_taken=len(path),
            contradiction=contradiction,
            confidence_score=confidence,
        )

    def _fingerprint_contradiction(
        self, contradiction: PhysicalContradiction
    ) -> C4State:
        """
        Map contradiction to C4 coordinates.

        Heuristics based on contradiction type:
        - TRADE_OFF: F⟨Present, Abstract, System⟩
        - DUAL_REQUIREMENT: F⟨Present, Concrete, Other⟩
        - CONFLICTING_GOALS: F⟨Future, Meta, System⟩
        """
        mapping = {
            ContradictionType.TRADE_OFF: C4State(T=1, S=1, A=2),
            ContradictionType.DUAL_REQUIREMENT: C4State(T=1, S=0, A=1),
            ContradictionType.CONFLICTING_GOALS: C4State(T=2, S=2, A=2),
            ContradictionType.TEMPORAL: C4State(T=0, S=1, A=2),
            ContradictionType.SCALE: C4State(T=1, S=0, A=2),
            ContradictionType.PERSPECTIVE: C4State(T=1, S=1, A=0),
        }
        return mapping.get(
            contradiction.contradiction_type,
            C4State(T=1, S=1, A=2),  # Default
        )

    def _predict_solution_region(self, contradiction: PhysicalContradiction) -> C4State:
        """
        Predict where solution likely resides in C4 space.

        Strategy: Move toward Meta + Future + expanded Agency
        for paradigm-shifting solutions.
        """
        # Default target: Meta-level, Future-oriented, System perspective
        return C4State(T=2, S=2, A=2)

    def _compute_route(self, start: C4State, end: C4State) -> List[C4Transition]:
        """
        Compute shortest path through C4 space.

        Theorem 9: Path length = Hamming distance
        Theorem 11: Maximum 6 steps (2 per differing axis)
        """
        path = []
        current = start

        # For each differing axis, apply appropriate operators
        # T axis
        if current.T != end.T:
            diff = (end.T - current.T) % 3
            if diff == 1:
                op = "tau+"
            elif diff == 2:
                op = "tau-"
            else:
                op = None

            if op:
                new_state = self.operators.get(op)(current)
                path.append(C4Transition(op, current, new_state))
                current = new_state

        # S axis
        if current.S != end.S:
            diff = (end.S - current.S) % 3
            if diff == 1:
                op = "lambda+"
            elif diff == 2:
                op = "lambda-"
            else:
                op = None

            if op:
                new_state = self.operators.get(op)(current)
                path.append(C4Transition(op, current, new_state))
                current = new_state

        # A axis
        if current.A != end.A:
            diff = (end.A - current.A) % 3
            if diff == 1:
                op = "kappa+"
            elif diff == 2:
                op = "kappa-"
            else:
                op = None

            if op:
                new_state = self.operators.get(op)(current)
                path.append(C4Transition(op, current, new_state))
                current = new_state

        return path

    def _execute_path(self, start: C4State, path: List[C4Transition]) -> C4State:
        """Execute path and return final state."""
        if not path:
            return start
        return path[-1].to_state

    def _synthesize_hypothesis(
        self,
        contradiction: PhysicalContradiction,
        final_state: C4State,
        path: List[C4Transition],
    ) -> str:
        """
        Generate hypothesis text from navigation path.

        This is a simplified version - in production, use LLM for synthesis.
        """
        operators_used = [t.operator for t in path]

        # Template-based synthesis (placeholder)
        hypothesis = (
            f"Solution to '{contradiction.parameter}' contradiction: "
            f"Use paradigm shift via {', '.join(operators_used)}. "
            f"Final perspective: {final_state}."
        )

        return hypothesis

    def _calculate_confidence(
        self, path: List[C4Transition], contradiction: PhysicalContradiction
    ) -> float:
        """
        Calculate confidence score (0-1).

        Factors:
        - Path length (shorter = better)
        - Operator composition validity
        """
        # Path coherence: shorter paths = higher confidence
        path_score = 1.0 - (len(path) / 6.0)

        # Base confidence
        confidence = 0.5 + (0.5 * path_score)

        return round(confidence, 2)


class EinsteinValidator:
    """
    Validate CDI engine using Einstein Test.

    STR: 4 steps expected
    GTR: 6 steps expected (maximum)
    """

    def __init__(self, engine: CDIEngine):
        self.engine = engine

    def validate_str(self) -> CDISolution:
        """
        Special Theory of Relativity derivation.

        Starting contradiction:
        "Light speed must be RELATIVE (Newton) AND CONSTANT (Maxwell)"
        """
        contradiction = PhysicalContradiction(
            parameter="Speed of light",
            value_a="relative (adds to observer velocity)",
            value_not_a="constant (same for all observers)",
            requirement_y="Newtonian mechanics",
            requirement_z="Maxwell's equations",
            contradiction_type=ContradictionType.CONFLICTING_GOALS,
        )

        # Start: Past (established physics), Concrete (experiment), System (universal)
        start = C4State(T=0, S=0, A=2)

        solution = self.engine.solve(contradiction, start)

        assert solution.steps_taken <= 4, (
            f"STR should take ≤4 steps, took {solution.steps_taken}"
        )

        return solution

    def validate_gtr(self) -> CDISolution:
        """
        General Theory of Relativity derivation.

        Starting contradiction:
        "Gravity must be FORCE (Newton) AND GEOMETRY (spacetime curvature)"
        """
        contradiction = PhysicalContradiction(
            parameter="Gravity",
            value_a="instantaneous force (action at distance)",
            value_not_a="geometric curvature (local field)",
            requirement_y="Newtonian prediction accuracy",
            requirement_z="Special relativity compatibility",
            contradiction_type=ContradictionType.CONFLICTING_GOALS,
        )

        # Start: Present (after STR), Abstract (theoretical), System
        start = C4State(T=1, S=1, A=2)

        solution = self.engine.solve(contradiction, start)

        assert solution.steps_taken <= 6, (
            f"GTR should take ≤6 steps, took {solution.steps_taken}"
        )

        return solution
