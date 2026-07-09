"""HIL Discovery Pipeline — Orchestrator that delegates to phase modules."""

from __future__ import annotations

import asyncio
import logging


logger = logging.getLogger(__name__)
from typing import Any

from src.core.user_profile import UserProfile
from src.discovery.gap_analyzer import AutoGapAnalyzer
from src.pipeline.base import BasePipeline, DiscoveryRecord
from src.pipeline.config import PipelineConfig
from src.pipeline.events import event_bus
from src.pipeline.hil_phases.phase_a_usp import PhaseA_USPCognitiveFraming
from src.pipeline.hil_phases.phase_b_knowledge import PhaseB_KnowledgeAcquisition
from src.pipeline.hil_phases.phase_c_gaps import PhaseC_GapAnalysis
from src.pipeline.hil_phases.phase_d_agents import PhaseD_CognitiveAgents
from src.pipeline.hil_phases.phase_e_simulation import PhaseE_SimulationVerification
from src.pipeline.hil_phases.phase_f_dissertation import PhaseF_DissertationGeneration
from src.pipeline.hil_phases.phase_g_quality import PhaseG_QualityControl
from src.publishing.dissertation import DissertationGenerator


class HILDiscoveryPipeline(BasePipeline):
    """Orchestrator for automated discovery pipeline."""

    def __init__(
        self, config: PipelineConfig | None = None, user_profile: UserProfile | None = None
    ) -> None:
        super().__init__(config=config, user_profile=user_profile)
        self.pattern_runner = None
        self.gap_analyzer = AutoGapAnalyzer()
        self.dissertation_gen = DissertationGenerator()

    async def _fetch_bibliography(self, topic: str, min_sources: int = 5) -> list[dict[str, Any]]:
        """Re-fetch bibliography (used by iterative quality improvement)."""
        phase_b = PhaseB_KnowledgeAcquisition(api_keys=self.config.api_keys)
        return await phase_b.run(topic, min_sources=min_sources, fallback_to_web=True)

    async def _regenerate_hypotheses(
        self, topic: str, gaps: list[dict[str, Any]], sources: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Re-generate hypotheses from gaps (used by iterative quality improvement)."""
        phase_c = PhaseC_GapAnalysis()
        _, hypotheses = phase_c.run(topic, sources, {})
        return hypotheses

    async def discover(
        self, topic: str, competing_hypotheses: int = 2, no_iterative: bool = False
    ) -> DiscoveryRecord:
        """Run fully automated discovery pipeline."""
        cfg = self.config
        record = DiscoveryRecord(topic=topic, config=cfg, user_profile=self.user_profile)

        # ── Architecture: CQRS command dispatch ────────────────────
        try:
            from src.architecture.cqrs import CommandHandler, CqrsBus, StartDiscoveryCommand

            class _DiscoveryHandler(CommandHandler):
                def handle(self, cmd):
                    logger.debug(
                        "CQRS: StartDiscoveryCommand handled for %s", cmd.problem_statement
                    )

            bus = CqrsBus()
            bus.register_command(StartDiscoveryCommand, _DiscoveryHandler())
            cmd = StartDiscoveryCommand(
                problem_statement=topic, domain="general", complexity_level=1
            )
            bus.execute(cmd)
        except Exception as e:
            logger.debug("CQRS dispatch skipped: %s", e)

        # ── Architecture: Saga orchestration ───────────────────────
        try:
            from src.architecture.saga import FunctionSagaStep

            saga = self.saga
            saga.add_step(FunctionSagaStep("discover", lambda ctx: None))
            ctx = saga.execute({"topic": topic})
            record.saga_id = ctx.saga_id
        except Exception:
            pass

        query_type = self._classify_query(topic)
        print(f"\n{'='*70}")
        print(f"  DISCOVERY: {topic}")
        print(f"  QUERY TYPE: {query_type}")
        print(f"{'='*70}")

        await event_bus.emit(
            "pipeline_start",
            {"topic": topic, "query_type": query_type, "config": cfg.to_dict()},
            mode="turbo",
        )

        # Phase A: USP Cognitive Framing
        await event_bus.emit(
            "phase_start", {"phase": "A", "name": "USP Cognitive Framing"}, mode="turbo"
        )
        phase_a = PhaseA_USPCognitiveFraming()
        usp_context = phase_a.run(topic)
        record.c4_state = usp_context.get("c4_state", "")
        record.plugins_context["impact"] = usp_context.get("impact", {})
        record.plugins_context["mp"] = usp_context.get("mp_rotation", [])
        record.plugins_context["qzrf"] = usp_context.get("qzrf", [])
        record.plugins_context["isomorphism"] = usp_context.get("isomorphism", [])
        record.plugins_context["matrix_dream"] = usp_context.get("matrix_dream", [])
        await event_bus.emit(
            "phase_end", {"phase": "A", "name": "USP Cognitive Framing"}, mode="turbo"
        )

        # Phase B: Knowledge Acquisition
        await event_bus.emit(
            "phase_start", {"phase": "B", "name": "Knowledge Acquisition"}, mode="turbo"
        )
        phase_b = PhaseB_KnowledgeAcquisition(api_keys=cfg.api_keys)
        bibliography = await phase_b.run(
            topic, min_sources=cfg.min_sources, fallback_to_web=cfg.fallback_to_web_search
        )
        record.sources = bibliography
        record.bibliography = bibliography[: cfg.max_sources]
        await event_bus.emit(
            "phase_end", {"phase": "B", "name": "Knowledge Acquisition"}, mode="turbo"
        )

        gate = self.quality.check_sources(record.sources)
        print(
            f"      {'✓' if gate.passed else '⚠'} Source gate: {gate.message} (score: {gate.score:.2f})"
        )

        # Phase C: Gap Analysis
        await event_bus.emit("phase_start", {"phase": "C", "name": "Gap Analysis"}, mode="turbo")
        phase_c = PhaseC_GapAnalysis()
        record.gaps, record.hypotheses = phase_c.run(topic, record.sources, usp_context)
        gate = self.quality.check_gaps(record.gaps)
        print(
            f"      {'✓' if gate.passed else '⚠'} Gap gate: {gate.message} (score: {gate.score:.2f})"
        )
        await event_bus.emit("phase_end", {"phase": "C", "name": "Gap Analysis"}, mode="turbo")

        # Phase D: Cognitive Agents (functors + plugins)
        await event_bus.emit(
            "phase_start", {"phase": "D", "name": "Cognitive Agents"}, mode="turbo"
        )
        phase_d = PhaseD_CognitiveAgents()
        if cfg.enable_functors:
            functor_result = await phase_d.run_functors(topic, record.hypotheses)
        else:
            print("\n[3.5/7] Functors disabled (--no-functors)")
            functor_result = {"novel_hypotheses": [], "total_agents": 0, "total_time": 0}
        plugins_result = await phase_d.run_plugins(topic, query_type)
        novel_hypotheses = functor_result.get("novel_hypotheses", [])
        if novel_hypotheses:
            record.hypotheses.extend(novel_hypotheses)
            record.plugins_context["functors"] = functor_result
        record.plugins_context["plugins"] = plugins_result
        await event_bus.emit("phase_end", {"phase": "D", "name": "Cognitive Agents"}, mode="turbo")

        # Phase E: Simulation & Verification
        await event_bus.emit(
            "phase_start", {"phase": "E", "name": "Simulation & Verification"}, mode="turbo"
        )
        phase_e = PhaseE_SimulationVerification()
        if record.hypotheses:
            sim_result = await phase_e.run_simulation(topic, record.hypotheses[0])
            if sim_result.get("status") == "failed" and any(
                keyword in str(sim_result.get("raw_output", "")).lower()
                for keyword in (
                    "insufficient",
                    "resource",
                    "out of memory",
                    "cuda",
                    "exceeded",
                    "unavailable",
                )
            ):
                logger.warning("Simulation failed due to resource limits")
            record.simulation = sim_result
            gate = self.quality.check_simulation(record.simulation)
            print(
                f"      {'✓' if gate.passed else '⚠'} Simulation gate: {gate.message} (score: {gate.score:.2f})"
            )

            verif_result = await phase_e.run_verification(topic, record.hypotheses, query_type)
            record.verification = verif_result
        else:
            record.simulation = {"status": "skipped", "raw_output": "No hypotheses to simulate"}
            record.verification = {"status": "skipped", "backend": "none"}
        await event_bus.emit(
            "phase_end", {"phase": "E", "name": "Simulation & Verification"}, mode="turbo"
        )

        # Phase F: Dissertation Generation (hard gate — no empty/placeholder prose)
        await event_bus.emit(
            "phase_start", {"phase": "F", "name": "Dissertation Generation"}, mode="turbo"
        )
        phase_f = PhaseF_DissertationGeneration(config=cfg, user_profile=self.user_profile)
        diss = ""
        plugins_context: dict[str, Any] = {}
        diss_gate = None
        max_diss_attempts = 3
        for diss_attempt in range(1, max_diss_attempts + 1):
            try:
                diss, plugins_context = phase_f.run(
                    topic=topic, record=record, c4_state=usp_context.get("c4_state", "unknown")
                )
                diss_gate = self.quality.check_dissertation(diss)
                if diss_gate.passed:
                    break
                print(
                    f"      ⚠ Dissertation gate failed (attempt {diss_attempt}/{max_diss_attempts}): "
                    f"{diss_gate.message}"
                )
            except Exception as e:
                logger.warning("Dissertation generation attempt %d failed: %s", diss_attempt, e)
                if diss_attempt >= max_diss_attempts:
                    raise RuntimeError(
                        f"Dissertation generation failed after {max_diss_attempts} attempts: {e}"
                    ) from e
        else:
            raise RuntimeError(
                f"Dissertation quality gate failed after {max_diss_attempts} attempts: "
                f"{diss_gate.message if diss_gate else 'unknown'}"
            )
        record.plugins_context.update(plugins_context)
        await event_bus.emit(
            "phase_end", {"phase": "F", "name": "Dissertation Generation"}, mode="turbo"
        )

        # Phase G: Quality Control
        await event_bus.emit("phase_start", {"phase": "G", "name": "Quality Control"}, mode="turbo")
        record.quality_report = self.quality.evaluate(
            record.sources,
            record.gaps,
            record.hypotheses,
            record.simulation,
            record.verification,
            record.bibliography,
            diss,
        )
        assert record.quality_report is not None
        await event_bus.emit("phase_end", {"phase": "G", "name": "Quality Control"}, mode="turbo")

        # PipelineObserver: instantiate before refinement to accumulate across iterations
        from src.pipeline.observer import PipelineObserver

        observer = PipelineObserver(stagnation_threshold=0.01, max_stagnant_iterations=2)

        phase_g = PhaseG_QualityControl()
        if record.quality_report.overall_score < cfg.min_quality_score:
            obs_metrics = {
                "novelty_score": record.quality_report.overall_score / 100,
                "gap_potential": len(record.gaps) / max(1, cfg.min_gaps),
                "hypothesis_text": record.hypotheses[0].get("text", "")
                if record.hypotheses
                else "",
                "abort_reasons": getattr(record, "abort_reasons", []),
            }
            observer.observe(iteration=0, metrics=obs_metrics)
            record, record.quality_report, _ = await phase_g.run_iterative_improvement(
                self, topic, record, record.quality_report
            )
            assert record.quality_report is not None
            if observer.should_halt():
                logger.warning("Observer stagnation in phase G: should_halt triggered")
                record.quality_report.recommendations.append("Observer: should_halt triggered")

        assert record.quality_report is not None
        observer.observe(
            iteration=1,
            metrics={
                "novelty_score": record.quality_report.overall_score / 100,
                "gap_potential": len(record.gaps) / max(1, cfg.min_gaps),
                "hypothesis_text": record.hypotheses[0].get("text", "")
                if record.hypotheses
                else "",
                "abort_reasons": getattr(record, "abort_reasons", []),
            },
        )
        if observer.should_halt():
            logger.warning("PipelineObserver: stagnation detected — quality may be capped")
            record.quality_report.recommendations.append(
                "Stagnation: refine hypothesis or broaden search"
            )

        path = DissertationGenerator().save(
            diss, filename=f"HIL_v2_{topic.replace(' ', '_')[:30]}.md"
        )
        print(f"\n✅ Research proposal saved: {path}")

        # SocialBridge: transfer dissertation to ~/.c4reqber/drafts/ for social publishing
        try:
            from src.social.social_bridge import transfer_to_drafts

            bridge_result = await transfer_to_drafts(record)
            print(f"📄 Draft saved for review: {bridge_result['draft_id']}")
        except Exception as e:
            logger.warning("SocialBridge unavailable: %s", e)

        # FinalVerifier: post-pipeline novelty check
        from src.pipeline.final_verifier import FinalVerifier

        verifier = FinalVerifier()
        try:
            verif_report = await verifier.verify(
                result={
                    "hypothesis": {"text": record.hypotheses[0].get("text", "")}
                    if record.hypotheses
                    else {},
                    "abort_reasons": getattr(record, "abort_reasons", []),
                    "refinement_history": getattr(record, "refinement_history", []),
                },
                papers=record.bibliography if hasattr(record, "bibliography") else record.sources,
            )
            if not verif_report.passed:
                print(
                    f"⚠ FinalVerifier: {verif_report.issue_count} issues — max_similarity={verif_report.max_similarity:.2f} to '{verif_report.closest_paper[:60]}'"
                )
                record.quality_report.recommendations.append(
                    f"FinalVerifier: {verif_report.issue_count} issues (max_similarity={verif_report.max_similarity:.2f})"
                )
        except Exception:
            logger.exception("FinalVerifier crash — post-pipeline verification skipped")
            record.quality_report.recommendations.append(
                "FinalVerifier: CRASH (verification unavailable)"
            )

        assert record.quality_report is not None
        await self.emit_event(
            "pipeline_complete",
            {
                "topic": topic,
                "path": path,
                "grade": record.quality_report.grade,
                "score": record.quality_report.overall_score,
                "sources": len(record.sources),
                "hypotheses": len(record.hypotheses),
            },
            mode="turbo",
        )

        # ── Saga completion ─────────────────────────────────────────
        try:
            logger.debug("Saga %s completed: %s", record.saga_id, self.saga.status)
        except Exception:
            pass

        return record

    def _classify_query(self, topic: str) -> str:
        topic_lower = topic.lower()
        scientific = [
            "hypothesis",
            "theory",
            "mechanism",
            "quantum",
            "neuro",
            "epigenetic",
            "research",
            "study",
            "experiment",
        ]
        practical = [
            "career",
            "business",
            "startup",
            "how to",
            "tutorial",
            "guide",
            "money",
            "build",
        ]
        sci_score = sum(1 for w in scientific if w in topic_lower)
        prac_score = sum(1 for w in practical if w in topic_lower)
        if sci_score > prac_score * 1.5:
            return "scientific"
        elif prac_score > sci_score * 1.5:
            return "practical"
        return "mixed"


def run_hil_pipeline(
    topic: str, config: PipelineConfig | None = None, user_profile: UserProfile | None = None
) -> None:
    """CLI entry point."""
    pipeline = HILDiscoveryPipeline(config=config, user_profile=user_profile)
    asyncio.run(pipeline.discover(topic))
