"""
Additional tests for src/validation/core.py to cover remaining branches.
"""
from __future__ import annotations

import sys
from pathlib import Path


_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pytest

from src.validation.core import (
    BayesianUpdater,
    CalibrationTracker,
    Experiment,
    ExperimentStatus,
    FalsifiabilityCriterion,
    Observation,
)


class TestBayesianUpdaterEdgeCases:
    def test_update_prior_zero(self):
        updater = BayesianUpdater()
        assert updater.update(0.0, 0.9, 0.1) == 0.0

    def test_update_prior_one(self):
        updater = BayesianUpdater()
        assert updater.update(1.0, 0.9, 0.1) == 1.0

    def test_update_zero_evidence_prob(self):
        updater = BayesianUpdater()
        result = updater.update(0.5, 0.0, 0.0)
        assert result == 0.5

    def test_update_clamps_high(self):
        updater = BayesianUpdater()
        result = updater.update(0.99, 0.99, 0.01)
        assert result <= 1.0

    def test_update_clamps_low(self):
        updater = BayesianUpdater()
        result = updater.update(0.01, 0.01, 0.99)
        assert result >= 0.0

    def test_update_from_outcome_validated_full(self):
        updater = BayesianUpdater()
        result = updater.update_from_outcome(0.5, "validated", strength=1.0)
        assert result == 1.0

    def test_update_from_outcome_falsified_full(self):
        updater = BayesianUpdater()
        result = updater.update_from_outcome(0.5, "falsified", strength=1.0)
        assert result == 0.0

    def test_update_from_outcome_invalid(self):
        updater = BayesianUpdater()
        result = updater.update_from_outcome(0.5, "unknown", strength=0.5)
        assert result == 0.25


class TestCalibrationTrackerStatus:
    def test_insufficient_data(self, tmp_path):
        tracker = CalibrationTracker(str(tmp_path / "cal.json"))
        for _ in range(5):
            tracker.record(0.7, True)
        status = tracker.get_calibration_status()
        assert "Insufficient data" in status

    def test_well_calibrated(self, tmp_path):
        tracker = CalibrationTracker(str(tmp_path / "cal.json"))
        for _ in range(20):
            tracker.record(0.8, True)
        status = tracker.get_calibration_status()
        assert "Well calibrated" in status

    def test_moderately_calibrated(self, tmp_path):
        tracker = CalibrationTracker(str(tmp_path / "cal.json"))
        for _ in range(15):
            tracker.record(0.7, True)
        for _ in range(5):
            tracker.record(0.7, False)
        status = tracker.get_calibration_status()
        assert "Moderately calibrated" in status

    def test_poorly_calibrated(self, tmp_path):
        tracker = CalibrationTracker(str(tmp_path / "cal.json"))
        for _ in range(20):
            tracker.record(0.99, True)
        for _ in range(20):
            tracker.record(0.99, False)
        status = tracker.get_calibration_status()
        assert "Poorly calibrated" in status

    def test_calibration_curve_bins(self, tmp_path):
        tracker = CalibrationTracker(str(tmp_path / "cal.json"))
        for conf in [0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95]:
            tracker.record(conf, True)
        curve = tracker.calibration_curve(bins=10)
        assert isinstance(curve, list)

    def test_calibration_curve_empty_bins(self, tmp_path):
        tracker = CalibrationTracker(str(tmp_path / "cal.json"))
        tracker.record(0.5, True)
        tracker.record(0.9, True)
        curve = tracker.calibration_curve(bins=10)
        assert isinstance(curve, list)
        # Only 2 bins should have data
        assert len(curve) == 2

    def test_calibration_curve_empty(self, tmp_path):
        tracker = CalibrationTracker(str(tmp_path / "cal.json"))
        assert tracker.calibration_curve() == []

    def test_brier_score_empty(self, tmp_path):
        tracker = CalibrationTracker(str(tmp_path / "cal.json"))
        assert tracker.brier_score() == 0.0

    def test_load_missing_file(self, tmp_path):
        tracker = CalibrationTracker(str(tmp_path / "nonexistent" / "cal.json"))
        assert tracker.predictions == []

    def test_load_json_decode_error(self, tmp_path, capsys):
        path = tmp_path / "bad.json"
        path.write_text("not json")
        tracker = CalibrationTracker(str(path))
        assert tracker.predictions == []
        captured = capsys.readouterr()
        assert "Failed to load calibration data" in captured.out

    def test_load_os_error(self, tmp_path, capsys):
        # Use a directory as the path so open() raises IsADirectoryError
        path = tmp_path / "is_a_dir"
        path.mkdir()
        tracker = CalibrationTracker(str(path))
        assert tracker.predictions == []
        captured = capsys.readouterr()
        assert "Failed to load calibration data" in captured.out

    def test_save_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "sub" / "dir" / "cal.json"
        tracker = CalibrationTracker(str(path))
        tracker.record(0.8, True)
        assert path.exists()


class TestObservation:
    def test_to_dict_with_context(self):
        from datetime import datetime
        obs = Observation(
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            value=42.0,
            unit="m",
            context={"loc": "lab"},
            notes="test",
        )
        d = obs.to_dict()
        assert d["value"] == 42.0
        assert d["context"] == {"loc": "lab"}
        assert d["notes"] == "test"


class TestExperiment:
    def test_to_dict_with_dates(self):
        from datetime import datetime
        exp = Experiment(
            id="e1",
            discovery_id="d1",
            name="Test",
            started_at=datetime(2024, 1, 1, 12, 0, 0),
            completed_at=datetime(2024, 1, 2, 12, 0, 0),
        )
        d = exp.to_dict()
        assert d["started_at"] is not None
        assert d["completed_at"] is not None
        assert "2024-01-01" in d["started_at"]
        assert "2024-01-02" in d["completed_at"]

    def test_to_dict_with_criteria_and_observations(self):
        from datetime import datetime
        fc = FalsifiabilityCriterion(statement="S", measurement="M", threshold="T")
        obs = Observation(timestamp=datetime.now(), value=1.0, unit="m")
        exp = Experiment(
            id="e1",
            discovery_id="d1",
            name="Test",
            falsifiability_criteria=[fc],
            observations=[obs],
            tags=["t1", "t2"],
        )
        d = exp.to_dict()
        assert len(d["falsifiability_criteria"]) == 1
        assert len(d["observations"]) == 1
        assert d["tags"] == ["t1", "t2"]


class TestFalsifiabilityCriterion:
    def test_to_dict_all_fields(self):
        fc = FalsifiabilityCriterion(
            statement="S",
            measurement="M",
            threshold="T",
            experiment_type="controlled",
            difficulty="hard",
        )
        d = fc.to_dict()
        assert d["statement"] == "S"
        assert d["measurement"] == "M"
        assert d["threshold"] == "T"
        assert d["experiment_type"] == "controlled"
        assert d["difficulty"] == "hard"


class TestExperimentStatus:
    def test_all_status_values(self):
        statuses = [s.value for s in ExperimentStatus]
        expected = ["design", "ready", "running", "analyzing", "validated", "falsified", "inconclusive", "cancelled"]
        assert sorted(statuses) == sorted(expected)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
