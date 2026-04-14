"""
Z₃³ Operators and BFS Path Finding

Ported from C4 COGNOS backend/operators.py

Theorem 11: Any state in Z₃³ is reachable from any other state
in at most 6 steps using the elementary shift operators.
"""

from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from typing import Optional


# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass(frozen=True)
class C4State:
    """A state in Z₃³: (T, D, A) where each coordinate is in {0, 1, 2}."""

    t: int  # Time axis: Past(0) / Present(1) / Future(2)
    d: int  # Detail axis: Concrete(0) / Abstract(1) / Meta(2)
    a: int  # Agency axis: Self(0) / Other(1) / System(2)

    def to_string(self) -> str:
        return f"{self.t}{self.d}{self.a}"


@dataclass
class TrajectoryPath:
    """Result of a shortest-path search between two C4 states."""

    from_state: C4State
    to_state: C4State
    path: list[C4State]
    operators: list[str]
    cost: int


# ============================================================================
# HELPERS
# ============================================================================


def _clamp(value: int, min_val: int = 0, max_val: int = 2) -> int:
    """Clamp value to the Z₃ range [0, 2]."""
    return max(min_val, min(max_val, value))


def _add_delta(state: C4State, dt: int, dd: int, da: int) -> C4State:
    """Apply a coordinate delta and clamp to Z₃ bounds."""
    return C4State(
        t=_clamp(state.t + dt),
        d=_clamp(state.d + dd),
        a=_clamp(state.a + da),
    )


def _manhattan_distance(s1: C4State, s2: C4State) -> int:
    return abs(s1.t - s2.t) + abs(s1.d - s2.d) + abs(s1.a - s2.a)


# ============================================================================
# ELEMENTARY Z₃³ OPERATORS
# ============================================================================


# Temporal operators (T-axis)
def U_T_plus(state: C4State) -> C4State:
    """Shift forward in time: Past → Present → Future."""
    return _add_delta(state, +1, 0, 0)


def U_T_minus(state: C4State) -> C4State:
    """Shift backward in time: Future → Present → Past."""
    return _add_delta(state, -1, 0, 0)


# Abstraction operators (D-axis)
def U_D_plus(state: C4State) -> C4State:
    """Increase abstraction: Concrete → Abstract → Meta."""
    return _add_delta(state, 0, +1, 0)


def U_D_minus(state: C4State) -> C4State:
    """Decrease abstraction: Meta → Abstract → Concrete."""
    return _add_delta(state, 0, -1, 0)


# Agency operators (A-axis)
def U_A_plus(state: C4State) -> C4State:
    """Expand agency: Self → Other → System."""
    return _add_delta(state, 0, 0, +1)


def U_A_minus(state: C4State) -> C4State:
    """Narrow agency: System → Other → Self."""
    return _add_delta(state, 0, 0, -1)


# Collection of all elementary operators for iteration
_ELEMENTARY_OPERATORS: list[tuple[str, tuple[int, int, int]]] = [
    ("U_T_plus", (1, 0, 0)),
    ("U_T_minus", (-1, 0, 0)),
    ("U_D_plus", (0, 1, 0)),
    ("U_D_minus", (0, -1, 0)),
    ("U_A_plus", (0, 0, 1)),
    ("U_A_minus", (0, 0, -1)),
]


# ============================================================================
# APPLY TRANSFORMATION
# ============================================================================


def apply_transformation(state: C4State, operator_name: str) -> C4State:
    """
    Apply a named elementary operator to a C4State.

    Supported operators:
      U_T_plus, U_T_minus, U_D_plus, U_D_minus, U_A_plus, U_A_minus
    """
    if operator_name == "U_T_plus":
        return U_T_plus(state)
    elif operator_name == "U_T_minus":
        return U_T_minus(state)
    elif operator_name == "U_D_plus":
        return U_D_plus(state)
    elif operator_name == "U_D_minus":
        return U_D_minus(state)
    elif operator_name == "U_A_plus":
        return U_A_plus(state)
    elif operator_name == "U_A_minus":
        return U_A_minus(state)
    else:
        raise ValueError(f"Unknown operator: {operator_name}")


# ============================================================================
# SHORTEST PATH (BFS)
# ============================================================================


def find_shortest_path(
    from_state: C4State,
    to_state: C4State,
    max_steps: int = 6,
) -> Optional[TrajectoryPath]:
    """
    Find the shortest sequence of elementary operators that transforms
    `from_state` into `to_state` using breadth-first search.

    By Theorem 11, any state in Z₃³ is reachable from any other in <= 6 steps.
    """
    if from_state == to_state:
        return TrajectoryPath(
            from_state=from_state,
            to_state=to_state,
            path=[from_state],
            operators=[],
            cost=0,
        )

    queue: deque[tuple[C4State, list[C4State], list[str]]] = deque()
    queue.append((from_state, [], []))
    visited: set[str] = {from_state.to_string()}

    while queue:
        current, path, ops = queue.popleft()

        if len(ops) >= max_steps:
            continue

        for op_name, (dt, dd, da) in _ELEMENTARY_OPERATORS:
            new_state = _add_delta(current, dt, dd, da)
            state_key = new_state.to_string()

            if state_key in visited:
                continue

            new_path = path + [new_state]
            new_ops = ops + [op_name]

            if new_state == to_state:
                return TrajectoryPath(
                    from_state=from_state,
                    to_state=to_state,
                    path=[from_state] + new_path,
                    operators=new_ops,
                    cost=len(new_ops),
                )

            visited.add(state_key)
            queue.append((new_state, new_path, new_ops))

    return None


# ============================================================================
# THEOREM 11 VERIFICATION
# ============================================================================


def verify_theorem_11() -> dict:
    """
    Verify Theorem 11: every state in Z₃³ is reachable from every other state
    in at most 6 elementary steps.

    Returns a summary dict with max_steps_observed and any failures.
    """
    states = [C4State(t, d, a) for t in range(3) for d in range(3) for a in range(3)]
    max_steps = 0
    failures: list[tuple[str, str]] = []

    for start in states:
        for goal in states:
            if start == goal:
                continue
            path_result = find_shortest_path(start, goal, max_steps=6)
            if path_result is None:
                failures.append((start.to_string(), goal.to_string()))
            else:
                max_steps = max(max_steps, path_result.cost)

    return {
        "verified": len(failures) == 0,
        "total_pairs_checked": len(states) * (len(states) - 1),
        "max_steps_observed": max_steps,
        "failures": failures,
    }


# ============================================================================
# SELF-TEST
# ============================================================================

if __name__ == "__main__":
    print("=== Z₃³ Operators Self-Test ===\n")

    s = C4State(t=0, d=0, a=0)
    print(f"Initial: {s.to_string()}")
    print(f"U_T_plus:  {U_T_plus(s).to_string()}")
    print(f"U_D_plus:  {U_D_plus(s).to_string()}")
    print(f"U_A_plus:  {U_A_plus(s).to_string()}")

    print("\n=== BFS Path Finding ===")
    start = C4State(0, 0, 0)
    goal = C4State(2, 2, 2)
    result = find_shortest_path(start, goal)
    if result:
        print(f"Path {start.to_string()} -> {goal.to_string()}")
        print(f"  Steps: {result.cost}")
        print(f"  Operators: {result.operators}")
        print(f"  Path: {[st.to_string() for st in result.path]}")
    else:
        print("No path found!")

    print("\n=== Theorem 11 Verification ===")
    verification = verify_theorem_11()
    print(f"Verified: {verification['verified']}")
    print(f"Max steps observed: {verification['max_steps_observed']}")
    print(f"Pairs checked: {verification['total_pairs_checked']}")
    if verification["failures"]:
        print(f"Failures: {verification['failures']}")
