"""
C4REQBER: Pipeline Step 10 — Pattern Simulation
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


logger = logging.getLogger("c4_cdi_turbo.pipeline")


class SimulationStep(PipelineStep):
    """Step 10: Pattern Simulation — run selected simulation pattern."""

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.SIMULATION

    def get_required_context(self) -> list[str]:
        return ["problem"]

    def get_optional_context(self) -> list[str]:
        return ["selected_pattern"]

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute."""
        problem: str = context["problem"]
        selected_pattern: str | None = context.get("selected_pattern")
        start = time.time()

        pattern_results: list[Any] = []
        if not selected_pattern:
            return PipelineStepResult(
                stage=self.stage,
                status="skipped",
                output_data={"pattern_results": []},
                duration_ms=(time.time() - start) * 1000,
            )

        try:
            from src.patterns.runner import get_runner

            runner = get_runner()
            pattern_result = await runner.run_pattern(
                selected_pattern,
                hypothesis={"text": problem},
            )
            pattern_results.append(pattern_result)
        except Exception as e:
            logger.warning("Pattern %s failed: %s", selected_pattern, e)

        status = "completed" if pattern_results else "skipped"
        return PipelineStepResult(
            stage=self.stage,
            status=status,
            output_data={"pattern_results": pattern_results},
            duration_ms=(time.time() - start) * 1000,
        )
