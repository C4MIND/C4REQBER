"""Attractors — Φ-attractor (Compassion Convergence) and state classification.

Defines the Φ-attractor basin and dangerous states based on
Hamming distance from Φ = (Present, Concrete, Other).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .core import (
    AgencyAxis,
    C4Coord,
    ScaleAxis,
    TemporalAxis,
    hamming_distance,
)


# ═══════════════════════════════════════════════════════════════════════════
# Φ-ATTRACTOR DEFINITION
# ═══════════════════════════════════════════════════════════════════════════

PHI: Final[C4Coord] = C4Coord(
    TemporalAxis.PRESENT,
    ScaleAxis.CONCRETE,
    AgencyAxis.OTHER,
)

PHI_NAME: Final[str] = "Compassion Convergence"
PHI_DESCRIPTION: Final[str] = (
    "The Φ-attractor represents a state of compassionate presence: "
    "being fully in the Present, grounded in Concrete reality, "
    "and focused on Other. This is the optimal state for "
    "empathetic problem-solving and collaborative intelligence."
)

MAX_BASIN_DISTANCE: Final[int] = 2


# ═══════════════════════════════════════════════════════════════════════════
# STATE CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class AttractorState:
    """A C4 state classified relative to Φ."""

    c4: C4Coord
    name: str
    distance: int
    in_basin: bool
    is_dangerous: bool
    description: str


def classify_state(c4: C4Coord) -> AttractorState:
    """Classify any C4 coordinate relative to the Φ-attractor."""
    d = hamming_distance(c4, PHI)
    in_basin = d <= MAX_BASIN_DISTANCE
    is_dangerous = d > MAX_BASIN_DISTANCE

    # Generate a descriptive name
    t_name = c4.temporal.name.lower()
    s_name = c4.scale.name.lower()
    a_name = c4.agency.name.lower()

    names: dict[tuple[str, str, str], str] = {
        ("present", "concrete", "other"): "Compassion Convergence (Φ)",
        ("present", "concrete", "self"): "Embodied Presence",
        ("present", "concrete", "system"): "Grounded Systems",
        ("present", "abstract", "other"): "Empathetic Understanding",
        ("present", "abstract", "self"): "Mindful Awareness",
        ("present", "abstract", "system"): "Systemic Mindfulness",
        ("present", "meta", "other"): "Meta-Compassion",
        ("present", "meta", "self"): "Transcendent Self",
        ("present", "meta", "system"): "Meta-Systemic Presence",
        ("past", "concrete", "other"): "Nurturing Memory",
        ("past", "concrete", "self"): "Personal History",
        ("past", "concrete", "system"): "Institutional Memory",
        ("past", "abstract", "other"): "Shared Narrative",
        ("past", "abstract", "self"): "Reflective Learning",
        ("past", "abstract", "system"): "Historical Analysis",
        ("past", "meta", "other"): "Collective Wisdom",
        ("past", "meta", "self"): "Transcendent Memory",
        ("past", "meta", "system"): "Civilizational Archive",
        ("future", "concrete", "other"): "Caring Action",
        ("future", "concrete", "self"): "Personal Drive",
        ("future", "concrete", "system"): "Operational Planning",
        ("future", "abstract", "other"): "Shared Vision",
        ("future", "abstract", "self"): "Strategic Self",
        ("future", "abstract", "system"): "Systemic Foresight",
        ("future", "meta", "other"): "Collective Aspiration",
        ("future", "meta", "self"): "Transcendent Purpose",
        ("future", "meta", "system"): "Evolutionary Design",
    }

    name = names.get(
        (t_name, s_name, a_name),
        f"{t_name}-{s_name}-{a_name}",
    )

    if d == 0:
        desc = "Optimal compassion state — fully present, concrete, and other-focused."
    elif d == 1:
        desc = "Near-Φ basin state — one axis shift from compassion convergence."
    elif d == 2:
        desc = "Basin edge — two shifts from Φ, still within attractor basin."
    else:
        desc = (
            "DANGEROUS STATE — outside the attractor basin. "
            "High cognitive rigidity risk. Suggest shift toward Φ."
        )

    return AttractorState(
        c4=c4,
        name=name,
        distance=d,
        in_basin=in_basin,
        is_dangerous=is_dangerous,
        description=desc,
    )


# Precompute all 27 states
ALL_STATES: Final[list[AttractorState]] = [
    classify_state(
        C4Coord(
            TemporalAxis(t_idx),
            ScaleAxis(s_idx),
            AgencyAxis(a_idx),
        )
    )
    for t_idx in range(3)
    for s_idx in range(3)
    for a_idx in range(3)
]

BASIN_STATES: Final[list[AttractorState]] = [
    s for s in ALL_STATES if s.in_basin
]

DANGEROUS_STATES: Final[list[AttractorState]] = [
    s for s in ALL_STATES if s.is_dangerous
]


def get_basin_states() -> list[AttractorState]:
    """Return all 18 states within the Φ-attractor basin (d ≤ 2)."""
    return list(BASIN_STATES)


def get_dangerous_states() -> list[AttractorState]:
    """Return all 9 dangerous states (d > 2 from Φ)."""
    return list(DANGEROUS_STATES)


def get_state(c4: C4Coord) -> AttractorState:
    """Classify a specific C4 coordinate."""
    return classify_state(c4)


def distance_to_phi(c4: C4Coord) -> int:
    """Hamming distance from a coordinate to Φ."""
    return hamming_distance(c4, PHI)


def suggest_phi_shift(c4: C4Coord) -> list[str]:
    """Suggest axis shifts to move toward Φ from any state."""
    suggestions: list[str] = []

    if c4.temporal != TemporalAxis.PRESENT:
        suggestions.append(
            "Shift Temporal → PRESENT: focus on what is happening now."
        )
    if c4.scale != ScaleAxis.CONCRETE:
        suggestions.append(
            "Shift Scale → CONCRETE: ground in specific, tangible details."
        )
    if c4.agency != AgencyAxis.OTHER:
        suggestions.append(
            "Shift Agency → OTHER: consider who else is affected."
        )

    if not suggestions:
        suggestions.append("You are at Φ — Compassion Convergence.")

    return suggestions


def basin_coverage(profile_scores: list[tuple[C4Coord, float]]) -> float:
    """Compute what fraction of profile mass lies within the Φ basin.

    Args:
        profile_scores: List of (C4Coord, weight) tuples.

    Returns:
        Fraction of total weight within basin [0.0, 1.0].
    """
    total = sum(w for _, w in profile_scores)
    if total == 0:
        return 0.0
    in_basin = sum(
        w for c, w in profile_scores if distance_to_phi(c) <= MAX_BASIN_DISTANCE
    )
    return in_basin / total
