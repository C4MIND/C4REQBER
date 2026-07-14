"""
C4REQBER: Observer Position (O₀/O₁/O₂)
Meta-cognitive dimension for self-reflection on problem-solving.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .engine import C4Space, C4State


class ObserverPosition(Enum):
    """
    Observer Position — meta-cognitive dimension.

    O₀: Inside the problem (immersed, experiencing)
    O₁: Outside the problem (observing, analyzing)
    O₂: Meta-observer (observing the observer, system-level)
    """

    IMMERSED = 0  # O₀
    OBSERVING = 1  # O₁
    META = 2  # O₂


@dataclass
class ObservationalFrame:
    """
    A frame of observation: what the observer sees from their position.
    """

    observer_position: ObserverPosition
    c4_state: C4State
    visible_states: list[C4State] = field(default_factory=list)
    blind_spots: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observer_position": self.observer_position.name,
            "position_level": self.observer_position.value,
            "c4_state": str(self.c4_state),
            "c4_coords": self.c4_state.to_tuple(),
            "visible_states": [str(s) for s in self.visible_states],
            "blind_spots": self.blind_spots,
            "insights": self.insights,
        }


class ObserverController:
    """
    Controls Observer Position shifts during problem-solving.

    Usage:
        controller = ObserverController()
        frame = controller.observe(O₀, current_state)
        frame = controller.shift_up(frame)  # O₀ → O₁
        frame = controller.shift_up(frame)  # O₁ → O₂
    """

    def __init__(self, c4_space: C4Space | None = None) -> None:
        self.c4_space = c4_space or C4Space()

    def observe(
        self, position: ObserverPosition, c4_state: C4State
    ) -> ObservationalFrame:
        """Create observational frame from given position."""
        visible = self._visible_states(position, c4_state)
        blind = self._blind_spots(position, c4_state)
        insights = self._generate_insights(position, c4_state)

        return ObservationalFrame(
            observer_position=position,
            c4_state=c4_state,
            visible_states=visible,
            blind_spots=blind,
            insights=insights,
        )

    def shift_up(self, frame: ObservationalFrame) -> ObservationalFrame:
        """Shift observer position up (O₀→O₁→O₂)."""
        new_pos = ObserverPosition(min(frame.observer_position.value + 1, 2))
        return self.observe(new_pos, frame.c4_state)

    def shift_down(self, frame: ObservationalFrame) -> ObservationalFrame:
        """Shift observer position down (O₂→O₁→O₀)."""
        new_pos = ObserverPosition(max(frame.observer_position.value - 1, 0))
        return self.observe(new_pos, frame.c4_state)

    def _visible_states(
        self, position: ObserverPosition, state: C4State
    ) -> list[C4State]:
        """Determine which C4 states are visible from this observer position."""
        all_states = self.c4_space.states
        if position == ObserverPosition.IMMERSED:
            # O₀: only immediate neighbors
            neighbors = [s for _, s in self.c4_space.neighbors(state)]
            return [state] + neighbors
        elif position == ObserverPosition.OBSERVING:
            # O₁: all states within Hamming distance 2
            return [
                s for s in all_states if self.c4_space.hamming_distance(state, s) <= 2
            ]
        else:
            # O₂: all states visible
            return all_states

    def _blind_spots(self, position: ObserverPosition, state: C4State) -> list[str]:
        """Identify what the observer cannot see."""
        if position == ObserverPosition.IMMERSED:
            return [
                "Meta-level patterns",
                "System-wide consequences",
                "Alternative problem framings",
            ]
        elif position == ObserverPosition.OBSERVING:
            return [
                "Own observational bias",
                "Second-order effects of the analysis itself",
            ]
        else:
            return [
                "Concrete emotional/tactical details",
            ]

    def _generate_insights(
        self, position: ObserverPosition, state: C4State
    ) -> list[str]:
        """Generate meta-insights based on observer position."""
        insights = []
        if position == ObserverPosition.IMMERSED:
            insights.append(f"Currently experiencing: {state}")
            insights.append("Consider stepping back (O₀→O₁) for broader view")
        elif position == ObserverPosition.OBSERVING:
            insights.append(f"Analyzing from distance: {state}")
            insights.append("Consider meta-observation (O₁→O₂) to check for bias")
        else:
            insights.append(f"System-level view: {state}")
            insights.append("All 27 states visible; verify O₂ doesn't miss details")
        return insights
