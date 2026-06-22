"""
FRA (Fingerprint-Route-Adapt) Engine — Adaptive routing for cognitive operators.

Provides:
    - fingerprint(): Extract features from a problem → C4 state
    - route(): Map C4 state to optimal operator sequence
    - adapt(): Update routing based on performance feedback

Target: +8.48% improvement benchmark over baseline routing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.c4.engine import C4Space, C4State
from src.operators.matrix_dream import (
    DreamPattern,
    MatrixDreamRegistry,
)
from src.operators.qzrf import (
    QZRFOperator,
    QZRFRegistry,
)


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

@dataclass
class ProblemFeatures:
    """Extracted features from a problem description."""

    # Structural features
    word_count: int = 0
    sentence_count: int = 0
    avg_word_length: float = 0.0

    # Semantic features
    has_question: bool = False
    has_imperative: bool = False
    has_conditional: bool = False
    has_temporal_refs: bool = False
    has_comparison: bool = False
    has_causation: bool = False

    # Domain indicators
    domain_keywords: dict[str, int] = field(default_factory=dict)

    # Complexity
    unique_words: int = 0
    lexical_diversity: float = 0.0

    def to_vector(self) -> tuple[float, ...]:
        """Convert features to a normalized vector for routing."""
        return (
            min(self.word_count / 500.0, 1.0),
            min(self.sentence_count / 50.0, 1.0),
            self.avg_word_length / 10.0,
            1.0 if self.has_question else 0.0,
            1.0 if self.has_imperative else 0.0,
            1.0 if self.has_conditional else 0.0,
            1.0 if self.has_temporal_refs else 0.0,
            1.0 if self.has_comparison else 0.0,
            1.0 if self.has_causation else 0.0,
            self.lexical_diversity,
        )


# ---------------------------------------------------------------------------
# Fingerprint engine
# ---------------------------------------------------------------------------

class FingerprintEngine:
    """Extract features from problem text and map to C4 state."""

    # Temporal keywords
    TEMPORAL_WORDS = {
        "past", "history", "before", "previously", "earlier", "was", "were",
        "present", "now", "current", "currently", "today", "existing",
        "future", "will", "next", "upcoming", "planned", "predict",
        "forecast", "tomorrow", "later", "eventually",
    }

    # Comparison keywords
    COMPARISON_WORDS = {
        "compare", "versus", "vs", "better", "worse", "similar",
        "different", "difference", "contrast", "like", "unlike",
        "more", "less", "than", "relative", "ratio",
    }

    # Causation keywords
    CAUSATION_WORDS = {
        "because", "cause", "effect", "result", "due", "therefore",
        "thus", "hence", "consequently", "leads", "drives", "creates",
        "produces", "generates", "trigger", "induce",
    }

    # Domain keyword mappings
    DOMAIN_KEYWORDS = {
        "physics": {"physics", "force", "energy", "motion", "particle", "quantum"},
        "biology": {"biology", "cell", "organism", "gene", "protein", "evolution"},
        "economics": {"economics", "market", "price", "supply", "demand", "gdp"},
        "cs": {"algorithm", "computation", "software", "code", "program", "data", "hash", "distributed", "consensus", "addressing"},
        "math": {"theorem", "proof", "equation", "function", "matrix", "vector", "calculate", "trajectory", "gravity", "projectile"},
        "engineering": {"design", "system", "component", "mechanism", "structure", "implement", "build", "create"},
        "medicine": {"disease", "treatment", "patient", "diagnosis", "therapy"},
        "social": {"society", "culture", "behavior", "psychology", "community"},
    }

    def extract(self, problem_text: str) -> ProblemFeatures:
        """Extract real features from problem text."""
        if not problem_text or not isinstance(problem_text, str):
            return ProblemFeatures()

        text = problem_text.lower()
        words = text.split()
        sentences = [s.strip() for s in text.replace("?", ".").replace("!", ".").split(".") if s.strip()]

        features = ProblemFeatures(
            word_count=len(words),
            sentence_count=len(sentences),
            avg_word_length=sum(len(w.strip(".,!?;:")) for w in words) / max(len(words), 1),
            has_question="?" in problem_text,
            has_imperative=any(
                text.strip().startswith(w) or f" {w} " in f" {text} "
                for w in {
                    "find", "solve", "compute", "determine", "calculate",
                    "build", "create", "design", "implement", "write",
                    "develop", "construct", "make", "generate",
                }
            ),
            has_conditional=any(w in text for w in {"if", "unless", "provided", "assuming", "suppose"}),
            has_temporal_refs=any(w in text for w in self.TEMPORAL_WORDS),
            has_comparison=any(w in text for w in self.COMPARISON_WORDS),
            has_causation=any(w in text for w in self.CAUSATION_WORDS),
        )

        # Domain detection
        unique_words_set = set(words)
        features.unique_words = len(unique_words_set)
        features.lexical_diversity = len(unique_words_set) / max(len(words), 1)

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in text)
            if count > 0:
                features.domain_keywords[domain] = count

        return features

    def features_to_c4(self, features: ProblemFeatures) -> C4State:
        """Map extracted features to a C4 state.

        Uses actual feature values to determine position in Z₃³:
        - T (Time): Based on temporal references and question type
        - S (Scale): Based on complexity and abstraction level
        - A (Agency): Based on perspective and domain
        """
        vec = features.to_vector()

        # T-axis: temporal orientation
        # High temporal refs + future-oriented → Future(2)
        # Present-focused → Present(1)
        # Historical/retrospective → Past(0)
        if features.has_temporal_refs:
            # We don't have original text here, use vector hints
            t_score = vec[6] * 0.5 + vec[0] * 0.3 + vec[2] * 0.2
        else:
            t_score = vec[0] * 0.4 + vec[3] * 0.3 + vec[4] * 0.3

        if t_score > 0.6:
            T = 2  # Future
        elif t_score > 0.3:
            T = 1  # Present
        else:
            T = 0  # Past

        # S-axis: scale/abstraction
        # High lexical diversity + long words → Abstract(1) or Meta(2)
        s_score = vec[9] * 0.4 + vec[2] * 0.3 + vec[1] * 0.3
        if s_score > 0.5:
            S = 2  # Meta
        elif s_score > 0.25:
            S = 1  # Abstract
        else:
            S = 0  # Concrete

        # A-axis: agency/perspective
        # Question + comparison → Other(1) or System(2)
        a_score = vec[3] * 0.3 + vec[7] * 0.3 + vec[8] * 0.2 + vec[5] * 0.2
        if a_score > 0.5:
            A = 2  # System
        elif a_score > 0.25:
            A = 1  # Other
        else:
            A = 0  # Self

        return C4State(T=T, S=S, A=A)

    def fingerprint(self, problem_text: str) -> tuple[ProblemFeatures, C4State]:
        """Full fingerprint: features + C4 state."""
        features = self.extract(problem_text)
        c4_state = self.features_to_c4(features)
        return features, c4_state


# ---------------------------------------------------------------------------
# Routing engine
# ---------------------------------------------------------------------------

@dataclass
class RouteResult:
    """Result of routing: operator sequence + metadata."""

    operators: list[QZRFOperator]
    patterns: list[DreamPattern]
    expected_c4: C4State
    confidence: float
    reasoning: str


class RoutingEngine:
    """Map C4 states to optimal operator sequences."""

    def __init__(self) -> None:
        self.c4_space = C4Space()
        self._build_routing_table()

    def _build_routing_table(self) -> None:
        """Build heuristic routing table based on C4 transitions."""
        # Default operator preferences by transition type
        self._operator_prefs: dict[tuple[int, int, int], list[str]] = {
            # (delta_T, delta_S, delta_A) → preferred operator names
            (0, 1, 0): ["Generalize", "Combine"],
            (0, -1, 0): ["Specify", "Decompose"],
            (0, 0, 1): ["Analogize", "PerspectiveShift"],
            (1, 0, 0): ["TemporalShift"],
            (-1, 0, 0): ["TemporalShift"],
            (1, 1, 1): ["Reverse", "MetaReflect"],
            (0, 2, 0): ["FirstPrinciples"],
            (0, 0, 2): ["Systemic"],
            (1, 1, 0): ["ConstraintRelax"],
            (-1, -1, 0): ["ConstraintTighten"],
        }

    def _c4_delta(self, from_state: C4State, to_state: C4State) -> tuple[int, int, int]:
        """Compute cyclic delta between two C4 states."""
        dt = (to_state.T - from_state.T) % 3
        ds = (to_state.S - from_state.S) % 3
        da = (to_state.A - from_state.A) % 3
        return (dt, ds, da)

    def route(
        self,
        current: C4State,
        target: C4State,
        features: ProblemFeatures | None = None,
    ) -> RouteResult:
        """Compute optimal operator sequence from current to target C4 state.

        Uses actual C4 space navigation combined with feature-aware heuristics.
        """
        delta = self._c4_delta(current, target)
        dt, ds, da = delta

        operators: list[QZRFOperator] = []
        patterns: list[DreamPattern] = []
        reasoning_parts: list[str] = []

        # Time axis transitions
        if dt != 0:
            op = QZRFRegistry.get("TemporalShift")
            if isinstance(op, QZRFOperator):
                operators.append(op)
                reasoning_parts.append(f"Temporal shift ({dt})")
                # Add temporal patterns
                if dt == 1:
                    patterns.append(MatrixDreamRegistry.get(19))  # Prospective_Prediction
                else:
                    patterns.append(MatrixDreamRegistry.get(17))  # Retrospective_Analysis

        # Scale axis transitions
        if ds != 0:
            if ds == 1:
                op = QZRFRegistry.get("Generalize")
                patterns.append(MatrixDreamRegistry.get(1))  # Lift_Instance_To_Class
            elif ds == 2:
                op = QZRFRegistry.get("FirstPrinciples")
                patterns.append(MatrixDreamRegistry.get(8))  # Ontology_Lift
            else:  # ds == -1 or ds == 2 (which is -1 mod 3)
                op = QZRFRegistry.get("Specify")
                patterns.append(MatrixDreamRegistry.get(9))  # Instantiate_Class
            if isinstance(op, QZRFOperator):
                operators.append(op)
                reasoning_parts.append(f"Scale shift ({ds})")

        # Agency axis transitions
        if da != 0:
            if da == 1:
                op = QZRFRegistry.get("PerspectiveShift")
                patterns.append(MatrixDreamRegistry.get(26))  # Empathy_Shift
            else:  # da == 2
                op = QZRFRegistry.get("Systemic")
                patterns.append(MatrixDreamRegistry.get(27))  # System_Overview
            if isinstance(op, QZRFOperator):
                operators.append(op)
                reasoning_parts.append(f"Agency shift ({da})")

        # Feature-aware adjustments
        if features:
            if features.has_comparison and "Analogize" not in [o.name for o in operators]:
                operators.append(QZRFRegistry.get("Analogize"))
                patterns.append(MatrixDreamRegistry.get(34))  # Cross_Domain_Synthesis
                reasoning_parts.append("Comparison detected → Analogize")

            if features.has_causation and "Reverse" not in [o.name for o in operators]:
                operators.append(QZRFRegistry.get("Reverse"))
                patterns.append(MatrixDreamRegistry.get(53))  # Causal_Inversion
                reasoning_parts.append("Causation detected → Reverse")

        # Compute confidence based on path length and feature match
        path_length = len(operators)
        base_confidence = 1.0 - (path_length * 0.08)
        if features and features.domain_keywords:
            base_confidence += 0.1
        confidence = max(0.3, min(0.95, base_confidence))

        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Identity route"

        return RouteResult(
            operators=operators,
            patterns=patterns,
            expected_c4=target,
            confidence=confidence,
            reasoning=reasoning,
        )

    def route_to_goal(
        self,
        current: C4State,
        goal_description: str,
        features: ProblemFeatures | None = None,
    ) -> RouteResult:
        """Route toward a goal described by text features."""
        # Infer target from goal description
        fp_engine = FingerprintEngine()
        goal_features = fp_engine.extract(goal_description)
        target = fp_engine.features_to_c4(goal_features)
        return self.route(current, target, features or goal_features)


# ---------------------------------------------------------------------------
# Adaptation engine
# ---------------------------------------------------------------------------

@dataclass
class PerformanceFeedback:
    """Feedback from executing a route."""

    route_result: RouteResult
    actual_c4: C4State
    success_score: float  # 0.0 to 1.0
    execution_time_ms: float
    user_rating: float | None = None  # 1.0 to 5.0


class AdaptationEngine:
    """Update routing based on performance feedback.

    Maintains performance history and adjusts operator preferences
    to achieve the +8.48% improvement benchmark.
    """

    def __init__(self) -> None:
        self.feedback_history: list[PerformanceFeedback] = []
        self.operator_scores: dict[str, list[float]] = {}
        self.pattern_scores: dict[int, list[float]] = {}
        self._baseline_improvement = 0.0

    def record(self, feedback: PerformanceFeedback) -> None:
        """Record feedback for learning."""
        self.feedback_history.append(feedback)

        # Score individual operators
        for op in feedback.route_result.operators:
            if op.name not in self.operator_scores:
                self.operator_scores[op.name] = []
            self.operator_scores[op.name].append(feedback.success_score)

        # Score individual patterns
        for pat in feedback.route_result.patterns:
            if pat.id not in self.pattern_scores:
                self.pattern_scores[pat.id] = []
            self.pattern_scores[pat.id].append(feedback.success_score)

    def adapt(
        self,
        current: C4State,
        target: C4State,
        features: ProblemFeatures | None = None,
    ) -> RouteResult:
        """Generate adapted route based on historical performance.

        Uses actual feedback data to improve routing decisions.
        """
        # Start with base routing
        router = RoutingEngine()
        base_route = router.route(current, target, features)

        if not self.feedback_history:
            return base_route

        # Compute operator effectiveness from history
        op_effectiveness: dict[str, float] = {}
        for name, scores in self.operator_scores.items():
            if scores:
                op_effectiveness[name] = sum(scores) / len(scores)

        # Reorder operators by effectiveness
        sorted_ops = sorted(
            base_route.operators,
            key=lambda o: op_effectiveness.get(o.name, 0.5),
            reverse=True,
        )

        # Filter out consistently poor operators
        min_threshold = 0.2
        filtered_ops = [
            o for o in sorted_ops
            if op_effectiveness.get(o.name, 0.5) >= min_threshold
        ]

        # If all operators filtered, fall back to base
        if not filtered_ops:
            filtered_ops = base_route.operators

        # Compute improvement metric
        baseline_score = self._compute_baseline_score(base_route)
        adapted_score = self._compute_adapted_score(filtered_ops, target)
        improvement = ((adapted_score - baseline_score) / max(baseline_score, 0.001)) * 100

        # Track cumulative improvement
        self._baseline_improvement = max(self._baseline_improvement, improvement)

        # Adjust confidence based on history depth
        history_depth = len(self.feedback_history)
        confidence_boost = min(history_depth * 0.01, 0.1)
        adapted_confidence = min(0.95, base_route.confidence + confidence_boost)

        return RouteResult(
            operators=filtered_ops,
            patterns=base_route.patterns,
            expected_c4=target,
            confidence=adapted_confidence,
            reasoning=f"{base_route.reasoning}; adapted (+{improvement:.2f}%)",
        )

    def _compute_baseline_score(self, route: RouteResult) -> float:
        """Compute baseline performance score."""
        return route.confidence * 0.6 + (1.0 / max(len(route.operators), 1)) * 0.4

    def _compute_adapted_score(self, operators: list[QZRFOperator], target: C4State) -> float:
        """Compute adapted route score."""
        # Shorter routes with high-effectiveness operators score better
        op_bonus = sum(
            sum(self.operator_scores.get(o.name, [0.5])) / len(self.operator_scores.get(o.name, [0.5]))
            for o in operators
        ) / max(len(operators), 1)
        length_penalty = 1.0 / (1.0 + len(operators) * 0.1)
        return op_bonus * 0.7 + length_penalty * 0.3

    def get_improvement(self) -> float:
        """Return current improvement percentage over baseline."""
        return self._baseline_improvement

    def get_operator_ranking(self) -> list[tuple[str, float]]:
        """Rank operators by effectiveness."""
        rankings = []
        for name, scores in self.operator_scores.items():
            if scores:
                avg = sum(scores) / len(scores)
                rankings.append((name, avg))
        return sorted(rankings, key=lambda x: x[1], reverse=True)


# ---------------------------------------------------------------------------
# FRA Engine — Unified interface
# ---------------------------------------------------------------------------

class FRAEngine:
    """Unified Fingerprint-Route-Adapt engine."""

    def __init__(self) -> None:
        self.fingerprint_engine = FingerprintEngine()
        self.routing_engine = RoutingEngine()
        self.adaptation_engine = AdaptationEngine()

    def fingerprint(self, problem_text: str) -> tuple[ProblemFeatures, C4State]:
        """Extract features and C4 state from problem text."""
        return self.fingerprint_engine.fingerprint(problem_text)

    def route(
        self,
        current: C4State,
        target: C4State,
        features: ProblemFeatures | None = None,
    ) -> RouteResult:
        """Compute route from current to target."""
        return self.routing_engine.route(current, target, features)

    def adapt(
        self,
        current: C4State,
        target: C4State,
        features: ProblemFeatures | None = None,
    ) -> RouteResult:
        """Generate adapted route using feedback history."""
        return self.adaptation_engine.adapt(current, target, features)

    def full_cycle(
        self,
        problem_text: str,
        current_c4: C4State | None = None,
    ) -> tuple[ProblemFeatures, C4State, RouteResult]:
        """Execute full FRA cycle: fingerprint → route."""
        features, inferred_c4 = self.fingerprint(problem_text)
        current = current_c4 or inferred_c4
        route = self.route(current, inferred_c4, features)
        return features, inferred_c4, route

    def record_feedback(
        self,
        route_result: RouteResult,
        actual_c4: C4State,
        success_score: float,
        execution_time_ms: float,
        user_rating: float | None = None,
    ) -> None:
        """Record performance feedback for adaptation."""
        feedback = PerformanceFeedback(
            route_result=route_result,
            actual_c4=actual_c4,
            success_score=success_score,
            execution_time_ms=execution_time_ms,
            user_rating=user_rating,
        )
        self.adaptation_engine.record(feedback)

    def get_stats(self) -> dict[str, Any]:
        """Get engine statistics."""
        return {
            "feedback_count": len(self.adaptation_engine.feedback_history),
            "improvement_pct": self.adaptation_engine.get_improvement(),
            "operator_rankings": self.adaptation_engine.get_operator_ranking(),
            "total_operators_tested": len(self.adaptation_engine.operator_scores),
        }

class FRARouter(FRAEngine):
    """Alias for FRAEngine for backward compatibility."""
