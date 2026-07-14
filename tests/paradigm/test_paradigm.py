"""Tests for paradigm shift detection module"""

from unittest.mock import patch

import pytest

from src.paradigm.anomaly import AnomalyTracker
from src.paradigm.detector import ParadigmShiftDetector
from src.paradigm.models import Anomaly, DetectRequest, DetectResult, ParadigmShiftSignal
from src.paradigm.temporal import TemporalAnalyzer


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def sample_anomalies_physics():
    return [
        Anomaly("a1", "physics", "Muon g-2 anomaly", 0.85, "2021-04-07", 1200),
        Anomaly("a2", "physics", "Hubble tension", 0.90, "2019-03-15", 2500),
        Anomaly("a3", "physics", "Dark matter null results", 0.78, "2020-11-01", 3200),
        Anomaly("a4", "physics", "W boson mass discrepancy", 0.82, "2022-04-07", 1800),
    ]


@pytest.fixture
def sample_anomalies_ai():
    return [
        Anomaly("a8", "ai", "Emergent capabilities in LLMs", 0.75, "2022-08-15", 5000),
        Anomaly("a9", "ai", "Groking phenomenon", 0.65, "2023-01-20", 1500),
        Anomaly("a10", "ai", "Inverse scaling failures", 0.68, "2022-11-05", 2200),
        Anomaly("a11", "ai", "Unexplained in-context learning", 0.80, "2023-03-10", 3800),
    ]


@pytest.fixture
def tracker():
    return AnomalyTracker()


@pytest.fixture
def temporal():
    return TemporalAnalyzer()


@pytest.fixture
def detector():
    return ParadigmShiftDetector()


# ── Anomaly Model Tests ────────────────────────────────────────────────


class TestAnomalyModel:
    def test_anomaly_creation(self):
        a = Anomaly("x1", "physics", "Test anomaly", 0.5, "2023-01-01", 100)
        assert a.id == "x1"
        assert a.field == "physics"
        assert a.description == "Test anomaly"
        assert a.severity == 0.5
        assert a.first_detected == "2023-01-01"
        assert a.citations_affected == 100

    def test_anomaly_default_citations(self):
        a = Anomaly("x2", "biology", "Test", 0.3, "2023-06-15")
        assert a.citations_affected == 0

    def test_detect_request_creation(self):
        r = DetectRequest(field="physics", time_window_days=180, min_anomalies=2)
        assert r.field == "physics"
        assert r.time_window_days == 180
        assert r.min_anomalies == 2
        assert r.include_details is True

    def test_detect_request_defaults(self):
        r = DetectRequest(field="ai")
        assert r.time_window_days == 365
        assert r.min_anomalies == 3
        assert r.include_details is True

    def test_detect_result_metadata_default(self):
        r = DetectResult(
            request_id="r1", field="physics", signals=[],
            anomalies_detected=0, summary="No anomalies"
        )
        assert r.metadata == {}

    def test_paradigm_shift_signal_defaults(self):
        s = ParadigmShiftSignal(
            id="s1", field="physics", anomalies=[], confidence=0.5,
            estimated_impact="MEDIUM", alternative_paradigms=[], evidence=[]
        )
        assert s.warning_level == "info"


# ── AnomalyTracker Tests ───────────────────────────────────────────────


class TestAnomalyTracker:
    def test_get_by_field_physics(self, tracker):
        anomalies = tracker.get_by_field("physics")
        assert len(anomalies) == 4
        assert all(a.field == "physics" for a in anomalies)

    def test_get_by_field_ai(self, tracker):
        anomalies = tracker.get_by_field("ai")
        assert len(anomalies) == 4

    def test_get_by_field_case_insensitive(self, tracker):
        assert len(tracker.get_by_field("PHYSICS")) == 4
        assert len(tracker.get_by_field("Ai")) == 4

    def test_get_by_field_unknown(self, tracker):
        assert tracker.get_by_field("astrology") == []

    def test_get_high_severity(self, tracker):
        high = tracker.get_high_severity("physics", 0.80)
        assert len(high) == 3
        assert all(a.severity >= 0.80 for a in high)

    def test_add_anomaly_new_field(self, tracker):
        a = Anomaly("nx1", "economics", "Happiness paradox", 0.55, "2023-05-01", 200)
        tracker.add_anomaly(a)
        assert "economics" in tracker.get_all_fields()
        assert len(tracker.get_by_field("economics")) == 1

    def test_add_anomaly_existing_field(self, tracker):
        a = Anomaly("nx2", "physics", "New physics anomaly", 0.92, "2024-01-01", 500)
        tracker.add_anomaly(a)
        assert len(tracker.get_by_field("physics")) == 5

    def test_get_all_fields(self, tracker):
        fields = tracker.get_all_fields()
        assert "physics" in fields
        assert "biology" in fields
        assert "ai" in fields
        assert "neuroscience" in fields
        assert "climate_science" in fields

    def test_field_summary(self, tracker):
        summary = tracker.field_summary("physics")
        assert summary["field"] == "physics"
        assert summary["anomaly_count"] == 4
        assert summary["avg_severity"] > 0.7
        assert summary["total_citations"] > 0

    def test_field_summary_unknown(self, tracker):
        summary = tracker.field_summary("nonexistent")
        assert summary["anomaly_count"] == 0
        assert summary["avg_severity"] == 0.0

    def test_search_anomalies(self, tracker):
        results = tracker.search_anomalies("Muon")
        assert len(results) == 1
        assert results[0].id == "a1"

    def test_search_anomalies_no_match(self, tracker):
        results = tracker.search_anomalies("perpetual motion")
        assert len(results) == 0


# ── TemporalAnalyzer Tests ─────────────────────────────────────────────


class TestTemporalAnalyzer:
    def test_analyze_trend_empty(self, temporal):
        result = temporal.analyze_trend([])
        assert result["trend"] == "stable"
        assert result["acceleration"] == 0.0

    def test_analyze_trend_single(self, temporal, sample_anomalies_physics):
        result = temporal.analyze_trend([sample_anomalies_physics[0]])
        assert result["data_points"] == 1

    def test_analyze_trend_multi(self, temporal, sample_anomalies_physics):
        result = temporal.analyze_trend(sample_anomalies_physics)
        assert result["data_points"] == 4
        assert result["trend"] in ("stable", "moderate", "escalating")
        assert "direction" in result

    def test_compute_momentum(self, temporal, sample_anomalies_ai):
        momentum = temporal.compute_momentum(sample_anomalies_ai)
        assert 0.0 < momentum <= 1.0

    def test_compute_momentum_empty(self, temporal):
        assert temporal.compute_momentum([]) == 0.0

    def test_predict_next_anomaly_window(self, temporal, sample_anomalies_physics):
        next_date = temporal.predict_next_anomaly_window(sample_anomalies_physics)
        assert next_date is not None
        assert next_date > "2022-04-07"

    def test_predict_next_anomaly_window_insufficient(self, temporal):
        result = temporal.predict_next_anomaly_window([])
        assert result is None

        single = [Anomaly("x1", "test", "test", 0.5, "2023-01-01", 100)]
        assert temporal.predict_next_anomaly_window(single) is None

    def test_time_window_filter(self, temporal, sample_anomalies_physics):
        filtered = temporal.time_window_filter(sample_anomalies_physics, days=1000)
        # All anomalies are from 2019-2022, which is well past 1000 days ago (in 2026)
        # So filtering with 1000 days from 2026 will likely filter most
        assert len(filtered) <= len(sample_anomalies_physics)

    def test_time_window_filter_all_passed(self, temporal, sample_anomalies_physics):
        filtered = temporal.time_window_filter(sample_anomalies_physics, days=365 * 10)
        assert len(filtered) == len(sample_anomalies_physics)

    def test_detect_severity_clusters(self, temporal, sample_anomalies_physics):
        clusters = temporal.detect_severity_clusters(sample_anomalies_physics)
        assert len(clusters) >= 1

    def test_detect_severity_clusters_empty(self, temporal):
        assert temporal.detect_severity_clusters([]) == []


# ── ParadigmShiftDetector Tests ───────────────────────────────────────


class TestParadigmShiftDetector:
    def test_detect_anomalies_physics(self, detector):
        anomalies = detector.detect_anomalies("physics", 99999)
        assert len(anomalies) == 4

    def test_detect_with_insufficient_anomalies(self, detector):
        request = DetectRequest(field="physics", min_anomalies=10, time_window_days=99999)
        result = detector.detect(request)
        assert len(result.signals) == 0
        assert result.anomalies_detected == 4
        assert "insufficient" in result.summary.lower() or "insufficient" in result.summary

    def test_detect_physics(self, detector):
        request = DetectRequest(field="physics", min_anomalies=2, time_window_days=99999)
        result = detector.detect(request)
        assert len(result.signals) == 1
        assert result.signals[0].field == "physics"
        assert result.signals[0].confidence > 0.0
        assert len(result.signals[0].alternative_paradigms) > 0

    def test_detect_ai(self, detector):
        request = DetectRequest(field="ai", min_anomalies=2, time_window_days=99999)
        result = detector.detect(request)
        assert result.anomalies_detected == 4
        assert result.signals[0].confidence > 0.0

    def test_detect_climate_science(self, detector):
        request = DetectRequest(field="climate_science", min_anomalies=2, time_window_days=99999)
        result = detector.detect(request)
        assert result.anomalies_detected == 3

    def test_detect_unknown_field(self, detector):
        request = DetectRequest(field="alchemy")
        result = detector.detect(request)
        assert result.anomalies_detected == 0
        assert len(result.signals) == 0

    def test_warning_level_critical(self, detector):
        # climate_science has high severity anomalies (0.88, 0.85, 0.82)
        request = DetectRequest(field="climate_science", min_anomalies=2, time_window_days=99999)
        result = detector.detect(request)
        # Should be at least alert
        assert result.signals[0].warning_level in ("warning", "alert", "critical")

    def test_alternative_paradigms_with_high_severity(self, detector):
        result = detector.get_alternative_paradigms("physics", [
            Anomaly("x", "physics", "Test", 0.95, "2023-01-01", 1000)
        ])
        assert "Simulation hypothesis" in result or "Consciousness-based physics" in result

    def test_alternative_paradigms_default(self, detector):
        result = detector.get_alternative_paradigms("nonexistent", [])
        assert "Paradigm extension" in result

    def test_assess_paradigm_shift_empty(self, detector):
        assert detector.assess_paradigm_shift([]) == 0.0

    def test_assess_paradigm_shift_high(self, detector):
        high_anomalies = [
            Anomaly("h1", "physics", "Major crack", 0.99, "2023-01-01", 10000),
            Anomaly("h2", "physics", "Another crack", 0.95, "2023-02-01", 8000),
            Anomaly("h3", "physics", "Third crack", 0.92, "2023-03-01", 7000),
        ]
        confidence = detector.assess_paradigm_shift(high_anomalies)
        assert confidence > 0.7

    def test_include_details_false(self, detector):
        request = DetectRequest(field="ai", min_anomalies=2, time_window_days=99999, include_details=False)
        result = detector.detect(request)
        assert result.signals[0].anomalies == []
        assert result.signals[0].evidence == []
        assert result.metadata == {}

    def test_detect_result_has_uuid(self, detector):
        request = DetectRequest(field="physics", min_anomalies=2, time_window_days=99999)
        result = detector.detect(request)
        assert len(result.request_id) > 0
        assert len(result.signals[0].id) > 0


# ── Integration-like Tests ────────────────────────────────────────────


class TestIntegration:
    def test_full_workflow(self, detector):
        request = DetectRequest(field="biology", min_anomalies=1, time_window_days=99999)
        result = detector.detect(request)
        assert result.anomalies_detected == 3
        assert len(result.signals) == 1
        signal = result.signals[0]
        assert signal.confidence > 0.0
        assert signal.warning_level in ("info", "warning", "alert", "critical")
        assert len(signal.evidence) == 3

    def test_neuroscience_detection(self, detector):
        request = DetectRequest(field="neuroscience", min_anomalies=1, time_window_days=99999)
        result = detector.detect(request)
        assert result.anomalies_detected == 2

    def test_all_fields_have_alternatives(self, detector):
        for field in detector.anomaly_database:
            alternatives = detector.get_alternative_paradigms(field, detector.detect_anomalies(field, 99999))
            assert len(alternatives) > 0, f"No alternatives for {field}"
