"""
C4REQBER: Pipeline Step 04 — MP Rotation
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
from src.c4.state import C4State
from src.metamodels.mp.profiles import (
    AgentPerspective,
    MPRotationEngine,
)


logger = logging.getLogger("c4_cdi_turbo.pipeline")


class MPRotationStep(PipelineStep):
    """Step 4: MP Rotation — generate and enhance multiple perspectives."""

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.MP_ROTATION

    def get_required_context(self) -> list[str]:
        return [
            "problem",
            "c4_state",
            "mp_rotation",
            "mp_llm_generator",
            "provider_router",
        ]

    def get_optional_context(self) -> list[str]:
        return []

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute."""
        problem: str = context["problem"]
        c4_state: C4State = context["c4_state"]
        mp_rotation: MPRotationEngine = context["mp_rotation"]
        mp_llm_generator: Any = context["mp_llm_generator"]
        provider_router: Any = context["provider_router"]
        start = time.time()

        try:
            dynamic_perspectives = await mp_llm_generator.generate_dynamic_profiles(
                problem=problem, c4_state=c4_state, n=3
            )

            if dynamic_perspectives:
                perspectives = dynamic_perspectives
                logger.info("Using %d LLM-generated dynamic MP profiles", len(perspectives))
                enhanced = await _enhance_perspectives_with_llm(
                    problem, perspectives, provider_router
                )
                perspectives = enhanced
            else:
                logger.info("Using static MP profiles")
                rotation_result = mp_rotation.analyze(
                    problem, n_profiles=3, c4_state=c4_state
                )
                perspectives = rotation_result.perspectives
                enhanced = await _enhance_perspectives_with_llm(
                    problem, perspectives, provider_router
                )
                perspectives = enhanced

            output_data = {
                "perspectives": perspectives,
                "consensus_score": perspectives[0].confidence if perspectives else 0.5,
                "dynamic_profiles_used": len(dynamic_perspectives) > 0,
            }
            status = "completed"
            error = None
        except Exception as e:
            status = "error"
            error = str(e)
            output_data = {"perspectives": [], "consensus_score": 0.0}

        return PipelineStepResult(
            stage=self.stage,
            status=status,
            output_data=output_data,
            duration_ms=(time.time() - start) * 1000,
            error=error,
        )


async def step_mp_rotation(
    problem: str,
    c4_state: C4State,
    mp_rotation: MPRotationEngine,
    mp_llm_generator: Any,
    provider_router: Any,
) -> PipelineStepResult:
    """Legacy function-based API."""
    step = MPRotationStep()
    return await step.execute(
        {
            "problem": problem,
            "c4_state": c4_state,
            "mp_rotation": mp_rotation,
            "mp_llm_generator": mp_llm_generator,
            "provider_router": provider_router,
        }
    )


async def _enhance_perspectives_with_llm(
    problem: str,
    perspectives: list[AgentPerspective],
    provider_router: Any,
) -> list[AgentPerspective]:
    prompts = []
    for p in perspectives:
        prompt = (
            f"Analyze this problem from a '{p.profile_name}' perspective:\n\n"
            f"Problem: {problem}\n\n"
            f"Your cognitive style: {p.profile_name}\n"
            f"C4 State: {p.c4_state}\n\n"
            f"Provide 3 key insights and 2 potential blind spots. "
            f"Be concise (2-3 sentences per insight)."
        )
        prompts.append(prompt)

    try:
        if not provider_router:
            raise RuntimeError("LLM provider required for MP perspective enhancement")
        responses = await provider_router.generate_batch("mp_rotation", prompts)

        for i, response in enumerate(responses):
            if i < len(perspectives):
                content = getattr(response, "content", str(response))
                lines = [line.strip() for line in content.split("\n") if line.strip()]
                insights = [
                    line
                    for line in lines
                    if line[0].isdigit()
                    or line.startswith("-")
                    or line.startswith("*")
                ]
                if not insights:
                    insights = lines[:3]
                perspectives[i].analysis = content
                perspectives[i].key_insights = insights[:5]
                perspectives[i].confidence = min(0.7 + len(insights) * 0.05, 0.95)

        return perspectives
    except (ConnectionError, TimeoutError, RuntimeError, ValueError) as e:
        raise RuntimeError(f"MP perspective enhancement failed: {e}") from e
