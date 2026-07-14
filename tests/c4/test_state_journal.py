from __future__ import annotations

import json
import time

from c4.state_journal import C4StateFrame, C4StateJournal


class TestC4StateFrame:
    def test_construction_and_fields(self) -> None:
        frame = C4StateFrame(timestamp=1.5, state=(0, 1, 2), event="hypothesis", detail="test detail")
        assert frame.timestamp == 1.5
        assert frame.state == (0, 1, 2)
        assert frame.event == "hypothesis"
        assert frame.detail == "test detail"
        assert frame.layer == 1
        assert frame.citations == []

    def test_state_name_origin(self) -> None:
        frame = C4StateFrame(timestamp=0.0, state=(0, 0, 0), event="x", detail="d")
        assert frame.state_name == "Past:Concrete:Self"

    def test_state_name_future_meta_system(self) -> None:
        frame = C4StateFrame(timestamp=0.0, state=(2, 2, 2), event="x", detail="d")
        assert frame.state_name == "Future:Meta:System"

    def test_state_name_present_abstract_other(self) -> None:
        frame = C4StateFrame(timestamp=0.0, state=(1, 1, 1), event="x", detail="d")
        assert frame.state_name == "Present:Abstract:Other"

    def test_state_name_unknown_values(self) -> None:
        frame = C4StateFrame(timestamp=0.0, state=(9, 9, 9), event="x", detail="d")
        assert "?" in frame.state_name


class TestC4StateJournal:
    def test_initial_frame_count_is_zero(self) -> None:
        journal = C4StateJournal()
        assert journal.frame_count == 0
        assert journal.timeline == []

    def test_record_increments_frame_count(self) -> None:
        journal = C4StateJournal()
        journal.record(state=(1, 1, 1), event="pipeline_step", detail="start")
        assert journal.frame_count == 1
        journal.record(state=(2, 2, 2), event="verification", detail="lean4")
        assert journal.frame_count == 2

    def test_record_timestamps_are_relative_to_start(self) -> None:
        journal = C4StateJournal()
        journal.record(state=(0, 0, 0), event="x", detail="d")
        time.sleep(0.01)
        journal.record(state=(1, 1, 1), event="y", detail="d")
        frames = journal.timeline
        assert frames[0].timestamp >= 0.0
        assert frames[1].timestamp > frames[0].timestamp

    def test_diff_computes_correct_metrics(self) -> None:
        journal = C4StateJournal()
        journal.record(state=(0, 0, 0), event="pipeline_step", detail="start")
        journal.record(state=(1, 0, 0), event="pipeline_step", detail="middle")
        journal.record(state=(2, 0, 0), event="verification", detail="end")
        frames = journal.timeline
        diff = journal.diff(frames[0].timestamp, frames[2].timestamp)
        assert diff["frames"] == 3
        assert diff["states_visited"] == 3
        assert diff["duration"] >= 0.0
        assert "pipeline_step" in diff["event_types"]
        assert "verification" in diff["event_types"]

    def test_diff_no_frames_in_range(self) -> None:
        journal = C4StateJournal()
        journal.record(state=(0, 0, 0), event="x", detail="d")
        frames = journal.timeline
        t0 = frames[0].timestamp
        diff = journal.diff(t0 + 100, t0 + 200)
        assert diff["frames"] == 0
        assert diff["states_visited"] == 0

    def test_diff_includes_citations_count(self) -> None:
        journal = C4StateJournal()
        journal._frames.append(C4StateFrame(
            timestamp=0.5, state=(0, 0, 0), event="verification",
            detail="lean4", citations=["cit1", "cit2"],
        ))
        journal._frames.append(C4StateFrame(
            timestamp=1.5, state=(1, 1, 1), event="verification",
            detail="coq", citations=["cit3"],
        ))
        diff = journal.diff(0.0, 2.0)
        assert diff["citations_added"] == 3

    def test_to_json_returns_valid_json(self) -> None:
        journal = C4StateJournal()
        journal.record(state=(0, 1, 2), event="hypothesis", detail="test")
        raw = journal.to_json()
        data = json.loads(raw)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["state"] == [0, 1, 2]
        assert data[0]["event"] == "hypothesis"

    def test_timeline_returns_copy_not_reference(self) -> None:
        journal = C4StateJournal()
        journal.record(state=(0, 0, 0), event="x", detail="d")
        tl = journal.timeline
        assert len(tl) == 1
        tl.pop()
        assert journal.frame_count == 1
