"""
Comprehensive tests for src/validation/core.py, consensus_meter.py, empirical_layer.py

Covers: validation rules, consensus meter, empirical layer,
        Bayesian updating, calibration tracking, experiment lifecycle
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Prevent validation/__init__.py from importing heavy deps that fail
import types


_fake_agents = types.ModuleType('agents')
_fake_pipeline = types.ModuleType('pipeline')
_fake_pipeline.UniversalSolvePipeline = object
sys.modules['src.agents'] = _fake_agents
sys.modules['src.agents.pipeline'] = _fake_pipeline

_fake_complexity = types.ModuleType('complexity_adapter')
class _FakeLevel:
    LITE = 'lite'
    ADVANCED = 'advanced'
    EXPERT = 'expert'
_fake_complexity.ComplexityLevel = _FakeLevel
_fake_complexity.get_config = lambda x: MagicMock(show_operators=True, model_dump=lambda: {})
sys.modules['src.core.complexity_adapter'] = _fake_complexity

from src.validation.consensus_meter import (
    ConsensusMeter,
    ConsensusScore,
    Evidence,
    EvidenceStrength,
    EvidenceType,
    get_consensus_meter,
)
from src.validation.core import (
    BayesianUpdater,
    CalibrationTracker,
    Experiment,
    ExperimentStatus,
    FalsifiabilityCriterion,
    Observation,
)
from src.validation.empirical_layer import (
    BenchmarkType,
    EmpiricalLayer,
    EmpiricalResult,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def bayesian():
    return BayesianUpdater()


@pytest.fixture
def temp_calibration_file(tmp_path: Path):
    return tmp_path / "calibration.json"


@pytest.fixture
def calibration(temp_calibration_file):
    return CalibrationTracker(str(temp_calibration_file))


@pytest.fixture
def consensus_meter():
    return ConsensusMeter()


@pytest.fixture
def sample_evidence():
    return [
        Evidence(
            source="Study A",
            type=EvidenceType.SUPPORTING,
            strength=EvidenceStrength.STRONG,
            description="Strong evidence",
            citation_count=100,
            year=2023,
            peer_reviewed=True,
            sample_size=500,
        ),
        Evidence(
            source="Study B",
            type=EvidenceType.CONTRADICTING,
            strength=EvidenceStrength.MODERATE,
            description="Contradictory evidence",
            citation_count=20,
            year=2019,
            peer_reviewed=True,
            sample_size=50,
        ),
        Evidence(
            source="Study C",
            type=EvidenceType.NEUTRAL,
            strength=EvidenceStrength.WEAK,
            description="Neutral observation",
            citation_count=0,
            year=2021,
            peer_reviewed=False,
        ),
    ]


# ═══════════════════════════════════════════════════════════════════
# FalsifiabilityCriterion
# ═══════════════════════════════════════════════════════════════════


class TestFalsifiabilityCriterion:
    def test_creation(self):
        fc = FalsifiabilityCriterion(
            statement="If X > 10, hypothesis is false",
            measurement="Measure X",
            threshold="10",
            experiment_type="controlled",
            difficulty="hard",
        )
        assert fc.statement == "If X > 10, hypothesis is false"
        assert fc.difficulty == "hard"

    def test_to_dict(self):
        fc = FalsifiabilityCriterion(
            statement="S", measurement="M", threshold="T"
        )
        d = fc.to_dict()
        assert d["statement"] == "S"
        assert d["difficulty"] == "medium"
        assert d["experiment_type"] is None

    def test_defaults(self):
        fc = FalsifiabilityCriterion(statement="S", measurement="M", threshold="T")
        assert fc.experiment_type is None
        assert fc.difficulty == "medium"


# ═══════════════════════════════════════════════════════════════════
# Observation
# ═══════════════════════════════════════════════════════════════════


class TestObservation:
    def test_creation(self):
        obs = Observation(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            value=42.0,
            unit="meters",
            context={"location": "lab"},
            notes="Test note",
        )
        assert obs.value == 42.0
        assert obs.unit == "meters"

    def test_to_dict(self):
        obs = Observation(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            value=42.0,
            unit="m",
        )
        d = obs.to_dict()
        assert d["value"] == 42.0
        assert d["unit"] == "m"
        assert "2024-01-01" in d["timestamp"]


# ═══════════════════════════════════════════════════════════════════
# Experiment
# ═══════════════════════════════════════════════════════════════════


class TestExperiment:
    def test_creation(self):
        exp = Experiment(
            id="exp_1",
            discovery_id="disc_1",
            name="Test Experiment",
        )
        assert exp.id == "exp_1"
        assert exp.status == ExperimentStatus.DESIGN
        assert len(exp.observations) == 0
        assert exp.confidence_delta == 0.0

    def test_with_criteria(self):
        fc = FalsifiabilityCriterion(statement="S", measurement="M", threshold="T")
        exp = Experiment(
            id="exp_1",
            discovery_id="disc_1",
            name="Test",
            falsifiability_criteria=[fc],
        )
        assert len(exp.falsifiability_criteria) == 1

    def test_to_dict(self):
        exp = Experiment(id="e1", discovery_id="d1", name="Test")
        d = exp.to_dict()
        assert d["id"] == "e1"
        assert d["status"] == "design"
        assert d["started_at"] is None

    def test_status_transitions(self):
        exp = Experiment(id="e1", discovery_id="d1", name="Test")
        assert exp.status == ExperimentStatus.DESIGN

        exp.status = ExperimentStatus.RUNNING
        assert exp.status == ExperimentStatus.RUNNING

        exp.status = ExperimentStatus.VALIDATED
        assert exp.status == ExperimentStatus.VALIDATED

    def test_all_statuses_exist(self):
        statuses = list(ExperimentStatus)
        expected = [
            "design", "ready", "running", "analyzing",
            "validated", "falsified", "inconclusive", "cancelled",
        ]
        assert sorted([s.value for s in statuses]) == sorted(expected)


# ═══════════════════════════════════════════════════════════════════
# BayesianUpdater
# ═══════════════════════════════════════════════════════════════════


class TestBayesianUpdater:
    def test_update_validated_increases(self, bayesian):
        prior = 0.5
        posterior = bayesian.update_from_outcome(prior, "validated", strength=0.5)
        assert posterior > prior
        assert posterior == pytest.approx(0.75)

    def test_update_falsified_decreases(self, bayesian):
        prior = 0.8
        posterior = bayesian.update_from_outcome(prior, "falsified", strength=0.5)
        assert posterior < prior
        assert posterior == pytest.approx(0.4)

    def test_bayes_theorem_calculation(self, bayesian):
        prior = 0.5
        likelihood = 0.9
        fpr = 0.1
        posterior = bayesian.update(prior, likelihood, fpr)
        expected = (0.9 * 0.5) / (0.9 * 0.5 + 0.1 * 0.5)
        assert posterior == pytest.approx(expected, 0.01)

    def test_extreme_priors_unchanged(self, bayesian):
        assert bayesian.update(0.0, 0.9, 0.1) == 0.0
        assert bayesian.update(1.0, 0.9, 0.1) == 1.0

    def test_update_clamps_to_1(self, bayesian):
        result = bayesian.update_from_outcome(0.9, "validated", strength=0.9)
        assert result <= 1.0

    def test_update_clamps_to_0(self, bayesian):
        result = bayesian.update_from_outcome(0.1, "falsified", strength=0.9)
        assert result >= 0.0

    def test_zero_evidence_prob(self, bayesian):
        result = bayesian.update(0.5, 0.0, 0.0)
        assert result == 0.5


# ═══════════════════════════════════════════════════════════════════
# CalibrationTracker
# ═══════════════════════════════════════════════════════════════════


class TestCalibrationTracker:
    def test_empty_brier_score(self, calibration):
        assert calibration.brier_score() == 0.0

    def test_empty_calibration_curve(self, calibration):
        assert calibration.calibration_curve() == []

    def test_empty_status(self, calibration):
        assert "Insufficient" in calibration.get_calibration_status()

    def test_record_and_brier(self, calibration):
        for _ in range(8):
            calibration.record(0.8, True)
        for _ in range(2):
            calibration.record(0.8, False)
        brier = calibration.brier_score()
        assert brier < 0.2

    def test_overconfident_brier(self, calibration):
        for _ in range(10):
            calibration.record(0.9, True)
        for _ in range(10):
            calibration.record(0.9, False)
        brier = calibration.brier_score()
        assert brier > 0.15

    def test_calibration_curve(self, calibration):
        for conf in [0.5, 0.6, 0.7, 0.8, 0.9]:
            calibration.record(conf, True)
        curve = calibration.calibration_curve(bins=5)
        assert len(curve) > 0
        for point in curve:
            assert "confidence_bin" in point
            assert "actual_frequency" in point
            assert "count" in point

    def test_well_calibrated_status(self, calibration):
        for _ in range(50):
            calibration.record(0.8, True)
        status = calibration.get_calibration_status()
        assert "Well calibrated" in status or "Moderately" in status

    def test_save_and_load(self, temp_calibration_file):
        tracker1 = CalibrationTracker(str(temp_calibration_file))
        tracker1.record(0.7, True)
        tracker1.record(0.7, False)

        tracker2 = CalibrationTracker(str(temp_calibration_file))
        assert len(tracker2.predictions) == 2
        assert tracker2.brier_score() == tracker1.brier_score()

    def test_corrupt_file_handling(self, temp_calibration_file):
        temp_calibration_file.write_text("not json")
        tracker = CalibrationTracker(str(temp_calibration_file))
        assert tracker.predictions == []


# ═══════════════════════════════════════════════════════════════════
# ConsensusMeter
# ═══════════════════════════════════════════════════════════════════


class TestConsensusMeter:
    def test_calculate_consensus_basic(self, consensus_meter, sample_evidence):
        score = consensus_meter.calculate_consensus("h1", "Test hypothesis", sample_evidence)
        assert isinstance(score, ConsensusScore)
        assert score.supporting_count == 1
        assert score.contradicting_count == 1
        assert score.neutral_count == 1
        assert score.total_count == 3

    def test_consensus_levels(self, consensus_meter):
        for level_name, (min_val, max_val, label) in ConsensusMeter.CONSENSUS_LEVELS.items():
            assert min_val <= max_val
            assert isinstance(label, str)

    def test_strong_consensus(self, consensus_meter):
        evidence = [
            Evidence(
                source="S1", type=EvidenceType.SUPPORTING,
                strength=EvidenceStrength.STRONG, description="D1",
                citation_count=200, year=2023, peer_reviewed=True, sample_size=1000,
            ),
            Evidence(
                source="S2", type=EvidenceType.SUPPORTING,
                strength=EvidenceStrength.STRONG, description="D2",
                citation_count=150, year=2022, peer_reviewed=True, sample_size=800,
            ),
        ]
        score = consensus_meter.calculate_consensus("h1", "H", evidence)
        assert score.consensus_level == "strong"
        assert score.supporting_score > score.contradicting_score

    def test_contested_consensus(self, consensus_meter):
        evidence = [
            Evidence(
                source="S1", type=EvidenceType.SUPPORTING,
                strength=EvidenceStrength.STRONG, description="D1",
            ),
            Evidence(
                source="S2", type=EvidenceType.CONTRADICTING,
                strength=EvidenceStrength.STRONG, description="D2",
            ),
        ]
        score = consensus_meter.calculate_consensus("h1", "H", evidence)
        assert score.consensus_level in ["contested", "none", "weak"]

    def test_empty_evidence(self, consensus_meter):
        score = consensus_meter.calculate_consensus("h1", "H", [])
        assert score.supporting_count == 0
        assert score.contradicting_count == 0
        assert score.total_count == 0
        assert score.supporting_score == 0
        assert score.contradicting_score == 0

    def test_render_consensus_bar(self, consensus_meter, sample_evidence):
        score = consensus_meter.calculate_consensus("h1", "H", sample_evidence)
        bar = consensus_meter.render_consensus_bar(score, width=50)
        assert "[" in bar
        assert "]" in bar

    def test_render_rich_meter(self, consensus_meter, sample_evidence):
        score = consensus_meter.calculate_consensus("h1", "H", sample_evidence)
        rich = consensus_meter.render_rich_meter(score)
        assert "Confidence:" in rich

    def test_generate_summary_text(self, consensus_meter):
        for level in ["strong", "moderate", "weak", "none", "contested"]:
            score = MagicMock()
            score.consensus_level = level
            score.confidence_score = 50.0
            score.supporting_count = 5
            score.contradicting_count = 2
            text = consensus_meter.generate_summary_text(score)
            assert len(text) > 0

    def test_extract_evidence_from_papers(self, consensus_meter):
        papers = [
            {
                "paper": MagicMock(
                    title="Test Paper",
                    abstract="This supports the hypothesis about gravity",
                    citation_count=100,
                    year=2023,
                ),
            }
        ]
        evidence = consensus_meter.extract_evidence_from_papers(papers, "gravity hypothesis")
        assert len(evidence) >= 1

    def test_singleton(self):
        m1 = get_consensus_meter()
        m2 = get_consensus_meter()
        assert m1 is m2


# ═══════════════════════════════════════════════════════════════════
# EmpiricalLayer
# ═══════════════════════════════════════════════════════════════════


class TestEmpiricalLayer:
    @pytest.fixture
    def layer(self):
        with patch("src.validation.empirical_layer.UniversalSolvePipeline") as mock_pipeline, \
             patch("src.validation.empirical_layer.ValidationTracker") as mock_tracker:
            mock_pipeline.return_value = MagicMock()
            mock_tracker.return_value = MagicMock()
            mock_tracker.return_value.record_empirical = AsyncMock()
            return EmpiricalLayer()

    def test_init(self, layer):
        assert layer.benchmarks is not None
        assert "einstein_relativity" in layer.benchmarks
        assert "cross_domain_innovation" in layer.benchmarks

    def test_benchmarks_structure(self, layer):
        for bid, bm in layer.benchmarks.items():
            assert "type" in bm
            assert "problem" in bm
            assert "theoretical_max_steps" in bm
            assert isinstance(bm["type"], BenchmarkType)

    def test_get_metrics(self, layer):
        metrics = layer.get_metrics()
        assert "avg_reachability" in metrics
        assert "mean_cognitive_savings" in metrics
        assert "phi_convergence_rate" in metrics
        assert 0.0 <= metrics["avg_reachability"] <= 1.0

    @pytest.mark.anyio(backend="asyncio")
    async def test_run_benchmark_invalid_id_defaults(self, layer):
        with patch.object(
            layer.pipeline, "run", new_callable=AsyncMock
        ) as mock_run:
            mock_result = MagicMock()
            mock_result.steps = [1, 2, 3]
            mock_result.confidence = 0.9
            mock_run.return_value = mock_result

            result = await layer.run_benchmark("nonexistent")
            assert result.benchmark_id == "einstein_relativity"

    @pytest.mark.anyio(backend="asyncio")
    async def test_run_suite(self, layer):
        with patch.object(
            layer.pipeline, "run", new_callable=AsyncMock
        ) as mock_run:
            mock_result = MagicMock()
            mock_result.steps = [1, 2]
            mock_result.confidence = 0.85
            mock_run.return_value = mock_result

            results = await layer.run_suite()
            assert len(results) == len(layer.benchmarks)
            for r in results:
                assert isinstance(r, EmpiricalResult)


# ═══════════════════════════════════════════════════════════════════
# EmpiricalResult
# ═══════════════════════════════════════════════════════════════════


class TestEmpiricalResult:
    def test_creation(self):
        from src.core.complexity_adapter import ComplexityLevel
        result = EmpiricalResult(
            benchmark_id="test",
            benchmark_type=BenchmarkType.EINSTEIN_TEST,
            theoretical_steps=6,
            actual_steps=4,
            reachability_score=0.95,
            confidence=0.9,
            p_value=0.01,
            cognitive_savings=0.4,
            phi_attractor_converged=True,
            level=ComplexityLevel.LITE,
            timestamp=datetime.now().isoformat(),
            metadata={},
        )
        assert result.benchmark_id == "test"
        assert result.phi_attractor_converged is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
