from __future__ import annotations

import asyncio
import logging
from typing import Any

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

        result = {
            "status": "success",
            "topic": record.topic,
            "sources": len(record.sources),
            "gaps": len(record.gaps),
            "hypotheses": len(record.hypotheses),
            "simulation": record.simulation.status if record.simulation else "N/A",
            "verification": record.verification.status if record.verification else "N/A",
            "quality_grade": record.quality_report.grade if record.quality_report else "N/A",
            "quality_score": record.quality_report.overall_score if record.quality_report else 0,
            "dissertation_path": f"dissertations/live/HIL_v2_{problem.replace(' ', '_')[:30]}.md",
        }

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

        truncated = papers[:10]
        return {
            "status": "success",
            "data": truncated,
            "metadata": {
                "query": query,
                "sources": sources,
                "source_names": source_names,
                "total_found": len(papers),
                "returned": len(truncated),
            },
        }
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
        return {"problem": problem, "state": list(state.to_tuple()), "fingerprint": str(state)}
    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e)}
