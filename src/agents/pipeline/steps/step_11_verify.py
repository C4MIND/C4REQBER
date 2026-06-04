"""
c44tcdi: Pipeline Step 11 — Formal Verification
"""
from __future__ import annotations

import logging
import time
from typing import Any

from src.agents.pipeline.steps.base import (
    PipelineStage,
    PipelineStep,
    PipelineStepResult,
)
from src.pipeline.steps.step_10_verify import Step10Verify


logger = logging.getLogger("c44tcdi.pipeline")

_verifier = Step10Verify()


class FormalVerificationStep(PipelineStep):
    """Step 11: Formal Verification — run proof generation on discovery."""

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.FORMAL_VERIFICATION

    def get_required_context(self) -> list[str]:
        return ["problem"]

    def get_optional_context(self) -> list[str]:
        return ["discovery"]

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute."""
        discovery: dict[str, Any] = context.get("discovery", {})
        start = time.time()

        if not discovery:
            return PipelineStepResult(
                stage=self.stage,
                status="skipped",
                output_data={"verified": False, "reason": "no discovery data"},
                duration_ms=(time.time() - start) * 1000,
            )

        try:
            result = _verifier.run(discovery)
            return PipelineStepResult(
                stage=self.stage,
                status="completed",
                output_data={"verified": True, "discovery": result},
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            logger.warning("Formal verification failed: %s", e)
            discovery["formal_verification"] = {"verified": False, "error": str(e)}
            return PipelineStepResult(
                stage=self.stage,
                status="failed",
                output_data={"verified": False, "discovery": discovery, "error": str(e)},
                duration_ms=(time.time() - start) * 1000,
                error=str(e),
            )


async def step_formal_verification(
    discovery: dict[str, Any]
) -> tuple[dict[str, Any], str]:
    """Legacy function-based API.

    Args:
        discovery: Discovery dict from previous pipeline steps.

    Returns:
        Tuple of (updated_discovery, status).
    """
    step = FormalVerificationStep()
    result = await step.execute({"problem": "", "discovery": discovery})
    if result.status == "skipped":
        return {}, "skipped"
    if result.status == "failed":
        return result.output_data.get("discovery", discovery), "failed"
    return result.output_data.get("discovery", discovery), "completed"
