"""
C4REQBER: Schema Models
Domain-specific Pydantic models for discoveries, projects, and system health.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from .core import (
    C4StateModel,
    ContradictionType,
    DiscoveryStatus,
)


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
    domain: str | None = "general"

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
    experiment_type: str | None = None
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    estimated_cost: str | None = None
    estimated_time: str | None = None


class DiscoveryModel(BaseModel):
    """
    A scientific discovery/hypothesis.
    Complete provenance tracking.
    """

    id: int | None = None
    problem: str = Field(..., min_length=5, max_length=2000)
    contradiction: PhysicalContradictionModel
    hypothesis: str = Field(..., min_length=10, max_length=5000)
    c4_path: list[str] = Field(..., min_length=0, max_length=6)
    domain: str = Field(default="general", min_length=1)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    falsifiability_criteria: list[FalsifiabilityCriterionModel] = []
    status: DiscoveryStatus = DiscoveryStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    validated_at: datetime | None = None
    validation_notes: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    parent_discovery_id: int | None = None  # For version tracking
    tags: list[str] = []

    @field_validator("c4_path")
    def validate_path_length(cls, v: Any) -> Any:
        """Enforce Theorem 11: path ≤ 6 steps."""
        if len(v) > 6:
            raise ValueError(f"Path exceeds Theorem 11 bound: {len(v)} > 6")
        return v

    @field_validator("confidence_score")
    def validate_confidence(cls, v: Any) -> Any:
        """Confidence must be calibrated."""
        if v < 0 or v > 1:
            raise ValueError("Confidence must be in [0, 1]")
        return round(v, 4)  # Round to 4 decimal places

    def to_dict_for_export(self) -> dict[str, Any]:
        """Convert to dict for export (JSON-safe)."""
        return {
            "id": self.id,
            "problem": self.problem,
            "contradiction": self.contradiction.model_dump(),
            "hypothesis": self.hypothesis,
            "c4_path": self.c4_path,
            "domain": self.domain,
            "confidence_score": self.confidence_score,
            "falsifiability_criteria": [
                c.model_dump() for c in self.falsifiability_criteria
            ],
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "tags": self.tags,
        }


class ResearchProjectModel(BaseModel):
    """Research project with full tracking."""

    id: int | None = None
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    domain: str = Field(default="general")
    status: Literal["active", "completed", "on_hold", "archived"] = "active"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    start_date: datetime | None = None
    end_date: datetime | None = None
    objectives: list[str] = []
    discovery_ids: list[int] = []
    collaborator_ids: list[str] = []
    tags: list[str] = []
    notes: str = ""

    def add_discovery(self, discovery_id: int) -> None:
        """Link discovery to project."""
        if discovery_id not in self.discovery_ids:
            self.discovery_ids.append(discovery_id)
            self.updated_at = datetime.now()


class AnalogyMappingModel(BaseModel):
    """
    Cross-domain analogy mapping.
    Type I (horizontal) or Type II (vertical) isomorphism.
    """

    id: int | None = None
    source_domain: str = Field(..., min_length=1)
    target_domain: str = Field(..., min_length=1)
    mapping_type: Literal["horizontal", "vertical", "semantic", "structural"]
    source_concept: str = Field(..., min_length=1)
    target_concept: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    semantic_similarity: float | None = None  # Word2Vec cosine
    structural_similarity: float | None = None  # Graph isomorphism score
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
    validation_rate: float | None = None  # % of hypotheses validated
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
