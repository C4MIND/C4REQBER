"""
C4 Navigation Engine — Path finding, state transitions, FRA stub.

Provides:
    - BFS path finding between any two C4 states
    - State transition graph
    - FRA (Fingerprint-Route-Adapt) stub integration

Reference: formal-proofs/c4-comp-v5.agda
Authors: I.G. Selyutin, N.I. Kovalev
"""

from __future__ import annotations

from collections import deque

from .core import C4Operator, C4State, all_27_states, hamming_distance


def bfs_path(start: C4State, goal: C4State) -> list[str] | None:
    """
    Breadth-first search for shortest path between two C4 states.
    In Z₃³, BFS always finds the Hamming-distance-optimal path.
    """
    if start == goal:
        return []

    visited: set[tuple[int, int, int]] = {start.to_tuple()}
    queue: deque[tuple[C4State, list[str]]] = deque([(start, [])])

    while queue:
        current, path = queue.popleft()
        for op in C4Operator.all():
            nxt = current.apply_operator(op)
            nxt_key = nxt.to_tuple()
            if nxt_key in visited:
                continue
            new_path = path + [op]
            if nxt == goal:
                return new_path
            visited.add(nxt_key)
            queue.append((nxt, new_path))

    return None  # unreachable in theory (Theorem 1)


def shortest_path_length(start: C4State, goal: C4State) -> int:
    """Length of the shortest path (equals Hamming distance)."""
    if start == goal:
        return 0
    path = bfs_path(start, goal)
    if path is None:
        raise RuntimeError(f"No path found from {start} to {goal} — contradicts Theorem 1!")
    return len(path)


def all_pairs_shortest_paths() -> dict[tuple[C4State, C4State], list[str]]:
    """Compute shortest paths for all 27×27 pairs."""
    states = all_27_states()
    result: dict[tuple[C4State, C4State], list[str]] = {}
    for s1 in states:
        for s2 in states:
            path = bfs_path(s1, s2)
            if path is None:
                raise RuntimeError(f"Unreachable pair: {s1} -> {s2}")
            result[(s1, s2)] = path
    return result


def verify_canonical_equals_bfs() -> bool:
    """
    Verify Theorem 9: canonical path length == Hamming distance == BFS length.
    Returns True if verified for all pairs.
    """
    states = all_27_states()
    for s1 in states:
        for s2 in states:
            canon = s1.canonical_path(s2)
            bfs = bfs_path(s1, s2)
            if bfs is None:
                return False
            hd = hamming_distance(s1, s2)
            if not (len(canon) == len(bfs) == hd):
                return False
    return True


def _bfs_distance(start: C4State, goal: C4State, ops: list[str]) -> int:
    """BFS shortest-path distance using specified operator set."""
    if start == goal:
        return 0
    visited = {start.to_tuple()}
    queue: deque = deque([(start, 0)])
    while queue:
        current, dist = queue.popleft()
        for op in ops:
            nxt = current.apply_operator(op)
            nxt_key = nxt.to_tuple()
            if nxt_key in visited:
                continue
            if nxt == goal:
                return dist + 1
            visited.add(nxt_key)
            queue.append((nxt, dist + 1))
    raise RuntimeError(f"Unreachable: {start} -> {goal}")


class C4TransitionGraph:
    """
    The full transition graph of Z₃³ under all 6 operators.
    27 nodes, each with 6 outgoing edges (T, S, A, T_INV, S_INV, A_INV).
    """

    def __init__(self) -> None:
        self.states = all_27_states()
        self._edges: dict[C4State, dict[str, C4State]] = {}
        for s in self.states:
            self._edges[s] = {
                C4Operator.T: s.apply_T(),
                C4Operator.T_INV: s.apply_T_inv(),
                C4Operator.S: s.apply_S(),
                C4Operator.S_INV: s.apply_S_inv(),
                C4Operator.A: s.apply_A(),
                C4Operator.A_INV: s.apply_A_inv(),
            }

    def neighbors(self, state: C4State) -> dict[str, C4State]:
        return self._edges[state]

    def neighbor_count(self, state: C4State) -> int:
        return len(set(n.to_tuple() for n in self._edges[state].values()))

    def diameter(self) -> int:
        """Undirected diameter — max BFS distance with all operators."""
        max_dist = 0
        for s1 in self.states:
            for s2 in self.states:
                d = shortest_path_length(s1, s2)
                if d > max_dist:
                    max_dist = d
        return max_dist

    def directed_diameter(self) -> int:
        """Directed diameter with forward-only operators (T,S,A) — Theorem 11: 6."""
        forward_ops = [C4Operator.T, C4Operator.S, C4Operator.A]
        max_dist = 0
        for s1 in self.states:
            for s2 in self.states:
                d = _bfs_distance(s1, s2, forward_ops)
                if d > max_dist:
                    max_dist = d
        return max_dist

    def is_connected(self) -> bool:
        """True if the graph is connected (Theorem 1)."""
        for s1 in self.states:
            for s2 in self.states:
                if bfs_path(s1, s2) is None:
                    return False
        return True


class FRARouter:
    """
    FRA (Fingerprint-Route-Adapt) stub for C4 navigation.

    FRA is the adaptive routing meta-algorithm:
        fingerprint -> route -> adapt

    In the C4 context, a "fingerprint" is the current state F⟨T,S,A⟩,
    the "route" is the canonical path to the target state,
    and "adapt" adjusts based on intermediate feedback.
    """

    def fingerprint(self, state: C4State) -> tuple[int, int, int]:
        """Extract fingerprint from a C4 state."""
        return state.to_tuple()

    def route(self, current: C4State, target: C4State) -> list[str]:
        """Compute route (canonical path) from current to target."""
        return current.canonical_path(target)

    def adapt(
        self,
        current: C4State,
        target: C4State,
        feedback: C4State | None = None,
    ) -> list[str]:
        """
        Adapt route based on feedback.
        If feedback provides an intermediate state, route from there.
        """
        if feedback is not None:
            return feedback.canonical_path(target)
        return self.route(current, target)

    def fra_cycle(
        self,
        current: C4State,
        target: C4State,
    ) -> tuple[tuple[int, int, int], list[str], C4State]:
        """
        Full FRA cycle: fingerprint, route, then apply.
        Returns (fingerprint, route, new_state).
        """
        fp = self.fingerprint(current)
        path = self.route(current, target)
        new_state = current.apply_path(path)
        return fp, path, new_state
