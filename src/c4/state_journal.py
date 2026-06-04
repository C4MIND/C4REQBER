# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field


@dataclass
class C4StateFrame:
    """C4StateFrame."""
    timestamp: float
    state: tuple[int, int, int]  # (t, s, a)
    event: str  # "pipeline_step", "verification", "hypothesis", "user_input"
    detail: str
    layer: int = 1
    citations: list[str] = field(default_factory=list)

    @property
    def state_name(self) -> str:
        """State name."""
        t_names = {0: "Past", 1: "Present", 2: "Future"}
        s_names = {0: "Concrete", 1: "Abstract", 2: "Meta"}
        a_names = {0: "Self", 1: "Other", 2: "System"}
        t, s, a = self.state
        return f"{t_names.get(t,'?')}:{s_names.get(s,'?')}:{a_names.get(a,'?')}"


class C4StateJournal:
    """Records cognitive state transitions for replay."""

    def __init__(self) -> None:
        self._frames: list[C4StateFrame] = []
        self._start_time = time.time()

    def record(self, state: tuple[int, int, int], event: str, detail: str = "", layer: int = 1) -> None:
        self._frames.append(C4StateFrame(
            timestamp=time.time() - self._start_time,
            state=state, event=event, detail=detail, layer=layer,
        ))

    def diff(self, time_a: float, time_b: float) -> dict:
        """Diff."""
        frames_between = [f for f in self._frames if time_a <= f.timestamp <= time_b]
        states_touched = set(f.state for f in frames_between)
        events = [f.event for f in frames_between]
        return {
            "duration": time_b - time_a,
            "frames": len(frames_between),
            "states_visited": len(states_touched),
            "layers_touched": sorted(set(f.layer for f in frames_between)),
            "event_types": list(set(events)),
            "citations_added": sum(len(f.citations) for f in frames_between),
        }

    def to_json(self) -> str:
        return json.dumps([asdict(f) for f in self._frames], indent=2)

    @property
    def frame_count(self) -> int:
        return len(self._frames)

    @property
    def timeline(self) -> list[C4StateFrame]:
        return list(self._frames)
