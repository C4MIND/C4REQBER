"""
C4REQBER API: Pydantic Models
Request/Response schemas
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════
# BASE MODELS
# ═══════════════════════════════════════════════════════════════════


class HealthResponse(BaseModel):
    """HealthResponse."""
    status: str
    version: str
    timestamp: datetime
    services: dict[str, str]


class MetricsResponse(BaseModel):
    """MetricsResponse."""
    total_discoveries: int
    total_hypotheses: int
    active_experiments: int
    validation_rate: float
    avg_confidence: float
    api_requests_24h: int
    cache_hit_rate: float


# ═══════════════════════════════════════════════════════════════════
# AUTH MODELS
# ═══════════════════════════════════════════════════════════════════


class UserCreate(BaseModel):
    """UserCreate."""
    email: str
    password: str
    name: str | None = None


class User(BaseModel):
    """User."""
    id: str
    email: str
    name: str | None = None
    created_at: datetime | None = None


class UserResponse(BaseModel):
    """UserResponse."""
    id: str
    email: str
    name: str | None
    created_at: datetime


class TokenResponse(BaseModel):
    """TokenResponse."""
    access_token: str
    token_type: str = "bearer"


# ═══════════════════════════════════════════════════════════════════
# DISCOVERY MODELS
# ═══════════════════════════════════════════════════════════════════


class DiscoveryRequest(BaseModel):
    """DiscoveryRequest."""
    problem: str = Field(..., min_length=10, max_length=1000)
    max_hypotheses: int | None = Field(5, ge=1, le=20)
    include_validation: bool = True
    literature_search: bool = True


class HypothesisResponse(BaseModel):
    """HypothesisResponse."""
    id: str
    hypothesis: str
    confidence: float
    method: str
    c4_path: list[str]
    triz_principles: list[int]
    simulation: dict[str, Any] | None = None


class DiscoveryResponse(BaseModel):
    """DiscoveryResponse."""
    id: str
    problem: str
    hypotheses: list[HypothesisResponse]
    top_hypothesis: str | None
    duration_seconds: float
    estimated_cost: float
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════
# SEARCH MODELS
# ═══════════════════════════════════════════════════════════════════


class SearchRequest(BaseModel):
    """SearchRequest."""
    query: str = Field(..., min_length=3, max_length=500)
    limit: int | None = Field(10, ge=1, le=100)
    year_start: int | None = None
    year_end: int | None = None


class PaperResult(BaseModel):
    """PaperResult."""
    title: str
    authors: list[str]
    year: int
    citation_count: int
    abstract: str


class SearchResponse(BaseModel):
    """SearchResponse."""
    query: str
    total: int
    papers: list[dict[str, Any]]


# ═══════════════════════════════════════════════════════════════════
# VALIDATION MODELS
# ═══════════════════════════════════════════════════════════════════


class ValidationRequest(BaseModel):
    """ValidationRequest."""
    outcome: str  # validated, falsified, inconclusive
    notes: str | None = None
    confidence: float | None = Field(0.5, ge=0, le=1)


class ObservationData(BaseModel):
    """ObservationData."""
    data: dict[str, float]
    notes: str | None = None


class ValidationExperimentCreate(BaseModel):
    """ValidationExperimentCreate."""
    hypothesis_id: str
    name: str | None = None
    method: str | None = "simulation"


class ValidationExperimentResponse(BaseModel):
    """ValidationExperimentResponse."""
    id: str
    user_id: str | None = None
    hypothesis_id: str
    name: str
    method: str
    status: str  # draft, running, completed, cancelled
    observations: list[dict[str, Any]] = []
    conclusion: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


# ═══════════════════════════════════════════════════════════════════
# WEBSOCKET MODELS
# ═══════════════════════════════════════════════════════════════════


class WebSocketMessage(BaseModel):
    """WebSocketMessage."""
    type: str  # discover, ping, progress, result
    payload: dict[str, Any] | None = None
