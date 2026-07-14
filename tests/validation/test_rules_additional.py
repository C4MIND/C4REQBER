"""
Tests for src/validation/rules.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.validation.core import ExperimentStatus
from src.validation.rules import ValidationTracker, get_validation_tracker


class MockKnowledgeGraph:
    """Lightweight mock for KnowledgeGraph."""

    def __init__(self):
        self._nodes: dict[str, dict] = {}
        self.graph = MagicMock()
        self.graph.nodes = self._nodes
        self._node_return: dict | None = None
        self._nodes_by_type: list[dict] = []

    def get_nodes_by_type(self, node_type: str) -> list[dict]:
        return list(self._nodes_by_type)

    def get_node(self, node_id: str) -> dict | None:
        return self._node_return

    def set_node_return(self, value: dict | None) -> None:
        self._node_return = value

    def has_node(self, node_id: str) -> bool:
        return True

    def add_experiment_node(self, **kwargs) -> str:
        exp_id = kwargs.get("experiment_id")
        self._nodes[exp_id] = {"metadata": {}}
        return exp_id

    def add_edge(self, **kwargs) -> None:
        pass

    def save(self) -> None:
        pass


@pytest.fixture
def mock_kg():
    return MockKnowledgeGraph()


@pytest.fixture
def tracker(mock_kg):
    with patch("src.validation.rules.get_knowledge_graph", return_value=mock_kg):
        vt = ValidationTracker()
        vt._experiments.clear()
        return vt


@pytest.fixture
def sample_discovery():
    return {
        "node_id": "disc_1",
        "node_type": "discovery",
        "metadata": {
            "confidence_score": 0.5,
            "falsifiability_criteria": [
                {
                    "statement": "If X > 10, hypothesis is false",
                    "measurement": "Measure X",
                    "threshold": "10",
                }
            ],
        },
    }


class TestValidationTrackerInit:
    def test_init_loads_experiments(self, mock_kg):
        node = {
            "node_id": "exp_1",
            "node_type": "experiment",
            "created_at": datetime(2024, 1, 1).isoformat(),
            "metadata": {
                "discovery_id": "d1",
                "name": "Test",
                "status": "design",
                "falsifiability_criteria": [],
                "observations": [],
            },
        }
        mock_kg._nodes_by_type = [node]
        with patch("src.validation.rules.get_knowledge_graph", return_value=mock_kg):
            vt = ValidationTracker()
        assert "exp_1" in vt._experiments
        assert vt._experiments["exp_1"].name == "Test"


class TestCreateExperiment:
    def test_success(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        exp = tracker.create_experiment("disc_1", "Gravity Test", "Testing gravity", "Alice")
        assert exp.discovery_id == "disc_1"
        assert exp.name == "Gravity Test"
        assert exp.researcher == "Alice"
        assert exp.status == ExperimentStatus.DESIGN
        assert exp.id == "experiment_1"

    def test_not_found(self, tracker, mock_kg):
        mock_kg.set_node_return(None)
        with pytest.raises(ValueError, match="Discovery disc_missing not found"):
            tracker.create_experiment("disc_missing", "Test")

    def test_with_criteria(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        exp = tracker.create_experiment("disc_1", "Test")
        assert len(exp.falsifiability_criteria) == 1
        assert exp.falsifiability_criteria[0].statement == "If X > 10, hypothesis is false"

    def test_non_dict_criteria(self, tracker, mock_kg):
        from src.validation.core import FalsifiabilityCriterion
        discovery = {
            "node_id": "disc_1",
            "metadata": {
                "falsifiability_criteria": [
                    FalsifiabilityCriterion(statement="S", measurement="M", threshold="T")
                ]
            },
        }
        mock_kg.set_node_return(discovery)
        exp = tracker.create_experiment("disc_1", "Test")
        assert len(exp.falsifiability_criteria) == 1

    def test_empty_criteria(self, tracker, mock_kg):
        discovery = {"node_id": "disc_1", "metadata": {}}
        mock_kg.set_node_return(discovery)
        exp = tracker.create_experiment("disc_1", "Test")
        assert exp.falsifiability_criteria == []


class TestStartExperiment:
    def test_success(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        exp = tracker.create_experiment("disc_1", "Test")
        result = tracker.start_experiment(exp.id)
        assert result.status == ExperimentStatus.RUNNING
        assert result.started_at is not None

    def test_not_found(self, tracker):
        with pytest.raises(ValueError, match="Experiment missing not found"):
            tracker.start_experiment("missing")


class TestAddObservation:
    def test_success(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        exp = tracker.create_experiment("disc_1", "Test")
        obs = tracker.add_observation(exp.id, 3.14, "meters", {"loc": "lab"}, "good")
        assert obs.value == 3.14
        assert obs.unit == "meters"
        assert obs.context == {"loc": "lab"}
        assert obs.notes == "good"
        assert len(exp.observations) == 1

    def test_default_context(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        exp = tracker.create_experiment("disc_1", "Test")
        obs = tracker.add_observation(exp.id, 1.0, "kg")
        assert obs.context == {}

    def test_not_found(self, tracker):
        with pytest.raises(ValueError, match="Experiment missing not found"):
            tracker.add_observation("missing", 1.0, "kg")


class TestConcludeExperiment:
    def test_validated(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        exp = tracker.create_experiment("disc_1", "Test")
        result = tracker.conclude_experiment(exp.id, "validated", "It works", 0.5)
        assert exp.status == ExperimentStatus.VALIDATED
        assert result["outcome"] == "validated"
        assert result["new_confidence"] > result["old_confidence"]
        assert result["delta"] > 0

    def test_falsified(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        exp = tracker.create_experiment("disc_1", "Test")
        result = tracker.conclude_experiment(exp.id, "falsified", "It fails", 0.5)
        assert exp.status == ExperimentStatus.FALSIFIED
        assert result["new_confidence"] < result["old_confidence"]
        assert result["delta"] < 0

    def test_inconclusive(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        exp = tracker.create_experiment("disc_1", "Test")
        result = tracker.conclude_experiment(exp.id, "inconclusive", "Unclear")
        assert exp.status == ExperimentStatus.INCONCLUSIVE
        assert result["new_confidence"] == result["old_confidence"]
        assert result["delta"] == 0.0

    def test_exp_not_found(self, tracker):
        with pytest.raises(ValueError, match="Experiment missing not found"):
            tracker.conclude_experiment("missing", "validated")

    def test_discovery_not_found(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        exp = tracker.create_experiment("disc_1", "Test")
        mock_kg.set_node_return(None)
        with pytest.raises(ValueError, match="Discovery disc_1 not found"):
            tracker.conclude_experiment(exp.id, "validated")

    def test_updates_kg(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        exp = tracker.create_experiment("disc_1", "Test")
        tracker.conclude_experiment(exp.id, "validated", strength=0.5)
        assert mock_kg.graph.nodes["disc_1"]["metadata"]["confidence_score"] > 0.5
        assert mock_kg.graph.nodes["disc_1"]["metadata"]["status"] == "validated"

    def test_saves_calibration(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        exp = tracker.create_experiment("disc_1", "Test")
        prev = len(tracker.calibration.predictions)
        tracker.conclude_experiment(exp.id, "validated")
        assert len(tracker.calibration.predictions) == prev + 1


class TestUpdateExperimentNode:
    def test_updates_existing(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        exp = tracker.create_experiment("disc_1", "Test")
        tracker.start_experiment(exp.id)
        assert "experiment_1" in mock_kg.graph.nodes

    def test_skips_missing(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.has_node = lambda node_id: False
        exp = tracker.create_experiment("disc_1", "Test")
        tracker._update_experiment_node(exp)


class TestGetExperimentsForDiscovery:
    def test_filter(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        e1 = tracker.create_experiment("disc_1", "Test 1")
        e2 = tracker.create_experiment("disc_1", "Test 2")
        assert len(tracker.get_experiments_for_discovery("disc_1")) == 2
        assert e1 in tracker.get_experiments_for_discovery("disc_1")

    def test_empty(self, tracker):
        assert tracker.get_experiments_for_discovery("disc_x") == []


class TestGetValidationRate:
    def test_empty(self, tracker):
        assert tracker.get_validation_rate() == 0.0
        assert tracker.get_validation_rate("disc_1") == 0.0

    def test_all_validated(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        e1 = tracker.create_experiment("disc_1", "Test 1")
        e2 = tracker.create_experiment("disc_1", "Test 2")
        tracker.conclude_experiment(e1.id, "validated")
        tracker.conclude_experiment(e2.id, "validated")
        assert tracker.get_validation_rate("disc_1") == 1.0
        assert tracker.get_validation_rate() == 1.0

    def test_mixed(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        e1 = tracker.create_experiment("disc_1", "Test 1")
        e2 = tracker.create_experiment("disc_1", "Test 2")
        tracker.conclude_experiment(e1.id, "validated")
        tracker.conclude_experiment(e2.id, "falsified")
        assert tracker.get_validation_rate("disc_1") == 0.5

    def test_ignores_inconclusive(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        e1 = tracker.create_experiment("disc_1", "Test 1")
        tracker.conclude_experiment(e1.id, "inconclusive")
        assert tracker.get_validation_rate("disc_1") == 0.0


class TestGetValidationSummary:
    def test_empty(self, tracker):
        summary = tracker.get_validation_summary()
        assert summary["total_experiments"] == 0
        assert summary["by_status"] == {}
        assert summary["validation_rate"] == 0.0
        assert "brier_score" in summary["calibration"]

    def test_with_experiments(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        tracker.create_experiment("disc_1", "Test 1")
        e2 = tracker.create_experiment("disc_1", "Test 2")
        tracker.start_experiment(e2.id)
        summary = tracker.get_validation_summary()
        assert summary["total_experiments"] == 2
        assert summary["by_status"]["design"] == 1
        assert summary["by_status"]["running"] == 1

    def test_after_conclusion(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        e1 = tracker.create_experiment("disc_1", "Test 1")
        tracker.conclude_experiment(e1.id, "validated")
        summary = tracker.get_validation_summary()
        assert summary["by_status"]["validated"] == 1
        assert summary["validation_rate"] == 1.0


class TestGetValidationTracker:
    def test_singleton(self, mock_kg):
        with patch("src.validation.rules.get_knowledge_graph", return_value=mock_kg):
            vt1 = get_validation_tracker()
            vt2 = get_validation_tracker()
        assert vt1 is vt2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
