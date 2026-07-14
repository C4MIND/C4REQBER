"""
C4REQBER: Validation System — Rules Module
Validation rules, checks, and experiment lifecycle management.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from src.graph.knowledge_graph import get_knowledge_graph
from src.validation.core import (
    BayesianUpdater,
    CalibrationTracker,
    Experiment,
    ExperimentStatus,
    FalsifiabilityCriterion,
    Observation,
)


class ValidationTracker:
    """
    Main validation tracking system.

    Manages experiment lifecycle and updates hypothesis confidence
    based on experimental outcomes.
    """

    def __init__(self) -> None:
        self.kg = get_knowledge_graph()
        self.calibration = CalibrationTracker()
        self.bayesian = BayesianUpdater()
        self._experiments: dict[str, Experiment] = {}
        self._load_experiments()

    def _load_experiments(self) -> None:
        """Load experiments from knowledge graph."""
        nodes = self.kg.get_nodes_by_type("experiment")
        for node in nodes:
            exp = self._node_to_experiment(node)
            self._experiments[exp.id] = exp

    def _node_to_experiment(self, node: dict[str, Any]) -> Experiment:
        """Convert knowledge graph node to Experiment."""
        meta = node.get("metadata", {})

        criteria = [
            FalsifiabilityCriterion(**c)
            for c in meta.get("falsifiability_criteria", [])
        ]

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
        discovery = self.kg.get_node(discovery_id)
        if not discovery:
            raise ValueError(f"Discovery {discovery_id} not found")

        meta = discovery.get("metadata", {})
        criteria_data = meta.get("falsifiability_criteria", [])

        criteria = [
            FalsifiabilityCriterion(**c) if isinstance(c, dict) else c
            for c in criteria_data
        ]

        exp_id = f"experiment_{len(self._experiments) + 1}"
        experiment = Experiment(
            id=exp_id,
            discovery_id=discovery_id,
            name=name,
            description=description,
            falsifiability_criteria=criteria,
            researcher=researcher,
        )

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
        context: dict | None = None,  # type: ignore[type-arg]
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
    ) -> dict[str, Any]:
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

        exp.status = ExperimentStatus(outcome)
        exp.completed_at = datetime.now()
        exp.conclusion = conclusion

        discovery = self.kg.get_node(exp.discovery_id)
        if not discovery:
            raise ValueError(f"Discovery {exp.discovery_id} not found")

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

        self.kg.graph.nodes[exp.discovery_id]["metadata"]["confidence_score"] = (
            new_confidence
        )
        self.kg.graph.nodes[exp.discovery_id]["metadata"]["status"] = outcome

        self.calibration.record(old_confidence, outcome == "validated")

        self._update_experiment_node(exp)
        self.kg.save()
        self.calibration.save()

        return {
            "old_confidence": old_confidence,
            "new_confidence": new_confidence,
            "delta": exp.confidence_delta,
            "outcome": outcome,
        }

    def _update_experiment_node(self, exp: Experiment) -> None:
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

    def get_experiments_for_discovery(self, discovery_id: str) -> list[Experiment]:
        """Get all experiments testing a hypothesis."""
        return [
            exp
            for exp in self._experiments.values()
            if exp.discovery_id == discovery_id
        ]

    def get_validation_rate(self, discovery_id: str | None = None) -> float:
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

    def get_validation_summary(self) -> dict[str, Any]:
        """Get summary statistics for all validation activity."""
        total = len(self._experiments)
        by_status: Any = {}

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


def get_validation_tracker() -> ValidationTracker:
    """Get singleton validation tracker (backed by DI container)."""
    from src.di.container import get_container
    return get_container().get_or_register("validation_tracker", ValidationTracker)
