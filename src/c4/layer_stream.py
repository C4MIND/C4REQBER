# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from src.c4.engine import C4Space

_LAYER_KEYWORDS: dict[int, list[str]] = {
    1: ["search", "find", "explore", "hypothesize", "literature", "gap",
        "discover", "navigate", "past", "present", "future", "time", "temporal"],
    2: ["define", "formalize", "prove", "theorem", "axiom", "model",
        "scale", "concrete", "abstract", "meta", "structure", "system"],
    3: ["verify", "check", "validate", "counterexample", "contradict", "proof",
        "agency", "self", "other", "verify", "falsify", "reproduc"],
}

_LAYER_STATES: dict[int, list[str]] = {
    1: ["exploring", "formalizing", "verifying", "synthesizing"],
    2: ["exploring", "formalizing", "verifying", "synthesizing"],
    3: ["exploring", "formalizing", "verifying", "synthesizing"],
}

_LAYER_COLORS: dict[int, str] = {
    1: "cyan",
    2: "yellow",
    3: "magenta",
}


@dataclass
class C4LayerEvent:
    """C4LayerEvent."""
    layer: int
    depth: int
    state: str
    timestamp: float
    message: str


class C4LayerTracker:
    """C4LayerTracker."""
    def __init__(self, c4_space: C4Space | None = None) -> None:
        self._c4_space = c4_space
        self._timeline: list[C4LayerEvent] = []
        self._current_layer: int = 1

    def classify_activity(self, text: str) -> C4LayerEvent:
        """Classify activity."""
        text_lower = text.lower()
        layer = 1
        max_score = 0
        for lyr, keywords in _LAYER_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > max_score:
                max_score = score
                layer = lyr
        depth = min(max_score, 2)
        state = _LAYER_STATES[layer][depth]
        event = C4LayerEvent(
            layer=layer,
            depth=depth,
            state=state,
            timestamp=time.time(),
            message=text,
        )
        self._timeline.append(event)
        self._current_layer = layer
        return event

    def get_current_layer(self) -> int:
        return self._current_layer

    def get_layer_timeline(self) -> list[C4LayerEvent]:
        return list(self._timeline)

    def get_layer_color(self, layer: int | None = None) -> str:
        """Get layer color."""
        lyr = layer if layer is not None else self._current_layer
        return _LAYER_COLORS.get(lyr, "cyan")

    def get_layer_label(self, layer: int | None = None) -> str:
        """Get layer label."""
        lyr = layer if layer is not None else self._current_layer
        return f"C{lyr}"
