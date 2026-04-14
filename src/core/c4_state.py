"""
TURBO-CDI: Core C4 State Space Implementation
Z₃³ = 27 states (Time × Scale × Agency)
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import IntEnum


class TimeAxis(IntEnum):
    """T-axis: Temporal orientation"""

    PAST = 0
    PRESENT = 1
    FUTURE = 2


class ScaleAxis(IntEnum):
    """S-axis: Level of abstraction"""

    CONCRETE = 0
    ABSTRACT = 1
    META = 2


class AgencyAxis(IntEnum):
    """A-axis: Perspective"""

    SELF = 0
    OTHER = 1
    SYSTEM = 2


@dataclass(frozen=True)
class C4State:
    """
    Immutable state in C4 cognitive space.

    Z₃³ structure: 3 × 3 × 3 = 27 states
    Each coordinate is mod 3 (0, 1, 2)
    """

    T: int  # Time: 0=Past, 1=Present, 2=Future
    S: int  # Scale: 0=Concrete, 1=Abstract, 2=Meta
    A: int  # Agency: 0=Self, 1=Other, 2=System

    def __post_init__(self):
        assert all(0 <= x <= 2 for x in [self.T, self.S, self.A]), (
            f"C4 coordinates must be in 0-2, got T={self.T}, S={self.S}, A={self.A}"
        )

    def __str__(self) -> str:
        t_names = {0: "Past", 1: "Present", 2: "Future"}
        s_names = {0: "Concrete", 1: "Abstract", 2: "Meta"}
        a_names = {0: "Self", 1: "Other", 2: "System"}
        return f"F⟨{t_names[self.T]}, {s_names[self.S]}, {a_names[self.A]}⟩"

    def __repr__(self) -> str:
        return f"C4State(T={self.T}, S={self.S}, A={self.A})"

    def to_tuple(self) -> Tuple[int, int, int]:
        """Convert to tuple for hashing/keys."""
        return (self.T, self.S, self.A)

    @property
    def label(self) -> str:
        """Human-readable label."""
        return str(self)

    @classmethod
    def from_coords(cls, T: int, S: int, A: int) -> "C4State":
        """Factory from coordinates."""
        return cls(T=T % 3, S=S % 3, A=A % 3)

    @classmethod
    def all_states(cls) -> List["C4State"]:
        """Generate all 27 C4 states."""
        return [
            cls(T=t, S=s, A=a) for t in range(3) for s in range(3) for a in range(3)
        ]


class C4Space:
    """
    C4 State Space: Z₃³ = 27 states

    Key properties (Theorem 9 & 11):
    - Any state reachable from any other in ≤6 steps
    - Shortest path = Hamming distance
    """

    def __init__(self):
        self.states = C4State.all_states()
        self.state_map = {s.to_tuple(): s for s in self.states}

    def hamming_distance(self, s1: C4State, s2: C4State) -> int:
        """
        Theorem 9: Optimal path length = Hamming distance.

        Returns number of axes that differ between states.
        Maximum = 3 (all axes differ)
        """
        return sum(1 if a != b else 0 for a, b in zip(s1.to_tuple(), s2.to_tuple()))

    def shortest_path_length(self, s1: C4State, s2: C4State) -> int:
        """
        Theorem 11: Maximum path length = 6 (2 steps per differing axis).

        Each axis change requires 1 operator application.
        But for navigation: max 6 steps in full operadic structure.
        """
        return self.hamming_distance(s1, s2) * 2  # Conservative bound

    def get_state(self, T: int, S: int, A: int) -> C4State:
        """Get state by coordinates."""
        return self.state_map[(T % 3, S % 3, A % 3)]

    def find_by_pattern(self, pattern: str) -> List[C4State]:
        """Find states matching pattern (e.g., 'Present', 'Meta')."""
        results = []
        for state in self.states:
            if any(pattern in str(state) for _ in [0]):
                if pattern in str(state):
                    results.append(state)
        return results


# Predefined states for common reference points
C4_ORIGIN = C4State(T=0, S=0, A=0)  # Past, Concrete, Self
C4_PHI_ATTRACTOR = C4State(T=1, S=0, A=1)  # Present, Concrete, Other (Theorem 17)
C4_SYSTEMIC = C4State(T=1, S=2, A=2)  # Present, Meta, System
