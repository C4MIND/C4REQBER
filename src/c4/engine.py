"""
C4REQBER: Enhanced C4 State Space Engine
Z₃³ = 27 states with full navigation, pathfinding, and state analysis.

Copyright (C) 2026 C4REQBER Team

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

For commercial licensing, see LICENSE-COMMERCIAL.md.
"""
from __future__ import annotations


__all__ = [
    "TimeAxis",
    "ScaleAxis",
    "AgencyAxis",
    "C4State",
    "C4Space",
    "C4Path",
    "C4Engine",
]

from dataclasses import dataclass, field
from typing import Any

from src.c4.state import AgencyAxis, C4State, ScaleAxis, TimeAxis


@dataclass
class C4Transition:
    """Single step in C4 navigation."""

    operator: str
    from_state: C4State
    to_state: C4State
    description: str = ""


@dataclass
class C4Path:
    """A path through C4 state space."""

    transitions: list[C4Transition] = field(default_factory=list)
    start_state: C4State | None = None
    end_state: C4State | None = None

    @property
    def length(self) -> int:
        return len(self.transitions)

    @property
    def operators(self) -> list[str]:
        return [t.operator for t in self.transitions]

    def states_visited(self) -> list[C4State]:
        """States visited."""
        if not self.transitions:
            return []
        states = [self.transitions[0].from_state]
        for t in self.transitions:
            states.append(t.to_state)
        return states


class C4Space:
    """
    C4 State Space: Z₃³ = 27 states.

    Key properties (Theorem 9 & 11):
    - Any state reachable from any other in ≤6 steps
    - Shortest path = Hamming distance
    """

    def __init__(self) -> None:
        self.states = C4State.all_states()
        self.state_map: dict[tuple[int, int, int], C4State] = {
            s.to_tuple(): s for s in self.states
        }
        self._build_operator_map()

    def _build_operator_map(self) -> None:
        """Map operator names to state transformation functions."""
        self._ops = {
            "tau+": lambda s: s.shift_time(1),
            "tau-": lambda s: s.shift_time(-1),
            "lambda+": lambda s: s.shift_scale(1),
            "lambda-": lambda s: s.shift_scale(-1),
            "kappa+": lambda s: s.shift_agency(1),
            "kappa-": lambda s: s.shift_agency(-1),
            "iota": lambda s: s.invert(),
        }

    def axis_neighbors(self, s: C4State) -> list[C4State]:
        """Return 6 neighbors under ±1 axis operators (±τ, ±λ, ±κ)."""
        return [
            self._ops["tau+"](s),
            self._ops["tau-"](s),
            self._ops["lambda+"](s),
            self._ops["lambda-"](s),
            self._ops["kappa+"](s),
            self._ops["kappa-"](s),
        ]

    def hamming_distance(self, s1: C4State, s2: C4State) -> int:
        """Axis divergence count: number of differing axes (max 3)."""
        return sum(1 if a != b else 0 for a, b in zip(s1.to_tuple(), s2.to_tuple(), strict=False))

    def _heuristic_classify(self, problem: str) -> C4State:
        """Simple keyword-based C4 state classification fallback."""
        import re
        text = problem.lower()
        t_coords = {"past": 0, "present": 1, "future": 2}
        s_coords = {"micro": 0, "meso": 1, "macro": 2}
        a_coords = {"passive": 0, "reactive": 1, "proactive": 2}
        t = 1
        s = 1
        a = 1
        for label, val in t_coords.items():
            if re.search(rf"\b{label}\b", text):
                t = val
                break
        for label, val in s_coords.items():
            if re.search(rf"\b{label}\b", text):
                s = val
                break
        for label, val in a_coords.items():
            if re.search(rf"\b{label}\b", text):
                a = val
                break
        return self.get_state(t, s, a)

    def shortest_path_length(self, s1: C4State, s2: C4State) -> int:
        """Compute actual shortest directed path length between states via BFS."""
        if s1.to_tuple() == s2.to_tuple():
            return 0
        path = self.shortest_path(s1, s2)
        return len(path.transitions)

    def find_path(self, start: C4State, end: C4State) -> list[C4State]:
        """Find path as list of states (compatibility alias)."""
        path = self.shortest_path(start, end)
        result = [path.start_state]
        for t in path.transitions:
            result.append(t.to_state)
        return result  # type: ignore[return-value]

    def shortest_path(self, start: C4State, end: C4State) -> C4Path:
        """
        Compute shortest path through C4 space via greedy axis alignment.
        Each step corrects one axis: ±τ (time), ±λ (scale), ±κ (agency).
        Max 3 steps (undirected) — 6 steps directed (see state.py: directed_distance).
        Note: This algorithm uses Z₃ modular arithmetic — diff of 2 on an axis
        is covered with one -1 step, giving max path length = 3, not 6.
        """
        path = C4Path(start_state=start, end_state=end)
        current = start

        # Time axis
        if current.T != end.T:
            diff = (end.T - current.T) % 3
            op = "tau+" if diff == 1 else "tau-"
            new_state = self._ops[op](current)
            path.transitions.append(
                C4Transition(
                    operator=op,
                    from_state=current,
                    to_state=new_state,
                    description=f"Time: {current.time_label} → {new_state.time_label}",
                )
            )
            current = new_state

        # Scale axis
        if current.S != end.S:
            diff = (end.S - current.S) % 3
            op = "lambda+" if diff == 1 else "lambda-"
            new_state = self._ops[op](current)
            path.transitions.append(
                C4Transition(
                    operator=op,
                    from_state=current,
                    to_state=new_state,
                    description=f"Scale: {current.scale_label} → {new_state.scale_label}",
                )
            )
            current = new_state

        # Agency axis
        if current.A != end.A:
            diff = (end.A - current.A) % 3
            op = "kappa+" if diff == 1 else "kappa-"
            new_state = self._ops[op](current)
            path.transitions.append(
                C4Transition(
                    operator=op,
                    from_state=current,
                    to_state=new_state,
                    description=f"Agency: {current.agency_label} → {new_state.agency_label}",
                )
            )
            current = new_state

        path.end_state = current
        return path

    def all_paths(
        self, start: C4State, end: C4State, max_length: int = 6
    ) -> list[C4Path]:
        """Find all paths up to max_length (for analysis)."""
        # BFS to find all shortest paths
        from collections import deque

        queue: Any = deque([(start, [])])
        shortest_len = None
        paths = []

        while queue:
            state, transitions = queue.popleft()
            if shortest_len is not None and len(transitions) > shortest_len:
                break
            if state.to_tuple() == end.to_tuple():
                path = C4Path(
                    transitions=transitions, start_state=start, end_state=state
                )
                paths.append(path)
                shortest_len = len(transitions)
                continue
            if len(transitions) >= max_length:
                continue
            for op_name, op_fn in self._ops.items():
                if op_name == "iota":
                    continue
                new_state = op_fn(state)
                queue.append(
                    (new_state, transitions + [C4Transition(op_name, state, new_state)])
                )

        return paths

    def neighbors(self, state: C4State) -> list[tuple[str, C4State]]:
        """Get all neighboring states (one operator away, including iota)."""
        return [(name, op(state)) for name, op in self._ops.items()]

    def get_state(self, T: int, S: int, A: int) -> C4State:
        return self.state_map[(T % 3, S % 3, A % 3)]

    def state_by_name(self, name: str) -> C4State | None:
        """Find state by label fragment (e.g., 'Present', 'Meta')."""
        name_lower = name.lower()
        for state in self.states:
            if (
                name_lower in state.time_label.lower()
                or name_lower in state.scale_label.lower()
                or name_lower in state.agency_label.lower()
            ):
                return state
        return None


# Predefined reference states
C4_ORIGIN = C4State(T=0, S=0, A=0)
C4_PHI_ATTRACTOR = C4State(T=1, S=0, A=1)
C4_SYSTEMIC = C4State(T=1, S=2, A=2)
C4_FUTURE_META = C4State(T=2, S=2, A=2)
C4_PRESENT_ABSTRACT_SYSTEM = C4State(T=1, S=1, A=2)


class C4Engine(C4Space):
    """Alias for C4Space for backward compatibility."""
