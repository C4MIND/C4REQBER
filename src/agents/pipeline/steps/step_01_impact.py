"""
C4REQBER: Pipeline Step 01 — IMPACT Identify
"""
from __future__ import annotations

import time
from typing import Any

from src.agents.pipeline.steps.base import PipelineStage, PipelineStep, PipelineStepResult
from src.metamodels.impact import ImpactEngine, ImpactPhase


class ImpactIdentifyStep(PipelineStep):
    """Step 1: IMPACT Identify — analyze problem and extract entities."""

    def __init__(self, impact: ImpactEngine) -> None:
        self._impact = impact

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.IMPACT_IDENTIFY

    def get_required_context(self) -> list[str]:
        return ["problem"]

    def get_optional_context(self) -> list[str]:
        return ["domain_hint"]

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute."""
        problem = context["problem"]
        domain_hint = context.get("domain_hint")
        start = time.time()

        try:
            impact_result = self._impact.solve(problem, domain_hint)
            identify_phase = next(
                (s for s in impact_result.steps if s.phase == ImpactPhase.IDENTIFY),
                None,
            )
            output_data = {
                "entities": identify_phase.outputs.get("entities", [])
                if identify_phase
                else [],
                "stakeholders": identify_phase.outputs.get("stakeholders", [])
                if identify_phase
                else [],
                "success_criteria": identify_phase.outputs.get("success_criteria", [])
                if identify_phase
                else [],
            }
            status = "completed"
            error = None
        except Exception as e:
            status = "error"
            error = str(e)
            output_data = {
                "entities": [],
                "stakeholders": [],
                "success_criteria": [],
            }

        return PipelineStepResult(
            stage=self.stage,
            status=status,
            input_data={"problem": problem, "domain_hint": domain_hint},
            output_data=output_data,
            duration_ms=(time.time() - start) * 1000,
            error=error,
        )


# Backward compatibility: function-based API
async def step_impact_identify(
    problem: str, domain_hint: str | None, impact: ImpactEngine
) -> PipelineStepResult:
    """Legacy function-based API."""
    step = ImpactIdentifyStep(impact)
    return await step.execute({"problem": problem, "domain_hint": domain_hint})
