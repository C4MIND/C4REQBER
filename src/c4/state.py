# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations


"""
Canonical Unified C4State — single source of truth for C4 cognitive state.

Z₃³ = 27 states = Time(3) × Scale(3) × Agency(3)
- t / T: Time axis    — Past(0) / Present(1) / Future(2)
- s / S: Scale axis   — Concrete(0) / Abstract(1) / Meta(2)
- a / A: Agency axis  — Self(0) / Other(1) / System(2)

Operators: T/T_INV/S/S_INV/A/A_INV ∈ Z₃³ (period 3 cyclic shifts)
    plus tau+/tau-/lambda+/lambda-/kappa+/kappa-/iota (extended algebra)

All arithmetic is mod 3, matching Agda formal proofs.
Reference: formal-proofs/c4-comp-v5.agda

Replaces: src/c4/core.py::C4State, src/c4/types.py::C4State,
          src/c4/engine.py::C4State, src/core/c4_state.py::C4State
"""

from collections import deque
from dataclasses import dataclass, field
from enum import IntEnum
from typing import ClassVar


# ── Axis Enums ───────────────────────────────────────────────────────


class TimeOrientation(IntEnum):
    """T-axis: Temporal orientation (alias: Time, TimeAxis)."""
    PAST = 0
    PRESENT = 1
    FUTURE = 2


Time = TimeOrientation          # backward compat
TimeAxis = TimeOrientation      # backward compat


class ScaleLevel(IntEnum):
    """S-axis: Level of abstraction (alias: Scale, ScaleAxis)."""
    CONCRETE = 0
    ABSTRACT = 1
    META = 2


Scale = ScaleLevel              # backward compat
ScaleAxis = ScaleLevel          # backward compat


class AgencyPosition(IntEnum):
    """A-axis: Perspective (alias: Agency, AgencyAxis)."""
    SELF = 0
    OTHER = 1
    SYSTEM = 2


Agency = AgencyPosition         # backward compat
AgencyAxis = AgencyPosition     # backward compat


# ── C4Operator — named operator constants ────────────────────────────


class C4Operator:
    """The six fundamental operators of C4 (Agda-verified).

    T, T_INV, S, S_INV, A, A_INV — cyclic shifts with period 3
    in both directions.

    Also supports extended operator names:
        tau+/tau-, lambda+/lambda-, kappa+/kappa-, iota
    """

    T: ClassVar[str] = "T"
    T_INV: ClassVar[str] = "T_INV"
    S: ClassVar[str] = "S"
    S_INV: ClassVar[str] = "S_INV"
    A: ClassVar[str] = "A"
    A_INV: ClassVar[str] = "A_INV"

    _all: ClassVar[tuple[str, str, str, str, str, str]] = (
        "T", "T_INV", "S", "S_INV", "A", "A_INV",
    )

    @classmethod
    def all(cls) -> tuple[str, str, str, str, str, str]:
        return cls._all

    @classmethod
    def apply_n_times(cls, op: str, state: C4State, n: int) -> C4State:
        """Apply operator n times. Period 3: n mod 3 matters."""
        method = {
            "T": state.apply_T,
            "S": state.apply_S,
            "A": state.apply_A,
        }.get(op)
        if method is None:
            raise ValueError(f"Operator {op!r} not supported by apply_n_times")
        s = state
        for _ in range(n % 3):
            s = method()
        return s

    @classmethod
    def period_check(cls, op: str, state: C4State) -> bool:
        """Verify T̂³ = id, Ŝ³ = id, Â³ = id for a given state."""
        result = cls.apply_n_times(op, state, 3)
        return result == state


# ── Unified C4State — canonical Z₃³ state ────────────────────────────


@dataclass(frozen=True)
class C4State:
    """Immutable state in C4 cognitive space Z₃³.

    Notation: F⟨t,s,a⟩ where each coordinate ∈ {0,1,2}.

    Construction supports all legacy forms:
        C4State(0, 1, 2)            — positional t,s,a
        C4State(t=0, s=1, a=2)      — keyword t,s,a
        C4State(T=0, S=1, A=2)      — keyword T,S,A (backward compat)
        C4State(t=0, S=1, a=2)      — mixed
    """

    t: int = 0
    s: int = 0
    a: int = 0
    name_en: str | None = field(default=None, compare=False, hash=False, repr=False)
    name_ru: str | None = field(default=None, compare=False, hash=False, repr=False)
    description: str = field(default="", compare=False, hash=False, repr=False)
    metaphor: str = field(default="", compare=False, hash=False, repr=False)
    strengths: list[str] = field(default_factory=list, compare=False, hash=False, repr=False)
    color: str = field(default="", compare=False, hash=False, repr=False)

    STATE_NAMES: ClassVar[dict[tuple[int, int, int], str]] = {
        (0, 0, 0): "Retrospective_Concrete_Self",
        (0, 0, 1): "Retrospective_Concrete_Other",
        (0, 0, 2): "Retrospective_Concrete_System",
        (0, 1, 0): "Retrospective_Abstract_Self",
        (0, 1, 1): "Retrospective_Abstract_Other",
        (0, 1, 2): "Retrospective_Abstract_System",
        (0, 2, 0): "Retrospective_Meta_Self",
        (0, 2, 1): "Retrospective_Meta_Other",
        (0, 2, 2): "Retrospective_Meta_System",
        (1, 0, 0): "Present_Concrete_Self",
        (1, 0, 1): "Present_Concrete_Other",
        (1, 0, 2): "Present_Concrete_System",
        (1, 1, 0): "Present_Abstract_Self",
        (1, 1, 1): "Present_Abstract_Other",
        (1, 1, 2): "Present_Abstract_System",
        (1, 2, 0): "Present_Meta_Self",
        (1, 2, 1): "Present_Meta_Other",
        (1, 2, 2): "Present_Meta_System",
        (2, 0, 0): "Futuristic_Concrete_Self",
        (2, 0, 1): "Futuristic_Concrete_Other",
        (2, 0, 2): "Futuristic_Concrete_System",
        (2, 1, 0): "Futuristic_Abstract_Self",
        (2, 1, 1): "Futuristic_Abstract_Other",
        (2, 1, 2): "Futuristic_Abstract_System",
        (2, 2, 0): "Futuristic_Meta_Self",
        (2, 2, 1): "Futuristic_Meta_Other",
        (2, 2, 2): "Futuristic_Meta_System",
    }

    _LABEL_TO_INT_TIME: ClassVar[dict[str, int]] = {
        "past": 0, "present": 1, "future": 2,
    }
    _LABEL_TO_INT_SCALE: ClassVar[dict[str, int]] = {
        "concrete": 0, "abstract": 1, "meta": 2,
    }
    _LABEL_TO_INT_AGENCY: ClassVar[dict[str, int]] = {
        "self": 0, "other": 1, "system": 2,
    }

    def __init__(
        self,
        t: int = 0,
        s: int = 0,
        a: int = 0,
        T: int | None = None,
        S: int | None = None,
        A: int | None = None,
        code: str | None = None,
        time: str | int | None = None,
        scale: str | int | None = None,
        agency: str | int | None = None,
        name_en: str | None = None,
        name_ru: str | None = None,
        description: str = "",
        metaphor: str = "",
        strengths: list[str] | None = None,
        color: str = "",
    ) -> None:
        if code is not None:
            if len(code) != 3 or not all(c in "012" for c in code):
                raise ValueError(
                    f"C4State code must be a 3-digit string of 0/1/2, got {code!r}"
                )
            t = int(code[0])
            s = int(code[1])
            a = int(code[2])
        if time is not None:
            t = self._parse_axis(time, "time", self._LABEL_TO_INT_TIME)
        if scale is not None:
            s = self._parse_axis(scale, "scale", self._LABEL_TO_INT_SCALE)
        if agency is not None:
            a = self._parse_axis(agency, "agency", self._LABEL_TO_INT_AGENCY)
        tt_raw = T if T is not None else t
        ss_raw = S if S is not None else s
        aa_raw = A if A is not None else a
        for name, val in [("t", tt_raw), ("s", ss_raw), ("a", aa_raw)]:
            if not 0 <= val <= 2:
                raise ValueError(
                    f"C4State {name} must be in [0, 1, 2], got {val}"
                )
        object.__setattr__(self, "t", tt_raw)
        object.__setattr__(self, "s", ss_raw)
        object.__setattr__(self, "a", aa_raw)
        object.__setattr__(self, "name_en", name_en)
        object.__setattr__(self, "name_ru", name_ru)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "metaphor", metaphor)
        object.__setattr__(self, "strengths", strengths if strengths is not None else [])
        object.__setattr__(self, "color", color)

    @staticmethod
    def _parse_axis(value: str | int, axis_name: str, label_map: dict[str, int]) -> int:
        if isinstance(value, int):
            if value not in (0, 1, 2):
                raise ValueError(
                    f"C4State {axis_name} int must be in [0, 1, 2], got {value}"
                )
            return value
        if isinstance(value, str):
            low = value.lower()
            if low in label_map:
                return label_map[low]
            raise ValueError(
                f"C4State {axis_name} string must be one of "
                f"{list(label_map.keys())}, got {value!r}"
            )
        raise TypeError(
            f"C4State {axis_name} must be int or str, got {type(value).__name__}"
        )

    def __post_init__(self) -> None:
        pass

    # ── Uppercase property aliases ────────────────────────────────

    @property
    def T(self) -> int:
        """Backward-compat alias for t (Time coordinate)."""
        return self.t

    @property
    def S(self) -> int:
        """Backward-compat alias for s (Scale coordinate)."""
        return self.s

    @property
    def A(self) -> int:
        """Backward-compat alias for a (Agency coordinate)."""
        return self.a

    @property
    def code(self) -> str:
        """Three-digit C4 code string (e.g. '012')."""
        return f"{self.t}{self.s}{self.a}"

    @property
    def time(self) -> str:
        """String label for the Time axis (Past/Present/Future)."""
        return self.time_label

    @property
    def scale(self) -> str:
        """String label for the Scale axis (Concrete/Abstract/Meta)."""
        return self.scale_label

    @property
    def agency(self) -> str:
        """String label for the Agency axis (Self/Other/System)."""
        return self.agency_label

    # ── Human-readable labels ─────────────────────────────────────

    @property
    def time_label(self) -> str:
        return {0: "Past", 1: "Present", 2: "Future"}[self.t]

    @property
    def scale_label(self) -> str:
        return {0: "Concrete", 1: "Abstract", 2: "Meta"}[self.s]

    @property
    def agency_label(self) -> str:
        return {0: "Self", 1: "Other", 2: "System"}[self.a]

    @property
    def name(self) -> str:
        return self.STATE_NAMES[(self.t, self.s, self.a)]

    @property
    def label(self) -> str:
        """Human-readable label (backward compat with src/core/c4_state.py)."""
        return str(self)

    def __str__(self) -> str:
        return f"F⟨{self.time_label}, {self.scale_label}, {self.agency_label}⟩"

    def __repr__(self) -> str:
        return f"C4State(t={self.t}, s={self.s}, a={self.a})"

    # ── Serialization ─────────────────────────────────────────────

    @property
    def coordinates(self) -> tuple[int, int, int]:
        return (self.t, self.s, self.a)

    @property
    def label_ru(self) -> str:
        return self.name_ru or self.label

    @property
    def index(self) -> int:
        return self.t * 9 + self.s * 3 + self.a

    def to_tuple(self) -> tuple[int, int, int]:
        return (self.t, self.s, self.a)

    def to_coords(self) -> dict[str, int]:
        return {"T": self.t, "S": self.s, "A": self.a}

    @classmethod
    def from_tuple(cls, coords: tuple[int, int, int]) -> C4State:
        return cls(*coords)

    @classmethod
    def from_coords(cls, T: int, S: int, A: int) -> C4State:
        """Factory from coordinates with modulo wrap."""
        return cls(t=T % 3, s=S % 3, a=A % 3)

    @classmethod
    def from_name(cls, name: str) -> C4State:
        """From name."""
        reverse = {v: k for k, v in cls.STATE_NAMES.items()}
        t, s, a = reverse[name]
        return cls(t, s, a)

    @classmethod
    def all_states(cls) -> list[C4State]:
        return [
            cls(t, s, a)
            for t in range(3)
            for s in range(3)
            for a in range(3)
        ]

    # ── Shift operators (canonical API) ───────────────────────────

    def shift_time(self, delta: int = 1) -> C4State:
        return C4State(t=(self.t + delta) % 3, s=self.s, a=self.a)

    def shift_scale(self, delta: int = 1) -> C4State:
        return C4State(t=self.t, s=(self.s + delta) % 3, a=self.a)

    def shift_agency(self, delta: int = 1) -> C4State:
        return C4State(t=self.t, s=self.s, a=(self.a + delta) % 3)

    def invert(self) -> C4State:
        """Inversion operator (iota). Period 2 (involution)."""
        return C4State(t=2 - self.t, s=2 - self.s, a=2 - self.a)

    # ── Legacy operator methods ───────────────────────────────────

    def apply_T(self) -> C4State:
        """T̂: cyclic shift +1 along Time axis."""
        return self.shift_time(1)

    def apply_S(self) -> C4State:
        """Ŝ: cyclic shift +1 along Scale axis."""
        return self.shift_scale(1)

    def apply_A(self) -> C4State:
        """Â: cyclic shift +1 along Agency axis."""
        return self.shift_agency(1)

    def apply_T_inv(self) -> C4State:
        """T̂⁻¹: inverse cyclic shift along Time axis."""
        return self.shift_time(-1)

    def apply_S_inv(self) -> C4State:
        """Ŝ⁻¹: inverse cyclic shift along Scale axis."""
        return self.shift_scale(-1)

    def apply_A_inv(self) -> C4State:
        """Â⁻¹: inverse cyclic shift along Agency axis."""
        return self.shift_agency(-1)

    def apply_operator(self, op: str) -> C4State:
        """Apply a named operator (string or C4Operator constant)."""
        _op = str(op)
        if _op == "T" or _op == "tau+":
            return self.apply_T()
        elif _op == "S" or _op == "lambda+":
            return self.apply_S()
        elif _op == "A" or _op == "kappa+":
            return self.apply_A()
        elif _op == "T_INV" or _op == "tau-":
            return self.apply_T_inv()
        elif _op == "S_INV" or _op == "lambda-":
            return self.apply_S_inv()
        elif _op == "A_INV" or _op == "kappa-":
            return self.apply_A_inv()
        elif _op == "iota":
            return self.invert()
        else:
            raise ValueError(f"Unknown operator: {op}")

    def apply_path(self, path: list[str]) -> C4State:
        """Apply a sequence of operators (left-to-right)."""
        state = self
        for op in path:
            state = state.apply_operator(op)
        return state

    # ── Distance metrics ──────────────────────────────────────────

    @staticmethod
    def cyclic_distance(a: int, b: int) -> int:
        """Forward cyclic distance on Z₃: d(a,b) = (b - a) mod 3."""
        return (b - a) % 3

    @staticmethod
    def _symmetric_axis_dist(a: int, b: int) -> int:
        """Symmetric modular distance on a single Z₃ axis."""
        return min(abs(a - b), 3 - abs(a - b))

    @staticmethod
    def _directed_axis_dist(a: int, b: int) -> int:
        """Asymmetric directed distance on a single Z₃ axis."""
        return (b - a) % 3

    def distance(self, other: C4State) -> int:
        """Symmetric modular metric on Z₃³. Diameter = 3."""
        return (
            self._symmetric_axis_dist(self.t, other.t)
            + self._symmetric_axis_dist(self.s, other.s)
            + self._symmetric_axis_dist(self.a, other.a)
        )

    def directed_distance(self, other: C4State) -> int:
        """Asymmetric directed distance on Z₃³. Diameter = 6."""
        return (
            self._directed_axis_dist(self.t, other.t)
            + self._directed_axis_dist(self.s, other.s)
            + self._directed_axis_dist(self.a, other.a)
        )

    def hamming_distance(self, other: C4State) -> int:
        """Alias for directed_distance (backward-compatible, max 6)."""
        return self.directed_distance(other)

    def is_antipode(self, other: C4State) -> bool:
        """True if other is maximally distant in directed metric (dist = 6)."""
        return self.directed_distance(other) == 6

    # ── Neighbors & pathfinding ───────────────────────────────────

    def neighbors(self) -> list[C4State]:
        """6 neighbors on the Z₃³ torus (±1 step on each axis)."""
        return [
            self.shift_time(-1),
            self.shift_time(1),
            self.shift_scale(-1),
            self.shift_scale(1),
            self.shift_agency(-1),
            self.shift_agency(1),
        ]

    def shortest_path(self, target: C4State) -> list[C4State]:
        """BFS shortest path using symmetric modular distance."""
        if self == target:
            return []

        visited: set[tuple[int, int, int]] = {self.to_tuple()}
        queue: deque[tuple[C4State, list[C4State]]] = deque([(self, [])])

        while queue:
            current, path = queue.popleft()
            for nxt in current.neighbors():
                key = nxt.to_tuple()
                if key in visited:
                    continue
                new_path = path + [nxt]
                if nxt == target:
                    return new_path
                visited.add(key)
                queue.append((nxt, new_path))

        raise RuntimeError(
            f"No path found from {self} to {target} — "
            f"contradicts connectivity of Z₃³!"
        )

    def canonical_path(self, target: C4State) -> list[str]:
        """Canonical (optimal) directed path from self to target.
        Theorem 9: length of this path equals Hamming distance.
        Order: T shifts first, then S, then A.
        """
        path: list[str] = []
        dt = self.cyclic_distance(self.t, target.t)
        ds = self.cyclic_distance(self.s, target.s)
        da = self.cyclic_distance(self.a, target.a)
        path.extend(["T"] * dt)
        path.extend(["S"] * ds)
        path.extend(["A"] * da)
        return path


# ── Module-level helpers ──────────────────────────────────────────────


def all_27_states() -> list[C4State]:
    return C4State.all_states()


def cyclic_distance(a: int, b: int) -> int:
    return C4State.cyclic_distance(a, b)


def hamming_distance(s1: C4State, s2: C4State) -> int:
    return s1.hamming_distance(s2)


def undirected_distance(s1: C4State, s2: C4State) -> int:
    """Symmetric modular distance between two states."""
    return s1.distance(s2)


def canonical_path(s1: C4State, s2: C4State) -> list[str]:
    return s1.canonical_path(s2)


def apply_path(state: C4State, path: list[str]) -> C4State:
    return state.apply_path(path)


def verify_theorem_11() -> tuple[int, list[tuple[C4State, C4State, int]]]:
    """Verify Theorem 11 for all 27×27 pairs."""
    states = all_27_states()
    max_dist = 0
    antipodes: list[tuple[C4State, C4State, int]] = []
    for s1 in states:
        for s2 in states:
            d = hamming_distance(s1, s2)
            if d > max_dist:
                max_dist = d
            if d == 6:
                antipodes.append((s1, s2, d))
    return max_dist, antipodes
