"""Unified scoring API for C4REQBER verification.

Aggregates results from multiple verification backends into a single score 0–100.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BackendResult:
    """Result from a single verification backend."""

    backend: str
    status: str  # verified | rejected | partial | failed | timeout | uncertain
    confidence: float = 0.0  # 0.0–1.0
    proof_code: str = ""
    proof_text: str = ""
    error_message: str = ""
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "status": self.status,
            "confidence": round(self.confidence, 3),
            "proof_code": self.proof_code,
            "proof_text": self.proof_text,
            "error_message": self.error_message,
            "execution_time_ms": round(self.execution_time_ms, 1),
            "metadata": self.metadata,
        }


@dataclass
class UnifiedVerificationScore:
    """Aggregate verification score across all backends."""

    hypothesis: str
    overall_status: str = "not_attempted"  # verified | rejected | uncertain | error
    overall_score: int = 0  # 0–100
    overall_confidence: float = 0.0
    backend_results: list[BackendResult] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis": self.hypothesis,
            "overall_status": self.overall_status,
            "overall_score": self.overall_score,
            "overall_confidence": round(self.overall_confidence, 3),
            "backend_results": [
                {
                    "backend": r.backend,
                    "status": r.status,
                    "confidence": r.confidence,
                    "execution_time_ms": r.execution_time_ms,
                }
                for r in self.backend_results
            ],
            "recommendations": self.recommendations,
        }


def compute_unified_score(
    hypothesis: str,
    backend_results: list[BackendResult],
) -> UnifiedVerificationScore:
    """Compute unified score from multiple backend results.

    Scoring logic:
    - Each backend contributes up to 100 points
    - verified = 100, partial = 50, uncertain = 25, failed/rejected = 0
    - Weighted by confidence
    - Overall score = weighted average
    """
    if not backend_results:
        return UnifiedVerificationScore(
            hypothesis=hypothesis,
            overall_status="not_attempted",
            overall_score=0,
            recommendations=["No verification backends were run."],
        )

    status_weights = {
        "verified": 1.0,
        "partial": 0.5,
        "uncertain": 0.25,
        "failed": 0.0,
        "rejected": 0.0,
        "timeout": 0.0,
    }

    total_weight = 0.0
    total_score = 0.0
    has_rejection = False
    has_verification = False

    for r in backend_results:
        weight = status_weights.get(r.status, 0.0)
        adjusted = weight * r.confidence
        total_score += adjusted
        total_weight += 1.0
        if r.status == "rejected":
            has_rejection = True
        if r.status == "verified":
            has_verification = True

    if total_weight == 0:
        overall_score = 0
    else:
        overall_score = int((total_score / total_weight) * 100)

    # Determine overall status
    if has_rejection:
        overall_status = "rejected"
    elif has_verification:
        overall_status = "verified"
    elif any(r.status == "partial" for r in backend_results):
        overall_status = "partial"
    else:
        overall_status = "uncertain"

    # Confidence = average of backend confidences
    avg_confidence = sum(r.confidence for r in backend_results) / len(backend_results)

    # Recommendations
    recommendations: list[str] = []
    verified_count = sum(1 for r in backend_results if r.status == "verified")
    if verified_count >= 2:
        recommendations.append(f"Strong verification: {verified_count} backends agreed.")
    elif verified_count == 1:
        recommendations.append("Weak verification: only 1 backend succeeded. Consider running more backends.")
    if has_rejection:
        recommendations.append("At least one backend rejected the hypothesis. Review the proof or assumptions.")
    if any(r.status == "timeout" for r in backend_results):
        recommendations.append("Some backends timed out. Consider increasing timeout or simplifying the hypothesis.")
    if not recommendations:
        recommendations.append("Verification completed with no clear conclusion.")

    return UnifiedVerificationScore(
        hypothesis=hypothesis,
        overall_status=overall_status,
        overall_score=overall_score,
        overall_confidence=avg_confidence,
        backend_results=backend_results,
        recommendations=recommendations,
    )
