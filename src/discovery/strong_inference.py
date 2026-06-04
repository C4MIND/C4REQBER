"""
Strong Inference Engine — Platt's Strong Inference Method v7.

Implements John R. Platt's (1964) Strong Inference methodology:
  1. Devise alternative hypotheses
  2. Design crucial experiments to exclude hypotheses
  3. Carry out experiments and analyze results
  4. Recycle: eliminate falsified, generate new

Includes Bayesian updating after each experiment.

Usage example:
    >>> from src.discovery.strong_inference import StrongInferenceEngine, Hypothesis
    >>> engine = StrongInferenceEngine()
    >>> result = engine.run(
    ...     problem="Why do plants grow toward light?",
    ...     hypotheses=[
    ...         Hypothesis("H1", "Auxin accumulates on shaded side"),
    ...         Hypothesis("H2", "Light directly stimulates cell elongation"),
    ...     ]
    ... )
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Hypothesis:
    """A competing scientific hypothesis."""

    id: str
    description: str
    prior: float = 0.5
    posterior: float = 0.5
    is_falsified: bool = False
    evidence: list[str] = field(default_factory=list[Any])
    predictions: list[str] = field(default_factory=list[Any])
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])

    def __post_init__(self) -> None:
        if not 0.0 < self.prior <= 1.0:
            raise ValueError("prior must be in (0, 1]")
        self.posterior = self.prior

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "prior": round(self.prior, 4),
            "posterior": round(self.posterior, 4),
            "is_falsified": self.is_falsified,
            "evidence": self.evidence,
            "predictions": self.predictions,
            "metadata": self.metadata,
        }


@dataclass
class Experiment:
    """A designed experiment to test competing hypotheses."""

    id: str
    description: str
    distinguishes: list[str]  # Hypothesis IDs this experiment distinguishes
    predicted_outcomes: dict[str, str]  # hypothesis_id -> expected observation
    outcome: str = ""
    confidence: float = 1.0
    is_crucial: bool = False
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "distinguishes": self.distinguishes,
            "predicted_outcomes": self.predicted_outcomes,
            "outcome": self.outcome,
            "confidence": self.confidence,
            "is_crucial": self.is_crucial,
            "metadata": self.metadata,
        }


@dataclass
class InferenceResult:
    """Result of a Strong Inference cycle."""

    request_id: str
    problem: str
    hypotheses: list[Hypothesis]
    experiments: list[Experiment]
    surviving_hypotheses: list[Hypothesis]
    eliminated_hypotheses: list[Hypothesis]
    cycles: int
    explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "problem": self.problem,
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "experiments": [e.to_dict() for e in self.experiments],
            "surviving_hypotheses": [h.to_dict() for h in self.surviving_hypotheses],
            "eliminated_hypotheses": [h.to_dict() for h in self.eliminated_hypotheses],
            "cycles": self.cycles,
            "explanation": self.explanation,
            "metadata": self.metadata,
        }


def generate_competing_hypotheses(
    problem: str,
    domain: str = "general",
    count: int = 3,
) -> list[Hypothesis]:
    """
    Generate multiple competing hypotheses for a problem statement.

    Uses domain-specific templates to ensure genuine alternatives.

    Args:
        problem: The scientific problem to address.
        domain: Knowledge domain for template selection.
        count: Number of competing hypotheses to generate.

    Returns:
        List of Hypothesis objects with equal priors.

    Example:
        >>> hyps = generate_competing_hypotheses(
        ...     "Why is the night sky dark?",
        ...     domain="physics",
        ...     count=3,
        ... )
        >>> len(hyps) == 3
        True
    """
    templates: dict[str, list[str]] = {
        "physics": [
            "Finite age of universe limits observable stars",
            "Expansion redshifts light beyond visible range",
            "Interstellar dust absorbs starlight",
            "Universe is spatially finite with bounded stars",
            "Energy conservation in expanding space dims light",
        ],
        "biology": [
            "Hormonal signaling pathway activates response",
            "Mechanical stress triggers cellular adaptation",
            "Genetic mutation alters phenotype expression",
            "Epigenetic modification regulates gene activity",
            "Microbiome interaction modulates host behavior",
        ],
        "chemistry": [
            "Catalyst surface lowers activation energy",
            "Solvent polarity stabilizes transition state",
            "Concentration gradient drives diffusion",
            "Temperature increase accelerates reaction rate",
            "pH change shifts equilibrium position",
        ],
        "cognitive": [
            "Neural inhibition suppresses competing responses",
            "Predictive coding minimizes prediction error",
            "Working memory capacity limits processing",
            "Attentional selection filters sensory input",
            "Reinforcement learning updates action values",
        ],
        "general": [
            "Mechanism A is the primary causal driver",
            "Mechanism B operates via feedback modulation",
            "Mechanism C involves emergent collective effects",
            "Mechanism D results from historical path dependence",
            "Mechanism E arises from optimization constraints",
        ],
    }

    domain_templates = templates.get(domain, templates["general"])
    selected = domain_templates[:count]

    n = len(selected)
    prior = 1.0 / n if n > 0 else 0.5

    hypotheses: list[Hypothesis] = []
    for i, desc in enumerate(selected):
        hypotheses.append(
            Hypothesis(
                id=f"H{i + 1}",
                description=f"{desc}: {problem[:80]}",
                prior=prior,
                predictions=[f"If {desc}, then specific observation {i + 1} should occur"],
            )
        )

    return hypotheses


def design_crucial_experiment(
    hypotheses: list[Hypothesis],
    problem: str,
) -> Experiment | None:
    """
    Design a crucial experiment that distinguishes between competing hypotheses.

    A crucial experiment produces different predicted outcomes for different
    hypotheses, such that the actual outcome eliminates at least one hypothesis.

    Args:
        hypotheses: Competing hypotheses to distinguish.
        problem: The scientific problem context.

    Returns:
        An Experiment object, or None if no distinguishing experiment can be designed.

    Example:
        >>> h1 = Hypothesis("H1", "Light is a wave")
        >>> h2 = Hypothesis("H2", "Light is a particle")
        >>> exp = design_crucial_experiment([h1, h2], "Nature of light")
        >>> exp is not None
        True
    """
    if len(hypotheses) < 2:
        return None

    # Build predicted outcomes by analyzing hypothesis descriptions
    predicted_outcomes: dict[str, str] = {}
    for h in hypotheses:
        # Derive a distinguishing prediction from the hypothesis description
        keywords = set(h.description.lower().split())
        if "wave" in keywords or "oscillation" in keywords or "interference" in keywords:
            predicted_outcomes[h.id] = "interference pattern observed"
        elif "particle" in keywords or "corpuscular" in keywords or "discrete" in keywords:
            predicted_outcomes[h.id] = "discrete impacts observed"
        elif "chemical" in keywords or "reaction" in keywords or "catalyst" in keywords:
            predicted_outcomes[h.id] = "reaction rate changes with concentration"
        elif "genetic" in keywords or "mutation" in keywords or "gene" in keywords:
            predicted_outcomes[h.id] = "phenotype follows Mendelian ratios"
        elif "neural" in keywords or "brain" in keywords or "cognitive" in keywords:
            predicted_outcomes[h.id] = "fMRI activation in specific region"
        else:
            predicted_outcomes[h.id] = f"outcome consistent with {h.id}"

    # Check if predictions actually differ
    unique_outcomes = set(predicted_outcomes.values())
    is_crucial = len(unique_outcomes) > 1

    return Experiment(
        id=f"EXP-{uuid.uuid4().hex[:8]}",
        description=f"Crucial experiment to distinguish between {len(hypotheses)} hypotheses for: {problem[:60]}",
        distinguishes=[h.id for h in hypotheses],
        predicted_outcomes=predicted_outcomes,
        is_crucial=is_crucial,
    )


def bayesian_update(
    hypotheses: list[Hypothesis],
    experiment: Experiment,
    outcome: str,
    confidence: float = 1.0,
) -> list[Hypothesis]:
    """
    Update hypothesis probabilities using Bayes' theorem after an experiment.

    P(H_i | E) = P(E | H_i) * P(H_i) / sum_j P(E | H_j) * P(H_j)

    Args:
        hypotheses: Current hypotheses with priors/posteriors.
        experiment: The experiment that was conducted.
        outcome: The observed outcome.
        confidence: Confidence in the outcome observation (0-1).

    Returns:
        Updated hypotheses with new posterior probabilities.

    Example:
        >>> h1 = Hypothesis("H1", "Wave", prior=0.5)
        >>> h2 = Hypothesis("H2", "Particle", prior=0.5)
        >>> exp = Experiment("E1", "Double slit", ["H1", "H2"], {"H1": "interference", "H2": "no interference"})
        >>> updated = bayesian_update([h1, h2], exp, "interference")
        >>> updated[0].posterior > updated[1].posterior
        True
    """
    if not hypotheses:
        return []

    likelihoods: dict[str, float] = {}
    for h in hypotheses:
        predicted = experiment.predicted_outcomes.get(h.id, "")
        if predicted and outcome:
            # Compute likelihood based on outcome match
            pred_words = set(predicted.lower().split())
            out_words = set(outcome.lower().split())
            overlap = len(pred_words & out_words) / max(len(pred_words | out_words), 1)
            # Scale by confidence: perfect match -> high likelihood
            likelihoods[h.id] = 0.05 + 0.95 * overlap * confidence
        else:
            likelihoods[h.id] = 0.5

    # Compute marginal likelihood (denominator)
    marginal = sum(h.posterior * likelihoods.get(h.id, 0.5) for h in hypotheses)

    updated: list[Hypothesis] = []
    for h in hypotheses:
        prior = h.posterior
        likelihood = likelihoods.get(h.id, 0.5)
        if marginal > 0:
            posterior = (likelihood * prior) / marginal
        else:
            posterior = prior
        # Clamp to valid probability range
        posterior = max(0.001, min(0.999, posterior))

        new_h = Hypothesis(
            id=h.id,
            description=h.description,
            prior=h.prior,
            posterior=posterior,
            is_falsified=h.is_falsified,
            evidence=h.evidence + [f"{experiment.id}: {outcome}"],
            predictions=h.predictions,
            metadata=h.metadata,
        )
        updated.append(new_h)

    return updated


def eliminate_falsified(
    hypotheses: list[Hypothesis],
    experiment: Experiment,
    outcome: str,
    threshold: float = 0.01,
) -> tuple[list[Hypothesis], list[Hypothesis]]:
    """
    Separate hypotheses into surviving and eliminated based on experiment outcome.

    A hypothesis is eliminated if its predicted outcome is strongly inconsistent
    with the observed outcome and its posterior falls below threshold.

    Args:
        hypotheses: Current hypotheses.
        experiment: The experiment conducted.
        outcome: The observed outcome.
        threshold: Posterior probability threshold for elimination.

    Returns:
        Tuple of (surviving, eliminated) hypothesis lists.

    Example:
        >>> h1 = Hypothesis("H1", "Wave", posterior=0.9)
        >>> h2 = Hypothesis("H2", "Particle", posterior=0.1)
        >>> exp = Experiment("E1", "Test", ["H1", "H2"], {"H1": "interference", "H2": "no interference"})
        >>> surv, elim = eliminate_falsified([h1, h2], exp, "interference")
    """
    surviving: list[Hypothesis] = []
    eliminated: list[Hypothesis] = []

    for h in hypotheses:
        predicted = experiment.predicted_outcomes.get(h.id, "")
        pred_words = set(predicted.lower().split())
        out_words = set(outcome.lower().split())
        overlap = len(pred_words & out_words) / max(len(pred_words | out_words), 1) if pred_words or out_words else 0.5

        # A hypothesis is eliminated if its prediction is strongly inconsistent
        # with the observed outcome AND its posterior is low
        if overlap < 0.2 and h.posterior < threshold:
            h.is_falsified = True
            eliminated.append(h)
        elif overlap < 0.1:
            # Very strong inconsistency eliminates regardless of posterior
            h.is_falsified = True
            eliminated.append(h)
        else:
            surviving.append(h)

    return surviving, eliminated


def recycle_hypotheses(
    surviving: list[Hypothesis],
    eliminated: list[Hypothesis],
    problem: str,
    domain: str = "general",
    max_new: int = 2,
) -> list[Hypothesis]:
    """
    Generate new hypotheses from surviving ones, incorporating lessons from elimination.

    This implements Platt's "recycle" step: after eliminating falsified hypotheses,
    generate refined alternatives that preserve what worked and avoid what failed.

    Args:
        surviving: Hypotheses that survived falsification.
        eliminated: Hypotheses that were falsified.
        problem: The original problem statement.
        domain: Knowledge domain.
        max_new: Maximum new hypotheses to generate.

    Returns:
        Combined list of surviving + new hypotheses.

    Example:
        >>> h1 = Hypothesis("H1", "Wave theory")
        >>> h2 = Hypothesis("H2", "Particle theory", is_falsified=True)
        >>> combined = recycle_hypotheses([h1], [h2], "Nature of light")
        >>> len(combined) >= 1
        True
    """
    new_hypotheses: list[Hypothesis] = []

    if not surviving:
        # If all were eliminated, start fresh with more hypotheses
        return generate_competing_hypotheses(problem, domain, count=max_new + 2)

    # Generate refinements of surviving hypotheses
    for i, h in enumerate(surviving[:max_new]):
        # Create a refined version that addresses gaps
        refined_desc = f"Refined {h.description}: incorporating constraints from elimination"
        new_h = Hypothesis(
            id=f"H{h.id}-R{i + 1}",
            description=refined_desc,
            prior=0.5,
            predictions=h.predictions + [f"Refined prediction {i + 1}"],
            metadata={"parent": h.id, "generation": "recycled"},
        )
        new_hypotheses.append(new_h)

    # Also generate one completely novel hypothesis if room permits
    if len(new_hypotheses) < max_new:
        fresh = generate_competing_hypotheses(problem, domain, count=1)
        if fresh:
            fresh[0].id = f"H-NOVEL-{uuid.uuid4().hex[:4]}"
            new_hypotheses.append(fresh[0])

    result = surviving + new_hypotheses

    # Renormalize priors
    n = len(result)
    if n > 0:
        for h in result:
            h.prior = 1.0 / n
            h.posterior = h.prior

    return result


class StrongInferenceEngine:
    """
    Platt's Strong Inference engine for systematic scientific reasoning.

    Implements the four-step cycle:
      1. Devise alternative hypotheses
      2. Design crucial experiments
      3. Carry out experiments and analyze (Bayesian update)
      4. Recycle: eliminate falsified, generate new

    Attributes:
        max_cycles: Maximum inference cycles to run.
        elimination_threshold: Posterior threshold for hypothesis elimination.
    """

    def __init__(
        self,
        max_cycles: int = 5,
        elimination_threshold: float = 0.01,
    ) -> None:
        self.max_cycles = max_cycles
        self.elimination_threshold = elimination_threshold

    def run(
        self,
        problem: str,
        hypotheses: list[Hypothesis] | None = None,
        domain: str = "general",
        experiments: list[tuple[str, float]] | None = None,
    ) -> InferenceResult:
        """
        Execute the full Strong Inference cycle.

        Args:
            problem: The scientific problem statement.
            hypotheses: Initial competing hypotheses (auto-generated if None).
            domain: Knowledge domain for hypothesis generation.
            experiments: Optional list of (outcome, confidence) tuples to simulate.

        Returns:
            InferenceResult with final hypothesis states and experiment history.

        Example:
            >>> engine = StrongInferenceEngine(max_cycles=3)
            >>> result = engine.run(
            ...     problem="Why do plants bend toward light?",
            ...     domain="biology",
            ... )
            >>> result.cycles >= 1
            True
        """
        if hypotheses is None:
            hypotheses = generate_competing_hypotheses(problem, domain, count=3)

        all_hypotheses = list(hypotheses)
        all_experiments: list[Experiment] = []
        eliminated: list[Hypothesis] = []
        cycles = 0

        experiment_queue = list(experiments) if experiments else []

        while cycles < self.max_cycles and len([h for h in hypotheses if not h.is_falsified]) > 1:
            # Step 1: Design crucial experiment
            exp = design_crucial_experiment(hypotheses, problem)
            if exp is None:
                break

            all_experiments.append(exp)

            # Step 2: Execute (simulate or use provided)
            if experiment_queue:
                outcome, confidence = experiment_queue.pop(0)
            else:
                # Simulate: pick outcome from most likely hypothesis
                best_h = max(hypotheses, key=lambda h: h.posterior)
                outcome = exp.predicted_outcomes.get(best_h.id, "inconclusive")
                confidence = 0.95

            exp.outcome = outcome
            exp.confidence = confidence

            # Step 3: Bayesian update
            hypotheses = bayesian_update(hypotheses, exp, outcome, confidence)

            # Step 4: Eliminate falsified
            surviving, newly_eliminated = eliminate_falsified(
                hypotheses, exp, outcome, self.elimination_threshold
            )
            eliminated.extend(newly_eliminated)
            hypotheses = surviving

            cycles += 1

            # Step 5: Recycle if needed
            if len(hypotheses) <= 1 and cycles < self.max_cycles:
                hypotheses = recycle_hypotheses(
                    hypotheses, eliminated, problem, domain, max_new=2
                )
                all_hypotheses.extend([h for h in hypotheses if h not in all_hypotheses])

        surviving_final = [h for h in all_hypotheses if not h.is_falsified]
        eliminated_final = [h for h in all_hypotheses if h.is_falsified]

        explanation = ""
        if surviving_final:
            best = max(surviving_final, key=lambda h: h.posterior)
            explanation = (
                f"After {cycles} cycle(s), best surviving hypothesis is {best.id} "
                f"(posterior={best.posterior:.4f}): {best.description}"
            )
        elif eliminated_final:
            explanation = f"All hypotheses eliminated after {cycles} cycle(s)."
        else:
            explanation = "No hypotheses were evaluated."

        return InferenceResult(
            request_id=str(uuid.uuid4()),
            problem=problem,
            hypotheses=all_hypotheses,
            experiments=all_experiments,
            surviving_hypotheses=surviving_final,
            eliminated_hypotheses=eliminated_final,
            cycles=cycles,
            explanation=explanation,
            metadata={
                "method": "Strong Inference (Platt 1964)",
                "max_cycles": self.max_cycles,
                "elimination_threshold": self.elimination_threshold,
                "final_hypothesis_count": len(surviving_final),
                "eliminated_count": len(eliminated_final),
            },
        )
