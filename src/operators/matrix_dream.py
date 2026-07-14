"""
Matrix Dream — 72 transformation patterns for cognitive state transitions.

Organized into 9 functional categories × 8 patterns each.
Each pattern defines a micro-transformation applicable to cognitive frames.

Reference: UCOS v7.0 — Matrix Dream Metamodel
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable

from src.c4.state import C4State
from src.operators.qzrf import CognitiveFrame


class PatternCategory(Enum):
    """9 functional categories for Matrix Dream patterns."""

    ABSTRACTION = auto()      # Patterns 1-8
    CONCRETIZATION = auto()   # Patterns 9-16
    TEMPORAL = auto()         # Patterns 17-24
    PERSPECTIVE = auto()      # Patterns 25-32
    COMPOSITION = auto()      # Patterns 33-40
    DECOMPOSITION = auto()    # Patterns 41-48
    INVERSION = auto()        # Patterns 49-56
    CONSTRAINT = auto()       # Patterns 57-64
    META = auto()             # Patterns 65-72


@dataclass(frozen=True)
class C4Transform:
    """A concrete C4 state transformation specification."""

    delta_t: int = 0
    delta_s: int = 0
    delta_a: int = 0

    def apply(self, state: C4State) -> C4State:
        return C4State(
            T=(state.T + self.delta_t) % 3,
            S=(state.S + self.delta_s) % 3,
            A=(state.A + self.delta_a) % 3,
        )


@dataclass
class DreamPattern:
    """A single Matrix Dream transformation pattern."""

    id: int
    name: str
    description: str
    category: PatternCategory
    c4_transform: C4Transform
    semantic_transform: Callable[[dict[str, Any]], dict[str, Any]] = field(
        default_factory=lambda: lambda x: x
    )

    def apply(self, frame: CognitiveFrame) -> CognitiveFrame:
        """Apply pattern to a cognitive frame."""
        new_state = self.c4_transform.apply(frame.c4_state)
        new_content = self.semantic_transform(frame.content.copy())
        return CognitiveFrame(
            c4_state=new_state,
            content=new_content,
            metadata={
                **frame.metadata,
                "applied_pattern": self.name,
                "pattern_category": self.category.name,
            },
        )

    def __repr__(self) -> str:
        return f"DreamPattern({self.id}: {self.name})"


# =============================================================================
# Category 1: ABSTRACTION (Patterns 1-8)
# =============================================================================

PATTERNS_ABSTRACTION: list[DreamPattern] = [
    DreamPattern(
        id=1,
        name="Lift_Instance_To_Class",
        description="Transform specific instance into class definition",
        category=PatternCategory.ABSTRACTION,
        c4_transform=C4Transform(delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "abstraction": "class",
            "generalized_from": c.get("instance", "unknown"),
        },
    ),
    DreamPattern(
        id=2,
        name="Extract_Invariant",
        description="Find invariant structure across variations",
        category=PatternCategory.ABSTRACTION,
        c4_transform=C4Transform(delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "invariant": c.get("common_structure", []),
            "variations_abstracted": c.get("variation_count", 0),
        },
    ),
    DreamPattern(
        id=3,
        name="Parameterize_Constant",
        description="Replace fixed value with parameter",
        category=PatternCategory.ABSTRACTION,
        c4_transform=C4Transform(delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "parameterized": True,
            "free_parameters": c.get("constants", []),
        },
    ),
    DreamPattern(
        id=4,
        name="Type_Generalization",
        description="Widen type constraints",
        category=PatternCategory.ABSTRACTION,
        c4_transform=C4Transform(delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "type_widened": True,
            "original_type": c.get("type", "unknown"),
        },
    ),
    DreamPattern(
        id=5,
        name="Schema_Extraction",
        description="Extract schema from concrete data",
        category=PatternCategory.ABSTRACTION,
        c4_transform=C4Transform(delta_s=1, delta_t=1),
        semantic_transform=lambda c: {
            **c,
            "schema": c.get("data_structure", {}),
            "schema_source": "extraction",
        },
    ),
    DreamPattern(
        id=6,
        name="Model_Simplification",
        description="Simplify model by removing detail",
        category=PatternCategory.ABSTRACTION,
        c4_transform=C4Transform(delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "simplified": True,
            "detail_level": "reduced",
            "approximation_error": c.get("error_tolerance", 0.0),
        },
    ),
    DreamPattern(
        id=7,
        name="Dimensionality_Reduction",
        description="Project to lower-dimensional representation",
        category=PatternCategory.ABSTRACTION,
        c4_transform=C4Transform(delta_s=1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "dimensions_reduced": True,
            "projection_method": c.get("method", "PCA"),
        },
    ),
    DreamPattern(
        id=8,
        name="Ontology_Lift",
        description="Move to ontological level",
        category=PatternCategory.ABSTRACTION,
        c4_transform=C4Transform(delta_s=2),
        semantic_transform=lambda c: {
            **c,
            "ontological": True,
            "ontology_level": "meta",
            "categories": c.get("entities", []),
        },
    ),
]

# =============================================================================
# Category 2: CONCRETIZATION (Patterns 9-16)
# =============================================================================

PATTERNS_CONCRETIZATION: list[DreamPattern] = [
    DreamPattern(
        id=9,
        name="Instantiate_Class",
        description="Create instance from class definition",
        category=PatternCategory.CONCRETIZATION,
        c4_transform=C4Transform(delta_s=-1),
        semantic_transform=lambda c: {
            **c,
            "instantiated": True,
            "instance_of": c.get("class", "unknown"),
        },
    ),
    DreamPattern(
        id=10,
        name="Ground_In_Example",
        description="Anchor abstract concept with concrete example",
        category=PatternCategory.CONCRETIZATION,
        c4_transform=C4Transform(delta_s=-1),
        semantic_transform=lambda c: {
            **c,
            "grounded": True,
            "example": c.get("concrete_case", "none"),
        },
    ),
    DreamPattern(
        id=11,
        name="Substitute_Parameter",
        description="Bind parameter to concrete value",
        category=PatternCategory.CONCRETIZATION,
        c4_transform=C4Transform(delta_s=-1),
        semantic_transform=lambda c: {
            **c,
            "parameter_bound": True,
            "binding": c.get("parameter_values", {}),
        },
    ),
    DreamPattern(
        id=12,
        name="Type_Specialization",
        description="Narrow type constraints",
        category=PatternCategory.CONCRETIZATION,
        c4_transform=C4Transform(delta_s=-1),
        semantic_transform=lambda c: {
            **c,
            "type_narrowed": True,
            "specialized_type": c.get("subtype", "unknown"),
        },
    ),
    DreamPattern(
        id=13,
        name="Data_Population",
        description="Fill schema with concrete data",
        category=PatternCategory.CONCRETIZATION,
        c4_transform=C4Transform(delta_s=-1, delta_t=-1),
        semantic_transform=lambda c: {
            **c,
            "populated": True,
            "data_source": c.get("source", "synthetic"),
        },
    ),
    DreamPattern(
        id=14,
        name="Model_Detail_Addition",
        description="Add detail to simplified model",
        category=PatternCategory.CONCRETIZATION,
        c4_transform=C4Transform(delta_s=-1),
        semantic_transform=lambda c: {
            **c,
            "detail_added": True,
            "detail_level": "enhanced",
        },
    ),
    DreamPattern(
        id=15,
        name="Dimensionality_Expansion",
        description="Expand to higher-dimensional representation",
        category=PatternCategory.CONCRETIZATION,
        c4_transform=C4Transform(delta_s=-1, delta_a=-1),
        semantic_transform=lambda c: {
            **c,
            "dimensions_expanded": True,
            "new_dimensions": c.get("added_features", []),
        },
    ),
    DreamPattern(
        id=16,
        name="Ontology_Instantiation",
        description="Instantiate ontological categories",
        category=PatternCategory.CONCRETIZATION,
        c4_transform=C4Transform(delta_s=-2),
        semantic_transform=lambda c: {
            **c,
            "ontology_instantiated": True,
            "instances": c.get("categories", []),
        },
    ),
]

# =============================================================================
# Category 3: TEMPORAL (Patterns 17-24)
# =============================================================================

PATTERNS_TEMPORAL: list[DreamPattern] = [
    DreamPattern(
        id=17,
        name="Retrospective_Analysis",
        description="Analyze past events for causes",
        category=PatternCategory.TEMPORAL,
        c4_transform=C4Transform(delta_t=-1),
        semantic_transform=lambda c: {
            **c,
            "temporal_focus": "past",
            "causal_analysis": True,
        },
    ),
    DreamPattern(
        id=18,
        name="Present_Situation_Assessment",
        description="Assess current state comprehensively",
        category=PatternCategory.TEMPORAL,
        c4_transform=C4Transform(delta_t=0),
        semantic_transform=lambda c: {
            **c,
            "temporal_focus": "present",
            "situation_assessment": True,
        },
    ),
    DreamPattern(
        id=19,
        name="Prospective_Prediction",
        description="Predict future outcomes",
        category=PatternCategory.TEMPORAL,
        c4_transform=C4Transform(delta_t=1),
        semantic_transform=lambda c: {
            **c,
            "temporal_focus": "future",
            "prediction": True,
            "forecast_horizon": c.get("horizon", "short"),
        },
    ),
    DreamPattern(
        id=20,
        name="Trend_Extrapolation",
        description="Extend current trends forward",
        category=PatternCategory.TEMPORAL,
        c4_transform=C4Transform(delta_t=1, delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "extrapolation": True,
            "trend_model": c.get("model", "linear"),
        },
    ),
    DreamPattern(
        id=21,
        name="Historical_Pattern_Matching",
        description="Find analogies in historical data",
        category=PatternCategory.TEMPORAL,
        c4_transform=C4Transform(delta_t=-1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "historical_match": True,
            "analogy_period": c.get("period", "unknown"),
        },
    ),
    DreamPattern(
        id=22,
        name="Scenario_Generation",
        description="Generate alternative future scenarios",
        category=PatternCategory.TEMPORAL,
        c4_transform=C4Transform(delta_t=1, delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "scenarios_generated": True,
            "scenario_count": c.get("branches", 3),
        },
    ),
    DreamPattern(
        id=23,
        name="Causal_Chain_Reconstruction",
        description="Reconstruct sequence of causes",
        category=PatternCategory.TEMPORAL,
        c4_transform=C4Transform(delta_t=-1, delta_s=-1),
        semantic_transform=lambda c: {
            **c,
            "causal_chain": c.get("events", []),
            "reconstructed": True,
        },
    ),
    DreamPattern(
        id=24,
        name="Counterfactual_Exploration",
        description="Explore what-if scenarios",
        category=PatternCategory.TEMPORAL,
        c4_transform=C4Transform(delta_t=1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "counterfactual": True,
            "alternative_history": c.get("alternative", {}),
        },
    ),
]

# =============================================================================
# Category 4: PERSPECTIVE (Patterns 25-32)
# =============================================================================

PATTERNS_PERSPECTIVE: list[DreamPattern] = [
    DreamPattern(
        id=25,
        name="Self_Reflection",
        description="Examine from first-person perspective",
        category=PatternCategory.PERSPECTIVE,
        c4_transform=C4Transform(delta_a=0),
        semantic_transform=lambda c: {
            **c,
            "perspective": "self",
            "introspection": True,
        },
    ),
    DreamPattern(
        id=26,
        name="Empathy_Shift",
        description="Adopt another's perspective",
        category=PatternCategory.PERSPECTIVE,
        c4_transform=C4Transform(delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "perspective": "other",
            "empathy_target": c.get("target", "unknown"),
        },
    ),
    DreamPattern(
        id=27,
        name="System_Overview",
        description="View from system-level perspective",
        category=PatternCategory.PERSPECTIVE,
        c4_transform=C4Transform(delta_a=2),
        semantic_transform=lambda c: {
            **c,
            "perspective": "system",
            "system_scope": c.get("scope", "full"),
        },
    ),
    DreamPattern(
        id=28,
        name="Stakeholder_Mapping",
        description="Map all stakeholder perspectives",
        category=PatternCategory.PERSPECTIVE,
        c4_transform=C4Transform(delta_a=1, delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "stakeholders_mapped": True,
            "stakeholder_count": len(c.get("stakeholders", [])),
        },
    ),
    DreamPattern(
        id=29,
        name="Devils_Advocate",
        description="Adopt opposing viewpoint deliberately",
        category=PatternCategory.PERSPECTIVE,
        c4_transform=C4Transform(delta_a=1, delta_t=-1),
        semantic_transform=lambda c: {
            **c,
            "opposing_view": True,
            "challenge_mode": True,
        },
    ),
    DreamPattern(
        id=30,
        name="Multi_Agent_Simulation",
        description="Simulate multiple agent perspectives",
        category=PatternCategory.PERSPECTIVE,
        c4_transform=C4Transform(delta_a=1, delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "multi_agent": True,
            "agent_count": c.get("agents", 0),
        },
    ),
    DreamPattern(
        id=31,
        name="Ecological_View",
        description="View as ecosystem interaction",
        category=PatternCategory.PERSPECTIVE,
        c4_transform=C4Transform(delta_a=2, delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "ecological_view": True,
            "system_boundaries": c.get("boundaries", "open"),
        },
    ),
    DreamPattern(
        id=32,
        name="Temporal_Perspective_Fusion",
        description="Fuse past/present/future perspectives",
        category=PatternCategory.PERSPECTIVE,
        c4_transform=C4Transform(delta_t=1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "fused_temporal_perspective": True,
            "time_layers": ["past", "present", "future"],
        },
    ),
]

# =============================================================================
# Category 5: COMPOSITION (Patterns 33-40)
# =============================================================================

PATTERNS_COMPOSITION: list[DreamPattern] = [
    DreamPattern(
        id=33,
        name="Feature_Aggregation",
        description="Combine features from multiple sources",
        category=PatternCategory.COMPOSITION,
        c4_transform=C4Transform(delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "features_aggregated": True,
            "source_count": c.get("sources", 0),
        },
    ),
    DreamPattern(
        id=34,
        name="Cross_Domain_Synthesis",
        description="Synthesize across different domains",
        category=PatternCategory.COMPOSITION,
        c4_transform=C4Transform(delta_s=1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "cross_domain": True,
            "domains": c.get("source_domains", []),
        },
    ),
    DreamPattern(
        id=35,
        name="Hierarchical_Integration",
        description="Integrate at multiple hierarchy levels",
        category=PatternCategory.COMPOSITION,
        c4_transform=C4Transform(delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "hierarchical": True,
            "levels_integrated": c.get("levels", []),
        },
    ),
    DreamPattern(
        id=36,
        name="Temporal_Merging",
        description="Merge temporal sequences",
        category=PatternCategory.COMPOSITION,
        c4_transform=C4Transform(delta_t=1),
        semantic_transform=lambda c: {
            **c,
            "temporal_merge": True,
            "sequence_count": c.get("sequences", 0),
        },
    ),
    DreamPattern(
        id=37,
        name="Conflict_Resolution",
        description="Resolve conflicts between frames",
        category=PatternCategory.COMPOSITION,
        c4_transform=C4Transform(delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "conflict_resolved": True,
            "resolution_strategy": c.get("strategy", "consensus"),
        },
    ),
    DreamPattern(
        id=38,
        name="Pattern_Blending",
        description="Blend structural patterns",
        category=PatternCategory.COMPOSITION,
        c4_transform=C4Transform(delta_s=1, delta_t=1),
        semantic_transform=lambda c: {
            **c,
            "patterns_blended": True,
            "blend_type": c.get("blend", "conceptual"),
        },
    ),
    DreamPattern(
        id=39,
        name="Ensemble_Formation",
        description="Form ensemble from multiple models",
        category=PatternCategory.COMPOSITION,
        c4_transform=C4Transform(delta_s=1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "ensemble": True,
            "model_count": c.get("models", 0),
        },
    ),
    DreamPattern(
        id=40,
        name="Narrative_Weaving",
        description="Weave multiple narratives into one",
        category=PatternCategory.COMPOSITION,
        c4_transform=C4Transform(delta_t=1, delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "narrative_woven": True,
            "thread_count": c.get("threads", 0),
        },
    ),
]

# =============================================================================
# Category 6: DECOMPOSITION (Patterns 41-48)
# =============================================================================

PATTERNS_DECOMPOSITION: list[DreamPattern] = [
    DreamPattern(
        id=41,
        name="Component_Extraction",
        description="Extract independent components",
        category=PatternCategory.DECOMPOSITION,
        c4_transform=C4Transform(delta_s=-1),
        semantic_transform=lambda c: {
            **c,
            "components": c.get("parts", []),
            "extraction_method": "structural",
        },
    ),
    DreamPattern(
        id=42,
        name="Factor_Analysis",
        description="Decompose into latent factors",
        category=PatternCategory.DECOMPOSITION,
        c4_transform=C4Transform(delta_s=-1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "factors": c.get("latent_factors", []),
            "factor_count": c.get("k", 0),
        },
    ),
    DreamPattern(
        id=43,
        name="Goal_Decomposition",
        description="Break goal into subgoals",
        category=PatternCategory.DECOMPOSITION,
        c4_transform=C4Transform(delta_s=-1),
        semantic_transform=lambda c: {
            **c,
            "subgoals": c.get("subgoals", []),
            "goal_hierarchy": True,
        },
    ),
    DreamPattern(
        id=44,
        name="Process_Breakdown",
        description="Decompose process into steps",
        category=PatternCategory.DECOMPOSITION,
        c4_transform=C4Transform(delta_t=-1, delta_s=-1),
        semantic_transform=lambda c: {
            **c,
            "steps": c.get("process_steps", []),
            "step_count": len(c.get("process_steps", [])),
        },
    ),
    DreamPattern(
        id=45,
        name="Independent_Subproblem",
        description="Identify separable subproblems",
        category=PatternCategory.DECOMPOSITION,
        c4_transform=C4Transform(delta_s=-1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "subproblems": c.get("independent_parts", []),
            "separable": True,
        },
    ),
    DreamPattern(
        id=46,
        name="Aspect_Separation",
        description="Separate orthogonal aspects",
        category=PatternCategory.DECOMPOSITION,
        c4_transform=C4Transform(delta_a=-1),
        semantic_transform=lambda c: {
            **c,
            "aspects_separated": True,
            "aspect_count": len(c.get("aspects", [])),
        },
    ),
    DreamPattern(
        id=47,
        name="Granularity_Reduction",
        description="Reduce to finer granularity",
        category=PatternCategory.DECOMPOSITION,
        c4_transform=C4Transform(delta_s=-1),
        semantic_transform=lambda c: {
            **c,
            "granularity": "fine",
            "detail_level": "high",
        },
    ),
    DreamPattern(
        id=48,
        name="Boundary_Drawing",
        description="Draw boundaries around subsystems",
        category=PatternCategory.DECOMPOSITION,
        c4_transform=C4Transform(delta_a=-1, delta_s=-1),
        semantic_transform=lambda c: {
            **c,
            "boundaries_drawn": True,
            "subsystems": c.get("subsystems", []),
        },
    ),
]

# =============================================================================
# Category 7: INVERSION (Patterns 49-56)
# =============================================================================

PATTERNS_INVERSION: list[DreamPattern] = [
    DreamPattern(
        id=49,
        name="Assumption_Negation",
        description="Negate core assumptions",
        category=PatternCategory.INVERSION,
        c4_transform=C4Transform(delta_t=1, delta_s=1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "assumptions_negated": c.get("core_assumptions", []),
            "negation_count": len(c.get("core_assumptions", [])),
        },
    ),
    DreamPattern(
        id=50,
        name="Problem_Inversion",
        description="Invert the problem statement",
        category=PatternCategory.INVERSION,
        c4_transform=C4Transform(delta_t=1, delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "inverted_problem": c.get("problem", "")[::-1]
            if isinstance(c.get("problem"), str)
            else "inverted",
            "inversion_type": "structural",
        },
    ),
    DreamPattern(
        id=51,
        name="Goal_Reversal",
        description="Reverse the optimization goal",
        category=PatternCategory.INVERSION,
        c4_transform=C4Transform(delta_t=1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "goal_reversed": True,
            "original_goal": c.get("goal", "unknown"),
        },
    ),
    DreamPattern(
        id=52,
        name="Premise_Flipping",
        description="Flip logical premises",
        category=PatternCategory.INVERSION,
        c4_transform=C4Transform(delta_s=1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "premises_flipped": True,
            "flipped_premises": c.get("premises", []),
        },
    ),
    DreamPattern(
        id=53,
        name="Causal_Inversion",
        description="Invert cause-effect direction",
        category=PatternCategory.INVERSION,
        c4_transform=C4Transform(delta_t=-1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "causal_inverted": True,
            "effect_becomes_cause": c.get("effect", "unknown"),
        },
    ),
    DreamPattern(
        id=54,
        name="Value_Inversion",
        description="Invert value judgments",
        category=PatternCategory.INVERSION,
        c4_transform=C4Transform(delta_a=2),
        semantic_transform=lambda c: {
            **c,
            "values_inverted": True,
            "value_polarity": "reversed",
        },
    ),
    DreamPattern(
        id=55,
        name="Temporal_Reversal",
        description="Reverse temporal order",
        category=PatternCategory.INVERSION,
        c4_transform=C4Transform(delta_t=-1),
        semantic_transform=lambda c: {
            **c,
            "temporal_order": "reversed",
            "sequence_reversed": True,
        },
    ),
    DreamPattern(
        id=56,
        name="Paradox_Generation",
        description="Generate paradox by self-reference",
        category=PatternCategory.INVERSION,
        c4_transform=C4Transform(delta_s=2, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "paradox": True,
            "self_referential": True,
        },
    ),
]

# =============================================================================
# Category 8: CONSTRAINT (Patterns 57-64)
# =============================================================================

PATTERNS_CONSTRAINT: list[DreamPattern] = [
    DreamPattern(
        id=57,
        name="Constraint_Identification",
        description="Identify all active constraints",
        category=PatternCategory.CONSTRAINT,
        c4_transform=C4Transform(delta_s=-1),
        semantic_transform=lambda c: {
            **c,
            "constraints_identified": c.get("constraints", []),
            "constraint_count": len(c.get("constraints", [])),
        },
    ),
    DreamPattern(
        id=58,
        name="Hard_Soft_Classification",
        description="Classify constraints as hard or soft",
        category=PatternCategory.CONSTRAINT,
        c4_transform=C4Transform(delta_s=-1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "hard_constraints": c.get("hard", []),
            "soft_constraints": c.get("soft", []),
        },
    ),
    DreamPattern(
        id=59,
        name="Constraint_Relaxation",
        description="Relax soft constraints",
        category=PatternCategory.CONSTRAINT,
        c4_transform=C4Transform(delta_s=1, delta_t=1),
        semantic_transform=lambda c: {
            **c,
            "relaxed_constraints": c.get("soft", []),
            "relaxation_applied": True,
        },
    ),
    DreamPattern(
        id=60,
        name="Constraint_Tightening",
        description="Tighten constraints for precision",
        category=PatternCategory.CONSTRAINT,
        c4_transform=C4Transform(delta_s=-1, delta_t=-1),
        semantic_transform=lambda c: {
            **c,
            "tightened": True,
            "precision_increased": True,
        },
    ),
    DreamPattern(
        id=61,
        name="Tradeoff_Analysis",
        description="Analyze constraint tradeoffs",
        category=PatternCategory.CONSTRAINT,
        c4_transform=C4Transform(delta_a=1, delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "tradeoffs": c.get("tradeoff_matrix", {}),
            "pareto_front": c.get("pareto", []),
        },
    ),
    DreamPattern(
        id=62,
        name="Feasibility_Check",
        description="Check solution feasibility",
        category=PatternCategory.CONSTRAINT,
        c4_transform=C4Transform(delta_s=-1),
        semantic_transform=lambda c: {
            **c,
            "feasible": c.get("feasible", True),
            "violations": c.get("violations", []),
        },
    ),
    DreamPattern(
        id=63,
        name="Boundary_Exploration",
        description="Explore constraint boundaries",
        category=PatternCategory.CONSTRAINT,
        c4_transform=C4Transform(delta_t=1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "boundary_explored": True,
            "active_constraints": c.get("active", []),
        },
    ),
    DreamPattern(
        id=64,
        name="Constraint_Reformulation",
        description="Reformulate constraints equivalently",
        category=PatternCategory.CONSTRAINT,
        c4_transform=C4Transform(delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "reformulated": True,
            "equivalent_form": c.get("new_form", "unknown"),
        },
    ),
]

# =============================================================================
# Category 9: META (Patterns 65-72)
# =============================================================================

PATTERNS_META: list[DreamPattern] = [
    DreamPattern(
        id=65,
        name="Process_Reflection",
        description="Reflect on the reasoning process",
        category=PatternCategory.META,
        c4_transform=C4Transform(delta_s=2, delta_t=1),
        semantic_transform=lambda c: {
            **c,
            "process_reflection": True,
            "reasoning_trace": c.get("trace", []),
        },
    ),
    DreamPattern(
        id=66,
        name="Operator_Selection",
        description="Select appropriate operator for context",
        category=PatternCategory.META,
        c4_transform=C4Transform(delta_s=1, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "operator_selected": c.get("chosen_operator", "unknown"),
            "selection_criteria": c.get("criteria", []),
        },
    ),
    DreamPattern(
        id=67,
        name="Strategy_Evaluation",
        description="Evaluate current strategy effectiveness",
        category=PatternCategory.META,
        c4_transform=C4Transform(delta_s=1, delta_t=0),
        semantic_transform=lambda c: {
            **c,
            "strategy_evaluated": True,
            "effectiveness_score": c.get("score", 0.0),
        },
    ),
    DreamPattern(
        id=68,
        name="Bias_Detection",
        description="Detect cognitive biases in reasoning",
        category=PatternCategory.META,
        c4_transform=C4Transform(delta_a=1, delta_s=1),
        semantic_transform=lambda c: {
            **c,
            "biases_detected": c.get("biases", []),
            "mitigation_applied": c.get("mitigation", False),
        },
    ),
    DreamPattern(
        id=69,
        name="Confidence_Calibration",
        description="Calibrate confidence estimates",
        category=PatternCategory.META,
        c4_transform=C4Transform(delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "confidence_calibrated": True,
            "original_confidence": c.get("confidence", 0.5),
        },
    ),
    DreamPattern(
        id=70,
        name="Knowledge_Gap_Identification",
        description="Identify gaps in knowledge",
        category=PatternCategory.META,
        c4_transform=C4Transform(delta_s=1, delta_t=1),
        semantic_transform=lambda c: {
            **c,
            "knowledge_gaps": c.get("gaps", []),
            "gap_count": len(c.get("gaps", [])),
        },
    ),
    DreamPattern(
        id=71,
        name="Learning_Extraction",
        description="Extract learnings from experience",
        category=PatternCategory.META,
        c4_transform=C4Transform(delta_s=2, delta_t=-1),
        semantic_transform=lambda c: {
            **c,
            "learnings": c.get("insights", []),
            "experience_processed": True,
        },
    ),
    DreamPattern(
        id=72,
        name="Meta_Learning_Adaptation",
        description="Adapt based on meta-learning",
        category=PatternCategory.META,
        c4_transform=C4Transform(delta_s=2, delta_a=1),
        semantic_transform=lambda c: {
            **c,
            "meta_learning": True,
            "adaptation_applied": c.get("adaptation", {}),
        },
    ),
]

# =============================================================================
# Master registry
# =============================================================================

ALL_PATTERNS: list[DreamPattern] = (
    PATTERNS_ABSTRACTION
    + PATTERNS_CONCRETIZATION
    + PATTERNS_TEMPORAL
    + PATTERNS_PERSPECTIVE
    + PATTERNS_COMPOSITION
    + PATTERNS_DECOMPOSITION
    + PATTERNS_INVERSION
    + PATTERNS_CONSTRAINT
    + PATTERNS_META
)

assert len(ALL_PATTERNS) == 72, f"Expected 72 patterns, got {len(ALL_PATTERNS)}"


class MatrixDreamRegistry:
    """Registry for all 72 Matrix Dream patterns."""

    _patterns: dict[int, DreamPattern] = {}
    _by_name: dict[str, DreamPattern] = {}
    _by_category: dict[PatternCategory, list[DreamPattern]] = {
        cat: [] for cat in PatternCategory
    }

    @classmethod
    def _ensure_loaded(cls) -> None:
        if not cls._patterns:
            for p in ALL_PATTERNS:
                cls._patterns[p.id] = p
                cls._by_name[p.name] = p
                cls._by_category[p.category].append(p)

    @classmethod
    def get(cls, pattern_id: int) -> DreamPattern:
        """Get."""
        cls._ensure_loaded()
        if pattern_id not in cls._patterns:
            raise KeyError(f"Unknown pattern id: {pattern_id}")
        return cls._patterns[pattern_id]

    @classmethod
    def get_by_name(cls, name: str) -> DreamPattern:
        """Get by name."""
        cls._ensure_loaded()
        if name not in cls._by_name:
            raise KeyError(f"Unknown pattern name: {name}")
        return cls._by_name[name]

    @classmethod
    def all(cls) -> list[DreamPattern]:
        """All."""
        cls._ensure_loaded()
        return list(cls._patterns.values())

    @classmethod
    def by_category(cls, category: PatternCategory) -> list[DreamPattern]:
        """By category."""
        cls._ensure_loaded()
        return cls._by_category.get(category, [])

    @classmethod
    def categories(cls) -> list[PatternCategory]:
        return list(PatternCategory)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def apply_pattern_sequence(
    frame: CognitiveFrame, pattern_ids: list[int]
) -> CognitiveFrame:
    """Apply a sequence of Matrix Dream patterns to a frame."""
    current = frame
    for pid in pattern_ids:
        pattern = MatrixDreamRegistry.get(pid)
        current = pattern.apply(current)
    return current


def find_patterns_for_c4_transition(
    from_state: C4State, to_state: C4State
) -> list[DreamPattern]:
    """Find patterns whose C4 transform matches the given transition."""
    delta_t = (to_state.T - from_state.T) % 3
    delta_s = (to_state.S - from_state.S) % 3
    delta_a = (to_state.A - from_state.A) % 3
    matching = []
    for p in MatrixDreamRegistry.all():
        if (
            p.c4_transform.delta_t == delta_t
            and p.c4_transform.delta_s == delta_s
            and p.c4_transform.delta_a == delta_a
        ):
            matching.append(p)
    return matching


def get_category_distribution() -> dict[str, int]:
    """Get count of patterns per category."""
    return {
        cat.name: len(MatrixDreamRegistry.by_category(cat))
        for cat in PatternCategory
    }
