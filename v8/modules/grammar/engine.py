"""
TURBO-CDI v8.0 - Grammar Module
L5: Pentad × Septet (35 transformations)

Standalone module for transformation grammar.
No dependencies on other v8 modules.
"""

from dataclasses import dataclass
from typing import Optional, List
from modules import PentadOperation, SeptetObject


@dataclass(frozen=True)
class Transformation:
    """A Pentad × Septet transformation"""

    operation: PentadOperation
    target: SeptetObject

    def __repr__(self):
        return f"{self.operation.value} {self.target.value}"

    @property
    def effectiveness_base(self) -> float:
        """Base effectiveness before domain adjustment"""
        # Operations have different inherent effectiveness
        base_scores = {
            PentadOperation.ACTIVATE: 0.75,
            PentadOperation.INHIBIT: 0.70,
            PentadOperation.MODULATE: 0.85,
            PentadOperation.REGULATE: 0.80,
            PentadOperation.DISRUPT: 0.65,
        }
        return base_scores.get(self.operation, 0.70)


class GrammarEngine:
    """
    L5: Universal Grammar Engine

    Manages the 35 possible transformations (5 ops × 7 targets)
    with domain-specific effectiveness profiles.
    """

    def __init__(self):
        self._transformations: dict[tuple, Transformation] = {}
        self._build_transformations()

    def _build_transformations(self):
        """Build all 35 transformations"""
        for op in PentadOperation:
            for target in SeptetObject:
                key = (op, target)
                self._transformations[key] = Transformation(op, target)

    def get_transformation(
        self, operation: PentadOperation, target: SeptetObject
    ) -> Transformation:
        """Get a specific transformation"""
        return self._transformations.get((operation, target))

    def get_all_transformations(self) -> List[Transformation]:
        """Get all 35 transformations"""
        return list(self._transformations.values())

    def get_by_operation(self, operation: PentadOperation) -> List[Transformation]:
        """Get all transformations for an operation"""
        return [t for t in self._transformations.values() if t.operation == operation]

    def get_by_target(self, target: SeptetObject) -> List[Transformation]:
        """Get all transformations for a target"""
        return [t for t in self._transformations.values() if t.target == target]

    def validate_composition(self, transformations: List[Transformation]) -> bool:
        """
        Validate that a sequence of transformations is composable.

        Rules:
        - Max 6 steps (Theorem 11)
        - No consecutive DISRUPT operations (unstable)
        - MODULATE should follow major changes
        """
        if len(transformations) > 6:
            return False

        # Check for consecutive DISRUPT
        for i in range(len(transformations) - 1):
            if (
                transformations[i].operation == PentadOperation.DISRUPT
                and transformations[i + 1].operation == PentadOperation.DISRUPT
            ):
                return False

        return True

    def calculate_effectiveness(
        self, transformation: Transformation, domain_profile: Optional[dict] = None
    ) -> float:
        """
        Calculate effectiveness for a transformation.

        If domain_profile provided, uses domain-specific weights.
        Otherwise returns base effectiveness.
        """
        base = transformation.effectiveness_base

        if domain_profile and "pentad" in domain_profile:
            # Apply domain-specific adjustment
            op_key = transformation.operation.name.lower()
            domain_weight = domain_profile["pentad"].get(op_key, 0.5)
            return base * 0.7 + domain_weight * 0.3

        return base
