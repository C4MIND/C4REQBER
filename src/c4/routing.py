from __future__ import annotations


"""FRA Routing: Fingerprint-Route-Adapt with BFS and Theorem 9 integration.

FRA = Fingerprint-Route-Adapt
Input: C4 fingerprint (state)
Output: optimal operator sequence for reaching target state

Uses BFS with heuristic: prefer operators that decrease distance to target.
Theorem 9: path length = Hamming distance (for undirected C4 space).
Quality presets: synthesis, mp_rotation, validation.
"""

import re
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.c4.engine import C4Path, C4Space, C4State, C4Transition


class QualityPreset(Enum):
    """Quality presets for routing optimization."""

    SYNTHESIS = "synthesis"       # Favor creative/integrative operators
    MP_ROTATION = "mp_rotation"   # Favor metaprogram diversity
    VALIDATION = "validation"     # Favor verification/test operators


@dataclass
class RoutePlan:
    """A planned route through C4 state space."""

    start_state: C4State
    target_state: C4State
    path: C4Path
    preset: QualityPreset | None = None
    hamming_distance: int = 0
    convergence_check: dict[str, Any] = field(default_factory=dict)

    @property
    def operators(self) -> list[str]:
        return self.path.operators

    @property
    def is_optimal(self) -> bool:
        """Theorem 9: path is optimal if length equals Hamming distance."""
        return self.path.length == self.hamming_distance

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_state": str(self.start_state),
            "target_state": str(self.target_state),
            "operators": self.operators,
            "length": self.path.length,
            "hamming_distance": self.hamming_distance,
            "is_optimal": self.is_optimal,
            "preset": self.preset.value if self.preset else None,
            "convergence_check": self.convergence_check,
        }


class FRARouter:
    """
    FRA Router: Fingerprint-Route-Adapt for C4 state space.

    Implements BFS with heuristic routing through Z_3^3 = 27 states.
    Theorem 9: shortest path length = Hamming distance between states.
    Theorem 11: any state reachable from any other in <= 6 steps.
    """

    OPERATORS: dict[str, list[str]] = {
        'sense': ['detect', 'scan', 'focus', 'track'],
        'process': ['parse', 'filter', 'compress', 'expand'],
        'modulate': ['amplify', 'attenuate', 'tune', 'shift'],
        'structure': ['connect', 'separate', 'layer', 'crystallize'],
        'flow': ['channel', 'block', 'cycle', 'pulse'],
    }

    ALL_OPERATORS: list[str] = [
        op for family in OPERATORS.values() for op in family
    ]

    SITUATION_MATRIX: dict[str, tuple[str, ...]] = {
        'chaos': ('scan', 'parse', 'filter', 'focus'),
        'stagnation': ('pulse', 'shift', 'amplify', 'channel'),
        'conflict': ('separate', 'track', 'tune', 'connect'),
        'entropy': ('detect', 'block', 'layer', 'crystallize'),
        'overload': ('filter', 'compress', 'attenuate', 'focus'),
        'isolation': ('scan', 'connect', 'channel', 'pulse'),
        'rigidity': ('shift', 'expand', 'tune', 'cycle'),
    }

    SITUATION_KEYWORDS: dict[str, list[str]] = {
        'chaos': ['confusion', 'disorder', 'unpredictable', 'turbulence', 'messy', 'random'],
        'stagnation': ['stuck', 'plateau', 'stale', 'no progress', 'dead end', 'stagnant'],
        'conflict': ['contradiction', 'debate', 'opposing', 'tension', 'clash', 'disagree'],
        'entropy': ['decay', 'degradation', 'breakdown', 'deterioration', 'decaying', 'falling apart'],
        'overload': ['too much', 'overwhelm', 'excessive', 'complexity', 'information overload', 'drowning'],
        'isolation': ['alone', 'disconnect', 'gap', 'separated', 'fragmented', 'silo'],
        'rigidity': ['fixed', 'inflexible', 'rigid', 'resistance', 'orthodoxy', 'dogma', 'unchanging'],
    }

    SITUATION_TO_C4: dict[str, C4State] = {
        'chaos': C4State(T=0, S=0, A=0),
        'stagnation': C4State(T=0, S=1, A=0),
        'conflict': C4State(T=1, S=0, A=1),
        'entropy': C4State(T=0, S=0, A=2),
        'overload': C4State(T=1, S=2, A=0),
        'isolation': C4State(T=1, S=0, A=0),
        'rigidity': C4State(T=2, S=1, A=2),
    }

    # Quality-preset operator preferences
    PRESET_PREFERENCES: dict[QualityPreset, dict[str, float]] = {
        QualityPreset.SYNTHESIS: {
            'connect': 1.5, 'crystallize': 1.4, 'expand': 1.3,
            'layer': 1.2, 'pulse': 1.1,
        },
        QualityPreset.MP_ROTATION: {
            'shift': 1.5, 'tune': 1.4, 'cycle': 1.3,
            'amplify': 1.2, 'attenuate': 1.2,
        },
        QualityPreset.VALIDATION: {
            'detect': 1.5, 'track': 1.4, 'focus': 1.3,
            'scan': 1.2, 'filter': 1.1,
        },
    }

    def __init__(self) -> None:
        self.c4_space = C4Space()
        self._feedback_history: list[dict[str, Any]] = []

    # ── Fingerprint ──────────────────────────────────────────────────

    def fingerprint(self, problem: str) -> dict[str, Any]:
        """Classify problem into situation type -> operators -> C4 state."""
        problem_lower = problem.lower()
        scores: dict[str, int] = {}
        for situation, keywords in self.SITUATION_KEYWORDS.items():
            score = 0
            for kw in keywords:
                score += len(re.findall(re.escape(kw), problem_lower))
            scores[situation] = score

        best_situation = max(scores, key=lambda k: scores[k]) if max(scores.values()) > 0 else 'chaos'
        ops = list(self.SITUATION_MATRIX[best_situation])
        c4_state = self.SITUATION_TO_C4[best_situation]

        return {
            'situation': best_situation,
            'recommended_operators': ops,
            'c4_state': c4_state,
            'scores': scores,
        }

    def classify_c4_state(self, problem: str) -> C4State:
        """Map problem text directly to a C4 state via fingerprint."""
        fp = self.fingerprint(problem)
        return fp['c4_state']

    # ── Route (legacy API, preserved) ────────────────────────────────

    def route(self, situation: str, gap_pct: float) -> list[str]:
        """Build operator chain based on situation + gap size."""
        base_ops = list(self.SITUATION_MATRIX.get(situation, self.SITUATION_MATRIX['chaos']))

        if gap_pct < 30:
            chain = ['tune', 'adjust']
            chain += base_ops[:1]
            return chain

        if gap_pct <= 70:
            chain = base_ops[:2] + ['shift', 'transform']
            chain += base_ops[2:]
            return chain

        chain = base_ops + ['crystallize', 'verify']
        return chain

    # ── BFS Routing with Heuristic ───────────────────────────────────

    def find_route(
        self,
        start: C4State,
        target: C4State,
        preset: QualityPreset | None = None,
    ) -> RoutePlan:
        """
        Find optimal operator sequence from start to target using BFS.

        Theorem 9: For undirected C4 space, shortest path length equals
        Hamming distance between start and target states.
        """
        space = self.c4_space
        hamming = space.hamming_distance(start, target)

        if hamming == 0:
            path = C4Path(start_state=start, end_state=target)
            return RoutePlan(
                start_state=start,
                target_state=target,
                path=path,
                preset=preset,
                hamming_distance=0,
                convergence_check={"converged": True, "reason": "already_at_target"},
            )

        # BFS with heuristic: prefer operators decreasing Hamming distance
        queue: deque[tuple[C4State, list[C4Transition]]] = deque()
        queue.append((start, []))
        visited: set[tuple[int, int, int]] = {start.to_tuple()}
        shortest_len = None
        best_path: list[C4Transition] = []

        while queue:
            state, transitions = queue.popleft()

            if shortest_len is not None and len(transitions) >= shortest_len:
                break

            if state.to_tuple() == target.to_tuple():
                best_path = transitions
                shortest_len = len(transitions)
                break

            if len(transitions) >= 6:  # Theorem 11 upper bound
                continue

            # Generate neighbors, sorted by heuristic
            # Exclude iota: it is a global involution, not a single-axis step.
            neighbors = [
                (name, nxt) for name, nxt in space.neighbors(state)
                if name != "iota"
            ]
            neighbors = self._sort_by_heuristic(neighbors, target, preset)

            for op_name, new_state in neighbors:
                new_tuple = new_state.to_tuple()
                if new_tuple in visited:
                    continue
                visited.add(new_tuple)
                transition = C4Transition(
                    operator=op_name,
                    from_state=state,
                    to_state=new_state,
                    description=f"{state} -> {new_state} via {op_name}",
                )
                queue.append((new_state, transitions + [transition]))

        path = C4Path(
            transitions=best_path,
            start_state=start,
            end_state=best_path[-1].to_state if best_path else start,
        )

        converged = path.length == hamming
        convergence_check = {
            "converged": converged,
            "hamming_distance": hamming,
            "actual_length": path.length,
            "theorem_9_satisfied": converged,
        }

        return RoutePlan(
            start_state=start,
            target_state=target,
            path=path,
            preset=preset,
            hamming_distance=hamming,
            convergence_check=convergence_check,
        )

    def _sort_by_heuristic(
        self,
        neighbors: list[tuple[str, C4State]],
        target: C4State,
        preset: QualityPreset | None,
    ) -> list[tuple[str, C4State]]:
        """Sort neighbors by preference: closer to target, then preset bonuses."""
        space = self.c4_space
        preferences = self.PRESET_PREFERENCES.get(preset, {}) if preset else {}

        def _score_item(item: tuple[str, C4State]) -> float:
            """Score."""
            op_name, state = item
            dist = space.hamming_distance(state, target)
            bonus = preferences.get(op_name, 1.0)
            return dist / bonus  # Lower is better

        return sorted(neighbors, key=_score_item)

    # ── Adaptive Routing ─────────────────────────────────────────────

    def adaptive_route(
        self,
        start: C4State,
        target: C4State,
        preset: QualityPreset | None = None,
        max_steps: int = 6,
    ) -> RoutePlan:
        """
        Adaptive routing with feedback-based operator ranking.
        Re-routes if predicted next state diverges from expected.
        """
        space = self.c4_space
        current = start
        transitions: list[C4Transition] = []

        for step in range(max_steps):
            if current.to_tuple() == target.to_tuple():
                break

            neighbors = [
                (name, nxt) for name, nxt in space.neighbors(current)
                if name != "iota"
            ]
            neighbors = self._sort_by_heuristic(neighbors, target, preset)

            # Apply feedback-based re-ranking
            neighbors = self._apply_feedback_ranking(neighbors, target)

            if not neighbors:
                break

            op_name, next_state = neighbors[0]
            transitions.append(C4Transition(
                operator=op_name,
                from_state=current,
                to_state=next_state,
                description=f"Step {step + 1}: {op_name}",
            ))
            current = next_state

        path = C4Path(
            transitions=transitions,
            start_state=start,
            end_state=current,
        )
        hamming = space.hamming_distance(start, target)

        return RoutePlan(
            start_state=start,
            target_state=target,
            path=path,
            preset=preset,
            hamming_distance=hamming,
            convergence_check={
                "converged": current.to_tuple() == target.to_tuple(),
                "hamming_distance": hamming,
                "actual_length": path.length,
            },
        )

    def _apply_feedback_ranking(
        self,
        neighbors: list[tuple[str, C4State]],
        target: C4State,
    ) -> list[tuple[str, C4State]]:
        """Re-rank neighbors based on historical feedback scores."""
        if not self._feedback_history:
            return neighbors

        op_scores: dict[str, float] = {}
        for entry in self._feedback_history:
            op = entry.get("operator", "")
            score = entry.get("success_score", 0.5)
            op_scores[op] = op_scores.get(op, 0.0) + score

        # Normalize
        if op_scores:
            max_score = max(op_scores.values())
            op_scores = {k: v / max_score for k, v in op_scores.items()}

        def _score_item(item: tuple[str, C4State]) -> float:
            """Score."""
            op_name, state = item
            dist = self.c4_space.hamming_distance(state, target)
            feedback_bonus = op_scores.get(op_name, 0.5)
            return dist - feedback_bonus

        return sorted(neighbors, key=_score_item)

    def record_feedback(self, operator: str, success_score: float) -> None:
        """Record performance feedback for adaptive routing."""
        self._feedback_history.append({
            "operator": operator,
            "success_score": success_score,
        })

    # ── Quality Preset Helpers ───────────────────────────────────────

    def route_synthesis(self, start: C4State, target: C4State) -> RoutePlan:
        """Route optimized for synthesis/creative integration."""
        return self.find_route(start, target, preset=QualityPreset.SYNTHESIS)

    def route_mp_rotation(self, start: C4State, target: C4State) -> RoutePlan:
        """Route optimized for metaprogram diversity and rotation."""
        return self.find_route(start, target, preset=QualityPreset.MP_ROTATION)

    def route_validation(self, start: C4State, target: C4State) -> RoutePlan:
        """Route optimized for verification and validation."""
        return self.find_route(start, target, preset=QualityPreset.VALIDATION)

    # ── Utilities ────────────────────────────────────────────────────

    def operator_family(self, op: str) -> str | None:
        """Return the family name for a given operator."""
        for family, ops in self.OPERATORS.items():
            if op in ops:
                return family
        return None

    @classmethod
    def list_situations(cls) -> list[str]:
        return list(cls.SITUATION_MATRIX.keys())

    @classmethod
    def list_operator_families(cls) -> list[str]:
        return list(cls.OPERATORS.keys())

    @classmethod
    def list_all_operators(cls) -> list[str]:
        return [
            f"{family}:{op}"
            for family, ops in cls.OPERATORS.items()
            for op in ops
        ]

    def get_feedback_stats(self) -> dict[str, Any]:
        """Return statistics about recorded feedback."""
        if not self._feedback_history:
            return {"count": 0, "average_score": 0.0}

        scores = [e["success_score"] for e in self._feedback_history]
        return {
            "count": len(scores),
            "average_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
        }
