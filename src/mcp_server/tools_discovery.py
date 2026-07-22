from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.knowledge.flash_contract import sanitize_biblio_row, source_cards_from_papers
from src.mcp_server.honesty import (
    outer_status_from_hil_like,
    record_field_status,
    search_outer_status,
)
from src.mcp_server.tool_dependencies import (
    HAS_TOOLS,
    C4Space,
    MultiSourceSearcher,
    triz_search,
)


logger = logging.getLogger(__name__)


async def c4_solve(problem: str, domain: str = "science") -> dict[str, Any]:
    """Run 7-phase HIL discovery pipeline (phases A→G) with quality gates.

    Uses HILDiscoveryPipeline: literature → gaps → hypotheses → simulation →
    verification → dissertation → quality control.
    """
    try:
        if not HAS_TOOLS:
            return {"error": "Tool dependencies not available", "status": "error"}

        from src.core.profile_manager import UserProfileManager
        from src.pipeline.hil_pipeline import HILDiscoveryPipeline

        manager = UserProfileManager()
        user_profile = manager.load()
        config = manager.get_config()

        pipeline = HILDiscoveryPipeline(config=config, user_profile=user_profile)
        record = await pipeline.discover(problem)

        sim_status = record_field_status(record.simulation)
        score = record.quality_report.overall_score if record.quality_report else 0
        passed_all = bool(record.quality_report.passed_all) if record.quality_report else None
        source_report = source_cards_from_papers(record.sources)
        result = {
            "status": outer_status_from_hil_like(
                quality_passed_all=passed_all,
                quality_score=score,
                sim_status=str(sim_status),
                sources_requested=bool(record.sources),
                verified_count=source_report["verified_count"],
                quality_report_missing=record.quality_report is None,
            ),
            "topic": record.topic,
            "sources": source_report["sources"],
            "verified_count": source_report["verified_count"],
            "found_count": source_report["found_count"],
            "gaps": len(record.gaps),
            "hypotheses": len(record.hypotheses),
            "simulation": sim_status,
            "verification": record_field_status(record.verification),
            "quality_grade": record.quality_report.grade if record.quality_report else "N/A",
            "quality_score": score,
            "dissertation_path": f"dissertations/live/HIL_v2_{problem.replace(' ', '_')[:30]}.md",
        }
        if source_report["unverified_hits"]:
            result["unverified_hits"] = source_report["unverified_hits"]

        if record.quality_report and not record.quality_report.passed_all:
            result["warnings"] = record.quality_report.recommendations

        return result
    except Exception as e:
        logger.exception("MCP tool failed")
        return {"error": str(e), "status": "error"}


async def c4_search(query: str, sources: list[str] | None = None) -> dict[str, Any]:
    """Search the configured knowledge sources via the orchestrator."""
    try:
        if not HAS_TOOLS:
            return {
                "status": "error",
                "data": [],
                "errors": ["MultiSourceSearcher not available"],
                "metadata": {"query": query, "sources": sources},
            }
        searcher = MultiSourceSearcher()
        if sources:
            per_source = await asyncio.gather(
                *(searcher.search_single(source, query) for source in sources)
            )
            papers = [paper for result in per_source for paper in result]
            source_names = list(sources)
        else:
            search_result = await searcher.search_all(query)
            papers = list(search_result.get("papers", []))
            source_names = list(search_result.get("source_names", []))

        sanitized = [sanitize_biblio_row(p) for p in papers if isinstance(p, dict)]
        source_report = source_cards_from_papers(sanitized, sanitize=False)
        truncated_verified = source_report["sources"][:10]
        truncated_unverified = source_report["unverified_hits"][:10]
        status = search_outer_status(
            total_found=len(sanitized),
            sources_requested=bool(sources),
            verified_count=source_report["verified_count"],
        )
        out: dict[str, Any] = {
            "status": status,
            "data": truncated_verified or truncated_unverified,
            "sources": truncated_verified,
            "verified_count": source_report["verified_count"],
            "found_count": source_report["found_count"],
            "metadata": {
                "query": query,
                "sources": sources,
                "source_names": source_names,
                "total_found": len(papers),
                "returned": len(truncated_verified or truncated_unverified),
            },
        }
        if source_report["unverified_hits"]:
            out["unverified_hits"] = truncated_unverified
        if status == "partial":
            out["warnings"] = ["No papers found — empty search is not success"]
        return out
    except (AttributeError, ImportError, TypeError, ValueError) as e:
        logger.exception("MCP knowledge search failed")
        return {
            "status": "error",
            "data": [],
            "errors": [str(e)],
            "metadata": {"query": query, "sources": sources},
        }


async def c4_triz(
    improving: int = 1,
    worsening: int = 2,
    mode: str = "matrix",
    problem: str = "",
) -> dict[str, Any]:
    """Resolve contradiction using TRIZ tools.

    Modes:
      matrix   — classic contradiction matrix (40 principles)
      ariz     — ARIZ-85C state machine analysis
      standard — 76 Standard Solutions lookup
      sufield  — Su-Field model analysis
    """
    try:
        if mode == "matrix":
            if not HAS_TOOLS:
                return {"error": "TRIZ module not available"}
            principles = triz_search(improving, worsening)
            return {
                "mode": mode,
                "improving": improving,
                "worsening": worsening,
                "principles": [p.number for p in principles[:5]],
            }

        if mode == "ariz":
            from src.triz.ariz import ARIZ85C, list_all_steps

            ariz = ARIZ85C()
            state = ariz.start(problem or "Unspecified problem")
            step = ariz.get_current_step(state)
            return {
                "mode": mode,
                "problem": problem,
                "current_step": step.step_id,
                "step_name": step.name,
                "prompt": step.prompt,
                "observer_level": step.c4_observer,
                "all_steps": list_all_steps(),
                "progress": ariz.get_progress(state),
            }

        if mode == "standard":
            from src.triz.standard_solutions import (
                count_solutions,
                get_all_solutions,
                search_solutions,
            )

            query = problem or ""
            results = search_solutions(query) if query else get_all_solutions()
            return {
                "mode": mode,
                "query": query,
                "counts": count_solutions(),
                "results": [s.to_dict() for s in results[:10]],
            }

        if mode == "sufield":
            from src.triz.sufield import SuFieldAnalyzer

            analyzer = SuFieldAnalyzer()
            analysis = analyzer.analyze(problem or "No problem text provided")
            return {
                "mode": mode,
                "problem": problem,
                "model": analysis.get("model"),
                "completeness": analysis.get("completeness"),
                "transformations": analysis.get("transformations"),
                "c4_mapping": analysis.get("c4_mapping"),
            }

        return {"error": f"Unknown mode: {mode}. Use matrix|ariz|standard|sufield"}

    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e)}


async def c4_fingerprint(problem: str) -> dict[str, Any]:
    """Classify problem to C4 state (Z₃³ cube coordinates) with C4 → GapAnalyzer ABC resolution scoring.

    Uses neural classifier (ONNX → PyTorch → LLM → heuristic) for best accuracy.
    """
    try:
        # Try neural classifier first (96.5% accuracy when available)
        try:
            from src.c4.neural_classifier.neural_fingerprint import NeuralFingerprint

            fp = NeuralFingerprint()
            if fp.is_available:
                result = fp.classify(problem)
                return {
                    "problem": problem,
                    "state": list(result.state.coordinates),
                    "fingerprint": result.state.label,
                    "confidence": result.confidence,
                    "backend": fp.backend,
                    "model": result.model,
                    "probabilities": result.probabilities,
                }
        except (ImportError, OSError, RuntimeError, ValueError):
            pass

        # Fallback: heuristic C4 engine
        if not HAS_TOOLS:
            return {"error": "C4 engine not available"}
        space = C4Space()
        try:
            from src.c4.routing import FRARouter

            router = FRARouter()
            state = router.classify_c4_state(problem)
        except (ImportError, AttributeError):
            state = space._heuristic_classify(problem)
            return {
                "problem": problem,
                "state": list(state.to_tuple()),
                "fingerprint": str(state),
                "backend": "heuristic",
                "heuristic": True,
            }
        return {
            "problem": problem,
            "state": list(state.to_tuple()),
            "fingerprint": str(state),
            "backend": "fra_router",
            "heuristic": False,
        }
    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e)}
