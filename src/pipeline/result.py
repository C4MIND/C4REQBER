from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineResult:
    """Unified result protocol for all pipeline implementations.

    Phase 2.3 (Alexander audit): Three different result types existed
    (SolvePipelineResult, DiscoveryRecord, untyped dict). This protocol
    provides a single contract.
    """

    problem: str
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[dict[str, Any]] = field(default_factory=list)
    quality_report: dict[str, Any] | None = None
    abort_reasons: list[str] = field(default_factory=list)
    confidence: float = 0.0
    detection_results: dict[str, Any] = field(default_factory=dict)
    paradigm_shift_status: dict[str, Any] = field(default_factory=dict)
    pipeline_version: str = "v5.3.0"
    total_duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "problem": self.problem,
            "hypotheses": self.hypotheses,
            "sources": self.sources,
            "gaps": self.gaps,
            "quality_report": self.quality_report,
            "abort_reasons": self.abort_reasons,
            "confidence": self.confidence,
            "detection_results": self.detection_results,
            "paradigm_shift_status": self.paradigm_shift_status,
            "pipeline_version": self.pipeline_version,
            "total_duration_ms": self.total_duration_ms,
        }
