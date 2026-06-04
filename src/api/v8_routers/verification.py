"""FastAPI router for hypothesis verification."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.api.errors import C4APIError, ValidationError

try:
    from src.verification import (  # type: ignore[attr-defined]
        UnifiedVerificationEngine,
        VerificationMethod,
        VerificationScore,
    )
except Exception:
    UnifiedVerificationEngine = None  # type: ignore[misc,assignment]
    VerificationMethod = None  # type: ignore[misc,assignment]
    VerificationScore = None  # type: ignore[misc,assignment]

router = APIRouter(prefix="/verification", tags=["verification"])

# Global engine instance (stateless, reusable)
_verification_engine: Any | None = None


def _get_engine() -> Any:
    global _verification_engine
    if _verification_engine is None and UnifiedVerificationEngine is not None:
        _verification_engine = UnifiedVerificationEngine()
    return _verification_engine


class VerifyRequest(BaseModel):
    """Request body for hypothesis verification."""

    hypothesis: str = Field(..., min_length=1, max_length=5000, json_schema_extra={"example": "Increasing temperature increases reaction rate"})
    context: dict[str, Any] = Field(default_factory=dict, json_schema_extra={"example": {"test_type": "correlation", "x": [1, 2, 3], "y": [2, 4, 6]}})
    methods: list[str] = Field(
        default_factory=list,
        json_schema_extra={"example": ["statistical", "smt"]},
    )
    timeout_per_method: float = Field(default=60.0, ge=1.0, le=300.0)


class VerifyResponse(BaseModel):
    """Response from hypothesis verification."""

    hypothesis_id: str
    hypothesis_text: str
    overall_status: str
    overall_confidence: float
    score: int = Field(ge=0, le=100)
    results: list[dict[str, Any]]
    recommendations: list[str]
    statistical_score: int
    formal_score: int
    simulation_score: int

    @classmethod
    def from_score(cls, score: Any) -> "VerifyResponse":
        return cls(
            hypothesis_id=score.hypothesis_id,
            hypothesis_text=score.hypothesis_text,
            overall_status=score.overall_status.value,
            overall_confidence=score.overall_confidence,
            score=score.score,
            results=[r.model_dump() for r in score.results],
            recommendations=score.recommendations,
            statistical_score=score.statistical_score,
            formal_score=score.formal_score,
            simulation_score=score.simulation_score,
        )


@router.post("/verify", response_model=VerifyResponse)
async def verify_hypothesis(req: VerifyRequest) -> VerifyResponse:
    """Verify a scientific hypothesis using multiple backends.

    Supports statistical testing (SciPy), SMT solving (Z3),
    and theorem proving (Dafny).

    Example context for statistical test:
    ```json
    {
      "test_type": "ttest",
      "group_a": [1.0, 2.0, 3.0],
      "group_b": [4.0, 5.0, 6.0],
      "alpha": 0.05
    }
    ```
    """
    if not req.hypothesis.strip():
        raise ValidationError("Hypothesis cannot be empty")

    # Parse method strings to enum values
    methods: list[Any] | None = None
    if req.methods:
        methods = []
        for m in req.methods:
            try:
                methods.append(VerificationMethod(m.lower()))
            except ValueError:
                raise ValidationError(f"Unknown verification method: {m}")

    engine = _get_engine()
    try:
        score = await engine.verify_hypothesis(
            hypothesis=req.hypothesis,
            context=req.context,
            methods=methods,
            timeout_per_method=req.timeout_per_method,
        )
    except Exception as exc:
        raise C4APIError(
            f"Verification failed: {exc}",
            status_code=500,
            error_code="verification_failed",
        ) from exc

    return VerifyResponse.from_score(score)


@router.get("/methods")
async def list_methods() -> dict[str, Any]:
    """List available verification backends and their status."""
    engine = _get_engine()
    available = engine.available_methods
    all_methods = list(VerificationMethod) if VerificationMethod is not None else []
    return {
        "available": [m.value for m in available],
        "all": [m.value for m in all_methods],
        "status": {m.value: (m in available) for m in all_methods},
    }
