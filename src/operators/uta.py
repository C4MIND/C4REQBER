"""UTA-20: Universal Transformation Algebra.

5 families x 4 operators = 20 base cognitive operations.
These are the LOWEST level of the operator hierarchy:
    UTA-20 -> Fractal27 (paradigms) -> QZRF-14 (meta-heuristics)

Usage:
    from src.operators.uta import UTAOperator, UTALibrary
    uta = UTALibrary()
    result = uta.apply("detect", target="anomaly", mode="instant")
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


class UTAFamily(Enum):
    """UTAFamily."""
    SENSING = "sensing"      # Detect, Scan, Focus, Track
    PROCESSING = "processing" # Parse, Filter, Compress, Expand
    MODULATING = "modulating" # Amplify, Attenuate, Tune, Shift
    STRUCTURING = "structuring" # Connect, Separate, Layer, Crystallize
    FLOWING = "flowing"      # Channel, Block, Cycle, Pulse


class UTAMode(Enum):
    """UTAMode."""
    INSTANT = "instant"
    GRADUAL = "gradual"
    CYCLIC = "cyclic"
    CASCADE = "cascade"


@dataclass(frozen=True)
class UTAOperator:
    """UTAOperator."""
    id: str
    name: str
    family: UTAFamily
    description: str
    # The apply function takes (context: dict) and returns transformed context
    apply: Callable[[dict[str, Any]], dict[str, Any]]


class UTALibrary:
    """Library of all 20 UTA operators."""

    OPERATORS = [
        # SENSING
        UTAOperator("UT-01", "Detect", UTAFamily.SENSING,
                    "Detect signal or anomaly in input",
                    lambda ctx: {**ctx, "_detected": True}),
        UTAOperator("UT-02", "Scan", UTAFamily.SENSING,
                    "Scan space or dataset for patterns",
                    lambda ctx: {**ctx, "_scanned": True}),
        UTAOperator("UT-03", "Focus", UTAFamily.SENSING,
                    "Focus attention on relevant subset",
                    lambda ctx: {**ctx, "_focused": True}),
        UTAOperator("UT-04", "Track", UTAFamily.SENSING,
                    "Track changes over time or iterations",
                    lambda ctx: {**ctx, "_tracked": True}),
        # PROCESSING
        UTAOperator("UT-05", "Parse", UTAFamily.PROCESSING,
                    "Decompose into elements",
                    lambda ctx: {**ctx, "_parsed": True}),
        UTAOperator("UT-06", "Filter", UTAFamily.PROCESSING,
                    "Remove noise or irrelevant data",
                    lambda ctx: {**ctx, "_filtered": True}),
        UTAOperator("UT-07", "Compress", UTAFamily.PROCESSING,
                    "Reduce dimensionality or information",
                    lambda ctx: {**ctx, "_compressed": True}),
        UTAOperator("UT-08", "Expand", UTAFamily.PROCESSING,
                    "Add detail or elaboration",
                    lambda ctx: {**ctx, "_expanded": True}),
        # MODULATING
        UTAOperator("UT-09", "Amplify", UTAFamily.MODULATING,
                    "Strengthen signal or effect",
                    lambda ctx: {**ctx, "_amplified": True}),
        UTAOperator("UT-10", "Attenuate", UTAFamily.MODULATING,
                    "Weaken or dampen effect",
                    lambda ctx: {**ctx, "_attenuated": True}),
        UTAOperator("UT-11", "Tune", UTAFamily.MODULATING,
                    "Adjust parameters for optimal performance",
                    lambda ctx: {**ctx, "_tuned": True}),
        UTAOperator("UT-12", "Shift", UTAFamily.MODULATING,
                    "Change characteristics or perspective",
                    lambda ctx: {**ctx, "_shifted": True}),
        # STRUCTURING
        UTAOperator("UT-13", "Connect", UTAFamily.STRUCTURING,
                    "Link elements into relationships",
                    lambda ctx: {**ctx, "_connected": True}),
        UTAOperator("UT-14", "Separate", UTAFamily.STRUCTURING,
                    "Divide components",
                    lambda ctx: {**ctx, "_separated": True}),
        UTAOperator("UT-15", "Layer", UTAFamily.STRUCTURING,
                    "Create hierarchical levels",
                    lambda ctx: {**ctx, "_layered": True}),
        UTAOperator("UT-16", "Crystallize", UTAFamily.STRUCTURING,
                    "Fix structure or form",
                    lambda ctx: {**ctx, "_crystallized": True}),
        # FLOWING
        UTAOperator("UT-17", "Channel", UTAFamily.FLOWING,
                    "Direct flow or process",
                    lambda ctx: {**ctx, "_channeled": True}),
        UTAOperator("UT-18", "Block", UTAFamily.FLOWING,
                    "Stop or inhibit flow",
                    lambda ctx: {**ctx, "_blocked": True}),
        UTAOperator("UT-19", "Cycle", UTAFamily.FLOWING,
                    "Create iterative process",
                    lambda ctx: {**ctx, "_cycled": True}),
        UTAOperator("UT-20", "Pulse", UTAFamily.FLOWING,
                    "Create impulsive impact",
                    lambda ctx: {**ctx, "_pulsed": True}),
    ]

    def __init__(self) -> None:
        self._by_id: dict[str, UTAOperator] = {op.id: op for op in self.OPERATORS}
        self._by_name: dict[str, UTAOperator] = {op.name.lower(): op for op in self.OPERATORS}

    def get(self, op_id: str) -> UTAOperator | None:
        return self._by_id.get(op_id) or self._by_name.get(op_id.lower())

    def by_family(self, family: UTAFamily) -> list[UTAOperator]:
        return [op for op in self.OPERATORS if op.family == family]

    def apply(self, op_id: str, context: dict[str, Any]) -> dict[str, Any]:
        """Apply."""
        op = self.get(op_id)
        if op is None:
            return context
        return op.apply(context)

    def apply_sequence(self, sequence: list[str], context: dict[str, Any]) -> dict[str, Any]:
        """Apply sequence."""
        for op_id in sequence:
            context = self.apply(op_id, context)
        return context
