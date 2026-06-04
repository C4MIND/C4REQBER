"""
C44TCDI: Pipeline Step 02c — Quality Gate
"""
from __future__ import annotations

import time
from typing import Any

from src.agents.pipeline.steps.base import PipelineStage, PipelineStep, PipelineStepResult
from src.pipeline.quality import QualityGates


class QualityGateStep(PipelineStep):
    """Step 2c: Quality Gates — enforce A+ standards on sources and gaps."""

    def __init__(self, quality_gates: QualityGates) -> None:
        self._quality_gates = quality_gates

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.QUALITY_GATE

    def get_required_context(self) -> list[str]:
        return ["sources"]

    def get_optional_context(self) -> list[str]:
        return ["gaps"]

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute."""
        sources = context.get("sources", [])
        gaps = context.get("gaps", [])
        start = time.time()

        try:
            source_gate = self._quality_gates.check_sources(sources)
            gap_gate = self._quality_gates.check_gaps(gaps)
            status = "completed"
            error = None
        except Exception as e:
            status = "error"
            error = str(e)
            source_gate = None
            gap_gate = None

        output_data: dict[str, Any] = {
            "source_gate": {
                "step": source_gate.step if source_gate else "sources",
                "passed": source_gate.passed if source_gate else False,
                "score": source_gate.score if source_gate else 0.0,
                "message": source_gate.message if source_gate else str(error),
                "details": source_gate.details if source_gate else {},
            }
            if source_gate
            else None,
            "gap_gate": {
                "step": gap_gate.step if gap_gate else "gaps",
                "passed": gap_gate.passed if gap_gate else False,
                "score": gap_gate.score if gap_gate else 0.0,
                "message": gap_gate.message if gap_gate else str(error),
                "details": gap_gate.details if gap_gate else {},
            }
            if gap_gate
            else None,
            "all_passed": (
                (source_gate.passed if source_gate else False)
                and (gap_gate.passed if gap_gate else False)
            ),
        }

        # Store quality gate results in context for downstream steps
        context["quality_gate_results"] = output_data

        return PipelineStepResult(
            stage=self.stage,
            status=status,
            input_data={"source_count": len(sources), "gap_count": len(gaps)},
            output_data=output_data,
            duration_ms=(time.time() - start) * 1000,
            error=error,
        )


# Function-based API
async def step_quality_gate(
    sources: list[dict[str, Any]],
    gaps: list[dict[str, Any]],
    quality_gates: QualityGates,
) -> PipelineStepResult:
    """Run quality gates on sources and gaps."""
    step = QualityGateStep(quality_gates)
    return await step.execute({"sources": sources, "gaps": gaps})
