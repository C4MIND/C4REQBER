"""
C4REQBER: Validation System — Core Module
Base classes, data models, and Bayesian updating logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal

import numpy as np


class ExperimentStatus(Enum):
    """States in the validation workflow."""

    DESIGN = "design"
    READY = "ready"
    RUNNING = "running"
    ANALYZING = "analyzing"
    VALIDATED = "validated"
    FALSIFIED = "falsified"
    INCONCLUSIVE = "inconclusive"
    CANCELLED = "cancelled"


@dataclass
class FalsifiabilityCriterion:
    """A single falsifiability test for a hypothesis."""

    statement: str
    measurement: str
    threshold: str
    experiment_type: str | None = None
    difficulty: Literal["easy", "medium", "hard"] = "medium"

    def to_dict(self) -> dict[str, Any]:
        return {
            "statement": self.statement,
            "measurement": self.measurement,
            "threshold": self.threshold,
            "experiment_type": self.experiment_type,
            "difficulty": self.difficulty,
        }


@dataclass
class Observation:
    """A single data point from an experiment."""

    timestamp: datetime
    value: float
    unit: str
    context: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "unit": self.unit,
            "context": self.context,
            "notes": self.notes,
        }


@dataclass
class Experiment:
    """
    A scientific experiment to validate/falsify a hypothesis.

    Follows Popperian falsifiability: experiments seek to disprove hypotheses.
    """

    id: str
    discovery_id: str
    name: str
    description: str = ""

    falsifiability_criteria: list[FalsifiabilityCriterion] = field(default_factory=list)

    status: ExperimentStatus = ExperimentStatus.DESIGN

    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    observations: list[Observation] = field(default_factory=list)
    expected_observations: int = 1

    conclusion: str | None = None
    confidence_delta: float = 0.0

    researcher: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "discovery_id": self.discovery_id,
            "name": self.name,
            "description": self.description,
            "falsifiability_criteria": [
                c.to_dict() for c in self.falsifiability_criteria
            ],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "observations": [o.to_dict() for o in self.observations],
            "expected_observations": self.expected_observations,
            "conclusion": self.conclusion,
            "confidence_delta": self.confidence_delta,
            "researcher": self.researcher,
            "tags": self.tags,
        }


class BayesianUpdater:
    """
    Bayesian updating of hypothesis confidence based on evidence.

    P(H|E) = P(E|H) * P(H) / P(E)
    """

    @staticmethod
    def update(
        prior: float,
        likelihood: float,
        false_positive_rate: float = 0.1,
    ) -> float:
        """
        Update confidence using Bayes' theorem.

        Args:
            prior: Initial confidence [0, 1]
            likelihood: P(E|H) - probability of evidence given hypothesis [0, 1]
            false_positive_rate: P(E|¬H) - false positive rate [0, 1]

        Returns:
            Posterior confidence [0, 1]
        """
        if prior <= 0 or prior >= 1:
            return prior

        evidence_prob = likelihood * prior + false_positive_rate * (1 - prior)

        if evidence_prob == 0:
            return prior

        posterior = (likelihood * prior) / evidence_prob

        return min(1.0, max(0.0, posterior))

    @staticmethod
    def update_from_outcome(
        prior: float,
        outcome: Literal["validated", "falsified"],
        strength: float = 0.5,
    ) -> float:
        """
        Simple update based on binary outcome.

        Args:
            prior: Initial confidence
            outcome: "validated" increases confidence, "falsified" decreases
            strength: How much to update (0.1 = weak, 0.9 = strong)
        """
        if outcome == "validated":
            return prior + (1.0 - prior) * strength
        else:
            return prior * (1.0 - strength)


class CalibrationTracker:
    """
    Track prediction accuracy to calibrate confidence scores.

    Uses Brier score: lower is better calibrated.
    Brier = mean((confidence - actual_outcome)²)
    """

    def __init__(self, storage_path: str | None = None) -> None:
        import os
        from pathlib import Path

        # Default is env-overridable so tests can redirect persistent state to
        # a tmp path instead of mutating the tracked repo file (see conftest).
        self.storage_path = Path(
            storage_path or os.getenv("CALIBRATION_STORE", "data/calibration.json")
        )
        self.predictions: list[tuple] = []  # type: ignore[type-arg]
        self._load()

    def _load(self) -> None:
        """Load calibration data."""
        import json

        if self.storage_path.exists():
            try:
                with open(self.storage_path) as f:
                    data = json.load(f)
                    self.predictions = [
                        (p["confidence"], p["actual"])
                        for p in data.get("predictions", [])
                    ]
            except Exception as e:
                print(f"⚠️  Failed to load calibration data: {e}")

    def save(self) -> None:
        """Save calibration data."""
        import json

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "predictions": [
                {"confidence": c, "actual": a} for c, a in self.predictions
            ],
            "brier_score": self.brier_score(),
            "total_predictions": len(self.predictions),
        }
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def record(self, confidence: float, actual_outcome: bool) -> None:
        """Record a prediction and its outcome."""
        self.predictions.append((confidence, actual_outcome))
        self.save()

    def brier_score(self) -> float:
        """
        Calculate Brier score (mean squared error of probabilities).

        Perfect calibration = 0.0
        Random guessing = ~0.25
        """
        if not self.predictions:
            return 0.0

        actuals = [1.0 if a else 0.0 for _, a in self.predictions]
        confidences = [c for c, _ in self.predictions]

        return np.mean([(c - a) ** 2 for c, a in zip(confidences, actuals, strict=False)])  # type: ignore[no-any-return]

    def calibration_curve(self, bins: int = 10) -> list[dict[str, float]]:
        """
        Get calibration curve data for plotting.

        Returns list of {confidence_bin, actual_frequency, count}
        """
        if not self.predictions:
            return []

        bin_edges = np.linspace(0, 1, bins + 1)
        results = []

        for i in range(bins):
            lower, upper = bin_edges[i], bin_edges[i + 1]

            in_bin = [(c, a) for c, a in self.predictions if lower <= c < upper]

            if in_bin:
                actual_rate = np.mean([1.0 if a else 0.0 for _, a in in_bin])

                results.append(
                    {
                        "confidence_bin": (lower + upper) / 2,
                        "actual_frequency": actual_rate,
                        "count": len(in_bin),
                    }
                )

        return results

    def get_calibration_status(self) -> str:
        """Get human-readable calibration status."""
        brier = self.brier_score()
        n = len(self.predictions)

        if n < 10:
            return f"Insufficient data ({n} predictions)"
        elif brier < 0.1:
            return f"Well calibrated (Brier: {brier:.3f})"
        elif brier < 0.2:
            return f"Moderately calibrated (Brier: {brier:.3f})"
        else:
            return f"Poorly calibrated (Brier: {brier:.3f}) - overconfident?"
