from __future__ import annotations

from dataclasses import dataclass, field

from src.agents.pipeline.steps.base import PipelineStage


STEP_MODULES: dict[str, str] = {
    "step_impact_identify": "src.agents.pipeline.steps.step_01_impact",
    "step_prior_art": "src.agents.pipeline.steps.step_02_prior_art",
    "step_gap_analysis": "src.agents.pipeline.steps.step_02b_gap_analysis",
    "step_quality_gate": "src.agents.pipeline.steps.step_02c_quality_gate",
    "step_reality_check": "src.agents.pipeline.steps.step_02d_reality_check",
    "step_c4_fingerprint": "src.agents.pipeline.steps.step_03_c4_fingerprint",
    "step_cross_domain_transfer": "src.agents.pipeline.steps.step_05b_cross_domain_transfer",
    "step_mp_rotation": "src.agents.pipeline.steps.step_04_mp_rotation",
    "step_qzrf_select": "src.agents.pipeline.steps.step_05_qzrf",
    "step_isomorphism_search": "src.agents.pipeline.steps.step_06_isomorphism",
    "step_plugins": "src.agents.pipeline.steps.step_07_plugins",
    "step_synthesis": "src.agents.pipeline.steps.step_08_synthesis",
    "step_validation": "src.agents.pipeline.steps.step_09_tote",
    "step_simulation": "src.agents.pipeline.steps.step_10_simulation",
}


@dataclass
class StepDefinition:
    """StepDefinition."""
    stage: PipelineStage
    step_fn_name: str
    required_context: list[str]
    optional_context: list[str] = field(default_factory=list)
    skip_conditions: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.step_fn_name not in STEP_MODULES:
            raise ValueError(
                f"Unknown step_fn_name {self.step_fn_name!r}. "
                f"Must be one of {list(STEP_MODULES)}"
            )
