"""
TURBO-CDI API: Pydantic Models
Request/Response schemas
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════
# BASE MODELS
# ═══════════════════════════════════════════════════════════════════


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]


class MetricsResponse(BaseModel):
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
    email: str
    password: str
    name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ═══════════════════════════════════════════════════════════════════
# DISCOVERY MODELS
# ═══════════════════════════════════════════════════════════════════


class DiscoveryRequest(BaseModel):
    problem: str = Field(..., min_length=10, max_length=1000)
    max_hypotheses: Optional[int] = Field(5, ge=1, le=20)
    include_validation: bool = True
    literature_search: bool = True


class HypothesisResponse(BaseModel):
    id: str
    hypothesis: str
    confidence: float
    method: str
    c4_path: List[str]
    triz_principles: List[int]
    simulation: Optional[Dict[str, Any]] = None


class DiscoveryResponse(BaseModel):
    id: str
    problem: str
    hypotheses: List[HypothesisResponse]
    top_hypothesis: Optional[str]
    duration_seconds: float
    estimated_cost: float
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════
# SEARCH MODELS
# ═══════════════════════════════════════════════════════════════════


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    limit: Optional[int] = Field(10, ge=1, le=100)
    year_start: Optional[int] = None
    year_end: Optional[int] = None


class PaperResult(BaseModel):
    title: str
    authors: List[str]
    year: int
    citation_count: int
    abstract: str


class SearchResponse(BaseModel):
    query: str
    total: int
    papers: List[Dict[str, Any]]


# ═══════════════════════════════════════════════════════════════════
# VALIDATION MODELS
# ═══════════════════════════════════════════════════════════════════


class ValidationRequest(BaseModel):
    outcome: str  # validated, falsified, inconclusive
    notes: Optional[str] = None
    confidence: Optional[float] = Field(0.5, ge=0, le=1)


# ═══════════════════════════════════════════════════════════════════
# WEBSOCKET MODELS
# ═══════════════════════════════════════════════════════════════════


class WebSocketMessage(BaseModel):
    type: str  # discover, ping, progress, result
    payload: Optional[Dict[str, Any]] = None
