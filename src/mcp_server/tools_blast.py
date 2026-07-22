from __future__ import annotations

from typing import Any

from src.knowledge.flash_contract import source_cards_from_papers
from src.mcp_server.honesty import outer_status_from_hil_like, record_field_status


async def blast_solve(
    problem: str, output_format: str = "auto", domain: str | None = None
) -> dict[str, Any]:
    """Run BLAST solve mode — produces strategic artifacts (PRD, plan, blueprint, code).

    Uses UniversalSolvePipeline v2 with HIL enhancements:
    - MultiSourceSearcher (33 sources)
    - Gap Analysis
    - Quality Gates + Reality Check
    - Plugin Auto-Selection
    - 36 simulation engines (including 32 P1 adapters)
    """
    try:
        from src.agents.pipeline import UniversalSolvePipeline
        from src.core.profile_manager import UserProfileManager

        manager = UserProfileManager()
        manager.load()
        config = manager.get_config()

        pipeline = UniversalSolvePipeline(config=config)
        result = await pipeline.solve(problem, mode="autopilot", domain_hint=domain)

        qr = result.quality_report or {}
        nested_fail = False
        if isinstance(qr, dict):
            nested_fail = (
                any(
                    (isinstance(v, dict) and v.get("passed") is False)
                    or (hasattr(v, "passed") and v.passed is False)
                    for v in qr.values()
                )
                if qr
                else False
            )
        status = outer_status_from_hil_like(
            quality_passed_all=None if not nested_fail else False,
            quality_score=(result.confidence or 0) * 100,
            sim_status=None,
            gate_any_failed=nested_fail,
            min_score=30.0,
            sources_requested=bool(result.sources),
            verified_count=source_cards_from_papers(result.sources).get("verified_count"),
            quality_report_missing=not bool(qr),
        )
        if (result.confidence or 0) < 0.3:
            status = "partial"

        source_report = source_cards_from_papers(result.sources)
        out: dict[str, Any] = {
            "status": status,
            "mode": "solve",
            "problem": result.problem,
            "final_solution": result.final_solution[:2000],
            "confidence": result.confidence,
            "sources": source_report["sources"],
            "verified_count": source_report["verified_count"],
            "found_count": source_report["found_count"],
            "gaps": len(result.gaps),
            "quality_report": result.quality_report,
            "c4_path": result.c4_path,
            "plugin_selection": result.plugin_selection,
            "cost_usd": result.cost_usd,
        }
        if source_report["unverified_hits"]:
            out["unverified_hits"] = source_report["unverified_hits"]
        return out
    except Exception as e:
        return {"error": str(e), "status": "error", "mode": "solve"}


async def blast_turbo(
    topic: str, verify_backend: str = "hybrid", functors: bool = True
) -> dict[str, Any]:
    """Run BLAST turbo mode — generates paradigm-shifting research proposal (A+ quality).

    Uses HILDiscoveryPipeline v4 with USP components:
    - IMPACT, C4 Fingerprint, MP Rotation, QZRF, Isomorphism, CDI, TOTE, MatrixDream
    - 33 knowledge sources, 9 functor agents, hybrid verification (6 backends)
    - 36 simulation engines (including 32 P1 adapters + 4 Virtual Bio bridges)
    """
    try:
        from src.core.profile_manager import UserProfileManager
        from src.pipeline.hil_pipeline import HILDiscoveryPipeline

        manager = UserProfileManager()
        user_profile = manager.load()
        config = manager.get_config()
        config.verification_backend = verify_backend
        config.enable_functors = functors

        pipeline = HILDiscoveryPipeline(config=config, user_profile=user_profile)
        record = await pipeline.discover(topic)

        sim_status = record_field_status(record.simulation)
        ver_status = record_field_status(record.verification)
        grade = record.quality_report.grade if record.quality_report else "N/A"
        score = record.quality_report.overall_score if record.quality_report else 0
        gates = list(record.quality_report.gates) if record.quality_report else []
        gate_fail = any(getattr(g, "passed", True) is False for g in gates)
        source_report = source_cards_from_papers(record.sources)
        status = outer_status_from_hil_like(
            quality_passed_all=False if gate_fail else True,
            quality_score=score,
            sim_status=str(sim_status),
            gate_any_failed=gate_fail,
            sources_requested=bool(record.sources),
            verified_count=source_report["verified_count"],
            quality_report_missing=record.quality_report is None,
        )

        out: dict[str, Any] = {
            "status": status,
            "mode": "turbo",
            "topic": record.topic,
            "sources": source_report["sources"],
            "verified_count": source_report["verified_count"],
            "found_count": source_report["found_count"],
            "gaps": len(record.gaps),
            "hypotheses": len(record.hypotheses),
            "simulation": sim_status,
            "verification": ver_status,
            "quality_grade": grade,
            "quality_score": score,
            "quality_gates": [
                {
                    "step": g.step,
                    "passed": g.passed,
                    "score": round(g.score, 2),
                    "message": g.message,
                }
                for g in gates
            ],
            "dissertation_path": f"dissertations/live/HIL_v2_{topic.replace(' ', '_')[:30]}.md",
        }
        if source_report["unverified_hits"]:
            out["unverified_hits"] = source_report["unverified_hits"]
        return out
    except Exception as e:
        return {"error": str(e), "status": "error", "mode": "turbo"}


async def blast_flash(
    question: str, with_sources: bool = False, deep: bool = False
) -> dict[str, Any]:
    """Run BLAST flash mode — quick LLM answer with optional USP cognitive analysis.

    Args:
        question: Question to answer
        with_sources: Include source citations
        deep: Run USP cognitive components (IMPACT, C4, MP, QZRF, CDI, TOTE)
    """
    try:
        from src.config.paths import apply_config_to_env
        from src.knowledge.flash_runner import run_flash

        try:
            apply_config_to_env()
        except Exception as exc:
            import logging

            logging.getLogger(__name__).debug("apply_config_to_env: %s", exc)

        result = await run_flash(question, with_sources=with_sources, deep=deep, format="concise")
        out: dict[str, Any] = {
            "status": result.get("status", "success"),
            "mode": "flash",
            "answer": result.get("answer", ""),
            "sources": result.get("sources") or [],
            "verified_count": result.get("verified_count", 0),
            "found_count": result.get("found_count", 0),
            "usp_context": result.get("usp_context") or {},
            "search_meta": result.get("search_meta") or {},
        }
        unverified = result.get("unverified_hits") or []
        if unverified:
            out["unverified_hits"] = unverified
        warnings = result.get("warnings") or []
        if warnings:
            out["warnings"] = warnings
        return out
    except Exception as e:
        return {"error": str(e), "status": "error", "mode": "flash"}
