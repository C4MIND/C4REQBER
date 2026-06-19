"""
C4REQBER: Pipeline Step 09 — TOTE Validation

Replaces the simple word-overlap heuristic with a real TOTE-based
validation engine that checks whether a solution actually addresses
the problem using structured criteria (completeness, relevance,
feasibility, etc.) and returns a proper validation result.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from src.agents.pipeline.steps.base import PipelineStage, PipelineStep, PipelineStepResult
from src.metamodels.tote import ToteEngine, ToteResult


if TYPE_CHECKING:
    from src.validation.core import BayesianUpdater

logger = logging.getLogger(__name__)

_bayesian_updater_cls: type[BayesianUpdater] | None = None


def _get_bayesian_updater() -> type[BayesianUpdater]:
    global _bayesian_updater_cls
    if _bayesian_updater_cls is None:
        from src.validation.core import BayesianUpdater as _BU
        _bayesian_updater_cls = _BU
    return _bayesian_updater_cls


@dataclass
class ValidationCriterion:
    """A single validation criterion with scoring logic."""

    name: str
    weight: float
    check_fn: Any = field(repr=False)

    def evaluate(self, problem: str, solution: str) -> dict[str, Any]:
        """Evaluate."""
        score, critique = self.check_fn(problem, solution)
        return {
            "criterion": self.name,
            "weight": self.weight,
            "score": score,
            "critique": critique,
        }


class ToteValidationEngine:
    """
    TOTE-based validation engine for pipeline step 09.

    Uses the TOTE metamodel (Test-Operate-Test-Exit) to iteratively
    assess whether a solution meets the problem requirements across
    multiple structured criteria.
    """

    # Configurable thresholds
    DEFAULT_PASS_THRESHOLD: float = 0.65
    DEFAULT_REVISION_THRESHOLD: float = 0.45
    DEFAULT_MAX_CRITIQUES: int = 4
    DEFAULT_FALSE_POSITIVE_RATE: float = 0.2
    MAX_SOLUTION_LENGTH: int = 50000

    def __init__(
        self,
        pass_threshold: float | None = None,
        revision_threshold: float | None = None,
        max_critiques: int | None = None,
        false_positive_rate: float | None = None,
    ) -> None:
        self.tote = ToteEngine()
        self.criteria = self._build_criteria()
        self.pass_threshold = pass_threshold if pass_threshold is not None else self.DEFAULT_PASS_THRESHOLD
        self.revision_threshold = revision_threshold if revision_threshold is not None else self.DEFAULT_REVISION_THRESHOLD
        self.max_critiques = max_critiques if max_critiques is not None else self.DEFAULT_MAX_CRITIQUES
        self.false_positive_rate = false_positive_rate if false_positive_rate is not None else self.DEFAULT_FALSE_POSITIVE_RATE

    def _build_criteria(self) -> list[ValidationCriterion]:
        """Define structured validation criteria."""
        return [
            ValidationCriterion(
                name="relevance",
                weight=0.30,
                check_fn=_check_relevance,
            ),
            ValidationCriterion(
                name="completeness",
                weight=0.25,
                check_fn=_check_completeness,
            ),
            ValidationCriterion(
                name="feasibility",
                weight=0.20,
                check_fn=_check_feasibility,
            ),
            ValidationCriterion(
                name="clarity",
                weight=0.15,
                check_fn=_check_clarity,
            ),
            ValidationCriterion(
                name="actionability",
                weight=0.10,
                check_fn=_check_actionability,
            ),
        ]

    def validate(self, problem: str, solution: str) -> dict[str, Any]:
        """
        Run TOTE validation loop on problem/solution pair.

        Returns structured result with needs_revision, confidence,
        critique points, and improvement suggestions.
        """
        if len(solution) > self.MAX_SOLUTION_LENGTH:
            logger.warning("Solution exceeds max length (%d > %d), truncating for validation", len(solution), self.MAX_SOLUTION_LENGTH)
            solution = solution[:self.MAX_SOLUTION_LENGTH]

        target_state = "solution_addresses_problem"
        initial_state = "unvalidated"

        def test_fn(state: str) -> bool:
            return state == target_state

        def operate_fn(state: str) -> str:
            # Run all criteria and aggregate scores
            """Operate fn."""
            results = [c.evaluate(problem, solution) for c in self.criteria]
            total_weight = sum(c.weight for c in self.criteria)
            weighted_score = sum(
                r["score"] * r["weight"] for r in results
            ) / max(total_weight, 1e-6)

            # Store results in instance for later retrieval
            self._last_results = results
            self._last_weighted_score = weighted_score

            return target_state if weighted_score >= self.pass_threshold else "needs_improvement"

        def mismatch_fn(state: str, target: str) -> float:
            return 1.0 - getattr(self, "_last_weighted_score", 0.0)

        tote_result: ToteResult = self.tote.run(
            target_state=target_state,
            initial_state=initial_state,
            test_fn=test_fn,
            operate_fn=operate_fn,
            max_iterations=3,
            mismatch_fn=mismatch_fn,
        )

        # Build final validation report
        results = getattr(self, "_last_results", [])
        weighted_score = getattr(self, "_last_weighted_score", 0.0)

        critiques = []
        suggestions = []
        for r in results:
            if r["score"] < 0.5:
                critiques.append(
                    f"{r['criterion']}: {r['critique']} (score: {r['score']:.2f})"
                )
                suggestions.extend(
                    _get_suggestions(r["criterion"], r["score"])
                )

        confidence = weighted_score
        # Revision needed if confidence is low OR there are many significant critiques
        needs_revision = confidence < self.revision_threshold or len(critiques) >= self.max_critiques

        # Apply Bayesian update for confidence calibration
        prior = 0.5
        likelihood = confidence
        BU = _get_bayesian_updater()
        posterior = BU().update(prior, likelihood, false_positive_rate=self.false_positive_rate)

        return {
            "needs_revision": needs_revision,
            "confidence": round(posterior, 3),
            "raw_score": round(weighted_score, 3),
            "criteria_scores": {
                r["criterion"]: round(r["score"], 3) for r in results
            },
            "critique_points": critiques,
            "improvement_suggestions": list(dict.fromkeys(suggestions)),
            "tote_iterations": tote_result.total_iterations,
            "tote_success": tote_result.success,
            "revised_solution": (
                solution
                if not needs_revision
                else (
                    solution
                    + "\n\n[Validation Feedback — this solution may need refinement]: "
                    + "; ".join(critiques)
                    + "\n[Suggestions]: "
                    + "; ".join(list(dict.fromkeys(suggestions)))
                )
            ),
        }


# ---------------------------------------------------------------------------
# Criterion check functions (heuristic, no LLM required)
# ---------------------------------------------------------------------------


def _check_relevance(problem: str, solution: str) -> tuple[float, str]:
    """Check if solution keywords overlap with problem keywords."""
    p_words = set(_extract_keywords(problem))
    s_words = set(_extract_keywords(solution))
    if not p_words:
        return 0.0, "Problem statement is empty"
    overlap = len(p_words & s_words)
    score = overlap / len(p_words)
    if score >= 0.5:
        return score, "Solution is highly relevant to the problem"
    elif score >= 0.2:
        return score, "Solution has partial relevance"
    return score, "Solution appears off-topic or irrelevant"


def _check_completeness(problem: str, solution: str) -> tuple[float, str]:
    """Check if solution length and structure indicate completeness."""
    word_count = len(solution.split())
    if word_count >= 300:
        return 0.9, "Solution is comprehensive"
    elif word_count >= 150:
        return 0.7, "Solution covers main points but may lack detail"
    elif word_count >= 50:
        return 0.4, "Solution is brief and may be incomplete"
    return 0.1, "Solution is too short to be complete"


def _check_feasibility(problem: str, solution: str) -> tuple[float, str]:
    """Check for feasibility markers (steps, resources, constraints)."""
    feasibility_markers = [
        "step", "phase", "first", "second", "third", "next", "then",
        "using", "via", "by", "implement", "deploy", "build", "create",
        "resource", "cost", "time", "budget", "constraint", "limit",
    ]
    s_lower = solution.lower()
    matches = sum(1 for m in feasibility_markers if m in s_lower)
    score = min(1.0, matches / 5.0)
    if score >= 0.6:
        return score, "Solution includes actionable steps"
    return score, "Solution lacks clear implementation path"


def _check_clarity(problem: str, solution: str) -> tuple[float, str]:
    """Check for clarity markers (structure, punctuation, coherence)."""
    sentences = [s.strip() for s in solution.split(".") if s.strip()]
    if not sentences:
        return 0.0, "Solution has no discernible sentences"
    avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
    if 5 <= avg_len <= 25:
        return 0.85, "Solution is well-structured and clear"
    elif avg_len > 40:
        return 0.4, "Sentences are overly long and may be unclear"
    return 0.6, "Solution clarity is acceptable"


def _check_actionability(problem: str, solution: str) -> tuple[float, str]:
    """Check for actionable language (verbs, outcomes)."""
    action_verbs = [
        "develop", "design", "build", "implement", "create", "establish",
        "optimize", "improve", "reduce", "increase", "enhance", "apply",
        "use", "integrate", "deploy", "test", "validate", "measure",
    ]
    s_lower = solution.lower()
    matches = sum(1 for v in action_verbs if v in s_lower)
    score = min(1.0, matches / 3.0)
    if score >= 0.5:
        return score, "Solution uses actionable language"
    return score, "Solution lacks actionable recommendations"


def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from text."""
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "shall",
        "can", "need", "dare", "ought", "used", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "as", "into",
        "through", "during", "before", "after", "above", "below",
        "between", "under", "and", "but", "or", "yet", "so", "if",
        "because", "although", "though", "while", "where", "when",
        "that", "which", "who", "whom", "whose", "what", "this",
        "these", "those", "i", "you", "he", "she", "it", "we",
        "they", "me", "him", "her", "us", "them", "my", "your",
        "his", "its", "our", "their", "how", "why",
    }
    words = []
    for w in text.lower().split():
        w = w.strip(".,;:!?()[]{}\"'")
        if len(w) > 2 and w not in stopwords:
            words.append(w)
    return words


def _get_suggestions(criterion: str, score: float) -> list[str]:
    """Return improvement suggestions for a given criterion."""
    suggestions = {
        "relevance": [
            "Restate the core problem in your solution",
            "Use terminology from the problem statement",
        ],
        "completeness": [
            "Expand with more details and examples",
            "Address edge cases and assumptions",
        ],
        "feasibility": [
            "Break down into concrete implementation steps",
            "Mention required resources and constraints",
        ],
        "clarity": [
            "Use shorter, clearer sentences",
            "Add structure with headings or bullet points",
        ],
        "actionability": [
            "Use action verbs (develop, implement, test)",
            "Define clear next steps and deliverables",
        ],
    }
    return suggestions.get(criterion, ["Review and refine this aspect"])


# ---------------------------------------------------------------------------
# Pipeline step class and backward-compat entry points
# ---------------------------------------------------------------------------

_engine: ToteValidationEngine | None = None


def _get_engine() -> ToteValidationEngine:
    global _engine
    if _engine is None:
        _engine = ToteValidationEngine()
    return _engine


class ToteValidationStep(PipelineStep):
    """Step 9: TOTE Validation — validate solution with structured criteria."""

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.VALIDATION

    def get_required_context(self) -> list[str]:
        return ["problem"]

    def get_optional_context(self) -> list[str]:
        return ["solution"]

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute."""
        problem: str = context["problem"]
        solution: str = context.get("solution", "")
        start = time.time()

        try:
            engine = _get_engine()
            result = engine.validate(problem, solution)

            output_data = {
                "needs_revision": result["needs_revision"],
                "confidence": result["confidence"],
                "raw_score": result["raw_score"],
                "criteria_scores": result["criteria_scores"],
                "critique_points": result["critique_points"],
                "improvement_suggestions": result["improvement_suggestions"],
                "tote_iterations": result["tote_iterations"],
                "tote_success": result["tote_success"],
                "revised_solution": result["revised_solution"],
                "coverage": result["criteria_scores"].get("relevance", 0.0),
            }
            status = "completed"
            error = None
        except Exception as e:
            status = "error"
            error = str(e)
            output_data = {
                "needs_revision": False,
                "confidence": 0.0,
                "raw_score": 0.0,
                "criteria_scores": {},
                "critique_points": [f"Validation engine error: {e}"],
                "improvement_suggestions": [],
                "tote_iterations": 0,
                "tote_success": False,
                "revised_solution": solution,
            }

        return PipelineStepResult(
            stage=self.stage,
            status=status,
            output_data=output_data,
            duration_ms=(time.time() - start) * 1000,
            error=error,
        )
