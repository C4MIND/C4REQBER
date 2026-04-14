"""
TURBO-CDI: Validation System v4.0
Scientific experiment tracking and hypothesis validation

Implements:
- Experiment lifecycle management
- Bayesian confidence updating
- Falsifiability tracking (Popper-style)
- Validation workflow states
"""

from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

import numpy as np

from src.graph.knowledge_graph import get_knowledge_graph


class ExperimentStatus(Enum):
    """States in the validation workflow."""

    DESIGN = "design"  # Experiment being designed
    READY = "ready"  # Ready to execute
    RUNNING = "running"  # Data collection in progress
    ANALYZING = "analyzing"  # Data analysis ongoing
    VALIDATED = "validated"  # Hypothesis supported
    FALSIFIED = "falsified"  # Hypothesis rejected
    INCONCLUSIVE = "inconclusive"  # Insufficient evidence
    CANCELLED = "cancelled"  # Experiment aborted


@dataclass
class FalsifiabilityCriterion:
    """A single falsifiability test for a hypothesis."""

    statement: str  # "If X, then hypothesis is false"
    measurement: str  # How to measure X
    threshold: str  # Specific numeric threshold
    experiment_type: Optional[str] = None
    difficulty: Literal["easy", "medium", "hard"] = "medium"

    def to_dict(self) -> Dict[str, Any]:
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
    context: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
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
    discovery_id: str  # Links to hypothesis in knowledge graph
    name: str
    description: str = ""

    # Falsifiability criteria (Popper-style)
    falsifiability_criteria: List[FalsifiabilityCriterion] = field(default_factory=list)

    # Experiment state
    status: ExperimentStatus = ExperimentStatus.DESIGN

    # Timeline
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Data
    observations: List[Observation] = field(default_factory=list)
    expected_observations: int = 1

    # Results
    conclusion: Optional[str] = None
    confidence_delta: float = 0.0  # Change in hypothesis confidence

    # Metadata
    researcher: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
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

    Where:
    - P(H) = prior confidence
    - P(E|H) = likelihood (how likely is evidence if hypothesis is true)
    - P(E|¬H) = false positive rate
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

        # P(E) = P(E|H) * P(H) + P(E|¬H) * P(¬H)
        evidence_prob = likelihood * prior + false_positive_rate * (1 - prior)

        if evidence_prob == 0:
            return prior

        # P(H|E) = P(E|H) * P(H) / P(E)
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
            # Move toward 1.0
            return prior + (1.0 - prior) * strength
        else:  # falsified
            # Move toward 0.0
            return prior * (1.0 - strength)


class CalibrationTracker:
    """
    Track prediction accuracy to calibrate confidence scores.

    Uses Brier score: lower is better calibrated.
    Brier = mean((confidence - actual_outcome)²)
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = (
            Path(storage_path) if storage_path else Path("data/calibration.json")
        )
        self.predictions: List[tuple] = []  # (confidence, actual_outcome)
        self._load()

    def _load(self):
        """Load calibration data."""
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

    def save(self):
        """Save calibration data."""
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

    def record(self, confidence: float, actual_outcome: bool):
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

        # Convert bool to 0/1
        actuals = [1.0 if a else 0.0 for _, a in self.predictions]
        confidences = [c for c, _ in self.predictions]

        return np.mean([(c - a) ** 2 for c, a in zip(confidences, actuals)])

    def calibration_curve(self, bins: int = 10) -> List[Dict[str, float]]:
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

            # Find predictions in this bin
            in_bin = [(c, a) for c, a in self.predictions if lower <= c < upper]

            if in_bin:
                avg_confidence = np.mean([c for c, _ in in_bin])
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


class ValidationTracker:
    """
    Main validation tracking system.

    Manages experiment lifecycle and updates hypothesis confidence
    based on experimental outcomes.
    """

    def __init__(self):
        self.kg = get_knowledge_graph()
        self.calibration = CalibrationTracker()
        self.bayesian = BayesianUpdater()
        self._experiments: Dict[str, Experiment] = {}
        self._load_experiments()

    def _load_experiments(self):
        """Load experiments from knowledge graph."""
        nodes = self.kg.get_nodes_by_type("experiment")
        for node in nodes:
            # Convert back to Experiment object
            exp = self._node_to_experiment(node)
            self._experiments[exp.id] = exp

    def _node_to_experiment(self, node: Dict) -> Experiment:
        """Convert knowledge graph node to Experiment."""
        meta = node.get("metadata", {})

        # Parse falsifiability criteria
        criteria = [
            FalsifiabilityCriterion(**c)
            for c in meta.get("falsifiability_criteria", [])
        ]

        # Parse observations
        observations = [
            Observation(
                timestamp=datetime.fromisoformat(o["timestamp"]),
                value=o["value"],
                unit=o["unit"],
                context=o.get("context", {}),
                notes=o.get("notes", ""),
            )
            for o in meta.get("observations", [])
        ]

        return Experiment(
            id=node["node_id"],
            discovery_id=meta.get("discovery_id", ""),
            name=meta.get("name", ""),
            description=meta.get("description", ""),
            falsifiability_criteria=criteria,
            status=ExperimentStatus(meta.get("status", "design")),
            created_at=datetime.fromisoformat(node["created_at"]),
            started_at=datetime.fromisoformat(meta["started_at"])
            if meta.get("started_at")
            else None,
            completed_at=datetime.fromisoformat(meta["completed_at"])
            if meta.get("completed_at")
            else None,
            observations=observations,
            expected_observations=meta.get("expected_observations", 1),
            conclusion=meta.get("conclusion"),
            confidence_delta=meta.get("confidence_delta", 0.0),
            researcher=meta.get("researcher", ""),
            tags=meta.get("tags", []),
        )

    def create_experiment(
        self,
        discovery_id: str,
        name: str,
        description: str = "",
        researcher: str = "",
    ) -> Experiment:
        """
        Create a new experiment for a hypothesis.

        Args:
            discovery_id: ID of the hypothesis to test
            name: Experiment name
            description: Experiment description
            researcher: Who is conducting the experiment

        Returns:
            New Experiment instance
        """
        # Get discovery to extract falsifiability criteria
        discovery = self.kg.get_node(discovery_id)
        if not discovery:
            raise ValueError(f"Discovery {discovery_id} not found")

        meta = discovery.get("metadata", {})
        criteria_data = meta.get("falsifiability_criteria", [])

        criteria = [
            FalsifiabilityCriterion(**c) if isinstance(c, dict) else c
            for c in criteria_data
        ]

        # Create experiment
        exp_id = f"experiment_{len(self._experiments) + 1}"
        experiment = Experiment(
            id=exp_id,
            discovery_id=discovery_id,
            name=name,
            description=description,
            falsifiability_criteria=criteria,
            researcher=researcher,
        )

        # Store in knowledge graph
        self.kg.add_experiment_node(
            experiment_id=exp_id,
            discovery_id=discovery_id,
            name=name,
            description=description,
            researcher=researcher,
            status="design",
            metadata={
                "falsifiability_criteria": [c.to_dict() for c in criteria],
                "expected_observations": 1,
            },
        )

        # Link to discovery
        self.kg.add_edge(
            from_id=exp_id,
            to_id=discovery_id,
            edge_type="tests",
        )

        self.kg.save()
        self._experiments[exp_id] = experiment

        return experiment

    def start_experiment(self, exp_id: str) -> Experiment:
        """Mark experiment as running."""
        exp = self._experiments.get(exp_id)
        if not exp:
            raise ValueError(f"Experiment {exp_id} not found")

        exp.status = ExperimentStatus.RUNNING
        exp.started_at = datetime.now()

        self._update_experiment_node(exp)
        return exp

    def add_observation(
        self,
        exp_id: str,
        value: float,
        unit: str,
        context: Optional[Dict] = None,
        notes: str = "",
    ) -> Observation:
        """Add a data point to an experiment."""
        exp = self._experiments.get(exp_id)
        if not exp:
            raise ValueError(f"Experiment {exp_id} not found")

        obs = Observation(
            timestamp=datetime.now(),
            value=value,
            unit=unit,
            context=context or {},
            notes=notes,
        )

        exp.observations.append(obs)
        self._update_experiment_node(exp)

        return obs

    def conclude_experiment(
        self,
        exp_id: str,
        outcome: Literal["validated", "falsified", "inconclusive"],
        conclusion: str = "",
        strength: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Conclude an experiment and update hypothesis confidence.

        Args:
            exp_id: Experiment ID
            outcome: validated (supports hypothesis), falsified (rejects), or inconclusive
            conclusion: Text explanation
            strength: How strongly this outcome affects confidence (0.1-0.9)

        Returns:
            Dict with old_confidence, new_confidence, delta
        """
        exp = self._experiments.get(exp_id)
        if not exp:
            raise ValueError(f"Experiment {exp_id} not found")

        # Update experiment
        exp.status = ExperimentStatus(outcome)
        exp.completed_at = datetime.now()
        exp.conclusion = conclusion

        # Get hypothesis
        discovery = self.kg.get_node(exp.discovery_id)
        if not discovery:
            raise ValueError(f"Discovery {exp.discovery_id} not found")

        # Update confidence using Bayesian update
        old_confidence = discovery.get("metadata", {}).get("confidence_score", 0.5)

        if outcome == "validated":
            new_confidence = self.bayesian.update_from_outcome(
                old_confidence, "validated", strength
            )
        elif outcome == "falsified":
            new_confidence = self.bayesian.update_from_outcome(
                old_confidence, "falsified", strength
            )
        else:
            new_confidence = old_confidence

        exp.confidence_delta = new_confidence - old_confidence

        # Update discovery in knowledge graph
        self.kg.graph.nodes[exp.discovery_id]["metadata"]["confidence_score"] = (
            new_confidence
        )
        self.kg.graph.nodes[exp.discovery_id]["metadata"]["status"] = outcome

        # Record for calibration
        self.calibration.record(old_confidence, outcome == "validated")

        # Save
        self._update_experiment_node(exp)
        self.kg.save()
        self.calibration.save()

        return {
            "old_confidence": old_confidence,
            "new_confidence": new_confidence,
            "delta": exp.confidence_delta,
            "outcome": outcome,
        }

    def _update_experiment_node(self, exp: Experiment):
        """Update experiment node in knowledge graph."""
        node_data = {
            "node_id": exp.id,
            "node_type": "experiment",
            "created_at": exp.created_at.isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": exp.to_dict(),
        }

        if self.kg.has_node(exp.id):
            for key, value in node_data.items():
                self.kg.graph.nodes[exp.id][key] = value

    def get_experiments_for_discovery(self, discovery_id: str) -> List[Experiment]:
        """Get all experiments testing a hypothesis."""
        return [
            exp
            for exp in self._experiments.values()
            if exp.discovery_id == discovery_id
        ]

    def get_validation_rate(self, discovery_id: Optional[str] = None) -> float:
        """
        Calculate validation rate for a hypothesis or overall.

        Returns: Proportion of experiments that validated (0.0 - 1.0)
        """
        experiments = (
            self.get_experiments_for_discovery(discovery_id)
            if discovery_id
            else list(self._experiments.values())
        )

        concluded = [
            exp
            for exp in experiments
            if exp.status in (ExperimentStatus.VALIDATED, ExperimentStatus.FALSIFIED)
        ]

        if not concluded:
            return 0.0

        validated = len(
            [e for e in concluded if e.status == ExperimentStatus.VALIDATED]
        )
        return validated / len(concluded)

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all validation activity."""
        total = len(self._experiments)
        by_status = {}

        for exp in self._experiments.values():
            status = exp.status.value
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total_experiments": total,
            "by_status": by_status,
            "validation_rate": self.get_validation_rate(),
            "calibration": {
                "brier_score": self.calibration.brier_score(),
                "total_predictions": len(self.calibration.predictions),
                "status": self.calibration.get_calibration_status(),
            },
        }


# ═══════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════

_validation_tracker: Optional[ValidationTracker] = None


def get_validation_tracker() -> ValidationTracker:
    """Get singleton validation tracker."""
    global _validation_tracker
    if _validation_tracker is None:
        _validation_tracker = ValidationTracker()
    return _validation_tracker
