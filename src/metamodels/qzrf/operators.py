"""
C4REQBER: QZRF 14 Operators
Quantum-Zonal Recursion Framework — universal meta-heuristics for optimization.

QZRF Phases:
1. Дивергенция (Divergence)    — expand search space
2. Модуляция (Modulation)      — adjust parameters
3. Сеть (Network)              — connect partial solutions
4. Интеграция (Integration)    — merge into coherent whole
5. Топология (Topology)        — transform structure itself

14 Operators mapped to C4 target coordinates.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.c4.state import C4State


class QzrfPhase(Enum):
    """QzrfPhase."""
    DIVERGENCE = "divergence"
    MODULATION = "modulation"
    NETWORK = "network"
    INTEGRATION = "integration"
    TOPOLOGY = "topology"


@dataclass(frozen=True)
class QzrfOperator:
    """QZRF Operator: meta-heuristic with C4 target coordinates."""

    id: str
    name: str
    name_ru: str
    phase: QzrfPhase
    description: str
    c4_target: C4State  # Target C4 state after applying this operator
    applicable_states: list[
        tuple[int, int, int]
    ]  # C4 coords where this operator is effective

    def is_applicable(self, state: C4State) -> bool:
        return state.to_tuple() in self.applicable_states


class QzrfLibrary:
    """Library of all 14 QZRF operators."""

    OPERATORS = [
        # ═══════════════════════════════════════════════════════
        # PHASE 1: DIVERGENCE (expand, decompose, explore)
        # ═══════════════════════════════════════════════════════
        QzrfOperator(
            id="QZ-01",
            name="Branching",
            name_ru="Ветвление",
            phase=QzrfPhase.DIVERGENCE,
            description="Decompose problem into independent sub-problems and solve in parallel",
            c4_target=C4State(T=2, S=0, A=2),  # Future, Concrete, System
            applicable_states=[
                (0, 0, 0),
                (0, 0, 1),
                (0, 0, 2),
                (1, 0, 0),
                (1, 0, 1),
                (1, 0, 2),
            ],
        ),
        QzrfOperator(
            id="QZ-02",
            name="Annealing",
            name_ru="Отжиг",
            phase=QzrfPhase.DIVERGENCE,
            description="Introduce controlled randomness to escape local optima",
            c4_target=C4State(T=2, S=1, A=1),  # Future, Abstract, Other
            applicable_states=[
                (1, 1, 0),
                (1, 1, 1),
                (1, 1, 2),
                (2, 1, 0),
                (2, 1, 1),
                (2, 1, 2),
            ],
        ),
        QzrfOperator(
            id="QZ-03",
            name="Projection",
            name_ru="Проекция",
            phase=QzrfPhase.DIVERGENCE,
            description="Project problem onto a different domain where it's easier to solve",
            c4_target=C4State(T=2, S=2, A=2),  # Future, Meta, System
            applicable_states=[
                (0, 1, 0),
                (0, 1, 1),
                (0, 1, 2),
                (1, 1, 0),
                (1, 1, 1),
                (1, 1, 2),
                (2, 1, 0),
                (2, 1, 1),
                (2, 1, 2),
            ],
        ),
        # ═══════════════════════════════════════════════════════
        # PHASE 2: MODULATION (adjust, tune, refine)
        # ═══════════════════════════════════════════════════════
        QzrfOperator(
            id="QZ-04",
            name="Gradient Step",
            name_ru="Градиентный шаг",
            phase=QzrfPhase.MODULATION,
            description="Move in the direction of steepest improvement",
            c4_target=C4State(T=1, S=0, A=1),  # Present, Concrete, Other
            applicable_states=[
                (0, 0, 0),
                (1, 0, 0),
                (2, 0, 0),
                (0, 0, 1),
                (1, 0, 1),
                (2, 0, 1),
            ],
        ),
        QzrfOperator(
            id="QZ-05",
            name="Parametric Sweep",
            name_ru="Параметрический разброс",
            phase=QzrfPhase.MODULATION,
            description="Systematically vary parameters to find optimal configuration",
            c4_target=C4State(T=1, S=1, A=2),  # Present, Abstract, System
            applicable_states=[
                (0, 1, 2),
                (1, 1, 2),
                (2, 1, 2),
                (0, 2, 2),
                (1, 2, 2),
                (2, 2, 2),
            ],
        ),
        QzrfOperator(
            id="QZ-06",
            name="Resonance Tuning",
            name_ru="Резонансная настройка",
            phase=QzrfPhase.MODULATION,
            description="Adjust to match natural frequencies/patterns of the system",
            c4_target=C4State(T=1, S=2, A=0),  # Present, Meta, Self
            applicable_states=[
                (0, 2, 0),
                (1, 2, 0),
                (2, 2, 0),
                (0, 2, 1),
                (1, 2, 1),
                (2, 2, 1),
            ],
        ),
        # ═══════════════════════════════════════════════════════
        # PHASE 3: NETWORK (connect, relate, synthesize)
        # ═══════════════════════════════════════════════════════
        QzrfOperator(
            id="QZ-07",
            name="Graph Weave",
            name_ru="Плетение графа",
            phase=QzrfPhase.NETWORK,
            description="Connect partial solutions into a network of dependencies",
            c4_target=C4State(T=1, S=1, A=2),  # Present, Abstract, System
            applicable_states=[
                (0, 0, 2),
                (1, 0, 2),
                (2, 0, 2),
                (0, 1, 2),
                (1, 1, 2),
                (2, 1, 2),
            ],
        ),
        QzrfOperator(
            id="QZ-08",
            name="Cross-Linking",
            name_ru="Перекрёстное связывание",
            phase=QzrfPhase.NETWORK,
            description="Create unexpected connections between unrelated components",
            c4_target=C4State(T=2, S=2, A=1),  # Future, Meta, Other
            applicable_states=[
                (0, 1, 1),
                (1, 1, 1),
                (2, 1, 1),
                (0, 2, 1),
                (1, 2, 1),
                (2, 2, 1),
            ],
        ),
        QzrfOperator(
            id="QZ-09",
            name="Eigenmode Extraction",
            name_ru="Извлечение собственных мод",
            phase=QzrfPhase.NETWORK,
            description="Find fundamental modes/structures that compose the whole",
            c4_target=C4State(T=1, S=2, A=2),  # Present, Meta, System
            applicable_states=[
                (0, 2, 2),
                (1, 2, 2),
                (2, 2, 2),
            ],
        ),
        # ═══════════════════════════════════════════════════════
        # PHASE 4: INTEGRATION (merge, unify, synthesize)
        # ═══════════════════════════════════════════════════════
        QzrfOperator(
            id="QZ-10",
            name="Synthesis",
            name_ru="Синтез",
            phase=QzrfPhase.INTEGRATION,
            description="Merge multiple partial solutions into a coherent whole",
            c4_target=C4State(T=1, S=2, A=2),  # Present, Meta, System
            applicable_states=[
                (0, 0, 2),
                (1, 0, 2),
                (2, 0, 2),
                (0, 1, 2),
                (1, 1, 2),
                (2, 1, 2),
                (0, 2, 2),
                (1, 2, 2),
                (2, 2, 2),
            ],
        ),
        QzrfOperator(
            id="QZ-11",
            name="Harmonization",
            name_ru="Гармонизация",
            phase=QzrfPhase.INTEGRATION,
            description="Resolve conflicts between solution components",
            c4_target=C4State(T=1, S=1, A=1),  # Present, Abstract, Other
            applicable_states=[
                (0, 0, 1),
                (1, 0, 1),
                (2, 0, 1),
                (0, 1, 1),
                (1, 1, 1),
                (2, 1, 1),
            ],
        ),
        QzrfOperator(
            id="QZ-12",
            name="Crystallization",
            name_ru="Кристаллизация",
            phase=QzrfPhase.INTEGRATION,
            description="Freeze the solution structure into stable form",
            c4_target=C4State(T=1, S=0, A=0),  # Present, Concrete, Self
            applicable_states=[
                (0, 0, 0),
                (1, 0, 0),
                (2, 0, 0),
                (0, 0, 1),
                (1, 0, 1),
                (2, 0, 1),
                (0, 0, 2),
                (1, 0, 2),
                (2, 0, 2),
            ],
        ),
        # ═══════════════════════════════════════════════════════
        # PHASE 5: TOPOLOGY (transform structure)
        # ═══════════════════════════════════════════════════════
        QzrfOperator(
            id="QZ-13",
            name="Space Folding",
            name_ru="Свёртка пространства",
            phase=QzrfPhase.TOPOLOGY,
            description="Change the topology of the problem space itself",
            c4_target=C4State(T=2, S=2, A=2),  # Future, Meta, System
            applicable_states=[
                (0, 1, 2),
                (0, 2, 2),
                (1, 1, 2),
                (1, 2, 2),
            ],
        ),
        QzrfOperator(
            id="QZ-14",
            name="Dimensional Lift",
            name_ru="Подъём размерности",
            phase=QzrfPhase.TOPOLOGY,
            description="Embed problem in higher-dimensional space for new solutions",
            c4_target=C4State(T=2, S=2, A=2),  # Future, Meta, System
            applicable_states=[
                (0, 0, 0),
                (0, 1, 0),
                (0, 2, 0),
                (1, 0, 0),
                (1, 1, 0),
                (1, 2, 0),
            ],
        ),
    ]

    def __init__(self) -> None:
        self._by_id = {op.id: op for op in self.OPERATORS}
        self._by_phase: dict[str, Any] = {}
        for op in self.OPERATORS:
            self._by_phase.setdefault(op.phase, []).append(op)  # type: ignore[call-overload]

    def get(self, op_id: str) -> QzrfOperator | None:
        return self._by_id.get(op_id)

    def by_phase(self, phase: QzrfPhase) -> list[QzrfOperator]:
        return self._by_phase.get(phase, [])  # type: ignore[call-overload, no-any-return]

    def applicable_to(self, state: C4State) -> list[QzrfOperator]:
        return [op for op in self.OPERATORS if op.is_applicable(state)]

    def recommend_sequence(self, start: C4State, end: C4State) -> list[str]:
        """Recommend QZRF operator sequence for a C4 transition."""
        # Simple heuristic: find operators whose target states are on the path
        from src.c4.engine import C4Space

        space = C4Space()
        path = space.shortest_path(start, end)
        recommended = []

        for transition in path.transitions:
            candidates = self.applicable_to(transition.from_state)
            if candidates:
                # Pick the one whose target is closest to the transition's goal
                best = min(
                    candidates,
                    key=lambda op: space.hamming_distance(
                        op.c4_target, transition.to_state
                    ),
                )
                recommended.append(best.id)
            else:
                recommended.append("QZ-01")  # Default fallback

        return recommended

    def all_operators(self) -> list[QzrfOperator]:
        return list(self.OPERATORS)
