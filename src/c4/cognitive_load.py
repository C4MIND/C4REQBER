# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CognitiveLoad:
    """CognitiveLoad."""
    level: str
    score: float
    pipeline_depth: int
    errors_recent: int
    time_in_session: float


LEVEL_COLORS: dict[str, str] = {
    "low": "green",
    "medium": "yellow",
    "high": "orange",
    "overload": "red",
}

LEVEL_PERMISSION: dict[str, str] = {
    "low": "prompt-every-step",
    "medium": "auto-accept-readonly",
    "high": "auto-accept-all",
    "overload": "suggest-break",
}


class CogLoadDetector:
    """CogLoadDetector."""
    def __init__(self) -> None:
        self._session_start: float = time.time()
        self._error_timestamps: list[float] = []
        self._total_events: int = 0
        self._current_depth: int = 1

    def assess(self, events: list[dict[str, Any]] | None = None, depth: int | None = None,
               errors: int | None = None, session_time: float | None = None) -> CognitiveLoad:
        """Assess."""
        self._total_events += len(events) if events else 0
        if errors is not None and errors > 0:
            self._error_timestamps.extend([time.time() for _ in range(errors)])

        effective_depth = depth if depth is not None else self._current_depth
        self._current_depth = effective_depth

        now = time.time()
        recent_cutoff = now - 300
        errors_recent = sum(1 for ts in self._error_timestamps if ts >= recent_cutoff)
        total_recent = max(self._total_events, 1)
        error_rate = errors_recent / total_recent if total_recent > 0 else 0.0

        effective_time = session_time if session_time is not None else (now - self._session_start) / 60.0

        if error_rate > 0.3 and effective_depth > 8:
            level = "overload"
            score = 0.85 + min(error_rate * 0.15, 0.15)
        elif effective_depth > 6 and effective_time > 15:
            level = "high"
            score = 0.65 + min((effective_time - 15) * 0.01 + error_rate * 0.1, 0.2)
        elif effective_depth > 4 or error_rate > 0.1:
            level = "medium"
            score = 0.35 + min(effective_depth * 0.03 + error_rate * 0.2, 0.3)
        else:
            level = "low"
            score = 0.05 + min(effective_depth * 0.02 + error_rate * 0.1, 0.3)

        return CognitiveLoad(
            level=level,
            score=max(0.0, min(score, 1.0)),
            pipeline_depth=effective_depth,
            errors_recent=errors_recent,
            time_in_session=effective_time,
        )

    def recommend_mode(self, load: CognitiveLoad) -> str:
        return LEVEL_PERMISSION.get(load.level, "prompt-every-step")

    def record_error(self, count: int = 1) -> None:
        self._error_timestamps.extend([time.time() for _ in range(count)])

    def record_event(self) -> None:
        self._total_events += 1

    def set_depth(self, depth: int) -> None:
        self._current_depth = depth


def render_cognitive_load_gauge(load: CognitiveLoad, width: int = 12) -> str:
    """Render cognitive load gauge."""
    blocks = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
    segments = 4
    active_segments = {
        "low": 0,
        "medium": 1,
        "high": 2,
        "overload": 3,
    }.get(load.level, 0)

    colors = ["green", "yellow", "orange", "red"]
    result_parts: list[str] = []
    for i in range(segments):
        seg_width = width // segments
        if i <= active_segments:
            color = colors[min(i, len(colors) - 1)]
            result_parts.append(f"[{color}]{'█' * seg_width}[/{color}]")
        else:
            result_parts.append(f"[dim]{'░' * seg_width}[/dim]")
    return "".join(result_parts)
