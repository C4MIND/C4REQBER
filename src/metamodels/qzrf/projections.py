"""
C4REQBER: QZRF Projections to C4
Each QZRF operator maps to target C4 coordinates and transformation paths.
"""
from __future__ import annotations

from src.c4.state import C4State
from src.metamodels.qzrf.operators import QzrfPhase


class QzrfC4Projections:
    """
    Maps QZRF operators to C4 state space projections.

    For each QZRF phase, defines the typical C4 trajectory:
    - Divergence:    S↓ (concretize), A↑ (expand agency)
    - Modulation:    T→Present (focus), S→Abstract (tune)
    - Network:       A→System (connect), S→Abstract (relate)
    - Integration:   S→Meta (unify), A→System (merge all)
    - Topology:      T→Future (transform), S→Meta (restructure)
    """

    PHASE_C4_PATTERNS = {
        QzrfPhase.DIVERGENCE: {
            "time_shift": +1,  # Future-oriented
            "scale_shift": -1,  # Concretize to expand
            "agency_shift": +1,  # Expand perspective
            "description": "Expand search space: Future, Concrete, System-wide",
        },
        QzrfPhase.MODULATION: {
            "time_shift": 0,  # Present focus
            "scale_shift": +1,  # Abstract to tune
            "agency_shift": 0,  # Maintain perspective
            "description": "Adjust parameters: Present, Abstract, balanced Agency",
        },
        QzrfPhase.NETWORK: {
            "time_shift": 0,  # Present
            "scale_shift": +1,  # Abstract to connect
            "agency_shift": +1,  # System perspective
            "description": "Connect components: Present, Abstract, System",
        },
        QzrfPhase.INTEGRATION: {
            "time_shift": 0,  # Present
            "scale_shift": +2,  # Meta to unify
            "agency_shift": +1,  # System-wide
            "description": "Merge into whole: Present, Meta, System",
        },
        QzrfPhase.TOPOLOGY: {
            "time_shift": +1,  # Future
            "scale_shift": +2,  # Meta
            "agency_shift": +1,  # System
            "description": "Transform structure: Future, Meta, System",
        },
    }

    @classmethod
    def project_phase_to_c4(cls, phase: QzrfPhase, current_state: C4State) -> C4State:
        """Project a QZRF phase onto a target C4 state."""
        pattern = cls.PHASE_C4_PATTERNS[phase]
        return C4State(
            T=(current_state.T + pattern["time_shift"]) % 3,  # type: ignore[operator]
            S=(current_state.S + pattern["scale_shift"]) % 3,  # type: ignore[operator]
            A=(current_state.A + pattern["agency_shift"]) % 3,  # type: ignore[operator]
        )

    @classmethod
    def get_phase_trajectory(cls, phase: QzrfPhase) -> dict[str, any]:  # type: ignore[valid-type]
        """Get the C4 trajectory pattern for a phase."""
        return cls.PHASE_C4_PATTERNS.get(phase, {})

    @classmethod
    def full_qzrf_pipeline(
        cls, start_state: C4State
    ) -> list[tuple[QzrfPhase, C4State]]:
        """
        Full QZRF pipeline: apply all 5 phases in sequence.
        Returns list of (phase, target_state) pairs.
        """
        states = []
        current = start_state
        for phase in QzrfPhase:
            target = cls.project_phase_to_c4(phase, current)
            states.append((phase, target))
            current = target
        return states
