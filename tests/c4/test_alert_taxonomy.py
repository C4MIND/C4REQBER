from __future__ import annotations

import time

from c4.alert_taxonomy import AlertClassifier, C4Alert


class TestC4Alert:
    def test_construction_with_required_fields(self) -> None:
        alert = C4Alert(severity="C1:INFO", layer=1, title="Test", message="hello", source="pipeline")
        assert alert.severity == "C1:INFO"
        assert alert.layer == 1
        assert alert.title == "Test"
        assert alert.message == "hello"
        assert alert.source == "pipeline"

    def test_color_c1_info(self) -> None:
        alert = C4Alert(severity="C1:INFO", layer=1, title="X", message="m", source="pipeline")
        assert alert.color == "dim cyan"

    def test_color_c2_progress(self) -> None:
        alert = C4Alert(severity="C2:PROGRESS", layer=2, title="X", message="m", source="pipeline")
        assert alert.color == "yellow"

    def test_color_c3_critical(self) -> None:
        alert = C4Alert(severity="C3:CRITICAL", layer=3, title="X", message="m", source="pipeline")
        assert alert.color == "bold red"

    def test_ttl_c1_is_finite(self) -> None:
        alert = C4Alert(severity="C1:INFO", layer=1, title="X", message="m", source="pipeline")
        assert alert.ttl == 10.0

    def test_ttl_c3_is_infinite(self) -> None:
        alert = C4Alert(severity="C3:CRITICAL", layer=3, title="X", message="m", source="pipeline")
        assert alert.ttl == float("inf")

    def test_default_timestamp_is_recent(self) -> None:
        before = time.time()
        alert = C4Alert(severity="C1:INFO", layer=1, title="X", message="m", source="pipeline")
        after = time.time()
        assert before <= alert.timestamp <= after


class TestAlertClassifier:
    def test_classify_c3_critical_pattern(self) -> None:
        alert = AlertClassifier.classify("contradiction found in proof")
        assert alert.severity == "C3:CRITICAL"
        assert alert.layer == 3

    def test_classify_c2_progress_pattern(self) -> None:
        alert = AlertClassifier.classify("hypothesis confirmed via test")
        assert alert.severity == "C2:PROGRESS"
        assert alert.layer == 2

    def test_classify_c1_info_fallback(self) -> None:
        alert = AlertClassifier.classify("unmatched random text")
        assert alert.severity == "C1:INFO"
        assert alert.layer == 1

    def test_classify_first_match_wins_criticals_checked_first(self) -> None:
        alert = AlertClassifier.classify("searching cache hit contradiction found hypothesis confirmed")
        assert alert.severity == "C3:CRITICAL"

    def test_classify_respects_source_parameter(self) -> None:
        alert = AlertClassifier.classify("pipeline started", source="verification")
        assert alert.source == "verification"
        assert alert.severity == "C1:INFO"
