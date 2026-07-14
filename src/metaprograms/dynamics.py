"""
UCOS Layer 3: Dynamics

Integrates QZRF operators with FRARouter for adaptive C4 state navigation.
Provides the dynamic execution layer of the UCOS stack.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from metamodels.qzrf.operators import QzrfLibrary, QzrfOperator
from src.c4.routing import FRARouter, QualityPreset, RoutePlan
from src.c4.state import C4State


@dataclass
class DynamicsResult:
    """Result of a Layer 3 dynamics execution."""

    start_state: C4State
    target_state: C4State
    route: RoutePlan
    qzrf_sequence: list[QzrfOperator]
    adaptive_steps: list[dict[str, Any]] = field(default_factory=list)
    convergence_achieved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_state": str(self.start_state),
            "target_state": str(self.target_state),
            "route": self.route.to_dict(),
            "qzrf_sequence": [op.id for op in self.qzrf_sequence],
            "adaptive_steps": self.adaptive_steps,
            "convergence_achieved": self.convergence_achieved,
        }


class UCOSLayer3Dynamics:
    """
    UCOS Layer 3: Dynamics

    Responsibilities:
    - Execute QZRF operators within C4 state transitions
    - Use FRARouter for optimal pathfinding
    - Adapt routes based on intermediate state feedback
    - Map QZRF operators to C4 transitions
    """

    def __init__(self) -> None:
        self.router = FRARouter()
        self.qzrf = QzrfLibrary()

    def execute_transition(
        self,
        start: C4State,
        target: C4State,
        preset: QualityPreset | None = None,
    ) -> DynamicsResult:
        """
        Execute a full C4 state transition using FRARouter + QZRF operators.
        """
        route = self.router.find_route(start, target, preset=preset)

        # Map route operators to QZRF operators
        qzrf_sequence = self._map_to_qzrf(route, start, target)

        # Simulate adaptive execution
        adaptive_steps = self._simulate_adaptive_execution(route, qzrf_sequence)

        convergence = route.path.length == route.hamming_distance

        return DynamicsResult(
            start_state=start,
            target_state=target,
            route=route,
            qzrf_sequence=qzrf_sequence,
            adaptive_steps=adaptive_steps,
            convergence_achieved=convergence,
        )

    def _map_to_qzrf(
        self,
        route: RoutePlan,
        start: C4State,
        target: C4State,
    ) -> list[QzrfOperator]:
        """Map C4 route transitions to QZRF operators."""
        sequence: list[QzrfOperator] = []
        current = start

        for transition in route.path.transitions:
            # Find QZRF operators applicable to current state
            applicable = self.qzrf.applicable_to(current)

            # Pick operator whose target is closest to transition destination
            if applicable:
                best = min(
                    applicable,
                    key=lambda op: self.router.c4_space.hamming_distance(
                        op.c4_target, transition.to_state
                    ),
                )
                sequence.append(best)
            else:
                # Fallback: use first operator
                all_ops = self.qzrf.all_operators()
                if all_ops:
                    sequence.append(all_ops[0])

            current = transition.to_state

        return sequence

    def _simulate_adaptive_execution(
        self,
        route: RoutePlan,
        qzrf_sequence: list[QzrfOperator],
    ) -> list[dict[str, Any]]:
        """Simulate step-by-step execution with feedback."""
        steps: list[dict[str, Any]] = []
        current = route.start_state

        for i, (transition, qzrf_op) in enumerate(
            zip(route.path.transitions, qzrf_sequence, strict=False)
        ):
            step = {
                "step": i + 1,
                "operator": transition.operator,
                "qzrf_operator": qzrf_op.id,
                "from_state": str(current),
                "expected_state": str(transition.to_state),
                "actual_state": str(transition.to_state),  # Simulated perfect execution
                "deviation": 0.0,
            }
            steps.append(step)
            current = transition.to_state

        return steps

    def adaptive_reroute(
        self,
        current: C4State,
        target: C4State,
        last_operator: str,
        success_score: float,
    ) -> RoutePlan:
        """
        Re-route from current position after recording feedback.
        """
        self.router.record_feedback(last_operator, success_score)
        return self.router.adaptive_route(current, target)
