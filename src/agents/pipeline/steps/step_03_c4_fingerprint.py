"""Pipeline Step 03 — C4 Fingerprinting."""
from __future__ import annotations

import logging
import time
from typing import Any

from src.agents.pipeline.steps.base import PipelineStage, PipelineStep, PipelineStepResult
from src.c4.state import C4State


logger = logging.getLogger("c4_cdi_turbo.pipeline")


class C4FingerprintStep(PipelineStep):
    """Step 3: C4 Fingerprinting — classify problem into C4 cognitive state."""

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.C4_FINGERPRINT

    def get_required_context(self) -> list[str]:
        return ["problem"]

    def get_optional_context(self) -> list[str]:
        return ["domain_hint"]

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute."""
        problem = context["problem"]
        start = time.time()

        try:
            from src.c4.llm_classifier import get_c4_classifier

            classifier = get_c4_classifier()
            c4_state, confidence, reasoning = await classifier.classify(problem)

            output_data = {
                "c4_state": c4_state,
                "c4_label": str(c4_state),
                "c4_coords": c4_state.to_tuple(),
                "classification_method": "llm",
                "classification_confidence": confidence,
                "classification_reasoning": reasoning,
            }
            status = "completed"
            error = None
        except Exception as e:
            logger.error("LLM C4 classification failed: %s", e)
            output_data = {
                "c4_state": C4State(T=1, S=1, A=1),
                "c4_label": "F[1,1,1]",
                "c4_coords": (1, 1, 1),
                "classification_method": "error",
                "classification_confidence": 0.0,
                "classification_reasoning": "LLM classification failed",
            }
            status = "failed"
            error = str(e)

        # Store c4_state in context for downstream steps
        context["c4_state"] = output_data["c4_state"]

        return PipelineStepResult(
            stage=self.stage,
            status=status,
            input_data={"problem": problem},
            output_data=output_data,
            duration_ms=(time.time() - start) * 1000,
            error=error,
        )




# Backward compatibility: function-based API
async def step_c4_fingerprint(
    problem: str,
    domain_hint: str | None,
) -> PipelineStepResult:
    """Legacy function-based API."""
    step = C4FingerprintStep()
    return await step.execute({"problem": problem, "domain_hint": domain_hint})
