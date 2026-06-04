"""Dempster-Shafer Theory: belief functions and combination rules."""

from __future__ import annotations

from typing import Iterable

import numpy as np
from numpy.typing import NDArray


class FrameOfDiscernment:
    """Frame of Discernment (universal set of hypotheses)."""

    def __init__(self, elements: Iterable[str]) -> None:
        self.elements = tuple(sorted(set(elements)))
        self._index = {e: i for i, e in enumerate(self.elements)}

    def __len__(self) -> int:
        return len(self.elements)

    def __contains__(self, item: str) -> bool:
        return item in self._index

    def __repr__(self) -> str:
        return f"FrameOfDiscernment({list(self.elements)})"

    def index(self, element: str) -> int:
        """Index."""
        if element not in self._index:
            raise ValueError(f"Element {element!r} not in frame")
        return self._index[element]

    def power_set(self) -> list[frozenset[str]]:
        """Return all subsets as frozensets."""
        n = len(self.elements)
        result: list[frozenset[str]] = []
        for i in range(1 << n):
            subset = {self.elements[j] for j in range(n) if (i >> j) & 1}
            result.append(frozenset(subset))
        return result


class BasicBeliefAssignment:
    """Basic Belief Assignment (mass function)."""

    def __init__(self, frame: FrameOfDiscernment) -> None:
        self.frame = frame
        self._masses: dict[frozenset[str], float] = {}

    def assign(self, subset: set[str] | frozenset[str] | str, mass: float) -> BasicBeliefAssignment:
        """Assign mass to a subset."""
        if isinstance(subset, str):
            subset = frozenset({subset})
        else:
            subset = frozenset(subset)
        if not subset.issubset(set(self.frame.elements)):
            raise ValueError("Subset must be within the frame of discernment")
        if mass < 0 or mass > 1:
            raise ValueError("Mass must be in [0, 1]")
        self._masses[subset] = self._masses.get(subset, 0.0) + mass
        return self

    def normalize(self) -> BasicBeliefAssignment:
        """Normalize so masses sum to 1."""
        total = sum(self._masses.values())
        if total == 0:
            raise ValueError("Cannot normalize empty BBA")
        self._masses = {k: v / total for k, v in self._masses.items()}
        return self

    def get_mass(self, subset: set[str] | frozenset[str]) -> float:
        return self._masses.get(frozenset(subset), 0.0)

    def belief(self, subset: set[str] | frozenset[str]) -> float:
        """Belief function Bel(A) = sum_{B ⊆ A} m(B)."""
        target = frozenset(subset)
        return sum(m for s, m in self._masses.items() if s.issubset(target))

    def plausibility(self, subset: set[str] | frozenset[str]) -> float:
        """Plausibility function Pl(A) = sum_{B ∩ A ≠ ∅} m(B)."""
        target = frozenset(subset)
        return sum(m for s, m in self._masses.items() if s & target)

    def __repr__(self) -> str:
        lines = ["BasicBeliefAssignment:"]
        for s, m in sorted(self._masses.items(), key=lambda x: len(x[0])):
            lines.append(f"  {set(s)}: {m:.4f}")
        return "\n".join(lines)

    def focal_elements(self) -> list[frozenset[str]]:
        """Return focal elements (subsets with non-zero mass)."""
        return [s for s, m in self._masses.items() if m > 0]


def dempster_combination(
    bba1: BasicBeliefAssignment,
    bba2: BasicBeliefAssignment,
) -> BasicBeliefAssignment:
    """Dempster's rule of combination for two BBAs."""
    if bba1.frame.elements != bba2.frame.elements:
        raise ValueError("BBAs must share the same frame of discernment")

    result = BasicBeliefAssignment(bba1.frame)
    conflict = 0.0

    for s1, m1 in bba1._masses.items():
        for s2, m2 in bba2._masses.items():
            inter = s1 & s2
            if inter:
                result._masses[inter] = result._masses.get(inter, 0.0) + m1 * m2
            else:
                conflict += m1 * m2

    if conflict >= 1.0 - 1e-12:
        raise ValueError("Complete conflict: Dempster's rule undefined")

    # Normalize by 1 - conflict
    norm = 1.0 - conflict
    result._masses = {k: v / norm for k, v in result._masses.items()}
    return result


def combine_multiple(*bbas: BasicBeliefAssignment) -> BasicBeliefAssignment:
    """Combine multiple BBAs sequentially."""
    if not bbas:
        raise ValueError("At least one BBA required")
    result = bbas[0]
    for bba in bbas[1:]:
        result = dempster_combination(result, bba)
    return result


class EvidenceSensor:
    """Helper to build BBAs from sensor evidence."""

    def __init__(self, frame: FrameOfDiscernment) -> None:
        self.frame = frame

    def from_likelihoods(
        self,
        likelihoods: dict[str, float],
        uncertainty: float = 0.0,
    ) -> BasicBeliefAssignment:
        """Build BBA from likelihoods over singletons."""
        bba = BasicBeliefAssignment(self.frame)
        total = sum(likelihoods.values())
        if total == 0:
            raise ValueError("Likelihoods sum to zero")
        for element, lh in likelihoods.items():
            bba.assign({element}, lh / total * (1 - uncertainty))
        if uncertainty > 0:
            bba.assign(set(self.frame.elements), uncertainty)
        return bba.normalize()

    def from_confusion_matrix(
        self,
        matrix: NDArray[np.float64],
        observed_class: int,
    ) -> BasicBeliefAssignment:
        """Build BBA from a confusion matrix row."""
        if matrix.ndim != 2:
            raise ValueError("Matrix must be 2D")
        row = matrix[observed_class]
        bba = BasicBeliefAssignment(self.frame)
        for i, val in enumerate(row):
            if val > 0:
                bba.assign({self.frame.elements[i]}, float(val))
        return bba.normalize()
