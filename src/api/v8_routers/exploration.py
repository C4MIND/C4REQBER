"""
c4reqber: Exploration API Router (v8)

Endpoints for open-ended anomaly detection and research question generation.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from fastapi import APIRouter, status
from pydantic import BaseModel, Field, field_validator

from src.api.errors import C4APIError, ValidationError
from src.exploration.anomaly_detector import AnomalyDetector
from src.exploration.formal_extender import FormalFrameworkExtender
from src.exploration.question_generator import SurpriseDrivenQuestionGenerator


router = APIRouter(prefix="/exploration", tags=["v8-exploration"])


class AnomalyRequest(BaseModel):
    """Request to detect anomalies in literature and simulation data."""

    model_config = {"json_schema_extra": {"example": {
        "embeddings": [[0.1, 0.2, 0.3], [0.9, 0.8, 0.7], [0.15, 0.25, 0.35]],
        "papers": [{"title": "Paper A"}, {"title": "Paper B"}, {"title": "Paper C"}],
        "predicted": [1.0, 2.0, 3.0, 4.0, 5.0],
        "expected": [1.1, 2.1, 3.1, 4.1, 5.1],
        "contamination": 0.05,
        "threshold_sigma": 3.0,
    }}}

    embeddings: list[list[float]] | None = Field(
        default=None,
        description="Paper embeddings as list of vectors",
    )
    papers: list[dict[str, Any]] = Field(default_factory=list)
    predicted: list[float] | None = Field(
        default=None,
        description="Predicted simulation values",
    )
    expected: list[float] | None = Field(
        default=None,
        description="Expected/theoretical values for comparison",
    )
    contamination: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Expected outlier fraction for literature anomalies",
    )
    threshold_sigma: float = Field(
        default=3.0,
        ge=0.5,
        le=10.0,
        description="Std-dev threshold for simulation residual outliers",
    )

    @field_validator("embeddings")
    @classmethod
    def check_embeddings_shape(cls, v: list[list[float]] | None) -> list[list[float]] | None:
        """Ensure all embedding vectors have the same dimension."""
        if v is None or len(v) == 0:
            return v
        first_len = len(v[0])
        if any(len(vec) != first_len for vec in v):
            raise ValueError("All embedding vectors must have the same dimension")
        return v


class QuestionRequest(BaseModel):
    """Request to generate surprise-driven research questions."""

    model_config = {"json_schema_extra": {"example": {
        "existing_questions": ["Does X cause Y?"],
        "topic": "causal inference in quantum systems",
        "n_candidates": 50,
        "top_k": 5,
    }}}

    existing_questions: list[str] = Field(default_factory=list)
    topic: str = Field(default="", min_length=1, max_length=500)
    n_candidates: int = Field(default=50, ge=1, le=200)
    top_k: int = Field(default=5, ge=1, le=20)

    @field_validator("top_k")
    @classmethod
    def top_k_not_greater_than_candidates(cls, v: int, info: Any) -> int:
        """Ensure top_k does not exceed n_candidates."""
        candidates = info.data.get("n_candidates", 50)
        if v > candidates:
            raise ValueError("top_k cannot exceed n_candidates")
        return v


class ExtendRequest(BaseModel):
    """Request to extend a formal framework with a new definition."""

    model_config = {"json_schema_extra": {"example": {
        "library": "mathlib4",
        "language": "lean4",
        "concept_gap": "continuity of composed functions",
    }}}

    library: str = Field(default="mathlib4", min_length=1, max_length=100)
    language: str = Field(default="lean4", min_length=1, max_length=20)
    concept_gap: str = Field(..., min_length=1, max_length=1000)

    @field_validator("library")
    @classmethod
    def library_no_path_traversal(cls, v: str) -> str:
        """Reject library names that contain path traversal or path separators."""
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("library name must not contain path traversal characters")
        return v


@router.post("/anomalies")
async def detect_anomalies(req: AnomalyRequest) -> dict[str, Any]:
    """Detect anomalies in literature embeddings and simulation residuals."""
    detector = AnomalyDetector()
    results: dict[str, Any] = {}
    total = 0

    try:
        if req.embeddings and req.papers:
            embeddings = np.array(req.embeddings)
            if embeddings.shape[0] != len(req.papers):
                raise ValidationError(
                    message=(
                        f"embeddings count ({embeddings.shape[0]}) must match "
                        f"papers count ({len(req.papers)})"
                    ),
                    detail={
                        "embeddings_count": embeddings.shape[0],
                        "papers_count": len(req.papers),
                    },
                )
            literature_anomalies = detector.detect_literature_anomalies(
                embeddings, req.papers, req.contamination
            )
            results["literature_anomalies"] = literature_anomalies
            results["literature_anomaly_count"] = len(literature_anomalies)
            total += len(literature_anomalies)

        if req.predicted is not None and req.expected is not None:
            if len(req.predicted) != len(req.expected):
                raise ValidationError(
                    message=(
                        f"predicted length ({len(req.predicted)}) must match "
                        f"expected length ({len(req.expected)})"
                    ),
                    detail={
                        "predicted_length": len(req.predicted),
                        "expected_length": len(req.expected),
                    },
                )
            predicted_arr = np.array(req.predicted)
            expected_arr = np.array(req.expected)
            sim_anomalies = detector.detect_simulation_residuals(
                predicted_arr, expected_arr, req.threshold_sigma
            )
            results["simulation_anomalies"] = sim_anomalies
            results["simulation_anomaly_count"] = len(sim_anomalies)
            total += len(sim_anomalies)

        return {
            "anomalies": results,
            "total_detected": total,
        }
    except C4APIError:
        raise
    except Exception as e:
        raise C4APIError(
            message=f"Anomaly detection failed: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="anomaly_detection_failed",
        ) from e


@router.post("/questions")
async def generate_questions(req: QuestionRequest) -> dict[str, Any]:
    """Generate surprise-driven research questions."""
    try:
        generator = SurpriseDrivenQuestionGenerator()
        questions = await generator.generate(
            existing_questions=req.existing_questions,
            topic=req.topic,
            n_candidates=req.n_candidates,
            top_k=req.top_k,
        )
        return {
            "questions": questions,
            "count": len(questions),
            "topic": req.topic,
        }
    except Exception as e:
        raise C4APIError(
            message=f"Question generation failed: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="question_generation_failed",
        ) from e


@router.post("/extend-formal")
async def extend_formal_framework(req: ExtendRequest) -> dict[str, Any]:
    """Propose formal framework extension."""
    try:
        extender = FormalFrameworkExtender()
        proposal = await extender.propose(
            library=req.library,
            language=req.language,
            concept_gap=req.concept_gap,
        )
        if proposal is None:
            raise C4APIError("Extension proposal generation failed", status_code=500, error_code="proposal_failed")
        return {
            "proposal": proposal.to_dict(),
            "library": req.library,
            "language": req.language,
        }
    except Exception as e:
        raise C4APIError(
            message=f"Formal extension failed: {e}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="formal_extension_failed",
        ) from e
