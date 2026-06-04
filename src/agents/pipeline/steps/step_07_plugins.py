"""
C4REQBER: Pipeline Step 07 — Plugin Execution
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


class PluginExecutionStep(PipelineStep):
    """Step 7: Plugin Execution — run selected cognitive plugins."""

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.PLUGIN_EXECUTION

    def get_required_context(self) -> list[str]:
        return ["problem"]

    def get_optional_context(self) -> list[str]:
        return ["selected_plugins"]

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute."""
        problem: str = context["problem"]
        selected_plugins: list[str] = context.get("selected_plugins", [])
        start = time.time()

        plugin_results: list[dict[str, Any]] = []
        if not selected_plugins:
            return PipelineStepResult(
                stage=self.stage,
                status="skipped",
                output_data={"plugin_results": []},
                duration_ms=(time.time() - start) * 1000,
            )

        from src.plugins.v2_registry import execute_plugin

        for plugin_id in selected_plugins:
            try:
                plugin_result = execute_plugin(plugin_id, problem=problem)
                plugin_results.append({"plugin_id": plugin_id, "result": plugin_result})
            except Exception as e:
                logger.warning("Plugin %s failed: %s", plugin_id, e)

        status = "completed" if plugin_results else "skipped"
        return PipelineStepResult(
            stage=self.stage,
            status=status,
            output_data={"plugin_results": plugin_results},
            duration_ms=(time.time() - start) * 1000,
        )


async def step_plugins(
    problem: str, selected_plugins: list[str]
) -> tuple[list[dict[str, Any]], str]:
    """Legacy function-based API."""
    step = PluginExecutionStep()
    result = await step.execute({"problem": problem, "selected_plugins": selected_plugins})
    return result.output_data.get("plugin_results", []), result.status
