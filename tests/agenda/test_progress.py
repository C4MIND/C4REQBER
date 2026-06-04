"""Tests for agenda progress tracker."""
from __future__ import annotations

from src.agenda.progress import ProgressTracker


class TestProgressTracker:
    def test_update_records_result(self) -> None:
        tracker = ProgressTracker()
        tracker.update({"hypothesis": {"text": "Dark matter interacts weakly"}})
        assert tracker.to_dict()["results_count"] == 1

    def test_get_open_gaps_dedup(self) -> None:
        tracker = ProgressTracker()
        tracker.update({"gaps": ["gap1", "gap2"]})
        tracker.update({"gaps": ["gap1", "gap3"]})
        gaps = tracker.get_open_gaps()
        assert gaps == ["gap1", "gap2", "gap3"]

    def test_covered_topics(self) -> None:
        tracker = ProgressTracker()
        tracker.update({"hypothesis": {"text": "Quantum gravity emerges from entanglement"}})
        topics = tracker.get_covered_topics()
        assert "quantum gravity emerges" in topics

    def test_approve_reject(self) -> None:
        tracker = ProgressTracker()
        tracker.add_approved("Q1")
        tracker.add_rejected("Q2")
        d = tracker.to_dict()
        assert d["approved_count"] == 1
        assert d["rejected_count"] == 1
        assert d["latest_approved"] == ["Q1"]
