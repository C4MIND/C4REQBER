"""
TURBO-CDI: Validation Tests
Tests for experiment tracking and Bayesian updating
"""

import pytest
from datetime import datetime
from src.validation.tracker import (
    BayesianUpdater,
    CalibrationTracker,
    Experiment,
    ExperimentStatus,
    FalsifiabilityCriterion,
)


class TestBayesianUpdater:
    """Test Bayesian confidence updating."""

    def test_simple_update_validated(self):
        """Test confidence increase on validation."""
        updater = BayesianUpdater()

        prior = 0.5
        new_confidence = updater.update_from_outcome(prior, "validated", strength=0.5)

        assert new_confidence > prior
        assert new_confidence == 0.75  # 0.5 + (1-0.5)*0.5

    def test_simple_update_falsified(self):
        """Test confidence decrease on falsification."""
        updater = BayesianUpdater()

        prior = 0.8
        new_confidence = updater.update_from_outcome(prior, "falsified", strength=0.5)

        assert new_confidence < prior
        assert new_confidence == 0.4  # 0.8 * (1-0.5)

    def test_bayes_theorem(self):
        """Test proper Bayesian updating."""
        updater = BayesianUpdater()

        prior = 0.5
        likelihood = 0.9  # High likelihood if hypothesis is true
        false_positive = 0.1

        posterior = updater.update(prior, likelihood, false_positive)

        # P(H|E) = P(E|H) * P(H) / P(E)
        # P(E) = 0.9*0.5 + 0.1*0.5 = 0.5
        # P(H|E) = 0.9 * 0.5 / 0.5 = 0.9
        assert pytest.approx(posterior, 0.01) == 0.9

    def test_extreme_priors(self):
        """Test handling of extreme priors."""
        updater = BayesianUpdater()

        # Prior of 0 stays 0
        assert updater.update(0.0, 0.9, 0.1) == 0.0

        # Prior of 1 stays 1
        assert updater.update(1.0, 0.9, 0.1) == 1.0


class TestCalibrationTracker:
    """Test calibration tracking."""

    def setup_method(self):
        """Set up tracker with temp file."""
        import tempfile
        import os

        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.tracker = CalibrationTracker(self.temp_file.name)

    def teardown_method(self):
        """Clean up temp file."""
        import os

        os.unlink(self.temp_file.name)

    def test_brier_score_perfect(self):
        """Test Brier score with perfect calibration."""
        # Predict 0.8, actual True (80% of the time)
        for _ in range(8):
            self.tracker.record(0.8, True)
        for _ in range(2):
            self.tracker.record(0.8, False)

        # Should be well calibrated
        brier = self.tracker.brier_score()
        assert brier < 0.1

    def test_brier_score_overconfident(self):
        """Test Brier score with overconfidence."""
        # Always predict 0.9, but only 50% correct
        for _ in range(10):
            self.tracker.record(0.9, True)
        for _ in range(10):
            self.tracker.record(0.9, False)

        # Should show poor calibration
        brier = self.tracker.brier_score()
        assert brier > 0.15  # Overconfident

    def test_calibration_curve(self):
        """Test calibration curve generation."""
        # Add some predictions
        for conf in [0.5, 0.6, 0.7, 0.8, 0.9]:
            self.tracker.record(conf, True)

        curve = self.tracker.calibration_curve(bins=5)
        assert len(curve) > 0

    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        status = self.tracker.get_calibration_status()
        assert "Insufficient" in status


class TestExperiment:
    """Test Experiment dataclass."""

    def test_experiment_creation(self):
        """Test basic experiment creation."""
        exp = Experiment(
            id="test_1",
            discovery_id="discovery_1",
            name="Test Experiment",
        )

        assert exp.id == "test_1"
        assert exp.status == ExperimentStatus.DESIGN
        assert len(exp.observations) == 0

    def test_experiment_with_criteria(self):
        """Test experiment with falsifiability criteria."""
        criterion = FalsifiabilityCriterion(
            statement="If X > 10, hypothesis is false",
            measurement="Measure X",
            threshold="10",
            difficulty="medium",
        )

        exp = Experiment(
            id="test_1",
            discovery_id="discovery_1",
            name="Test",
            falsifiability_criteria=[criterion],
        )

        assert len(exp.falsifiability_criteria) == 1
        assert exp.falsifiability_criteria[0].threshold == "10"

    def test_experiment_to_dict(self):
        """Test serialization."""
        exp = Experiment(
            id="test_1",
            discovery_id="discovery_1",
            name="Test",
        )

        data = exp.to_dict()
        assert data["id"] == "test_1"
        assert data["status"] == "design"


class TestExperimentLifecycle:
    """Test experiment state transitions."""

    def test_lifecycle_design_to_validated(self):
        """Test full lifecycle."""
        exp = Experiment(
            id="test_1",
            discovery_id="discovery_1",
            name="Test",
        )

        assert exp.status == ExperimentStatus.DESIGN

        # Start
        exp.status = ExperimentStatus.RUNNING
        exp.started_at = datetime.now()
        assert exp.status == ExperimentStatus.RUNNING

        # Conclude
        exp.status = ExperimentStatus.VALIDATED
        exp.completed_at = datetime.now()
        exp.conclusion = "Hypothesis supported"

        assert exp.status == ExperimentStatus.VALIDATED
        assert exp.conclusion == "Hypothesis supported"

    def test_lifecycle_falsified(self):
        """Test falsification path."""
        exp = Experiment(
            id="test_1",
            discovery_id="discovery_1",
            name="Test",
        )

        exp.status = ExperimentStatus.FALSIFIED
        exp.confidence_delta = -0.3

        assert exp.status == ExperimentStatus.FALSIFIED
        assert exp.confidence_delta < 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
