"""
Falsification Engine — Popper's Falsification Framework v7.

Implements Karl Popper's philosophy of science:
  - Falsifiability: is a hypothesis empirically testable?
  - Severity: how severely has the hypothesis been tested?
  - Modus tollens: logical structure of falsification
  - Demarcation: science vs non-science

Usage example:
    >>> from src.discovery.falsification import FalsificationEngine
    >>> engine = FalsificationEngine()
    >>> result = engine.evaluate("All swans are white", ["Swan A is white", "Swan B is black"])
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Hypothesis:
    """A scientific hypothesis with testable predictions."""

    id: str
    statement: str
    predictions: list[str] = field(default_factory=list[Any])
    assumptions: list[str] = field(default_factory=list[Any])
    is_falsified: bool = False
    severity_score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "predictions": self.predictions,
            "assumptions": self.assumptions,
            "is_falsified": self.is_falsified,
            "severity_score": round(self.severity_score, 4),
            "metadata": self.metadata,
        }


@dataclass
class TestResult:
    """Result of a single empirical test."""

    prediction: str
    observation: str
    outcome: str  # "confirmed", "falsified", "inconclusive"
    confidence: float = 1.0
    severity: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction": self.prediction,
            "observation": self.observation,
            "outcome": self.outcome,
            "confidence": self.confidence,
            "severity": self.severity,
            "metadata": self.metadata,
        }


@dataclass
class FalsificationReport:
    """Complete falsification evaluation report for a hypothesis."""

    hypothesis_id: str
    hypothesis_statement: str
    is_falsifiable: bool
    is_falsified: bool
    tests: list[TestResult]
    overall_severity: float
    corroboration: float
    demarcation: str
    modus_tollens_valid: bool
    explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "hypothesis_statement": self.hypothesis_statement,
            "is_falsifiable": self.is_falsifiable,
            "is_falsified": self.is_falsified,
            "tests": [t.to_dict() for t in self.tests],
            "overall_severity": self.overall_severity,
            "corroboration": self.corroboration,
            "demarcation": self.demarcation,
            "modus_tollens_valid": self.modus_tollens_valid,
            "explanation": self.explanation,
            "metadata": self.metadata,
        }


def is_falsifiable(statement: str) -> tuple[bool, str]:
    """
    Check if a statement is empirically falsifiable.

    A statement is falsifiable if it forbids at least one possible observation.
    Non-falsifiable statements include tautologies, vague claims, and
    unfalsifiable metaphysical assertions.

    Args:
        statement: The hypothesis statement to evaluate.

    Returns:
        Tuple of (is_falsifiable, reason).

    Example:
        >>> is_falsifiable("All swans are white")
        (True, 'Universal claim with clear counterexample condition')
        >>> is_falsifiable("God exists")
        (False, 'No possible observation could contradict this claim')
    """
    s = statement.strip().lower()

    # Empty or too short
    if len(s) < 5:
        return False, "Statement too short to be meaningful"

    # Tautologies
    tautology_patterns = [
        r"\b(a=a|b=b|true is true|always happens|never doesn't)\b",
        r"\b(either it is or it isn't)\b",
        r"\b(all bachelors are unmarried)\b",
    ]
    for pattern in tautology_patterns:
        if re.search(pattern, s):
            return False, "Tautology: true by definition, no empirical content"

    # Vague / unfalsifiable metaphysical claims
    unfalsifiable_patterns = [
        r"\b(god exists|divine|supernatural|beyond observation)\b",
        r"\b(everything happens for a reason|meant to be)\b",
        r"\b(invisible|undetectable|unobservable).*(force|entity|being)\b",
    ]
    for pattern in unfalsifiable_patterns:
        if re.search(pattern, s):
            return False, "No possible observation could contradict this claim"

    # Universal claims with clear counterexamples are falsifiable
    universal_patterns = [
        r"\ball\s+\w+\s+are\b",
        r"\bno\s+\w+\s+can\b",
        r"\bnever\b",
        r"\balways\b",
        r"\bevery\s+\w+\s+(is|has|does)\b",
    ]
    for pattern in universal_patterns:
        if re.search(pattern, s):
            return True, "Universal claim with clear counterexample condition"

    # Conditional / causal claims
    causal_patterns = [
        r"\b(if|when|causes|leads to|produces|results in)\b",
        r"\b(increases|decreases|correlates with|depends on)\b",
    ]
    for pattern in causal_patterns:
        if re.search(pattern, s):
            return True, "Conditional/causal claim with testable implications"

    # Statistical claims
    if re.search(r"\b(probability|chance|likely|unlikely|p\s*=\s*\d)\b", s):
        return True, "Statistical claim with measurable frequencies"

    # Specific existential claims
    if re.search(r"\b(there is|there exists|some|at least one)\b", s):
        return True, "Existential claim with search procedure"

    # Default: if it mentions observable entities, it's likely falsifiable
    observable_terms = [
        "measure", "observe", "detect", "record", "count", "weigh",
        "temperature", "pressure", "speed", "distance", "time",
        "move", "expand", "conduct", "bend", "shift", "drift",
    ]
    if any(term in s for term in observable_terms):
        return True, "Contains observable/measurable terms"

    # Broader pattern: statements about physical entities or processes
    physical_entity_patterns = [
        r"\b(planets?|stars?|galax|light|gravity|matter|energy)\b",
        r"\b(metal|water|air|gas|liquid|solid)\b",
        r"\b(animals?|plants?|cells?|organisms?)\b",
        r"\b(electrons?|protons?|neutrons?|atoms?|molecules?)\b",
    ]
    for pattern in physical_entity_patterns:
        if re.search(pattern, s):
            return True, "Refers to observable physical entities"

    # Claims that make predictions about human traits/behavior are falsifiable
    if re.search(r"\b(predicts?|determines?|influences?).*\b(personality|behavior|trait|character)\b", s):
        return True, "Predictive claim about human characteristics"

    return False, "Statement too vague or general to be tested"


def severity_score(
    hypothesis: Hypothesis,
    test_result: TestResult,
) -> float:
    """
    Compute the severity of a test (Mayo 1996).

    A severe test is one that would very probably fail if the hypothesis
    were false, but passes. Severity = P(test passes | H is false).

    Higher severity means the test provides stronger evidence for H.

    Args:
        hypothesis: The hypothesis being tested.
        test_result: The result of the test.

    Returns:
        Severity score in [0, 1].

    Example:
        >>> h = Hypothesis("H1", "Gravity bends light", predictions=["star shift"])
        >>> tr = TestResult("star shift", "1.75 arcsec deflection", "confirmed", 0.99)
        >>> severity_score(h, tr)
        0.99
    """
    if test_result.outcome == "falsified":
        # A falsification is maximally severe for the hypothesis
        return 1.0

    if test_result.outcome == "inconclusive":
        return 0.0

    # For confirmations, severity depends on:
    # 1. Confidence in the observation
    # 2. How specific the prediction was (more specific = more severe)
    # 3. How unlikely the outcome would be if H were false

    confidence = test_result.confidence

    # Specificity: longer, more detailed predictions are more severe
    prediction = test_result.prediction
    specificity = min(1.0, len(prediction.split()) / 20.0)

    # Risk: tests with clear falsification conditions are more severe
    risk = 0.5
    if hypothesis.predictions:
        # If the prediction was explicitly listed, the test was designed
        pred_set = set(p.lower() for p in hypothesis.predictions)
        if any(prediction.lower() in p or p in prediction.lower() for p in pred_set):
            risk = 0.9

    severity = confidence * (0.4 + 0.3 * specificity + 0.3 * risk)
    return round(min(1.0, severity), 4)


def modus_tollens(
    hypothesis_statement: str,
    prediction: str,
    observation: str,
) -> tuple[bool, str]:
    """
    Apply modus tollens to evaluate falsification.

    Modus tollens logic:
        If H, then P
        Not P (observation contradicts prediction)
        Therefore, not H

    Args:
        hypothesis_statement: The hypothesis being tested.
        prediction: What the hypothesis predicts.
        observation: What was actually observed.

    Returns:
        Tuple of (is_falsified, reasoning).

    Example:
        >>> modus_tollens("All swans are white", "Swan X is white", "Swan X is black")
        (True, 'Observation contradicts prediction: modus tollens applies')
        >>> modus_tollens("All swans are white", "Swan X is white", "Swan X is white")
        (False, 'Observation confirms prediction')
    """
    pred_lower = prediction.lower()
    obs_lower = observation.lower()

    # Direct contradiction check
    contradictions = [
        ("white", "black"),
        ("exists", "does not exist"),
        ("true", "false"),
        ("positive", "negative"),
        ("increases", "decreases"),
        ("hot", "cold"),
        ("fast", "slow"),
        ("up", "down"),
        ("present", "absent"),
    ]

    for term1, term2 in contradictions:
        if term1 in pred_lower and term2 in obs_lower:
            return True, "Observation contradicts prediction: modus tollens applies"
        if term2 in pred_lower and term1 in obs_lower:
            return True, "Observation contradicts prediction: modus tollens applies"

    # Check for negation in observation vs prediction
    negation_terms = ["not ", "no ", "never", "absent", "missing", "lacking"]
    pred_has_negation = any(term in pred_lower for term in negation_terms)
    obs_has_negation = any(term in obs_lower for term in negation_terms)

    # CRITICAL FIX: Check for contradiction BEFORE checking confirmation.
    # A direct contradiction (e.g., "All swans are white" vs "Not all swans are white")
    # shares ~80% word overlap, so the confirmation check would falsely return
    # "Observation confirms prediction" if it runs first.
    if pred_has_negation != obs_has_negation:
        # One is negated, the other isn't — potential contradiction
        # Check if they share subject matter
        pred_words = set(pred_lower.split())
        obs_words = set(obs_lower.split())
        shared = pred_words & obs_words
        if len(shared) >= 2:
            return True, "Observation contradicts prediction: modus tollens applies"

    # Check for similarity (confirmation) ONLY if no contradiction was found
    pred_words = set(pred_lower.split())
    obs_words = set(obs_lower.split())
    if pred_words and obs_words:
        overlap = len(pred_words & obs_words) / max(len(pred_words | obs_words), 1)
        if overlap > 0.3:
            return False, "Observation confirms prediction"

    return False, "Observation is inconclusive with respect to prediction"


def demarcation(statement: str) -> str:
    """
    Apply Popper's demarcation criterion: science vs non-science.

    Science is distinguished by falsifiability — the logical possibility
    that an observation could contradict the theory.

    Args:
        statement: The statement to classify.

    Returns:
        Classification string: "science", "pseudoscience", "metaphysics",
        "mathematics", or "insufficient_information".

    Example:
        >>> demarcation("All planets move in ellipses")
        'science'
        >>> demarcation("The universe has a purpose")
        'metaphysics'
    """
    falsifiable, reason = is_falsifiable(statement)

    s = statement.strip().lower()

    # Mathematics / logic
    math_patterns = [
        r"\b(theorem|lemma|proof|axiom|tautology|logically equivalent)\b",
        r"\b(for all|there exists|implies|if and only if)\b.*\b(numbers?|sets?|functions?)\b",
        r"\b\d+\s*[+\-*/]\s*\d+\s*=\s*\d+\b",
    ]
    for pattern in math_patterns:
        if re.search(pattern, s):
            return "mathematics"

    # Direct identity / equality (mathematics)
    if re.search(r"\b\w+\s*=\s*\w+\b", s) and len(s) < 30:
        return "mathematics"

    if falsifiable:
        # Check for pseudoscience indicators
        pseudo_indicators = [
            r"\b(astrology|horoscope|zodiac|mercury retrograde)\b",
            r"\b(crystal healing|energy field|aura)\b.*\b(cure|heal|treat)\b",
            r"\b(irreducible complexity|intelligent design)\b.*\b(scientific|evidence)\b",
        ]
        for pattern in pseudo_indicators:
            if re.search(pattern, s):
                return "pseudoscience"
        # Broader check for astrology-related claims
        if "astrology" in s or "horoscope" in s or "zodiac" in s:
            return "pseudoscience"
        # Broader check for crystal healing / energy healing claims
        if ("crystal" in s and "heal" in s) or ("energy" in s and "heal" in s):
            return "pseudoscience"
        return "science"

    # Not falsifiable — distinguish metaphysics from insufficient info
    if len(s) < 10 or reason == "Statement too short to be meaningful":
        return "insufficient_information"

    metaphysical_indicators = [
        r"\b(purpose|meaning|destiny|fate|soul|spirit)\b",
        r"\b(ultimate|fundamental|essential).*(nature|reality|truth)\b",
        r"\b(god|divine|sacred|holy|transcendent)\b",
    ]
    for pattern in metaphysical_indicators:
        if re.search(pattern, s):
            return "metaphysics"

    return "non_science"


def evaluate_hypothesis(
    hypothesis: Hypothesis,
    observations: list[tuple[str, str, float]],
) -> FalsificationReport:
    """
    Full falsification evaluation of a hypothesis against observations.

    Args:
        hypothesis: The hypothesis to evaluate.
        observations: List of (prediction, observation, confidence) tuples.

    Returns:
        FalsificationReport with complete evaluation.

    Example:
        >>> h = Hypothesis("H1", "All metals expand when heated")
        >>> obs = [("Iron expands at 100C", "Iron expanded 0.1%", 0.95)]
        >>> report = evaluate_hypothesis(h, obs)
        >>> report.is_falsifiable
        True
    """
    falsifiable, falsifiability_reason = is_falsifiable(hypothesis.statement)

    tests: list[TestResult] = []
    is_falsified = False
    total_severity = 0.0
    confirmed_count = 0

    for prediction, observation, confidence in observations:
        falsified, reasoning = modus_tollens(
            hypothesis.statement, prediction, observation
        )

        if falsified:
            outcome = "falsified"
        elif "confirms" in reasoning:
            outcome = "confirmed"
            confirmed_count += 1
        else:
            outcome = "inconclusive"

        test = TestResult(
            prediction=prediction,
            observation=observation,
            outcome=outcome,
            confidence=confidence,
        )
        test.severity = severity_score(hypothesis, test)
        tests.append(test)

        if outcome == "falsified":
            is_falsified = True

        total_severity += test.severity

    overall_severity = total_severity / len(tests) if tests else 0.0
    corroboration = confirmed_count / len(tests) if tests else 0.0

    demarc = demarcation(hypothesis.statement)

    # Modus tollens is valid if at least one falsification occurred
    modus_tollens_valid = any(t.outcome == "falsified" for t in tests)

    explanation = ""
    if is_falsified:
        explanation = (
            f"Hypothesis '{hypothesis.statement}' was falsified by {sum(1 for t in tests if t.outcome == 'falsified')} "
            f"test(s). Modus tollens applies."
        )
    elif tests:
        explanation = (
            f"Hypothesis '{hypothesis.statement}' survived {len(tests)} test(s) with "
            f"corroboration={corroboration:.2f} and severity={overall_severity:.2f}."
        )
    else:
        explanation = f"No tests conducted for '{hypothesis.statement}'."

    return FalsificationReport(
        hypothesis_id=hypothesis.id,
        hypothesis_statement=hypothesis.statement,
        is_falsifiable=falsifiable,
        is_falsified=is_falsified,
        tests=tests,
        overall_severity=overall_severity,
        corroboration=corroboration,
        demarcation=demarc,
        modus_tollens_valid=modus_tollens_valid,
        explanation=explanation,
        metadata={
            "falsifiability_reason": falsifiability_reason,
            "test_count": len(tests),
        },
    )


class FalsificationEngine:
    """
    Popper's Falsification framework engine.

    Provides tools for:
      - Checking falsifiability of hypotheses
      - Computing severity of tests
      - Applying modus tollens
      - Demarcating science from non-science

    Attributes:
        default_confidence: Default confidence level for observations.
    """

    def __init__(self, default_confidence: float = 0.95) -> None:
        self.default_confidence = default_confidence

    def evaluate(
        self,
        hypothesis_statement: str,
        observations: list[tuple[str, str]],
        hypothesis_id: str = "H1",
    ) -> FalsificationReport:
        """
        Evaluate a hypothesis statement against observations.

        Args:
            hypothesis_statement: The hypothesis to test.
            observations: List of (prediction, observation) tuples.
            hypothesis_id: Identifier for the hypothesis.

        Returns:
            FalsificationReport with complete evaluation.

        Example:
            >>> engine = FalsificationEngine()
            >>> report = engine.evaluate(
            ...     "All swans are white",
            ...     [("Swan in Australia is white", "Black swan observed")],
            ... )
            >>> report.is_falsified
            True
        """
        hypothesis = Hypothesis(
            id=hypothesis_id,
            statement=hypothesis_statement,
            predictions=[pred for pred, _ in observations],
        )
        obs_with_conf = [
            (pred, obs, self.default_confidence) for pred, obs in observations
        ]
        return evaluate_hypothesis(hypothesis, obs_with_conf)

    def check_falsifiability(self, statement: str) -> tuple[bool, str]:
        """
        Check if a statement is empirically falsifiable.

        Args:
            statement: The statement to check.

        Returns:
            Tuple of (is_falsifiable, reason).

        Example:
            >>> engine = FalsificationEngine()
            >>> engine.check_falsifiability("All ravens are black")
            (True, 'Universal claim with clear counterexample condition')
        """
        return is_falsifiable(statement)

    def classify(self, statement: str) -> str:
        """
        Classify a statement using Popper's demarcation criterion.

        Args:
            statement: The statement to classify.

        Returns:
            Classification: "science", "pseudoscience", "metaphysics",
            "mathematics", or "insufficient_information".

        Example:
            >>> engine = FalsificationEngine()
            >>> engine.classify("Planets move in ellipses")
            'science'
        """
        return demarcation(statement)

    def apply_modus_tollens(
        self,
        hypothesis: str,
        prediction: str,
        observation: str,
    ) -> tuple[bool, str]:
        """
        Apply modus tollens to determine if a hypothesis is falsified.

        Args:
            hypothesis: The hypothesis statement.
            prediction: The predicted outcome.
            observation: The actual observation.

        Returns:
            Tuple of (is_falsified, reasoning).

        Example:
            >>> engine = FalsificationEngine()
            >>> engine.apply_modus_tollens("H", "P is true", "P is false")
            (True, 'Observation contradicts prediction: modus tollens applies')
        """
        return modus_tollens(hypothesis, prediction, observation)
