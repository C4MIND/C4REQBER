"""
C4REQBER: Core Models
Base enums and fundamental Pydantic models for C4 cognitive architecture.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import ConfigDict, field_validator

import sys

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum
    class StrEnum(str, Enum):  # noqa: UP042
        """Fallback StrEnum for Python < 3.11."""
        def __str__(self) -> str:
            return str(self.value)

from pydantic import BaseModel, Field, validator


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


class ContradictionType(StrEnum):
    """Types of physical contradictions."""

    TRADE_OFF = "trade_off"
    DUAL_REQUIREMENT = "dual_requirement"
    CONFLICTING_GOALS = "conflicting_goals"
    TEMPORAL = "temporal"
    SCALE = "scale"
    PERSPECTIVE = "perspective"


class DiscoveryStatus(StrEnum):
    """Status of a discovery/hypothesis."""

    PENDING = "pending"
    VALIDATED = "validated"
    FALSIFIED = "falsified"
    UNDER_TEST = "under_test"
    DEPRECATED = "deprecated"


class BaseOperator(StrEnum):
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

    model_config = ConfigDict(validate_assignment=True, frozen=True)

    def to_tuple(self) -> tuple[int, int, int]:
        """Convert to tuple for hashing."""
        return (self.T.value, self.S.value, self.A.value)

    def to_coords(self) -> dict[str, int]:
        """Convert to coordinate dict."""
        return {"T": self.T.value, "S": self.S.value, "A": self.A.value}

    @property
    def label(self) -> str:
        """Human-readable label."""
        t_names = {0: "Past", 1: "Present", 2: "Future"}
        s_names = {0: "Concrete", 1: "Abstract", 2: "Meta"}
        a_names = {0: "Self", 1: "Other", 2: "System"}
        return f"F⟨{t_names[self.T.value]}, {s_names[self.S.value]}, {a_names[self.A.value]}⟩"

    def hamming_distance(self, other: C4StateModel) -> int:
        """Calculate Hamming distance to another state."""
        return sum(
            1 if a != b else 0 for a, b in zip(self.to_tuple(), other.to_tuple(), strict=False)
        )

    @classmethod
    def from_coords(cls, T: int, S: int, A: int) -> C4StateModel:
        """Create from raw coordinates with validation."""
        return cls(T=TimeAxis(T % 3), S=ScaleAxis(S % 3), A=AgencyAxis(A % 3))

    @classmethod
    def all_states(cls) -> list[C4StateModel]:
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
    description: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @field_validator("operator")
    def validate_operator(cls, v: Any) -> Any:
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
