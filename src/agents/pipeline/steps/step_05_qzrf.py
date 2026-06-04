"""
C4REQBER: Pipeline Step 05 — QZRF Selection
"""
from __future__ import annotations

import time
from typing import Any

from src.agents.pipeline.steps.base import (
    PipelineStage,
    PipelineStep,
    PipelineStepResult,
)
from src.c4.state import C4State
from src.metamodels.qzrf.operators import QzrfLibrary


class QzrfSelectStep(PipelineStep):
    """Step 5: QZRF Select — find applicable operators for C4 state."""

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.QZRF_SELECT

    def get_required_context(self) -> list[str]:
        return ["c4_state", "qzrf"]

    def get_optional_context(self) -> list[str]:
        return []

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute."""
        c4_state: C4State = context["c4_state"]
        qzrf: QzrfLibrary = context["qzrf"]
        start = time.time()

        try:
            operators = qzrf.applicable_to(c4_state)
            output_data = {
                "operators": [op.id for op in operators[:5]],
                "operator_details": [
                    {"id": op.id, "name": op.name, "phase": op.phase.value}
                    for op in operators[:5]
                ],
            }
            status = "completed"
            error = None
        except Exception as e:
            status = "error"
            error = str(e)
            output_data = {"operators": []}

        return PipelineStepResult(
            stage=self.stage,
            status=status,
            output_data=output_data,
            duration_ms=(time.time() - start) * 1000,
            error=error,
        )


async def step_qzrf_select(c4_state: C4State, qzrf: QzrfLibrary) -> PipelineStepResult:
    """Legacy function-based API."""
    step = QzrfSelectStep()
    return await step.execute({"c4_state": c4_state, "qzrf": qzrf})
