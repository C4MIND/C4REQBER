"""
Abduction Engine — Inference to the Best Explanation (Peirce) v7.

Implements Peircean abduction with IBE scoring, retroduction (hypothesis
generation from observations), and best explanation selection.

Usage example:
    >>> from src.discovery.abduction import AbductionEngine, Observation
    >>> engine = AbductionEngine()
    >>> result = engine.infer_to_best_explanation([
    ...     Observation("The sky appears red at sunset"),
    ...     Observation("Blue light is scattered more than red"),
    ... ])
    >>> print(result.best_explanation.description)
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Observation:
    """A single observation or surprising fact to be explained."""

    description: str
    confidence: float = 1.0
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass
class Hypothesis:
    """A candidate explanatory hypothesis with multi-dimensional scoring."""

    id: str
    description: str
    likelihood_score: float = 0.0
    coherence_score: float = 0.0
    simplicity_score: float = 0.0
    predictive_score: float = 0.0
    overall_score: float = 0.0
    evidence: list[str] = field(default_factory=list[Any])
    assumptions: list[str] = field(default_factory=list[Any])
    explains: list[str] = field(default_factory=list[Any])
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "likelihood_score": round(self.likelihood_score, 4),
            "coherence_score": round(self.coherence_score, 4),
            "simplicity_score": round(self.simplicity_score, 4),
            "predictive_score": round(self.predictive_score, 4),
            "overall_score": round(self.overall_score, 4),
            "evidence": self.evidence,
            "assumptions": self.assumptions,
            "explains": self.explains,
            "metadata": self.metadata,
        }


@dataclass
class AbductionResult:
    """Result of Inference to the Best Explanation (IBE)."""

    request_id: str
    observations: list[Observation]
    hypotheses: list[Hypothesis]
    best_explanation: Hypothesis | None = None
    explanation: str = ""
    domain: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "observations": [
                {"description": o.description, "confidence": o.confidence, "source": o.source}
                for o in self.observations
            ],
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "best_explanation": self.best_explanation.to_dict() if self.best_explanation else None,
            "explanation": self.explanation,
            "domain": self.domain,
            "metadata": self.metadata,
        }


# Domain-specific retroductive templates for hypothesis generation
DOMAIN_TEMPLATES: dict[str, list[str]] = {
    "c4": [
        "Cognitive state transition in C4 space explains {}",
        "Operator-mediated transformation pattern accounts for {}",
        "Memory consolidation anomaly underlies {}",
        "Attention modulation cascade drives {}",
        "Meta-cognitive recursion event produces {}",
    ],
    "physics": [
        "Wave-mediated propagation explains {}",
        "Field perturbation induced by {} leads to observed effects",
        "Quantum superposition collapse during {} produces the outcome",
        "Thermodynamic entropy increase from {} drives the phenomenon",
        "Electromagnetic resonance with {} accounts for the data",
    ],
    "biology": [
        "Enzymatic cascade triggered by {} produces the observed response",
        "Gene regulatory network activation via {} explains the pattern",
        "Population selection pressure from {} drives the adaptation",
        "Epigenetic modification in response to {} alters expression",
        "Symbiotic microbial interaction with {} produces the effect",
    ],
    "chemistry": [
        "Catalytic surface reaction with {} accelerates the process",
        "Electron transfer between {} and substrate drives reduction",
        "Hydrogen bonding network around {} stabilizes the conformation",
        "Free radical chain reaction initiated by {} propagates",
        "Coordination complex formation with {} shifts equilibrium",
    ],
    "cognitive": [
        "Attentional bottleneck during {} causes the observed limitation",
        "Working memory chunking of {} explains capacity constraints",
        "Predictive coding error for {} generates the surprise signal",
        "Heuristic bias applied to {} produces the systematic deviation",
        "Neural ensemble synchronization around {} enables binding",
    ],
    "triz": [
        "Inventive principle application resolves {}",
        "Contradiction resolution pattern addresses {}",
        "Functional idealization trajectory optimizes {}",
        "S-curve evolution transition transforms {}",
        "Substance-field reconfiguration restructures {}",
    ],
    "general": [
        "Causal mechanism linking {} to the effect",
        "Emergent property arising from interactions in {}",
        "Feedback loop driven by {} amplifies the signal",
        "Hidden variable correlated with {} explains the correlation",
        "Stochastic process with mean dependent on {}",
    ],
}


def _token_overlap(text1: str, text2: str) -> float:
    """Compute Jaccard-like token overlap between two texts."""
    tokens1 = set(text1.lower().split())
    tokens2 = set(text2.lower().split())
    if not tokens1 or not tokens2:
        return 0.0
    return len(tokens1 & tokens2) / max(len(tokens1 | tokens2), 1)


def ibe_score(
    hypothesis: Hypothesis,
    observations: list[Observation],
    likelihood_weight: float = 0.40,
    coherence_weight: float = 0.25,
    simplicity_weight: float = 0.20,
    predictive_weight: float = 0.15,
) -> float:
    """
    Compute the IBE (Inference to the Best Explanation) score.

    The score is a weighted combination of:
      - Likelihood: P(observations | hypothesis)
      - Coherence: internal consistency and fit with background
      - Simplicity: Occam's razor (fewer assumptions, shorter description)
      - Predictive: novel predictions beyond the observations

    Args:
        hypothesis: The candidate hypothesis to score.
        observations: List of observations to explain.
        likelihood_weight: Weight for likelihood (default 0.40).
        coherence_weight: Weight for coherence (default 0.25).
        simplicity_weight: Weight for simplicity (default 0.20).
        predictive_weight: Weight for predictive power (default 0.15).

    Returns:
        Composite IBE score in [0, 1].

    Example:
        >>> h = Hypothesis(id="H1", description="Gravity bends light")
        >>> obs = [Observation("Star positions shift during eclipse")]
        >>> score = ibe_score(h, obs)
    """
    # Likelihood: how well does H explain the observations?
    if observations:
        likelihood = sum(
            _token_overlap(hypothesis.description, obs.description)
            for obs in observations
        ) / len(observations)
    else:
        likelihood = 0.0

    # Coherence: inverse of average contradiction with other hypotheses
    # (simplified: based on assumption consistency)
    coherence = 1.0
    if hypothesis.assumptions:
        # Penalize if assumptions contradict each other (naive check)
        contradictions = 0
        for i, a1 in enumerate(hypothesis.assumptions):
            for a2 in hypothesis.assumptions[i + 1 :]:
                negators = {"not", "no", "never", "without", "absence"}
                a1_tokens = set(a1.lower().split())
                a2_tokens = set(a2.lower().split())
                if a1_tokens & negators and a2_tokens & negators:
                    continue
                if (a1_tokens & negators and not (a2_tokens & negators)) or (
                    a2_tokens & negators and not (a1_tokens & negators)
                ):
                    if a1_tokens & a2_tokens:
                        contradictions += 1
        coherence = max(0.0, 1.0 - contradictions / len(hypothesis.assumptions))

    # Simplicity: inverse log complexity
    n_assumptions = len(hypothesis.assumptions)
    desc_len = len(hypothesis.description.split())
    complexity = 1.0 + n_assumptions + desc_len / 50.0
    simplicity = 1.0 / math.log1p(math.e - 1 + complexity)

    # Predictive: fraction of description not in observations
    obs_text = " ".join(o.description.lower() for o in observations)
    obs_words = set(obs_text.split())
    desc_words = set(hypothesis.description.lower().split())
    if desc_words:
        novel = desc_words - obs_words
        predictive = len(novel) / len(desc_words)
    else:
        predictive = 0.0

    total_weight = likelihood_weight + coherence_weight + simplicity_weight + predictive_weight
    if total_weight == 0.0:
        return 0.0

    score = (
        likelihood_weight * likelihood
        + coherence_weight * coherence
        + simplicity_weight * simplicity
        + predictive_weight * predictive
    ) / total_weight

    return round(score, 6)


def retroduction(
    observations: list[Observation],
    domain: str = "general",
    max_hypotheses: int = 5,
    custom_templates: list[str] | None = None,
) -> list[Hypothesis]:
    """
    Generate candidate hypotheses from observations via retroduction.

    Retroduction (Peirce) is the process of inferring a hypothesis H
    from observations O such that if H were true, O would be expected.

    Args:
        observations: Surprising facts to explain.
        domain: Knowledge domain for template selection.
        max_hypotheses: Maximum number of hypotheses to generate.
        custom_templates: Optional user-provided templates.

    Returns:
        List of candidate Hypothesis objects.

    Example:
        >>> obs = [Observation("Mercury perihelion precesses unexpectedly")]
        >>> hyps = retroduction(obs, domain="physics", max_hypotheses=3)
        >>> len(hyps) <= 3
        True
    """
    templates = custom_templates or DOMAIN_TEMPLATES.get(domain, DOMAIN_TEMPLATES["general"])
    observation_summary = " and ".join(o.description[:60] for o in observations[:3])
    if not observation_summary:
        observation_summary = "the observed phenomena"

    hypotheses: list[Hypothesis] = []
    for i, template in enumerate(templates[:max_hypotheses]):
        description = template.format(observation_summary)
        hypotheses.append(
            Hypothesis(
                id=f"H{i + 1}",
                description=description,
                explains=[o.description for o in observations],
                assumptions=[f"Template: {template.split()[0]} mechanism"],
            )
        )

    return hypotheses


def select_best_explanation(
    hypotheses: list[Hypothesis],
    observations: list[Observation],
    likelihood_weight: float = 0.40,
    coherence_weight: float = 0.25,
    simplicity_weight: float = 0.20,
    predictive_weight: float = 0.15,
) -> Hypothesis | None:
    """
    Select the best explanation from candidate hypotheses using IBE scoring.

    Args:
        hypotheses: Candidate hypotheses to evaluate.
        observations: Observations to explain.
        likelihood_weight: Weight for likelihood scoring.
        coherence_weight: Weight for coherence scoring.
        simplicity_weight: Weight for simplicity scoring.
        predictive_weight: Weight for predictive scoring.

    Returns:
        The highest-scoring hypothesis, or None if no candidates.

    Example:
        >>> h1 = Hypothesis(id="H1", description="Gravity bends light", assumptions=[])
        >>> h2 = Hypothesis(id="H2", description="Refraction in ether", assumptions=["ether exists"])
        >>> obs = [Observation("Star shift during eclipse")]
        >>> best = select_best_explanation([h1, h2], obs)
    """
    if not hypotheses:
        return None

    for h in hypotheses:
        h.overall_score = ibe_score(
            h,
            observations,
            likelihood_weight=likelihood_weight,
            coherence_weight=coherence_weight,
            simplicity_weight=simplicity_weight,
            predictive_weight=predictive_weight,
        )

    return max(hypotheses, key=lambda h: h.overall_score)


def rank_hypotheses(
    hypotheses: list[Hypothesis],
    observations: list[Observation],
    likelihood_weight: float = 0.40,
    coherence_weight: float = 0.25,
    simplicity_weight: float = 0.20,
    predictive_weight: float = 0.15,
) -> list[tuple[Hypothesis, float]]:
    """
    Rank hypotheses by IBE score with softmax normalization.

    Returns a list of (hypothesis, probability) tuples where probabilities
    sum to 1.0, enabling probabilistic interpretation of IBE.

    Args:
        hypotheses: Candidate hypotheses.
        observations: Observations to explain.
        likelihood_weight: Weight for likelihood.
        coherence_weight: Weight for coherence.
        simplicity_weight: Weight for simplicity.
        predictive_weight: Weight for predictive power.

    Returns:
        List of (Hypothesis, probability) tuples, sorted descending.
    """
    if not hypotheses:
        return []

    scored = []
    for h in hypotheses:
        score = ibe_score(
            h,
            observations,
            likelihood_weight=likelihood_weight,
            coherence_weight=coherence_weight,
            simplicity_weight=simplicity_weight,
            predictive_weight=predictive_weight,
        )
        h.overall_score = score
        scored.append((h, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    scores = [s for _, s in scored]
    max_score = max(scores)
    min_score = min(scores)

    if max_score == min_score:
        prob = 1.0 / len(scored)
        return [(h, prob) for h, _ in scored]

    exp_scores = [math.exp(3.0 * (s - max_score)) for s in scores]
    sum_exp = sum(exp_scores)

    return [
        (scored[i][0], exp_scores[i] / sum_exp if sum_exp > 0 else 0.0)
        for i in range(len(scored))
    ]


class AbductionEngine:
    """
    Inference to the Best Explanation (IBE) engine.

    Implements Peircean abduction:
      1. Observe surprising facts
      2. Generate candidate explanatory hypotheses (retroduction)
      3. Score by explanatory virtue (likelihood, coherence, simplicity, predictive)
      4. Select the best explanation

    Attributes:
        likelihood_weight: Weight for likelihood scoring.
        coherence_weight: Weight for coherence scoring.
        simplicity_weight: Weight for simplicity (Occam's razor).
        predictive_weight: Weight for predictive power.
    """

    def __init__(
        self,
        likelihood_weight: float = 0.40,
        coherence_weight: float = 0.25,
        simplicity_weight: float = 0.20,
        predictive_weight: float = 0.15,
    ) -> None:
        self.likelihood_weight = likelihood_weight
        self.coherence_weight = coherence_weight
        self.simplicity_weight = simplicity_weight
        self.predictive_weight = predictive_weight

    def infer_to_best_explanation(
        self,
        observations: list[Observation],
        domain: str = "general",
        max_hypotheses: int = 5,
        custom_templates: list[str] | None = None,
    ) -> AbductionResult:
        """
        Perform full IBE abductive reasoning cycle.

        Steps:
          1. Generate candidate hypotheses via retroduction
          2. Score each across four dimensions
          3. Select and rank hypotheses
          4. Return structured result with best explanation

        Args:
            observations: Surprising facts to explain.
            domain: Knowledge domain for template selection.
            max_hypotheses: Maximum hypotheses to generate.
            custom_templates: Optional custom hypothesis templates.

        Returns:
            AbductionResult with ranked hypotheses and best explanation.

        Example:
            >>> engine = AbductionEngine()
            >>> obs = [Observation("Unexpected cognitive load spike")]
            >>> result = engine.infer_to_best_explanation(obs, domain="cognitive")
            >>> result.best_explanation is not None
            True
        """
        hypotheses = retroduction(
            observations=observations,
            domain=domain,
            max_hypotheses=max_hypotheses,
            custom_templates=custom_templates,
        )

        best = select_best_explanation(
            hypotheses,
            observations,
            likelihood_weight=self.likelihood_weight,
            coherence_weight=self.coherence_weight,
            simplicity_weight=self.simplicity_weight,
            predictive_weight=self.predictive_weight,
        )

        ranked = rank_hypotheses(
            hypotheses,
            observations,
            likelihood_weight=self.likelihood_weight,
            coherence_weight=self.coherence_weight,
            simplicity_weight=self.simplicity_weight,
            predictive_weight=self.predictive_weight,
        )

        for h, prob in ranked:
            h.metadata["ibe_probability"] = round(prob, 6)

        explanation = ""
        if best:
            explanation = (
                f"Best explanation (score={best.overall_score:.4f}): {best.description}. "
                f"Explains {len(best.explains)} observation(s) with "
                f"{len(best.assumptions)} assumption(s)."
            )

        return AbductionResult(
            request_id=str(uuid.uuid4()),
            observations=observations,
            hypotheses=hypotheses,
            best_explanation=best,
            explanation=explanation,
            domain=domain,
            metadata={
                "method": "Inference to the Best Explanation (Peirce)",
                "scoring_dimensions": 4,
                "scoring_weights": {
                    "likelihood": self.likelihood_weight,
                    "coherence": self.coherence_weight,
                    "simplicity": self.simplicity_weight,
                    "predictive": self.predictive_weight,
                },
                "generated_count": len(hypotheses),
                "domain": domain,
            },
        )
