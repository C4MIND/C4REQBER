"""
C4REQBER: Matrix Dream 72 Pattern Matcher
72 patterns = 9 × 8 matrix for pattern recognition and generation.

9 rows: Fundamental pattern types
8 columns: Variation dimensions
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PatternType(Enum):
    """9 fundamental pattern types (rows)."""

    RECURSION = "recursion"  # 1. Самоподобие
    OSCILLATION = "oscillation"  # 2. Колебание
    ACCUMULATION = "accumulation"  # 3. Накопление
    DIVERGENCE = "divergence"  # 4. Расхождение
    CONVERGENCE = "convergence"  # 5. Схождение
    TRANSFORMATION = "transformation"  # 6. Преобразование
    RESONANCE = "resonance"  # 7. Резонанс
    EMERGENCE = "emergence"  # 8. Эмерджентность
    COLLAPSE = "collapse"  # 9. Коллапс


class VariationDim(Enum):
    """8 variation dimensions (columns)."""

    TEMPORAL = "temporal"  # Time-based variation
    SPATIAL = "spatial"  # Space-based variation
    SCALAR = "scalar"  # Scale-based variation
    CAUSAL = "causal"  # Cause-effect variation
    STRUCTURAL = "structural"  # Structure-based variation
    FUNCTIONAL = "functional"  # Function-based variation
    ENTROPIC = "entropic"  # Entropy-based variation
    INFORMATIONAL = "informational"  # Information-based variation


@dataclass
class MatrixDreamPattern:
    """A single pattern in the Matrix Dream 72 grid."""

    pattern_type: PatternType
    variation: VariationDim
    id: str
    name: str
    description: str
    indicators: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    c4_bias: tuple[int, int, int] | None = None  # Preferred C4 state

    def matches(self, text: str) -> float:
        """Score how well this pattern matches given text (0-1)."""
        text_lower = text.lower()
        score = 0.0
        for indicator in self.indicators:
            if indicator.lower() in text_lower:
                score += 1.0
        return min(score / max(len(self.indicators), 1), 1.0)


class MatrixDreamLibrary:
    """
    Matrix Dream: 72 patterns = 9 types × 8 variations.
    """

    def __init__(self) -> None:
        self.patterns: list[MatrixDreamPattern] = []
        self._build_patterns()
        self._by_id: dict[str, MatrixDreamPattern] = {p.id: p for p in self.patterns}
        self._by_type: dict[PatternType, list[MatrixDreamPattern]] = {}
        for p in self.patterns:
            self._by_type.setdefault(p.pattern_type, []).append(p)

    def _build_patterns(self) -> None:
        """Build all 72 patterns programmatically."""
        pattern_defs = {
            PatternType.RECURSION: {
                "base_indicators": [
                    "self-similar",
                    "recursive",
                    "fractal",
                    "nested",
                    "repeating",
                ],
                "examples": [
                    "Fractal geometry",
                    "Recursive algorithms",
                    "Nested structures",
                ],
            },
            PatternType.OSCILLATION: {
                "base_indicators": ["cycle", "periodic", "wave", "swing", "fluctuate"],
                "examples": ["Business cycles", "Waves", "Pendulum"],
            },
            PatternType.ACCUMULATION: {
                "base_indicators": [
                    "build up",
                    "accumulate",
                    "grow",
                    "increase",
                    "gather",
                ],
                "examples": ["Compound interest", "Snowball effect", "Critical mass"],
            },
            PatternType.DIVERGENCE: {
                "base_indicators": ["split", "branch", "separate", "diverge", "spread"],
                "examples": [
                    "Branching processes",
                    "Divergent series",
                    "Decision trees",
                ],
            },
            PatternType.CONVERGENCE: {
                "base_indicators": [
                    "merge",
                    "converge",
                    "focus",
                    "centralize",
                    "unify",
                ],
                "examples": ["Consensus formation", "Convergent evolution", "Focus"],
            },
            PatternType.TRANSFORMATION: {
                "base_indicators": [
                    "transform",
                    "convert",
                    "change",
                    "morph",
                    "transmute",
                ],
                "examples": ["Phase transitions", "Catalysis", "Metamorphosis"],
            },
            PatternType.RESONANCE: {
                "base_indicators": [
                    "resonate",
                    "amplify",
                    "harmonize",
                    "synchronize",
                    "match",
                ],
                "examples": ["Acoustic resonance", "Viral spread", "Network effects"],
            },
            PatternType.EMERGENCE: {
                "base_indicators": [
                    "emerge",
                    "appear",
                    "arise",
                    "spontaneous",
                    "unexpected",
                ],
                "examples": ["Consciousness", "Flocking behavior", "Market bubbles"],
            },
            PatternType.COLLAPSE: {
                "base_indicators": [
                    "collapse",
                    "break down",
                    "fail",
                    "crash",
                    "dissolve",
                ],
                "examples": ["Market crashes", "Bridge collapse", "Phase collapse"],
            },
        }

        variation_modifiers = {
            VariationDim.TEMPORAL: {
                "indicators": ["time", "history", "future", "sequence"],
                "suffix": "_t",
            },
            VariationDim.SPATIAL: {
                "indicators": ["space", "location", "distance", "area"],
                "suffix": "_s",
            },
            VariationDim.SCALAR: {
                "indicators": ["scale", "size", "magnitude", "level"],
                "suffix": "_sc",
            },
            VariationDim.CAUSAL: {
                "indicators": ["cause", "effect", "because", "lead to"],
                "suffix": "_c",
            },
            VariationDim.STRUCTURAL: {
                "indicators": ["structure", "form", "shape", "organization"],
                "suffix": "_st",
            },
            VariationDim.FUNCTIONAL: {
                "indicators": ["function", "purpose", "use", "role"],
                "suffix": "_f",
            },
            VariationDim.ENTROPIC: {
                "indicators": ["entropy", "disorder", "chaos", "decay"],
                "suffix": "_e",
            },
            VariationDim.INFORMATIONAL: {
                "indicators": ["information", "data", "signal", "message"],
                "suffix": "_i",
            },
        }

        idx = 1
        for ptype, pdef in pattern_defs.items():
            for vdim, vdef in variation_modifiers.items():
                indicators = list(set(pdef["base_indicators"] + vdef["indicators"]))  # type: ignore[operator]
                self.patterns.append(
                    MatrixDreamPattern(
                        pattern_type=ptype,
                        variation=vdim,
                        id=f"MD-{idx:02d}",
                        name=f"{ptype.value.title()} ({vdim.value})",
                        description=f"{ptype.value} pattern in {vdim.value} dimension",
                        indicators=indicators,
                        examples=pdef["examples"],
                    )
                )
                idx += 1

    def get(self, pattern_id: str) -> MatrixDreamPattern | None:
        return self._by_id.get(pattern_id)

    def by_type(self, pattern_type: PatternType) -> list[MatrixDreamPattern]:
        return self._by_type.get(pattern_type, [])

    def match(
        self, text: str, top_k: int = 5
    ) -> list[tuple[MatrixDreamPattern, float]]:
        """Find top-k matching patterns for given text."""
        scored = [(p, p.matches(text)) for p in self.patterns]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def all_patterns(self) -> list[MatrixDreamPattern]:
        return list(self.patterns)

    def pattern_matrix(self) -> dict[str, list[dict[str, Any]]]:
        """Return the full 9×8 matrix as structured data."""
        matrix = {}
        for ptype in PatternType:
            matrix[ptype.value] = [
                {
                    "id": p.id,
                    "name": p.name,
                    "variation": p.variation.value,
                    "indicators": p.indicators[:3],
                }
                for p in self._by_type.get(ptype, [])
            ]
        return matrix
