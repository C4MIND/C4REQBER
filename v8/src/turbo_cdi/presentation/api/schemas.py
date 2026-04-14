"""
Pydantic schemas for TURBO-CDI v8.4 API
Request/response models with validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


# Base Response Models
class BaseAPIResponse(BaseModel):
    """Base API response structure"""

    status: str = "success"
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# Corpus Schemas
class CreateCorpusRequest(BaseModel):
    """Request schema for creating a corpus"""

    id: Optional[str] = Field(
        None, description="Optional corpus ID, auto-generated if not provided"
    )
    name: str = Field(..., description="Human-readable corpus name")
    domain: str = Field(..., description="Knowledge domain (e.g., 'physics', 'biology')")
    subdomains: Optional[List[str]] = Field(
        default_factory=list, description="Domain subcategories"
    )
    epoch_end: str = Field("2024", description="Historical cutoff year")

    @validator("name")
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v

    @validator("domain")
    def domain_not_empty(cls, v):
        if not v.strip():
            raise ValueError("domain cannot be empty")
        return v


class CreateCorpusResponse(BaseAPIResponse):
    """Response schema for corpus creation"""

    id: str
    name: str
    domain: str
    created_at: Optional[datetime] = None


class CorpusSummaryResponse(BaseModel):
    """Summary view of a corpus for listings"""

    id: str
    name: str
    domain: str
    subdomains: List[str]
    fact_count: int
    theory_count: int
    anomaly_count: int
    created_at: datetime
    updated_at: datetime


class CorpusDetailResponse(BaseModel):
    """Detailed corpus information"""

    id: str
    name: str
    domain: str
    subdomains: List[str]
    epoch_end: str
    facts: List[dict]  # Simplified - could be more detailed
    theories: List[dict]  # Simplified
    anomalies: List[dict]  # Simplified
    created_at: datetime
    updated_at: datetime


class UpdateCorpusRequest(BaseModel):
    """Request schema for updating a corpus"""

    name: Optional[str] = None
    domain: Optional[str] = None
    subdomains: Optional[List[str]] = None


class OptimizeCorpusRequest(BaseModel):
    """Request schema for corpus optimization"""

    level: str = Field("standard", description="Optimization level: 'basic', 'standard', 'deep'")

    @validator("level")
    def validate_level(cls, v):
        allowed = ["basic", "standard", "deep"]
        if v not in allowed:
            raise ValueError(f"level must be one of {allowed}")
        return v


class DeleteCorpusResponse(BaseAPIResponse):
    """Response schema for corpus deletion"""

    corpus_id: str
    deleted: bool = True


# Discovery Schemas
class DiscoverKnowledgeRequest(BaseModel):
    """Request schema for knowledge discovery"""

    corpus_id: str = Field(..., description="ID of corpus to analyze")
    anomaly_threshold: float = Field(0.7, description="Sensitivity for anomaly detection (0.0-1.0)")
    max_analysis_time: int = Field(300, description="Maximum analysis time in seconds")

    @validator("corpus_id")
    def validate_corpus_id(cls, v):
        if not v.strip():
            raise ValueError("corpus_id cannot be empty")
        return v

    @validator("anomaly_threshold")
    def validate_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("anomaly_threshold must be between 0.0 and 1.0")
        return v


class DiscoveryResponse(BaseAPIResponse):
    """Response schema for knowledge discovery"""

    corpus_id: str
    anomalies_found: int
    anomalies: List[dict]  # Could be more detailed with AnomalyDTO
    processing_time: float


# Presupposition Analysis Schemas
class AnalyzePresuppositionsRequest(BaseModel):
    """Request schema for presupposition analysis"""

    theory_id: str = Field(..., description="ID of theory to analyze")
    theory_text: str = Field(..., description="Text content of the theory")
    analysis_depth: str = Field(
        "standard", description="Analysis depth: 'basic', 'standard', 'deep'"
    )

    @validator("theory_id")
    def validate_theory_id(cls, v):
        if not v.strip():
            raise ValueError("theory_id cannot be empty")
        return v

    @validator("theory_text")
    def validate_theory_text(cls, v):
        if not v.strip():
            raise ValueError("theory_text cannot be empty")
        return v

    @validator("analysis_depth")
    def validate_depth(cls, v):
        allowed = ["basic", "standard", "deep"]
        if v not in allowed:
            raise ValueError(f"analysis_depth must be one of {allowed}")
        return v


class PresuppositionAnalysisResponse(BaseAPIResponse):
    """Response schema for presupposition analysis"""

    theory_id: str
    presuppositions_found: int
    presuppositions: List[dict]  # Could be more detailed
    analysis_score: float


# Transformation Schemas
class ApplyTransformationRequest(BaseModel):
    """Request schema for cognitive transformation"""

    input_concept: str = Field(..., description="Starting concept to transform")
    transformation_type: str = Field(..., description="Type of transformation to apply")
    domain: str = Field(..., description="Knowledge domain context")
    operator: Optional[str] = Field(None, description="Specific QZRF operator to use")

    @validator("transformation_type")
    def validate_transformation_type(cls, v):
        allowed = ["invert", "bridge", "synthesize", "abstract", "concretize"]
        if v not in allowed:
            raise ValueError(f"transformation_type must be one of {allowed}")
        return v


class TransformationResponse(BaseAPIResponse):
    """Response schema for cognitive transformation"""

    transformation: Optional[dict] = None  # Could be more detailed
    transformation_applied: bool = False


# Health and System Schemas
class HealthResponse(BaseAPIResponse):
    """Comprehensive health check response"""

    services: dict
    database: Optional[dict] = None
    cache: Optional[dict] = None
    external_services: Optional[dict] = None
    overall_health: str = "unknown"


class SystemInfoResponse(BaseAPIResponse):
    """System information response"""

    version: str
    build_info: dict
    configuration: dict
    environment: dict
    features: dict


# Administrative Schemas
class BackupRequest(BaseModel):
    """Request schema for backup operations"""

    include_data: bool = True
    include_config: bool = True
    compression: str = "gzip"

    @validator("compression")
    def validate_compression(cls, v):
        allowed = ["none", "gzip", "bz2"]
        if v not in allowed:
            raise ValueError(f"compression must be one of {allowed}")
        return v


class BackupStatus(BaseModel):
    """Backup operation status"""

    backup_id: str
    status: str  # "running", "completed", "failed"
    progress: int  # Percentage 0-100
    components_completed: List[str]
    download_url: Optional[str] = None
    error_message: Optional[str] = None


class RestoreRequest(BaseModel):
    """Request schema for restore operations"""

    backup_id: str
    restore_data: bool = True
    restore_config: bool = False

    @validator("backup_id")
    def validate_backup_id(cls, v):
        if not v.strip():
            raise ValueError("backup_id cannot be empty")
        return v


class MigrationStatus(BaseModel):
    """Database migration status"""

    status: str  # "pending", "running", "completed", "failed"
    migrations_applied: List[str]
    applied_at: str
    error_message: Optional[str] = None


# Exception Schemas
class ErrorResponse(BaseModel):
    """Standard error response"""

    error: str
    message: str
    details: Optional[dict] = None
    request_id: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Input validation failed",
                "details": {"field": "corpus_id", "reason": "cannot be empty"},
                "request_id": "123e4567-e89b-12d3-a456-426614174000",
            }
        }


# Enhanced error classification
class APIError(Exception):
    """Base API error with proper classification"""

    def __init__(
        self, message: str, error_code: str, status_code: int = 500, details: Optional[dict] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationAPIError(APIError):
    """Validation error"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message, error_code="VALIDATION_ERROR", status_code=422, details=details
        )


class AuthenticationAPIError(APIError):
    """Authentication error"""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message=message, error_code="AUTHENTICATION_ERROR", status_code=401)


class AuthorizationAPIError(APIError):
    """Authorization error"""

    def __init__(self, message: str = "Insufficient permissions", required_permission: str = None):
        details = {"required_permission": required_permission} if required_permission else None
        super().__init__(
            message=message, error_code="AUTHORIZATION_ERROR", status_code=403, details=details
        )


class NotFoundAPIError(APIError):
    """Resource not found error"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} '{resource_id}' not found",
            error_code="NOT_FOUND_ERROR",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ConflictAPIError(APIError):
    """Resource conflict error"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message, error_code="CONFLICT_ERROR", status_code=409, details=details
        )


class RateLimitAPIError(APIError):
    """Rate limiting error"""

    def __init__(self, message: str = "Rate limit exceeded", reset_time: int = None):
        details = {"reset_time": reset_time} if reset_time else None
        super().__init__(
            message=message, error_code="RATE_LIMIT_ERROR", status_code=429, details=details
        )
