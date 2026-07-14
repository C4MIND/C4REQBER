from __future__ import annotations

import time

from c4.layer_stream import C4LayerEvent, C4LayerTracker


class TestC4LayerEvent:
    def test_construction_and_fields(self) -> None:
        ts = time.time()
        evt = C4LayerEvent(layer=2, depth=1, state="formalizing", timestamp=ts, message="define model")
        assert evt.layer == 2
        assert evt.depth == 1
        assert evt.state == "formalizing"
        assert evt.timestamp == ts
        assert evt.message == "define model"

    def test_default_values_are_falsey(self) -> None:
        evt = C4LayerEvent(layer=1, depth=0, state="exploring", timestamp=0.0, message="")
        assert evt.timestamp == 0.0
        assert evt.message == ""


class TestC4LayerTracker:
    def test_initial_layer_is_one(self) -> None:
        tracker = C4LayerTracker()
        assert tracker.get_current_layer() == 1

    def test_empty_timeline_at_start(self) -> None:
        tracker = C4LayerTracker()
        assert tracker.get_layer_timeline() == []

    def test_classify_search_activity_returns_event(self) -> None:
        tracker = C4LayerTracker()
        evt = tracker.classify_activity("search for gaps in literature")
        assert isinstance(evt, C4LayerEvent)
        assert evt.message == "search for gaps in literature"
        assert evt.timestamp > 0

    def test_classify_updates_current_layer(self) -> None:
        tracker = C4LayerTracker()
        tracker.classify_activity("define formalize prove theorem axiom model")
        assert tracker.get_current_layer() == 2

    def test_classify_multiple_appends_timeline(self) -> None:
        tracker = C4LayerTracker()
        tracker.classify_activity("search")
        tracker.classify_activity("define model")
        timeline = tracker.get_layer_timeline()
        assert len(timeline) == 2

    def test_get_layer_color_default_current(self) -> None:
        tracker = C4LayerTracker()
        tracker.classify_activity("search explore find")
        assert tracker.get_layer_color() == "cyan"

    def test_get_layer_color_explicit_layer(self) -> None:
        tracker = C4LayerTracker()
        assert tracker.get_layer_color(3) == "magenta"

    def test_get_layer_color_unknown_defaults_cyan(self) -> None:
        tracker = C4LayerTracker()
        assert tracker.get_layer_color(99) == "cyan"

    def test_get_layer_label_current(self) -> None:
        tracker = C4LayerTracker()
        tracker.classify_activity("search explore find")
        assert tracker.get_layer_label() == "C1"

    def test_get_layer_label_explicit(self) -> None:
        tracker = C4LayerTracker()
        assert tracker.get_layer_label(3) == "C3"
