"""
TURBO-CDI: Pydantic Models v4.0
Production-grade type safety with strict validation
"""

from pydantic import BaseModel, Field, validator, root_validator
from typing import List, Optional, Literal, Dict, Any, Tuple
from datetime import datetime
from enum import Enum


class TimeAxis(int, Enum):
    """T-axis: Temporal orientation."""

    PAST = 0
    PRESENT = 1
    FUTURE = 2


class ScaleAxis(int, Enum):
    """S-axis: Level of abstraction."""

    CONCRETE = 0
    ABSTRACT = 1
    META = 2


class AgencyAxis(int, Enum):
    """A-axis: Perspective."""

    SELF = 0
    OTHER = 1
    SYSTEM = 2


class ContradictionType(str, Enum):
    """Types of physical contradictions."""

    TRADE_OFF = "trade_off"
    DUAL_REQUIREMENT = "dual_requirement"
    CONFLICTING_GOALS = "conflicting_goals"
    TEMPORAL = "temporal"
    SCALE = "scale"
    PERSPECTIVE = "perspective"


class DiscoveryStatus(str, Enum):
    """Status of a discovery/hypothesis."""

    PENDING = "pending"
    VALIDATED = "validated"
    FALSIFIED = "falsified"
    UNDER_TEST = "under_test"
    DEPRECATED = "deprecated"


class BaseOperator(str, Enum):
    """9 Base C4 operators."""

    TAU_PLUS = "tau+"
    TAU_MINUS = "tau-"
    SIGMA = "sigma"
    DELTA = "delta"
    RHO = "rho"
    IOTA = "iota"
    LAMBDA_PLUS = "lambda+"
    LAMBDA_MINUS = "lambda-"
    KAPPA_PLUS = "kappa+"
    KAPPA_MINUS = "kappa-"


class C4StateModel(BaseModel):
    """
    Immutable C4 state with strict validation.

    Z₃³ = {Time, Scale, Agency}
    Each coordinate ∈ {0, 1, 2}
    """

    T: TimeAxis = Field(..., description="Time axis: Past(0), Present(1), Future(2)")
    S: ScaleAxis = Field(
        ..., description="Scale axis: Concrete(0), Abstract(1), Meta(2)"
    )
    A: AgencyAxis = Field(..., description="Agency axis: Self(0), Other(1), System(2)")

    class Config:
        frozen = True  # Immutable
        validate_assignment = True

    def to_tuple(self) -> Tuple[int, int, int]:
        """Convert to tuple for hashing."""
        return (self.T.value, self.S.value, self.A.value)

    def to_coords(self) -> Dict[str, int]:
        """Convert to coordinate dict."""
        return {"T": self.T.value, "S": self.S.value, "A": self.A.value}

    @property
    def label(self) -> str:
        """Human-readable label."""
        t_names = {0: "Past", 1: "Present", 2: "Future"}
        s_names = {0: "Concrete", 1: "Abstract", 2: "Meta"}
        a_names = {0: "Self", 1: "Other", 2: "System"}
        return f"F⟨{t_names[self.T.value]}, {s_names[self.S.value]}, {a_names[self.A.value]}⟩"

    def hamming_distance(self, other: "C4StateModel") -> int:
        """Calculate Hamming distance to another state."""
        return sum(
            1 if a != b else 0 for a, b in zip(self.to_tuple(), other.to_tuple())
        )

    @classmethod
    def from_coords(cls, T: int, S: int, A: int) -> "C4StateModel":
        """Create from raw coordinates with validation."""
        return cls(T=TimeAxis(T % 3), S=ScaleAxis(S % 3), A=AgencyAxis(A % 3))

    @classmethod
    def all_states(cls) -> List["C4StateModel"]:
        """Generate all 27 C4 states."""
        return [
            cls(T=TimeAxis(t), S=ScaleAxis(s), A=AgencyAxis(a))
            for t in range(3)
            for s in range(3)
            for a in range(3)
        ]


class C4TransitionModel(BaseModel):
    """A single transition in C4 space."""

    operator: str = Field(..., min_length=1, max_length=20)
    from_state: C4StateModel
    to_state: C4StateModel
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @validator("operator")
    def validate_operator(cls, v):
        """Ensure operator is valid."""
        valid_ops = [
            "tau+",
            "tau-",
            "sigma",
            "delta",
            "rho",
            "iota",
            "lambda+",
            "lambda-",
            "kappa+",
            "kappa-",
            "tau_sigma",
            "tau_delta",
            "tau_rho",
            "sigma_iota",
            "delta_iota",
            "rho_tau",
            "rho_iota",
            "iota_lambda",
            "lambda_sigma",
            "lambda_iota",
            "kappa_sigma",
            "kappa_delta",
            "lambda_kappa",
            "sigma_phi",
            "delta_phi",
            "rho_phi",
            "kappa_phi",
            "mu_phi",
        ]
        if v not in valid_ops:
            raise ValueError(f"Invalid operator: {v}. Must be one of {valid_ops}")
        return v


class PhysicalContradictionModel(BaseModel):
    """
    Physical Contradiction (Altshuller-style).
    Format: "X must be A AND not-A simultaneously"
    """

    parameter: str = Field(..., min_length=1, max_length=200)
    value_a: str = Field(..., min_length=1, max_length=200)
    value_not_a: str = Field(..., min_length=1, max_length=200)
    requirement_y: str = Field(..., min_length=1, max_length=200)
    requirement_z: str = Field(..., min_length=1, max_length=200)
    contradiction_type: ContradictionType
    domain: Optional[str] = "general"

    model_config = {
        "json_schema_extra": {
            "example": {
                "parameter": "Charging speed",
                "value_a": "FAST (<10 min)",
                "value_not_a": "SLOW (preserve capacity)",
                "requirement_y": "User convenience",
                "requirement_z": "Cycle life >1000",
                "contradiction_type": "trade_off",
            }
        }
    }

    def __str__(self) -> str:
        return f"'{self.parameter}' must be {self.value_a} (for {self.requirement_y}) AND {self.value_not_a} (for {self.requirement_z})"


class FalsifiabilityCriterionModel(BaseModel):
    """Single falsifiability criterion (Popper-style)."""

    statement: str = Field(
        ..., min_length=10, description="'If X, then hypothesis is false'"
    )
    measurement: str = Field(..., min_length=1, description="How to measure X")
    threshold: str = Field(..., min_length=1, description="Specific numeric threshold")
    experiment_type: Optional[str] = None
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    estimated_cost: Optional[str] = None
    estimated_time: Optional[str] = None


class DiscoveryModel(BaseModel):
    """
    A scientific discovery/hypothesis.
    Complete provenance tracking.
    """

    id: Optional[int] = None
    problem: str = Field(..., min_length=5, max_length=2000)
    contradiction: PhysicalContradictionModel
    hypothesis: str = Field(..., min_length=10, max_length=5000)
    c4_path: List[str] = Field(..., min_items=0, max_items=6)
    domain: str = Field(default="general", min_length=1)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    falsifiability_criteria: List[FalsifiabilityCriterionModel] = []
    status: DiscoveryStatus = DiscoveryStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    validated_at: Optional[datetime] = None
    validation_notes: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    parent_discovery_id: Optional[int] = None  # For version tracking
    tags: List[str] = []

    @validator("c4_path")
    def validate_path_length(cls, v):
        """Enforce Theorem 11: path ≤ 6 steps."""
        if len(v) > 6:
            raise ValueError(f"Path exceeds Theorem 11 bound: {len(v)} > 6")
        return v

    @validator("confidence_score")
    def validate_confidence(cls, v):
        """Confidence must be calibrated."""
        if v < 0 or v > 1:
            raise ValueError("Confidence must be in [0, 1]")
        return round(v, 4)  # Round to 4 decimal places

    def to_dict_for_export(self) -> Dict[str, Any]:
        """Convert to dict for export (JSON-safe)."""
        return {
            "id": self.id,
            "problem": self.problem,
            "contradiction": self.contradiction.dict(),
            "hypothesis": self.hypothesis,
            "c4_path": self.c4_path,
            "domain": self.domain,
            "confidence_score": self.confidence_score,
            "falsifiability_criteria": [c.dict() for c in self.falsifiability_criteria],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags,
        }


class ResearchProjectModel(BaseModel):
    """Research project with full tracking."""

    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    domain: str = Field(default="general")
    status: Literal["active", "completed", "on_hold", "archived"] = "active"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    objectives: List[str] = []
    discovery_ids: List[int] = []
    collaborator_ids: List[str] = []
    tags: List[str] = []
    notes: str = ""

    def add_discovery(self, discovery_id: int):
        """Link discovery to project."""
        if discovery_id not in self.discovery_ids:
            self.discovery_ids.append(discovery_id)
            self.updated_at = datetime.now()


class AnalogyMappingModel(BaseModel):
    """
    Cross-domain analogy mapping.
    Type I (horizontal) or Type II (vertical) isomorphism.
    """

    id: Optional[int] = None
    source_domain: str = Field(..., min_length=1)
    target_domain: str = Field(..., min_length=1)
    mapping_type: Literal["horizontal", "vertical", "semantic", "structural"]
    source_concept: str = Field(..., min_length=1)
    target_concept: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    semantic_similarity: Optional[float] = None  # Word2Vec cosine
    structural_similarity: Optional[float] = None  # Graph isomorphism score
    discovered_at: datetime = Field(default_factory=datetime.now)
    verified: bool = False
    usage_count: int = 0  # How many times used successfully

    @property
    def composite_score(self) -> float:
        """Combined score for ranking analogies."""
        scores = [self.confidence]
        if self.semantic_similarity is not None:
            scores.append(self.semantic_similarity)
        if self.structural_similarity is not None:
            scores.append(self.structural_similarity)
        return sum(scores) / len(scores)


class SystemHealthModel(BaseModel):
    """System health and metrics."""

    timestamp: datetime = Field(default_factory=datetime.now)
    llm_provider: str
    llm_status: Literal["healthy", "degraded", "down"]
    db_status: Literal["healthy", "degraded", "down"]
    discoveries_total: int
    discoveries_today: int
    avg_confidence: float
    validation_rate: Optional[float] = None  # % of hypotheses validated
    api_calls_last_hour: int = 0
    api_errors_last_hour: int = 0

    @property
    def error_rate(self) -> float:
        """Calculate error rate."""
        if self.api_calls_last_hour == 0:
            return 0.0
        return self.api_errors_last_hour / self.api_calls_last_hour

    @property
    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return (
            self.llm_status == "healthy"
            and self.db_status == "healthy"
            and self.error_rate < 0.1  # <10% errors
        )


# Schema exports for LLM structured generation
DISCOVERY_SCHEMA = {
    "type": "object",
    "properties": {
        "hypothesis": {"type": "string", "minLength": 10},
        "mechanism": {"type": "string"},
        "testable_predictions": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
    },
    "required": ["hypothesis"],
}

FALSIFIABILITY_SCHEMA = {
    "type": "object",
    "properties": {
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "statement": {"type": "string"},
                    "measurement": {"type": "string"},
                    "threshold": {"type": "string"},
                    "difficulty": {
                        "type": "string",
                        "enum": ["easy", "medium", "hard"],
                    },
                },
                "required": ["statement", "threshold"],
            },
            "minItems": 1,
            "maxItems": 5,
        }
    },
    "required": ["criteria"],
}
