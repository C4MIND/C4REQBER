"""
Comprehensive tests for src/validation/rules.py

Covers: ValidationTracker experiment lifecycle, get_validation_rate,
        get_validation_summary, get_validation_tracker singleton,
        edge cases with mocked KnowledgeGraph and hypothesis objects.
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

# Prevent validation/__init__.py from importing heavy deps that fail
import types


_fake_agents = types.ModuleType("agents")
_fake_pipeline = types.ModuleType("pipeline")
_fake_pipeline.UniversalSolvePipeline = object
sys.modules["src.agents"] = _fake_agents
sys.modules["src.agents.pipeline"] = _fake_pipeline

_fake_complexity = types.ModuleType("complexity_adapter")


class _FakeLevel:
    LITE = "lite"
    ADVANCED = "advanced"
    EXPERT = "expert"


_fake_complexity.ComplexityLevel = _FakeLevel
_fake_complexity.get_config = lambda x: MagicMock(
    show_operators=True, model_dump=lambda: {}
)
sys.modules["src.core.complexity_adapter"] = _fake_complexity

from src.validation.core import (
    BayesianUpdater,
    CalibrationTracker,
    Experiment,
    ExperimentStatus,
    FalsifiabilityCriterion,
    Observation,
)
from src.validation.rules import ValidationTracker, get_validation_tracker


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


class MockKnowledgeGraph:
    """Custom mock that behaves like a real KnowledgeGraph for node dict ops."""

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
    """Return a fully mocked KnowledgeGraph."""
    return MockKnowledgeGraph()


@pytest.fixture
def tracker(mock_kg):
    """Return a ValidationTracker with mocked KG (no pre-loaded experiments)."""
    with patch(
        "src.validation.rules.get_knowledge_graph", return_value=mock_kg
    ):
        vt = ValidationTracker()
        vt._experiments.clear()
        return vt


@pytest.fixture
def sample_discovery():
    """Return a mocked discovery node (hypothesis) as stored in KG."""
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


@pytest.fixture
def sample_experiment_node():
    """Return a mocked experiment node as stored in KG."""
    return {
        "node_id": "experiment_1",
        "node_type": "experiment",
        "created_at": datetime(2024, 1, 1, 12, 0, 0).isoformat(),
        "metadata": {
            "discovery_id": "disc_1",
            "name": "Test Experiment",
            "description": "A test",
            "status": "design",
            "falsifiability_criteria": [],
            "observations": [],
            "expected_observations": 1,
            "researcher": "Alice",
            "tags": ["tag1"],
        },
    }


# ═══════════════════════════════════════════════════════════════════
# ValidationTracker — creation & loading
# ═══════════════════════════════════════════════════════════════════


class TestValidationTrackerCreation:
    def test_init_creates_empty_tracker(self, mock_kg):
        with patch(
            "src.validation.rules.get_knowledge_graph", return_value=mock_kg
        ):
            vt = ValidationTracker()
        assert vt._experiments == {}
        assert isinstance(vt.calibration, CalibrationTracker)
        assert isinstance(vt.bayesian, BayesianUpdater)

    def test_init_loads_existing_experiments(self, mock_kg, sample_experiment_node):
        mock_kg._nodes_by_type = [sample_experiment_node]
        with patch(
            "src.validation.rules.get_knowledge_graph", return_value=mock_kg
        ):
            vt = ValidationTracker()
        assert "experiment_1" in vt._experiments
        exp = vt._experiments["experiment_1"]
        assert exp.name == "Test Experiment"
        assert exp.discovery_id == "disc_1"
        assert exp.status == ExperimentStatus.DESIGN

    def test_init_loads_experiment_with_observations(self, mock_kg):
        node = {
            "node_id": "exp_obs",
            "node_type": "experiment",
            "created_at": datetime(2024, 1, 1).isoformat(),
            "metadata": {
                "discovery_id": "d1",
                "name": "Obs Exp",
                "status": "running",
                "falsifiability_criteria": [],
                "observations": [
                    {
                        "timestamp": datetime(2024, 1, 2).isoformat(),
                        "value": 42.0,
                        "unit": "m",
                        "context": {"loc": "lab"},
                        "notes": "note",
                    }
                ],
                "expected_observations": 3,
                "started_at": datetime(2024, 1, 1, 10, 0, 0).isoformat(),
            },
        }
        mock_kg._nodes_by_type = [node]
        with patch(
            "src.validation.rules.get_knowledge_graph", return_value=mock_kg
        ):
            vt = ValidationTracker()
        exp = vt._experiments["exp_obs"]
        assert len(exp.observations) == 1
        assert exp.observations[0].value == 42.0
        assert exp.observations[0].unit == "m"
        assert exp.started_at is not None


# ═══════════════════════════════════════════════════════════════════
# create_experiment
# ═══════════════════════════════════════════════════════════════════


class TestCreateExperiment:
    def test_create_experiment_success(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        exp = tracker.create_experiment(
            discovery_id="disc_1",
            name="Gravity Test",
            description="Testing gravity",
            researcher="Alice",
        )
        assert isinstance(exp, Experiment)
        assert exp.discovery_id == "disc_1"
        assert exp.name == "Gravity Test"
        assert exp.description == "Testing gravity"
        assert exp.researcher == "Alice"
        assert exp.status == ExperimentStatus.DESIGN
        assert exp.id == "experiment_1"
        assert exp in tracker._experiments.values()

    def test_create_experiment_increments_id(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        e1 = tracker.create_experiment("disc_1", "First")
        e2 = tracker.create_experiment("disc_1", "Second")
        assert e1.id == "experiment_1"
        assert e2.id == "experiment_2"

    def test_create_experiment_raises_when_discovery_missing(self, tracker, mock_kg):
        mock_kg.set_node_return(None)
        with pytest.raises(ValueError, match="Discovery disc_missing not found"):
            tracker.create_experiment("disc_missing", "Test")

    def test_create_experiment_with_criteria(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        exp = tracker.create_experiment("disc_1", "Test")
        assert len(exp.falsifiability_criteria) == 1
        assert exp.falsifiability_criteria[0].statement == "If X > 10, hypothesis is false"

    def test_create_experiment_copies_criteria_from_discovery(self, tracker, mock_kg):
        discovery = {
            "node_id": "disc_2",
            "metadata": {
                "falsifiability_criteria": [
                    {"statement": "S1", "measurement": "M1", "threshold": "T1"},
                    {"statement": "S2", "measurement": "M2", "threshold": "T2"},
                ]
            },
        }
        mock_kg.set_node_return(discovery)
        exp = tracker.create_experiment("disc_2", "Test")
        assert len(exp.falsifiability_criteria) == 2

    def test_create_experiment_adds_kg_node_and_edge(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        tracker.create_experiment("disc_1", "Test")
        assert "experiment_1" in mock_kg._nodes

    def test_create_experiment_empty_criteria(self, tracker, mock_kg):
        discovery = {"node_id": "disc_1", "metadata": {}}
        mock_kg.set_node_return(discovery)
        exp = tracker.create_experiment("disc_1", "Test")
        assert exp.falsifiability_criteria == []


# ═══════════════════════════════════════════════════════════════════
# start_experiment
# ═══════════════════════════════════════════════════════════════════


class TestStartExperiment:
    def test_start_experiment(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        exp = tracker.create_experiment("disc_1", "Test")
        result = tracker.start_experiment(exp.id)
        assert result.status == ExperimentStatus.RUNNING
        assert result.started_at is not None

    def test_start_experiment_not_found(self, tracker):
        with pytest.raises(ValueError, match="Experiment nonexistent not found"):
            tracker.start_experiment("nonexistent")


# ═══════════════════════════════════════════════════════════════════
# add_observation
# ═══════════════════════════════════════════════════════════════════


class TestAddObservation:
    def test_add_observation(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        exp = tracker.create_experiment("disc_1", "Test")
        obs = tracker.add_observation(
            exp.id, value=3.14, unit="meters", context={"loc": "lab"}, notes="good"
        )
        assert isinstance(obs, Observation)
        assert obs.value == 3.14
        assert obs.unit == "meters"
        assert obs.context == {"loc": "lab"}
        assert obs.notes == "good"
        assert len(exp.observations) == 1

    def test_add_observation_default_context(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        exp = tracker.create_experiment("disc_1", "Test")
        obs = tracker.add_observation(exp.id, value=1.0, unit="kg")
        assert obs.context == {}

    def test_add_observation_not_found(self, tracker):
        with pytest.raises(ValueError, match="Experiment missing not found"):
            tracker.add_observation("missing", 1.0, "kg")


# ═══════════════════════════════════════════════════════════════════
# conclude_experiment
# ═══════════════════════════════════════════════════════════════════


class TestConcludeExperiment:
    def test_conclude_validated(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        exp = tracker.create_experiment("disc_1", "Test")
        result = tracker.conclude_experiment(
            exp.id, outcome="validated", conclusion="It works", strength=0.5
        )
        assert exp.status == ExperimentStatus.VALIDATED
        assert exp.conclusion == "It works"
        assert exp.completed_at is not None
        assert result["outcome"] == "validated"
        assert result["old_confidence"] == 0.5
        assert result["new_confidence"] > result["old_confidence"]
        assert result["delta"] > 0

    def test_conclude_falsified(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        exp = tracker.create_experiment("disc_1", "Test")
        result = tracker.conclude_experiment(
            exp.id, outcome="falsified", conclusion="It fails", strength=0.5
        )
        assert exp.status == ExperimentStatus.FALSIFIED
        assert result["new_confidence"] < result["old_confidence"]
        assert result["delta"] < 0

    def test_conclude_inconclusive(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        exp = tracker.create_experiment("disc_1", "Test")
        result = tracker.conclude_experiment(
            exp.id, outcome="inconclusive", conclusion="Unclear"
        )
        assert exp.status == ExperimentStatus.INCONCLUSIVE
        assert result["new_confidence"] == result["old_confidence"]
        assert result["delta"] == 0.0

    def test_conclude_experiment_not_found(self, tracker):
        with pytest.raises(ValueError, match="Experiment missing not found"):
            tracker.conclude_experiment("missing", "validated")

    def test_conclude_discovery_not_found(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        exp = tracker.create_experiment("disc_1", "Test")
        mock_kg.set_node_return(None)
        with pytest.raises(ValueError, match="Discovery disc_1 not found"):
            tracker.conclude_experiment(exp.id, "validated")

    def test_conclude_updates_kg_confidence(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        exp = tracker.create_experiment("disc_1", "Test")
        tracker.conclude_experiment(exp.id, "validated", strength=0.5)
        assert mock_kg.graph.nodes["disc_1"]["metadata"]["confidence_score"] > 0.5
        assert mock_kg.graph.nodes["disc_1"]["metadata"]["status"] == "validated"

    def test_conclude_saves_kg_and_calibration(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        exp = tracker.create_experiment("disc_1", "Test")
        prev_count = len(tracker.calibration.predictions)
        tracker.conclude_experiment(exp.id, "validated")
        # Calibration save is also triggered
        assert len(tracker.calibration.predictions) == prev_count + 1


# ═══════════════════════════════════════════════════════════════════
# get_experiments_for_discovery
# ═══════════════════════════════════════════════════════════════════


class TestGetExperimentsForDiscovery:
    def test_filter_by_discovery(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        e1 = tracker.create_experiment("disc_1", "Test 1")
        e2 = tracker.create_experiment("disc_1", "Test 2")
        results = tracker.get_experiments_for_discovery("disc_1")
        assert len(results) == 2
        assert e1 in results
        assert e2 in results

    def test_no_experiments_for_discovery(self, tracker):
        assert tracker.get_experiments_for_discovery("disc_x") == []

    def test_different_discoveries(self, tracker, mock_kg):
        disc1 = {"node_id": "disc_1", "metadata": {}}
        disc2 = {"node_id": "disc_2", "metadata": {}}
        mock_kg.set_node_return(disc1)
        tracker.create_experiment("disc_1", "Test A")
        mock_kg.set_node_return(disc2)
        tracker.create_experiment("disc_2", "Test B")
        assert len(tracker.get_experiments_for_discovery("disc_1")) == 1
        assert len(tracker.get_experiments_for_discovery("disc_2")) == 1


# ═══════════════════════════════════════════════════════════════════
# get_validation_rate
# ═══════════════════════════════════════════════════════════════════


class TestGetValidationRate:
    def test_empty_returns_zero(self, tracker):
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

    def test_all_falsified(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        e1 = tracker.create_experiment("disc_1", "Test 1")
        tracker.conclude_experiment(e1.id, "falsified")
        assert tracker.get_validation_rate("disc_1") == 0.0

    def test_mixed_outcomes(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        e1 = tracker.create_experiment("disc_1", "Test 1")
        e2 = tracker.create_experiment("disc_1", "Test 2")
        tracker.conclude_experiment(e1.id, "validated")
        tracker.conclude_experiment(e2.id, "falsified")
        assert tracker.get_validation_rate("disc_1") == 0.5

    def test_ignores_non_concluded(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        tracker.create_experiment("disc_1", "Test 1")
        tracker.create_experiment("disc_1", "Test 2")
        assert tracker.get_validation_rate("disc_1") == 0.0

    def test_ignores_running_and_inconclusive(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        e1 = tracker.create_experiment("disc_1", "Test 1")
        e2 = tracker.create_experiment("disc_1", "Test 2")
        tracker.start_experiment(e1.id)
        tracker.conclude_experiment(e2.id, "inconclusive")
        assert tracker.get_validation_rate("disc_1") == 0.0


# ═══════════════════════════════════════════════════════════════════
# get_validation_summary
# ═══════════════════════════════════════════════════════════════════


class TestGetValidationSummary:
    def test_empty_summary(self, tracker):
        summary = tracker.get_validation_summary()
        assert summary["total_experiments"] == 0
        assert summary["by_status"] == {}
        assert summary["validation_rate"] == 0.0
        assert "brier_score" in summary["calibration"]
        assert summary["calibration"]["total_predictions"] >= 0

    def test_summary_with_experiments(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        tracker.create_experiment("disc_1", "Test 1")
        e2 = tracker.create_experiment("disc_1", "Test 2")
        tracker.start_experiment(e2.id)
        summary = tracker.get_validation_summary()
        assert summary["total_experiments"] == 2
        assert summary["by_status"]["design"] == 1
        assert summary["by_status"]["running"] == 1
        assert summary["validation_rate"] == 0.0

    def test_summary_after_conclusion(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        e1 = tracker.create_experiment("disc_1", "Test 1")
        prev_count = len(tracker.calibration.predictions)
        tracker.conclude_experiment(e1.id, "validated")
        summary = tracker.get_validation_summary()
        assert summary["by_status"]["validated"] == 1
        assert summary["validation_rate"] == 1.0
        assert summary["calibration"]["total_predictions"] == prev_count + 1


# ═══════════════════════════════════════════════════════════════════
# _update_experiment_node
# ═══════════════════════════════════════════════════════════════════


class TestUpdateExperimentNode:
    def test_updates_existing_node(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        exp = tracker.create_experiment("disc_1", "Test")
        tracker.start_experiment(exp.id)
        # Node should have been updated in the mocked graph
        assert "experiment_1" in mock_kg.graph.nodes

    def test_skips_when_node_missing(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.has_node = lambda node_id: False
        exp = tracker.create_experiment("disc_1", "Test")
        tracker._update_experiment_node(exp)
        # No exception, and graph.nodes should not be accessed


# ═══════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════


class TestGetValidationTracker:
    def test_returns_singleton(self, mock_kg):
        with patch(
            "src.validation.rules.get_knowledge_graph", return_value=mock_kg
        ):
            vt1 = get_validation_tracker()
            vt2 = get_validation_tracker()
        assert vt1 is vt2

    def test_singleton_is_validation_tracker(self, mock_kg):
        with patch(
            "src.validation.rules.get_knowledge_graph", return_value=mock_kg
        ):
            vt = get_validation_tracker()
        assert isinstance(vt, ValidationTracker)


# ═══════════════════════════════════════════════════════════════════
# Edge cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_create_experiment_with_empty_strings(self, tracker, mock_kg):
        discovery = {"node_id": "disc_1", "metadata": {}}
        mock_kg.set_node_return(discovery)
        exp = tracker.create_experiment("disc_1", "", description="", researcher="")
        assert exp.name == ""
        assert exp.description == ""
        assert exp.researcher == ""

    def test_node_to_experiment_missing_optional_fields(self, tracker):
        node = {
            "node_id": "exp_min",
            "node_type": "experiment",
            "created_at": datetime(2024, 1, 1).isoformat(),
            "metadata": {
                "discovery_id": "d1",
                "name": "Minimal",
                "status": "design",
            },
        }
        exp = tracker._node_to_experiment(node)
        assert exp.id == "exp_min"
        assert exp.description == ""
        assert exp.observations == []
        assert exp.falsifiability_criteria == []
        assert exp.started_at is None
        assert exp.completed_at is None
        assert exp.conclusion is None
        assert exp.confidence_delta == 0.0
        assert exp.researcher == ""
        assert exp.tags == []

    def test_conclude_with_high_strength(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        exp = tracker.create_experiment("disc_1", "Test")
        result = tracker.conclude_experiment(exp.id, "validated", strength=0.9)
        assert result["new_confidence"] == pytest.approx(0.95)

    def test_conclude_with_low_strength(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        mock_kg.graph.nodes["disc_1"] = {"metadata": {"confidence_score": 0.5}}
        exp = tracker.create_experiment("disc_1", "Test")
        result = tracker.conclude_experiment(exp.id, "validated", strength=0.1)
        assert result["new_confidence"] == pytest.approx(0.55)

    def test_add_multiple_observations(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        exp = tracker.create_experiment("disc_1", "Test")
        tracker.add_observation(exp.id, 1.0, "m")
        tracker.add_observation(exp.id, 2.0, "m")
        tracker.add_observation(exp.id, 3.0, "m")
        assert len(exp.observations) == 3
        assert [o.value for o in exp.observations] == [1.0, 2.0, 3.0]

    def test_load_experiments_with_malformed_observation(self, tracker, mock_kg):
        node = {
            "node_id": "exp_bad",
            "node_type": "experiment",
            "created_at": datetime(2024, 1, 1).isoformat(),
            "metadata": {
                "discovery_id": "d1",
                "name": "Bad Obs",
                "status": "design",
                "observations": [
                    {
                        "timestamp": datetime(2024, 1, 2).isoformat(),
                        "value": "not_a_float",
                        "unit": "x",
                    }
                ],
            },
        }
        mock_kg._nodes_by_type = [node]
        with patch(
            "src.validation.rules.get_knowledge_graph", return_value=mock_kg
        ):
            vt = ValidationTracker()
        exp = vt._experiments["exp_bad"]
        assert len(exp.observations) == 1
        assert exp.observations[0].value == "not_a_float"

    def test_load_experiments_with_missing_created_at(self, tracker, mock_kg):
        node = {
            "node_id": "exp_no_date",
            "node_type": "experiment",
            "metadata": {
                "discovery_id": "d1",
                "name": "No Date",
                "status": "design",
            },
        }
        mock_kg._nodes_by_type = [node]
        with pytest.raises(KeyError):
            with patch(
                "src.validation.rules.get_knowledge_graph", return_value=mock_kg
            ):
                ValidationTracker()

    def test_discovery_with_non_dict_criteria(self, tracker, mock_kg):
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
        assert exp.falsifiability_criteria[0].statement == "S"

    def test_validation_rate_with_no_concluded_for_discovery(self, tracker, sample_discovery, mock_kg):
        mock_kg.set_node_return(sample_discovery)
        tracker.create_experiment("disc_1", "Test 1")
        tracker.create_experiment("disc_1", "Test 2")
        assert tracker.get_validation_rate("disc_1") == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
