from __future__ import annotations

import time

import pytest

from src.c4.cognitive_load import LEVEL_COLORS, LEVEL_PERMISSION, CogLoadDetector, CognitiveLoad


class TestCogLoadDetector:
    def test_overload_high_error_rate_and_deep(self) -> None:
        detector = CogLoadDetector()
        result = detector.assess(depth=9, errors=1)
        detector._total_events = 2
        result = detector.assess(depth=9, errors=1)

        assert result.level == "overload"
        assert result.score > 0.8
        assert result.pipeline_depth == 9

    def test_high_depth_and_time(self) -> None:
        detector = CogLoadDetector()
        result = detector.assess(depth=7, session_time=16.0)

        assert result.level == "high"
        assert 0.65 <= result.score <= 0.85

    def test_low_load_shallow_and_short(self) -> None:
        detector = CogLoadDetector()
        result = detector.assess(depth=3, session_time=5.0)

        assert result.level == "low"
        assert 0.0 <= result.score <= 0.35

    def test_assess_explicit_params(self) -> None:
        detector = CogLoadDetector()
        result = detector.assess(depth=5, errors=0, session_time=10.0)

        assert result.level in ("low", "medium")
        assert 0.0 <= result.score <= 1.0
        assert result.pipeline_depth == 5
        assert result.errors_recent == 0
        assert result.time_in_session == 10.0

    def test_recommend_mode_maps_levels(self) -> None:
        detector = CogLoadDetector()
        assert detector.recommend_mode(CognitiveLoad(
            level="low", score=0.1, pipeline_depth=1, errors_recent=0, time_in_session=1.0
        )) == "prompt-every-step"
        assert detector.recommend_mode(CognitiveLoad(
            level="medium", score=0.4, pipeline_depth=4, errors_recent=1, time_in_session=8.0
        )) == "auto-accept-readonly"
        assert detector.recommend_mode(CognitiveLoad(
            level="high", score=0.7, pipeline_depth=7, errors_recent=2, time_in_session=16.0
        )) == "auto-accept-all"
        assert detector.recommend_mode(CognitiveLoad(
            level="overload", score=0.9, pipeline_depth=10, errors_recent=5, time_in_session=20.0
        )) == "suggest-break"


class TestCognitiveLoadDefaults:
    def test_dataclass_defaults_score(self) -> None:
        load = CognitiveLoad(level="low", score=0.05, pipeline_depth=1, errors_recent=0, time_in_session=5.0)
        assert load.level == "low"
        assert load.score == 0.05

    def test_dataclass_defaults_fields(self) -> None:
        load = CognitiveLoad(level="medium", score=0.5, pipeline_depth=3, errors_recent=2, time_in_session=12.0)
        assert load.level == "medium"
        assert load.score == 0.5
        assert load.pipeline_depth == 3
        assert load.errors_recent == 2
        assert load.time_in_session == 12.0

    def test_level_colors_mapping(self) -> None:
        assert LEVEL_COLORS["low"] == "green"
        assert LEVEL_COLORS["medium"] == "yellow"
        assert LEVEL_COLORS["high"] == "orange"
        assert LEVEL_COLORS["overload"] == "red"

    def test_level_permission_mapping(self) -> None:
        assert LEVEL_PERMISSION["low"] == "prompt-every-step"
        assert LEVEL_PERMISSION["medium"] == "auto-accept-readonly"
        assert LEVEL_PERMISSION["high"] == "auto-accept-all"
        assert LEVEL_PERMISSION["overload"] == "suggest-break"
