"""
C44TCDI: Pipeline Step — Cross-Domain Innovation Transfer
Auto-triggered when c4_fingerprint detects cross-domain potential.
"""
from __future__ import annotations

import time
from typing import Any

from src.agents.pipeline.steps.base import (
    PipelineStage,
    PipelineStep,
    PipelineStepResult,
)
from src.c4.transfer_pipeline import (
    TransferResult,
    cross_domain_transfer,
    should_auto_trigger,
)


class CrossDomainTransferStep(PipelineStep):
    """Step 3b: Cross-Domain Transfer — detect and run domain transfer."""

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.CROSS_DOMAIN_TRANSFER

    def get_required_context(self) -> list[str]:
        return ["problem", "domain_hint"]

    def get_optional_context(self) -> list[str]:
        return []

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute."""
        problem: str = context["problem"]
        domain_hint: str | None = context.get("domain_hint")
        start = time.time()

        auto_trigger = should_auto_trigger(problem)
        if not auto_trigger and not domain_hint:
            return PipelineStepResult(
                stage=self.stage,
                status="skipped",
                output_data={
                    "triggered": False,
                    "reason": "No cross-domain keywords detected",
                },
                duration_ms=(time.time() - start) * 1000,
            )

        try:
            result = cross_domain_transfer(
                problem=problem,
                source_domain=domain_hint,
            )

            output_data: dict[str, Any] = {
                "triggered": True,
                "auto_triggered": result.triggered_auto,
                "source_domain": result.source_domain,
                "target_domain": result.target_domain,
                "confidence": result.confidence,
                "mappings": result.mappings,
                "adaptation_rules": result.adaptation_rules,
                "triz_principles": result.triz_principles,
                "isomorphism_type": result.isomorphism_type,
            }
            status = "completed" if result.confidence > 0.0 else "completed_no_match"
            error = None
        except Exception as e:
            status = "error"
            error = str(e)
            output_data = {"triggered": False, "error": str(e)}

        return PipelineStepResult(
            stage=self.stage,
            status=status,
            output_data=output_data,
            duration_ms=(time.time() - start) * 1000,
            error=error,
        )


async def step_cross_domain_transfer(
    problem: str,
    domain_hint: str | None,
) -> PipelineStepResult:
    """Legacy function-based API."""
    step = CrossDomainTransferStep()
    return await step.execute(
        {"problem": problem, "domain_hint": domain_hint}
    )
