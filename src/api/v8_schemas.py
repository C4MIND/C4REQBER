"""
C4REQBER v8.0 API Schemas
Pydantic models for request/response validation.
"""
from __future__ import annotations

from pydantic import BaseModel, field_validator


class PhysicsRunRequest(BaseModel):
    """PhysicsRunRequest."""
    pattern_id: str
    hypothesis: dict
    engine: str | None = None
    force_cpu: bool = False


class PhysicsRunResponse(BaseModel):
    """PhysicsRunResponse."""
    pattern_id: str
    engine_used: str
    gpu_accelerated: bool
    execution_time: float
    result: dict


class KnowledgeSearchRequest(BaseModel):
    """KnowledgeSearchRequest."""
    query: str
    sources: list[str] | None = None
    max_results: int = 50


class Paper(BaseModel):
    """Paper."""
    title: str
    authors: list[str]
    abstract: str | None = None
    doi: str | None = None
    arxiv_id: str | None = None
    pmid: str | None = None
    year: int | None = None
    source: str


class NewtonSimulateRequest(BaseModel):
    """NewtonSimulateRequest."""
    initial_conditions: dict
    duration: float
    timestep: float = 0.01

    @field_validator("duration")
    @classmethod
    def duration_non_negative(cls, v: float) -> float:
        """Duration non negative."""
        if v < 0:
            raise ValueError("duration must be non-negative")
        return v


VALID_SORT_BY = ("relevance", "submittedDate", "lastUpdatedDate")


class KnowledgeSearchPostRequest(BaseModel):
    """KnowledgeSearchPostRequest."""
    query: str
    max_results: int = 50
    sort_by: str = "relevance"
    category: str | None = None

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Query not empty."""
        if not v.strip():
            raise ValueError("query must not be empty")
        return v

    @field_validator("sort_by")
    @classmethod
    def sort_by_valid(cls, v: str) -> str:
        """Sort by valid."""
        if v not in VALID_SORT_BY:
            raise ValueError(f"invalid sort_by: {v}")
        return v


class KnowledgeAddEntryRequest(BaseModel):
    """KnowledgeAddEntryRequest."""
    title: str
    authors: list[str] = []
    abstract: str | None = None


class KnowledgeFulltextRequest(BaseModel):
    """KnowledgeFulltextRequest."""
    query: str


class SocialPostRequest(BaseModel):
    """SocialPostRequest."""
    platform: str
    content: str
    media_urls: list[str] = []
    schedule_time: str | None = None


class VerificationVerifyRequest(BaseModel):
    """VerificationVerifyRequest."""
    code: str
    specification: dict | None = None
    formal_method: str = "hoare"


class VerificationLeanRequest(BaseModel):
    """VerificationLeanRequest."""
    theorem: str
    proof: str | None = None
    language: str = "lean4"
