"""
C44TCDI: Pipeline Step 02b — Gap Analysis
"""
from __future__ import annotations

import time
from typing import Any

from src.agents.pipeline.steps.base import PipelineStage, PipelineStep, PipelineStepResult
from src.discovery.gap_analyzer import AutoGapAnalyzer


class GapAnalysisStep(PipelineStep):
    """Step 2b: Gap Analysis — identify research gaps from prior art."""

    def __init__(self, gap_analyzer: AutoGapAnalyzer) -> None:
        self._gap_analyzer = gap_analyzer

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.GAP_ANALYSIS

    def get_required_context(self) -> list[str]:
        return ["problem", "sources"]

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute."""
        problem = context["problem"]
        sources = context.get("sources", [])
        start = time.time()

        try:
            gaps = self._gap_analyzer.analyze(sources, problem)
            status = "completed"
            error = None
        except Exception as e:
            status = "error"
            error = str(e)
            gaps = []

        output_data = {
            "gaps": gaps,
            "gap_count": len(gaps),
        }

        # Store gaps in context for downstream steps
        context["gap_results"] = gaps

        return PipelineStepResult(
            stage=self.stage,
            status=status,
            input_data={"problem": problem, "source_count": len(sources)},
            output_data=output_data,
            duration_ms=(time.time() - start) * 1000,
            error=error,
        )


# Function-based API
async def step_gap_analysis(
    sources: list[dict[str, Any]], topic: str, gap_analyzer: AutoGapAnalyzer
) -> PipelineStepResult:
    """Run gap analysis on prior art sources."""
    step = GapAnalysisStep(gap_analyzer)
    return await step.execute({"problem": topic, "sources": sources})
