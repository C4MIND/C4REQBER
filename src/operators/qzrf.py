"""
QZRF Meta-Operators — 14 cognitive transformation operators.

Each operator transforms a cognitive state (C4State) by applying
a specific meta-cognitive transformation. These are the high-level
operators used in UCOS Layer 3 (Dynamics) for cognitive state transitions.

Reference: UCOS v7.0 — QZRF Metamodel
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Protocol

from src.c4.state import C4State


class QZRFOpType(Enum):
    """Classification of QZRF operator effect on C4 state."""

    ABSTRACTION = auto()      # Moves S upward
    CONCRETIZATION = auto()   # Moves S downward
    TEMPORAL = auto()         # Moves T
    PERSPECTIVE = auto()      # Moves A
    COMPOSITION = auto()      # Combines multiple states
    INVERSION = auto()        # Flips state
    IDENTITY = auto()         # Preserves state structure


@dataclass(frozen=True)
class QZRFC4Rule:
    """C4 transformation rule for a QZRF operator.

    Specifies how the operator transforms each C4 axis.
    Values are delta shifts (mod 3) or None for no change.
    """

    delta_t: int | None = None
    delta_s: int | None = None
    delta_a: int | None = None

    def apply(self, state: C4State) -> C4State:
        """Apply this rule to a C4 state."""
        t = (state.T + self.delta_t) % 3 if self.delta_t is not None else state.T
        s = (state.S + self.delta_s) % 3 if self.delta_s is not None else state.S
        a = (state.A + self.delta_a) % 3 if self.delta_a is not None else state.A
        return C4State(T=t, S=s, A=a)


class CognitiveState(Protocol):
    """Protocol for cognitive states that QZRF operators can transform."""

    @property
    def c4_state(self) -> C4State: ...
    @property
    def content(self) -> dict[str, Any]: ...


@dataclass
class CognitiveFrame:
    """A concrete cognitive state with C4 coordinates and semantic content."""

    c4_state: C4State
    content: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_state(self, new_state: C4State) -> CognitiveFrame:
        return CognitiveFrame(
            c4_state=new_state,
            content=self.content.copy(),
            metadata=self.metadata.copy(),
        )

    def with_content(self, **kwargs: Any) -> CognitiveFrame:
        """With content."""
        new_content = self.content.copy()
        new_content.update(kwargs)
        return CognitiveFrame(
            c4_state=self.c4_state,
            content=new_content,
            metadata=self.metadata.copy(),
        )


# ---------------------------------------------------------------------------
# 14 QZRF Meta-Operators
# ---------------------------------------------------------------------------

class QZRFOperator:
    """Base class for all 14 QZRF meta-operators."""

    name: str
    description: str
    op_type: QZRFOpType
    c4_rule: QZRFC4Rule

    def __init__(
        self,
        name: str,
        description: str,
        op_type: QZRFOpType,
        c4_rule: QZRFC4Rule,
    ) -> None:
        self.name = name
        self.description = description
        self.op_type = op_type
        self.c4_rule = c4_rule

    def transform_c4(self, state: C4State) -> C4State:
        """Apply the C4 transformation rule."""
        return self.c4_rule.apply(state)

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Transform a full cognitive frame (C4 + content).

        Subclasses override to add semantic transformations.
        """
        new_state = self.transform_c4(frame.c4_state)
        return frame.with_state(new_state)

    def __repr__(self) -> str:
        return f"QZRFOperator({self.name})"


# 1. GENERALIZE — Move from concrete to abstract
class Generalize(QZRFOperator):
    """Abstract away details: Concrete -> Abstract -> Meta."""

    def __init__(self) -> None:
        super().__init__(
            name="Generalize",
            description="Abstract away details, move to higher scale level",
            op_type=QZRFOpType.ABSTRACTION,
            c4_rule=QZRFC4Rule(delta_s=1),
        )

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Transform."""
        new_state = self.transform_c4(frame.c4_state)
        content = frame.content.copy()
        # Semantic: lift specific instances to patterns
        if "instances" in content:
            content["pattern"] = self._extract_pattern(content["instances"])
            content["abstraction_level"] = content.get("abstraction_level", 0) + 1
        return frame.with_state(new_state).with_content(**content)

    @staticmethod
    def _extract_pattern(instances: list[Any]) -> dict[str, Any]:
        """Extract common pattern from instances."""
        if not instances:
            return {}
        # Find shared keys as structural pattern
        if isinstance(instances[0], dict):
            common_keys = set(instances[0].keys())
            for inst in instances[1:]:
                if isinstance(inst, dict):
                    common_keys &= set(inst.keys())
            return {"structural_invariant": sorted(common_keys), "count": len(instances)}
        return {"type": type(instances[0]).__name__, "count": len(instances)}


# 2. SPECIFY — Move from abstract to concrete
class Specify(QZRFOperator):
    """Add concrete details: Abstract -> Concrete, Meta -> Abstract."""

    def __init__(self) -> None:
        super().__init__(
            name="Specify",
            description="Add concrete details, instantiate abstractions",
            op_type=QZRFOpType.CONCRETIZATION,
            c4_rule=QZRFC4Rule(delta_s=-1),
        )

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Transform."""
        new_state = self.transform_c4(frame.c4_state)
        content = frame.content.copy()
        if "pattern" in content:
            content["instantiated"] = True
            content["concretization_level"] = content.get("concretization_level", 0) + 1
        return frame.with_state(new_state).with_content(**content)


# 3. ANALOGIZE — Find structural parallels across domains
class Analogize(QZRFOperator):
    """Map structure from one domain to another."""

    def __init__(self) -> None:
        super().__init__(
            name="Analogize",
            description="Find structural parallels across domains",
            op_type=QZRFOpType.PERSPECTIVE,
            c4_rule=QZRFC4Rule(delta_a=1),
        )

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Transform."""
        new_state = self.transform_c4(frame.c4_state)
        content = frame.content.copy()
        # Semantic: shift perspective, create cross-domain mapping
        content["analogy_source"] = content.get("domain", "unknown")
        content["perspective_shift"] = True
        content["mapping_type"] = "structural"
        return frame.with_state(new_state).with_content(**content)


# 4. REVERSE — Invert the cognitive frame
class Reverse(QZRFOperator):
    """Invert assumptions, flip perspective 180 degrees."""

    def __init__(self) -> None:
        super().__init__(
            name="Reverse",
            description="Invert assumptions and flip perspective",
            op_type=QZRFOpType.INVERSION,
            c4_rule=QZRFC4Rule(delta_t=1, delta_s=1, delta_a=1),
        )

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Transform."""
        new_state = self.transform_c4(frame.c4_state)
        content = frame.content.copy()
        # Semantic: negate key propositions
        if "proposition" in content:
            content["negated_proposition"] = self._negate(content["proposition"])
        content["inverted"] = True
        return frame.with_state(new_state).with_content(**content)

    @staticmethod
    def _negate(prop: str) -> str:
        """Simple structural negation."""
        negations = {
            "all": "some not",
            "some": "none",
            "is": "is not",
            "can": "cannot",
            "will": "will not",
        }
        result = prop
        for k, v in negations.items():
            if k in result.lower():
                result = result.replace(k, v, 1)
                break
        return f"NOT({result})"


# 5. COMBINE — Merge multiple cognitive frames
class Combine(QZRFOperator):
    """Synthesize by merging distinct cognitive frames."""

    def __init__(self) -> None:
        super().__init__(
            name="Combine",
            description="Synthesize by merging distinct frames",
            op_type=QZRFOpType.COMPOSITION,
            c4_rule=QZRFC4Rule(delta_s=1),
        )

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Transform."""
        new_state = self.transform_c4(frame.c4_state)
        content = frame.content.copy()
        content["synthesized"] = True
        content["merge_count"] = content.get("merge_count", 0) + 1
        return frame.with_state(new_state).with_content(**content)

    @classmethod
    def merge(cls, frames: list[CognitiveFrame]) -> CognitiveFrame:
        """Merge multiple frames into one."""
        if not frames:
            raise ValueError("Cannot merge empty list of frames")
        # Use highest scale level
        max_s = max(f.c4_state.S for f in frames)
        # Use most common T and A
        t_counts: dict[int, int] = {}
        a_counts: dict[int, int] = {}
        for f in frames:
            t_counts[f.c4_state.T] = t_counts.get(f.c4_state.T, 0) + 1
            a_counts[f.c4_state.A] = a_counts.get(f.c4_state.A, 0) + 1
        merged_t = max(t_counts, key=t_counts.get)  # type: ignore[arg-type]
        merged_a = max(a_counts, key=a_counts.get)  # type: ignore[arg-type]
        merged_state = C4State(T=merged_t, S=max_s, A=merged_a)
        merged_content: dict[str, Any] = {}
        for f in frames:
            merged_content.update(f.content)
        return CognitiveFrame(
            c4_state=merged_state,
            content={**merged_content, "merged_from": len(frames)},
        )


# 6. DECOMPOSE — Break into constituent parts
class Decompose(QZRFOperator):
    """Break a complex frame into constituent parts."""

    def __init__(self) -> None:
        super().__init__(
            name="Decompose",
            description="Break into constituent parts",
            op_type=QZRFOpType.CONCRETIZATION,
            c4_rule=QZRFC4Rule(delta_s=-1),
        )

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Transform."""
        new_state = self.transform_c4(frame.c4_state)
        content = frame.content.copy()
        content["decomposed"] = True
        if "components" in content:
            content["component_count"] = len(content["components"])
        return frame.with_state(new_state).with_content(**content)


# 7. TEMPORAL_SHIFT — Move along time axis
class TemporalShift(QZRFOperator):
    """Shift temporal perspective: Past -> Present -> Future."""

    def __init__(self, direction: int = 1) -> None:
        super().__init__(
            name="TemporalShift",
            description="Shift temporal perspective",
            op_type=QZRFOpType.TEMPORAL,
            c4_rule=QZRFC4Rule(delta_t=direction % 3),
        )
        self.direction = direction % 3

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Transform."""
        new_state = self.transform_c4(frame.c4_state)
        content = frame.content.copy()
        time_labels = {0: "Past", 1: "Present", 2: "Future"}
        content["temporal_context"] = time_labels.get(new_state.T, "Unknown")
        content["time_shifted"] = True
        return frame.with_state(new_state).with_content(**content)


# 8. PERSPECTIVE_SHIFT — Change agency perspective
class PerspectiveShift(QZRFOperator):
    """Change viewpoint: Self -> Other -> System."""

    def __init__(self) -> None:
        super().__init__(
            name="PerspectiveShift",
            description="Change agency perspective",
            op_type=QZRFOpType.PERSPECTIVE,
            c4_rule=QZRFC4Rule(delta_a=1),
        )

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Transform."""
        new_state = self.transform_c4(frame.c4_state)
        content = frame.content.copy()
        agency_labels = {0: "Self", 1: "Other", 2: "System"}
        content["viewpoint"] = agency_labels.get(new_state.A, "Unknown")
        content["perspective_shifted"] = True
        return frame.with_state(new_state).with_content(**content)


# 9. FIRST_PRINCIPLES — Strip to fundamental truths
class FirstPrinciples(QZRFOperator):
    """Reduce to fundamental truths, strip away assumptions."""

    def __init__(self) -> None:
        super().__init__(
            name="FirstPrinciples",
            description="Reduce to fundamental truths",
            op_type=QZRFOpType.ABSTRACTION,
            c4_rule=QZRFC4Rule(delta_s=2),  # Jump to Meta
        )

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Transform."""
        new_state = self.transform_c4(frame.c4_state)
        content = frame.content.copy()
        # Strip to fundamentals
        fundamentals = {}
        if "axioms" in content:
            fundamentals["axioms"] = content["axioms"]
        if "constraints" in content:
            fundamentals["constraints"] = content["constraints"]
        fundamentals["first_principles_applied"] = True
        fundamentals["assumptions_stripped"] = content.get("assumptions", [])
        return CognitiveFrame(
            c4_state=new_state,
            content=fundamentals,
            metadata={**frame.metadata, "source_frame": frame.c4_state.to_tuple()},
        )


# 10. SYSTEMIC — View from system perspective
class Systemic(QZRFOperator):
    """Elevate to system-level view."""

    def __init__(self) -> None:
        super().__init__(
            name="Systemic",
            description="Elevate to system-level perspective",
            op_type=QZRFOpType.PERSPECTIVE,
            c4_rule=QZRFC4Rule(delta_a=2),  # Jump to System
        )

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Transform."""
        new_state = self.transform_c4(frame.c4_state)
        content = frame.content.copy()
        content["systemic_view"] = True
        content["emergent_properties"] = content.get("emergent_properties", [])
        content["feedback_loops"] = content.get("feedback_loops", [])
        return frame.with_state(new_state).with_content(**content)


# 11. RECURSIVE — Apply operator to itself
class Recursive(QZRFOperator):
    """Apply transformation recursively."""

    def __init__(self, depth: int = 2) -> None:
        super().__init__(
            name="Recursive",
            description="Apply transformation recursively",
            op_type=QZRFOpType.COMPOSITION,
            c4_rule=QZRFC4Rule(),  # Identity on C4, recursive on content
        )
        self.depth = max(1, depth)

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        # C4 stays same, content gets recursive structure
        """Transform."""
        content = frame.content.copy()
        content["recursive_depth"] = self.depth
        content["self_similar"] = True
        if "substructure" in content:
            content["nested_levels"] = self.depth
        return frame.with_state(frame.c4_state).with_content(**content)


# 12. CONSTRAINT_RELAX — Remove constraints to explore
class ConstraintRelax(QZRFOperator):
    """Remove constraints to explore solution space."""

    def __init__(self) -> None:
        super().__init__(
            name="ConstraintRelax",
            description="Remove constraints to explore solution space",
            op_type=QZRFOpType.ABSTRACTION,
            c4_rule=QZRFC4Rule(delta_s=1, delta_t=1),
        )

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Transform."""
        new_state = self.transform_c4(frame.c4_state)
        content = frame.content.copy()
        relaxed = content.get("constraints", [])
        content["relaxed_constraints"] = relaxed
        content["constraints_removed"] = len(relaxed)
        content["exploration_mode"] = True
        return frame.with_state(new_state).with_content(**content)


# 13. CONSTRAINT_TIGHTEN — Add constraints to focus
class ConstraintTighten(QZRFOperator):
    """Add constraints to narrow solution space."""

    def __init__(self) -> None:
        super().__init__(
            name="ConstraintTighten",
            description="Add constraints to narrow solution space",
            op_type=QZRFOpType.CONCRETIZATION,
            c4_rule=QZRFC4Rule(delta_s=-1, delta_t=-1),
        )

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Transform."""
        new_state = self.transform_c4(frame.c4_state)
        content = frame.content.copy()
        content["focus_mode"] = True
        content["tightened"] = True
        return frame.with_state(new_state).with_content(**content)


# 14. META_REFLECT — Step back and observe the process
class MetaReflect(QZRFOperator):
    """Step back to observe and reflect on the cognitive process itself."""

    def __init__(self) -> None:
        super().__init__(
            name="MetaReflect",
            description="Step back and observe the cognitive process",
            op_type=QZRFOpType.ABSTRACTION,
            c4_rule=QZRFC4Rule(delta_s=2, delta_t=1),
        )

    def transform(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Transform."""
        new_state = self.transform_c4(frame.c4_state)
        content = frame.content.copy()
        content["meta_level"] = content.get("meta_level", 0) + 1
        content["reflective_mode"] = True
        content["process_observation"] = {
            "from_state": frame.c4_state.to_tuple(),
            "to_state": new_state.to_tuple(),
        }
        return frame.with_state(new_state).with_content(**content)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class QZRFRegistry:
    """Registry of all 14 QZRF meta-operators."""

    _operators: dict[str, QZRFOperator] = {}

    @classmethod
    def register(cls, op: QZRFOperator) -> None:
        cls._operators[op.name] = op

    @classmethod
    def get(cls, name: str) -> QZRFOperator:
        """Get."""
        if name not in cls._operators:
            raise KeyError(f"Unknown QZRF operator: {name}")
        return cls._operators[name]

    @classmethod
    def all(cls) -> list[QZRFOperator]:
        return list(cls._operators.values())

    @classmethod
    def names(cls) -> list[str]:
        return list(cls._operators.keys())

    @classmethod
    def by_type(cls, op_type: QZRFOpType) -> list[QZRFOperator]:
        return [op for op in cls.all() if op.op_type == op_type]


# Auto-register all operators
_OPERATORS_TO_REGISTER: list[QZRFOperator] = [
    Generalize(),
    Specify(),
    Analogize(),
    Reverse(),
    Combine(),
    Decompose(),
    TemporalShift(),
    PerspectiveShift(),
    FirstPrinciples(),
    Systemic(),
    Recursive(),
    ConstraintRelax(),
    ConstraintTighten(),
    MetaReflect(),
]

for _op in _OPERATORS_TO_REGISTER:
    QZRFRegistry.register(_op)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def apply_operator_sequence(
    frame: CognitiveFrame, operators: list[QZRFOperator]
) -> CognitiveFrame:
    """Apply a sequence of QZRF operators to a frame."""
    current = frame
    for op in operators:
        current = op.transform(current)
    return current


def get_operator_c4_transform(name: str, state: C4State) -> C4State:
    """Get the C4 transformation for a named operator."""
    op = QZRFRegistry.get(name)
    return op.transform_c4(state)


def list_operators() -> list[str]:
    """List all registered operator names."""
    return QZRFRegistry.names()

class QZRFEngine:
    """QZRF meta-operator engine."""

    def __init__(self) -> None:
        self.operators = QZRFRegistry

    def list_operators(self) -> list[str]:
        return list_operators()

    def apply(self, name: str, frame: CognitiveFrame) -> CognitiveFrame:
        op = QZRFRegistry.get(name)
        return op.transform(frame)

    def transform_c4(self, name: str, state: C4State) -> C4State:
        return get_operator_c4_transform(name, state)
