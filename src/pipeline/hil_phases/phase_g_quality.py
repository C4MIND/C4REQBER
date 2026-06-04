from __future__ import annotations


"""Phase G: Quality Gates — IterativeQualityLoop, SelfCorrectingDissertation."""

import logging
from typing import Any

from src.pipeline.config import PipelineConfig
from src.pipeline.quality import QualityGates, QualityReport


logger = logging.getLogger(__name__)


class PhaseG_QualityControl:
    """Run quality gates, iterative improvement, and self-correcting dissertation."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig(name="default")
        self.quality = QualityGates(self.config)

    def check_sources(self, sources: list[dict[str, Any]]) -> Any:
        """Check sources."""
        gate = self.quality.check_sources(sources)
        print(f"      {'✓' if gate.passed else '⚠'} Source gate: {gate.message} (score: {gate.score:.2f})")
        if not gate.passed and self.config.auto_retry_failed_steps:
            print(f"      Recommendations: {gate.message}")
        return gate

    def check_gaps(self, gaps: list[dict[str, Any]]) -> Any:
        """Check gaps."""
        gate = self.quality.check_gaps(gaps)
        print(f"      {'✓' if gate.passed else '⚠'} Gap gate: {gate.message} (score: {gate.score:.2f})")
        return gate

    def check_hypotheses(self, hypotheses: list[dict[str, Any]]) -> Any:
        """Check hypotheses."""
        gate = self.quality.check_hypotheses(hypotheses)
        print(f"      {'✓' if gate.passed else '⚠'} Hypothesis gate: {gate.message} (score: {gate.score:.2f})")
        return gate

    def check_simulation(self, simulation: Any) -> Any:
        """Check simulation."""
        gate = self.quality.check_simulation(simulation)
        print(f"      {'✓' if gate.passed else '⚠'} Simulation gate: {gate.message} (score: {gate.score:.2f})")
        return gate

    def check_verification(self, verification: Any) -> Any:
        """Check verification."""
        gate = self.quality.check_verification(verification)
        print(f"      {'✓' if gate.passed else '⚠'} Verification gate: {gate.message} (score: {gate.score:.2f})")
        return gate

    def check_bibliography(self, bibliography: list[dict[str, Any]]) -> Any:
        """Check bibliography."""
        gate = self.quality.check_bibliography(bibliography)
        print(f"      {'✓' if gate.passed else '⚠'} Bibliography gate: {gate.message} (score: {gate.score:.2f})")
        return gate

    def check_dissertation(self, diss: str) -> Any:
        """Check dissertation."""
        gate = self.quality.check_dissertation(diss)
        print(f"      {'✓' if gate.passed else '⚠'} Dissertation gate: {gate.message} (score: {gate.score:.2f})")
        return gate

    def evaluate(self, record: Any) -> QualityReport:
        """Run full quality evaluation and return report."""
        report = self.quality.evaluate(
            record.sources, record.gaps, record.hypotheses,
            record.simulation, record.verification, record.bibliography, "",
        )
        print(f"\n{'='*70}")
        print(f"  QUALITY REPORT: {report.grade} (Score: {report.overall_score}/100)")
        print(f"  PASSED ALL GATES: {'YES' if report.passed_all else 'NO'}")
        if report.recommendations:
            print("  RECOMMENDATIONS:")
            for r in report.recommendations:
                print(f"    - {r}")
        print(f"{'='*70}")
        return report

    async def run_iterative_improvement(self, pipeline: Any, topic: str, record: Any, report: QualityReport) -> tuple[Any, QualityReport, int]:
        """Run iterative quality improvement loop if score is below threshold."""
        cfg = self.config
        if cfg.enable_quality_score and report.overall_score < cfg.min_quality_score:
            print(f"\n❌ QUALITY BELOW THRESHOLD ({report.overall_score} < {cfg.min_quality_score})")
            print("   Recommendations:")
            for r in report.recommendations:
                print(f"   - {r}")

            print("\n🔄 Starting iterative quality improvement loop...")
            from src.pipeline.iterative_quality import IterativeQualityLoop
            quality_loop = IterativeQualityLoop(config=cfg)

            record, report, improvement_iterations = await quality_loop.run_improvement_cycle(
                pipeline, topic, record, report
            )

            print(f"\n{'='*70}")
            print(f"  AFTER IMPROVEMENT: {report.grade} (Score: {report.overall_score}/100)")
            print(f"  ITERATIONS: {improvement_iterations}")
            print(f"{'='*70}")

            # Self-correcting dissertation: surgical section fixes
            if not report.passed_all and hasattr(record, 'dissertation'):
                print("\n✏️  Applying self-correcting dissertation fixes...")
                from src.pipeline.self_correcting import SelfCorrectingDissertation
                corrector = SelfCorrectingDissertation()
                record.dissertation = await corrector.fix_dissertation(
                    record.dissertation, report, record, topic
                )
                print("   Dissertation sections corrected.")

            return record, report, improvement_iterations
        return record, report, 0
