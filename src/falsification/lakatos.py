from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResearchProgramme:
    """ResearchProgramme."""
    name: str
    hard_core: list[str]  # Unfalsifiable core claims
    protective_belt: list[str]  # Auxiliary hypotheses
    novel_predictions: list[str] = field(default_factory=list[Any])
    confirmed_predictions: list[str] = field(default_factory=list[Any])
    anomalies: list[str] = field(default_factory=list[Any])

@dataclass
class ProgrammeEvaluation:
    """ProgrammeEvaluation."""
    programme_name: str
    is_progressive: bool
    progress_score: float
    anomaly_count: int
    novel_prediction_count: int
    recommendation: str

def evaluate_programme(programme: ResearchProgramme) -> ProgrammeEvaluation:
    """Evaluate a Lakatos research programme as progressive or degenerating"""
    total_pred = len(programme.novel_predictions)
    confirmed = len(programme.confirmed_predictions)
    anomalies = len(programme.anomalies)

    progress = confirmed / max(total_pred, 1)
    anomaly_ratio = anomalies / max(confirmed + anomalies, 1)

    is_progressive = progress > anomaly_ratio

    return ProgrammeEvaluation(
        programme_name=programme.name,
        is_progressive=is_progressive,
        progress_score=progress,
        anomaly_count=anomalies,
        novel_prediction_count=total_pred,
        recommendation="Continue funding" if is_progressive else "Consider redirecting resources",
    )
