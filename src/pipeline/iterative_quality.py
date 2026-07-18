"""Iterative Quality Loop — auto-improve pipeline results on failed gates.

When quality score < threshold, analyzes failed gates, generates improvement
plan, and re-runs specific phases with enhanced parameters.
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from typing import Any

from src.pipeline.config import PipelineConfig
from src.pipeline.quality import QualityReport


logger = logging.getLogger(__name__)


@dataclass
class ImprovementPlan:
    """Actionable plan to fix failed quality gates."""

    iteration: int
    failed_gates: list[str] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    parameter_changes: dict[str, Any] = field(default_factory=dict)


class IterativeQualityLoop:
    """Iteratively improve pipeline output until quality threshold is met."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig(name="default")
        self.max_iterations = 3
        self.quality_threshold = self.config.min_quality_score

    def should_improve(self, report: QualityReport) -> bool:
        """Check if quality is below threshold and improvement is possible."""
        if report.overall_score >= self.quality_threshold:
            return False
        if report.passed_all:
            return False
        # Check if failed gates are improvable (not hard failures)
        improvable = {"sources", "gaps", "hypotheses", "bibliography", "dissertation"}
        failed = {g.step for g in report.gates if not g.passed}
        return bool(failed & improvable)

    def create_improvement_plan(self, report: QualityReport, iteration: int) -> ImprovementPlan:
        """Analyze failed gates and create improvement plan."""
        failed = [g for g in report.gates if not g.passed]
        actions = []
        param_changes: dict[str, Any] = {}

        for gate in failed:
            if gate.step == "sources":
                actions.append(
                    {
                        "phase": "B",
                        "action": "expand_source_search",
                        "detail": f"Increase min_sources from {self.config.min_sources} to {self.config.min_sources + 5}",
                    }
                )
                param_changes["min_sources"] = self.config.min_sources + 5
                # Prefer real MultiSourceSearcher web adapters (Tavily), never stub padding
                param_changes["fallback_to_web_search"] = True
                param_changes["include_web"] = True

            elif gate.step == "gaps":
                actions.append(
                    {
                        "phase": "C",
                        "action": "deepen_gap_analysis",
                        "detail": "Re-run gap analyzer with stricter evidence requirements",
                    }
                )
                param_changes["min_gaps"] = max(self.config.min_gaps, 3)

            elif gate.step == "hypotheses":
                actions.append(
                    {
                        "phase": "D",
                        "action": "regenerate_hypotheses",
                        "detail": f"Generate more ambitious hypotheses (current ambition: {self.config.hypothesis_ambition})",
                    }
                )
                param_changes["min_hypotheses"] = self.config.min_hypotheses + 2
                param_changes["llm_temperature"] = min(self.config.llm_temperature + 0.05, 0.5)
                actions.append(
                    {
                        "phase": "D",
                        "action": "diversify_prompting",
                        "detail": "Use alternative LLM prompt template for hypothesis diversity",
                    }
                )

            elif gate.step == "bibliography":
                actions.append(
                    {
                        "phase": "B",
                        "action": "expand_bibliography",
                        "detail": "Fetch additional sources via web search",
                    }
                )
                param_changes["max_sources"] = self.config.max_sources + 10

            elif gate.step == "dissertation":
                actions.append(
                    {
                        "phase": "F",
                        "action": "regenerate_dissertation",
                        "detail": "Add missing sections and expand content",
                    }
                )
                param_changes["min_dissertation_words"] = self.config.min_dissertation_words + 300
                param_changes["max_llm_tokens_per_section"] = (
                    self.config.max_llm_tokens_per_section + 500
                )

        return ImprovementPlan(
            iteration=iteration,
            failed_gates=[g.step for g in failed],
            actions=actions,
            parameter_changes=param_changes,
        )

    def apply_parameter_changes(
        self, config: PipelineConfig, plan: ImprovementPlan
    ) -> PipelineConfig:
        """Create new config with improved parameters."""
        new_config = copy.deepcopy(config)
        for key, value in plan.parameter_changes.items():
            if hasattr(new_config, key):
                setattr(new_config, key, value)
                logger.info("Quality loop: changed %s = %s", key, value)
        return new_config

    async def run_improvement_cycle(
        self,
        pipeline_instance: Any,
        topic: str,
        record: Any,
        report: QualityReport,
    ) -> tuple[Any, QualityReport, int]:
        """Run iterative improvement until threshold or max iterations.

        Returns:
            (final_record, final_report, iterations_performed)
        """
        iterations = 0
        current_record = record
        current_report = report
        current_config = self.config

        while self.should_improve(current_report) and iterations < self.max_iterations:
            iterations += 1
            logger.info(
                "Quality improvement cycle %d/%d (score: %d, threshold: %d)",
                iterations,
                self.max_iterations,
                current_report.overall_score,
                self.quality_threshold,
            )

            plan = self.create_improvement_plan(current_report, iterations)
            logger.info("Improvement plan: %s", plan.actions)

            # Apply parameter changes
            improved_config = self.apply_parameter_changes(current_config, plan)

            # Re-run specific phases based on failed gates
            if "sources" in plan.failed_gates or "bibliography" in plan.failed_gates:
                current_record.sources = await pipeline_instance._fetch_bibliography(topic)
                current_record.bibliography = current_record.sources[: improved_config.max_sources]

            if "gaps" in plan.failed_gates:
                current_record.gaps = pipeline_instance.gap_analyzer.analyze(
                    current_record.sources, topic
                )

            if "hypotheses" in plan.failed_gates:
                # Re-generate hypotheses with new config
                current_record.hypotheses = await pipeline_instance._regenerate_hypotheses(
                    topic, current_record.sources, current_record.gaps, improved_config
                )

            if "dissertation" in plan.failed_gates:
                # Regenerate dissertation
                diss = pipeline_instance.dissertation_gen.generate(
                    topic=topic,
                    hypotheses=current_record.hypotheses,
                    sources=current_record.bibliography,
                    user_profile=pipeline_instance.user_profile,
                    config=improved_config,
                )
                current_record.dissertation = diss

            # Re-evaluate quality
            current_report = pipeline_instance.quality.evaluate(
                current_record.sources,
                current_record.gaps,
                current_record.hypotheses,
                current_record.simulation,
                current_record.verification,
                current_record.bibliography,
                getattr(current_record, "dissertation", ""),
            )
            current_config = improved_config

            logger.info(
                "After improvement cycle %d: score = %d, grade = %s",
                iterations,
                current_report.overall_score,
                current_report.grade,
            )

        return current_record, current_report, iterations
