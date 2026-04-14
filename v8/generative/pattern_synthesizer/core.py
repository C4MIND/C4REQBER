"""
TURBO-CDI v8.0 - Pattern Synthesizer
Agent 3: Generative Systems

Synthesizes novel transformation patterns through combinatorial exploration.
Discovers emergent patterns not explicitly programmed.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any, Callable
from enum import Enum
import itertools
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from modules import C4State, PentadOperation, SeptetObject


@dataclass
class Pattern:
    """A synthesized transformation pattern"""

    id: str
    name: str
    operations: List[Tuple[PentadOperation, SeptetObject]]
    c4_path: List[C4State]
    effectiveness_estimate: float
    novelty_score: float  # 0-1, how unique is this pattern
    prerequisites: List[str]
    description: str


class PatternSynthesizer:
    """
    Synthesizes novel transformation patterns.

    Explores the combinatorial space of:
    - 5 operations × 7 objects = 35 base transformations
    - 27 C4 states for navigation context
    - Various compositions and sequences

    Discovers emergent patterns through:
    1. Compositional synthesis (combining known patterns)
    2. Analogical transfer (cross-domain pattern mapping)
    3. Emergence detection (unexpected effective combinations)
    """

    def __init__(self):
        self._known_patterns: Dict[str, Pattern] = {}
        self._effectiveness_cache: Dict[str, float] = {}
        self._initialize_base_patterns()

    def _initialize_base_patterns(self):
        """Initialize with base Pentad × Septet combinations"""
        counter = 0

        for op in PentadOperation:
            for obj in SeptetObject:
                counter += 1
                pattern_id = f"base_{counter:03d}"

                # Calculate base effectiveness
                base_eff = self._calculate_base_effectiveness(op, obj)

                pattern = Pattern(
                    id=pattern_id,
                    name=f"{op.name} {obj.value}",
                    operations=[(op, obj)],
                    c4_path=[],
                    effectiveness_estimate=base_eff,
                    novelty_score=0.0,  # Base patterns are not novel
                    prerequisites=[],
                    description=f"Base pattern: {op.value} applied to {obj.value}",
                )

                self._known_patterns[pattern_id] = pattern

    def _calculate_base_effectiveness(
        self, op: PentadOperation, obj: SeptetObject
    ) -> float:
        """Calculate base effectiveness for operation-object pair"""
        # Operation effectiveness
        op_weights = {
            PentadOperation.MODULATE: 0.85,
            PentadOperation.REGULATE: 0.80,
            PentadOperation.ACTIVATE: 0.75,
            PentadOperation.INHIBIT: 0.70,
            PentadOperation.DISRUPT: 0.65,
        }

        # Object accessibility
        obj_weights = {
            SeptetObject.CONTENT: 0.90,
            SeptetObject.STATE: 0.85,
            SeptetObject.STRUCTURE: 0.80,
            SeptetObject.FUNCTION: 0.75,
            SeptetObject.RELATIONS: 0.70,
            SeptetObject.MEMORY: 0.65,
            SeptetObject.BOUNDARY: 0.60,
        }

        return op_weights.get(op, 0.70) * obj_weights.get(obj, 0.70)

    def synthesize_composition(
        self, pattern_ids: List[str], composition_type: str = "sequence"
    ) -> Optional[Pattern]:
        """
        Synthesize new pattern by composing existing patterns.

        Args:
            pattern_ids: IDs of patterns to compose
            composition_type: "sequence", "parallel", or "nested"

        Returns:
            New synthesized Pattern or None if invalid composition
        """
        # Get component patterns
        components = []
        for pid in pattern_ids:
            if pid not in self._known_patterns:
                return None
            components.append(self._known_patterns[pid])

        if len(components) < 2:
            return None

        # Combine operations
        combined_ops = []
        for comp in components:
            combined_ops.extend(comp.operations)

        # Validate composition
        if not self._validate_composition(combined_ops):
            return None

        # Calculate combined effectiveness
        eff = self._calculate_composition_effectiveness(components, composition_type)

        # Calculate novelty
        novelty = self._calculate_novelty(combined_ops)

        # Generate ID and name
        new_id = f"syn_{len(self._known_patterns) + 1:04d}"
        new_name = self._generate_composition_name(components, composition_type)

        new_pattern = Pattern(
            id=new_id,
            name=new_name,
            operations=combined_ops,
            c4_path=[],  # Would be filled by navigator
            effectiveness_estimate=eff,
            novelty_score=novelty,
            prerequisites=pattern_ids,
            description=f"Synthesized {composition_type} of {len(components)} patterns",
        )

        # Store for future use
        self._known_patterns[new_id] = new_pattern

        return new_pattern

    def _validate_composition(
        self, operations: List[Tuple[PentadOperation, SeptetObject]]
    ) -> bool:
        """Validate that operation sequence is composable"""
        # Rule 1: Max 6 operations (Theorem 11 bound)
        if len(operations) > 6:
            return False

        # Rule 2: No consecutive DISRUPT (too unstable)
        for i in range(len(operations) - 1):
            if (
                operations[i][0] == PentadOperation.DISRUPT
                and operations[i + 1][0] == PentadOperation.DISRUPT
            ):
                return False

        # Rule 3: Balance - can't have all INHIBIT or all ACTIVATE
        op_counts = {}
        for op, _ in operations:
            op_counts[op] = op_counts.get(op, 0) + 1

        if len(operations) >= 3:
            for count in op_counts.values():
                if count > len(operations) * 0.6:  # No operation > 60%
                    return False

        return True

    def _calculate_composition_effectiveness(
        self, components: List[Pattern], composition_type: str
    ) -> float:
        """Calculate effectiveness of composed pattern"""
        base_effs = [c.effectiveness_estimate for c in components]

        if composition_type == "sequence":
            # Sequential effectiveness multiplies (with decay)
            eff = 1.0
            for e in base_effs:
                eff *= e
            return eff ** (1.0 / len(base_effs))  # Geometric mean

        elif composition_type == "parallel":
            # Parallel combines with diminishing returns
            return min(0.95, sum(base_effs) / len(base_effs) * 1.1)

        else:  # nested
            # Nested uses minimum (bottleneck principle)
            return min(base_effs) * 0.9

    def _calculate_novelty(
        self, operations: List[Tuple[PentadOperation, SeptetObject]]
    ) -> float:
        """Calculate novelty score based on uniqueness"""
        # Check against all known patterns
        min_similarity = 1.0

        for pattern in self._known_patterns.values():
            similarity = self._pattern_similarity(operations, pattern.operations)
            min_similarity = min(min_similarity, similarity)

        # Novelty = 1 - similarity to closest known pattern
        return round(1.0 - min_similarity, 2)

    def _pattern_similarity(
        self,
        ops1: List[Tuple[PentadOperation, SeptetObject]],
        ops2: List[Tuple[PentadOperation, SeptetObject]],
    ) -> float:
        """Calculate similarity between two operation sequences"""
        if len(ops1) != len(ops2):
            return 0.0

        matches = sum(
            1 for (o1, t1), (o2, t2) in zip(ops1, ops2) if o1 == o2 and t1 == t2
        )

        return matches / len(ops1)

    def _generate_composition_name(
        self, components: List[Pattern], composition_type: str
    ) -> str:
        """Generate human-readable name for composed pattern"""
        if composition_type == "sequence":
            return f"Sequence: {' → '.join(c.name for c in components)}"
        elif composition_type == "parallel":
            return f"Parallel: {' + '.join(c.name for c in components)}"
        else:
            return f"Nested: {'('.join(c.name for c in components)})"

    def discover_emergent_patterns(self, n_explore: int = 100) -> List[Pattern]:
        """
        Discover emergent patterns through random exploration.

        Args:
            n_explore: Number of random compositions to try

        Returns:
            List of novel patterns discovered
        """
        discovered = []
        base_pattern_ids = list(self._known_patterns.keys())

        for _ in range(n_explore):
            # Random composition size (2-4)
            size = random.randint(2, min(4, len(base_pattern_ids)))

            # Random selection
            selected = random.sample(base_pattern_ids, size)

            # Try to synthesize
            new_pattern = self.synthesize_composition(selected, "sequence")

            if new_pattern and new_pattern.novelty_score > 0.5:
                discovered.append(new_pattern)

        # Sort by novelty
        discovered.sort(key=lambda p: p.novelty_score, reverse=True)
        return discovered[:10]  # Top 10

    def suggest_patterns_for_goal(
        self,
        goal_description: str,
        current_state: Optional[C4State] = None,
        target_state: Optional[C4State] = None,
    ) -> List[Tuple[Pattern, float]]:
        """
        Suggest patterns that might help achieve a goal.

        Args:
            goal_description: Text description of the goal
            current_state: Optional current C4 state
            target_state: Optional target C4 state

        Returns:
            List of (pattern, relevance_score) tuples
        """
        # Extract keywords from goal
        goal_lower = goal_description.lower()

        # Score each pattern
        scored = []

        for pattern in self._known_patterns.values():
            score = 0

            # Check operation match
            for op, obj in pattern.operations:
                if op.name.lower() in goal_lower:
                    score += 0.3
                if obj.value.lower() in goal_lower:
                    score += 0.3

            # Check effectiveness
            score += pattern.effectiveness_estimate * 0.2

            # Prefer novel patterns for exploration
            score += pattern.novelty_score * 0.1

            if score > 0:
                scored.append((pattern, round(score, 2)))

        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:10]

    def get_pattern_library(
        self, min_effectiveness: float = 0.0, min_novelty: float = 0.0
    ) -> List[Pattern]:
        """
        Get library of known patterns.

        Args:
            min_effectiveness: Minimum effectiveness threshold
            min_novelty: Minimum novelty threshold

        Returns:
            Filtered list of patterns
        """
        filtered = [
            p
            for p in self._known_patterns.values()
            if p.effectiveness_estimate >= min_effectiveness
            and p.novelty_score >= min_novelty
        ]

        # Sort by effectiveness
        filtered.sort(key=lambda p: p.effectiveness_estimate, reverse=True)
        return filtered

    def analyze_pattern_space(self) -> Dict[str, Any]:
        """Analyze the pattern space and return statistics"""
        patterns = list(self._known_patterns.values())

        if not patterns:
            return {}

        # Calculate statistics
        eff_values = [p.effectiveness_estimate for p in patterns]
        novelty_values = [p.novelty_score for p in patterns]

        # Operation distribution
        op_counts = {}
        for p in patterns:
            for op, _ in p.operations:
                op_counts[op.name] = op_counts.get(op.name, 0) + 1

        return {
            "total_patterns": len(patterns),
            "avg_effectiveness": round(sum(eff_values) / len(eff_values), 3),
            "avg_novelty": round(sum(novelty_values) / len(novelty_values), 3),
            "max_effectiveness": round(max(eff_values), 3),
            "max_novelty": round(max(novelty_values), 3),
            "operation_distribution": op_counts,
            "synthesized_count": sum(1 for p in patterns if p.novelty_score > 0),
        }
