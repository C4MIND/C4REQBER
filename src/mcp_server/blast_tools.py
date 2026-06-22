# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
from typing import Any

from src.mcp_server.fallback_protocol import validate_tool_input


logger = logging.getLogger(__name__)


async def blast_solve(problem: str, output_format: str = "auto", domain: str | None = None) -> dict[str, Any]:
    """Run BLAST solve mode -- produces strategic artifacts (PRD, plan, blueprint, code).

    Uses UniversalSolvePipeline v2 with HIL enhancements:
    - MultiSourceSearcher (33 knowledge sources)
    - Gap Analysis
    - Quality Gates + Reality Check
    - Plugin Auto-Selection
    - 36 simulation engines (including 32 P1 adapters)
    """
    try:
        _ = validate_tool_input("blast_solve", {"problem": problem, "output_format": output_format, "domain": domain or ""})
        from src.agents.pipeline import UniversalSolvePipeline
        from src.core.profile_manager import UserProfileManager

        manager = UserProfileManager()
        user_profile = manager.load()
        config = manager.get_config()

        pipeline = UniversalSolvePipeline(config=config)
        result = await pipeline.solve(problem, mode="autopilot", domain_hint=domain)

        return {
            "status": "success",
            "mode": "solve",
            "problem": result.problem,
            "final_solution": result.final_solution[:2000],
            "confidence": result.confidence,
            "sources": len(result.sources),
            "gaps": len(result.gaps),
            "quality_report": result.quality_report,
            "c4_path": result.c4_path,
            "plugin_selection": result.plugin_selection,
            "cost_usd": result.cost_usd,
        }
    except Exception as e:
        return {"error": str(e), "status": "error", "mode": "solve"}


async def blast_turbo(topic: str, verify_backend: str = "hybrid", functors: bool = True) -> dict[str, Any]:
    """Run BLAST turbo mode -- generates paradigm-shifting research proposal (A+ quality).

    Uses HILDiscoveryPipeline v4 with USP components:
    - IMPACT, C4 Fingerprint, MP Rotation, QZRF, Isomorphism, CDI, TOTE, MatrixDream
    - 33 knowledge sources, 9 functor agents, hybrid verification (6 backends)
    - 36 simulation engines (including 32 P1 adapters + 4 Virtual Bio bridges)
    """
    try:
        _ = validate_tool_input("blast_turbo", {"topic": topic, "verify_backend": verify_backend})
        from src.core.profile_manager import UserProfileManager
        from src.pipeline.hil_pipeline import HILDiscoveryPipeline

        manager = UserProfileManager()
        user_profile = manager.load()
        config = manager.get_config()
        config.verification_backend = verify_backend
        config.enable_functors = functors

        pipeline = HILDiscoveryPipeline(config=config, user_profile=user_profile)
        record = await pipeline.discover(topic)

        progress_history = [
            {"stage": p.stage, "step": p.step, "total": p.total_steps, "message": p.message, "status": p.status}
            for p in pipeline.progress.get_history()
        ]

        return {
            "status": "success",
            "mode": "turbo",
            "topic": record.topic,
            "progress": progress_history,
            "sources": len(record.sources),
            "gaps": len(record.gaps),
            "hypotheses": len(record.hypotheses),
            "simulation": record.simulation.status if record.simulation else "N/A",
            "verification": record.verification.status if record.verification else "N/A",
            "quality_grade": record.quality_report.grade if record.quality_report else "N/A",
            "quality_score": record.quality_report.overall_score if record.quality_report else 0,
            "quality_gates": [
                {"step": g.step, "passed": g.passed, "score": round(g.score, 2), "message": g.message}
                for g in (record.quality_report.gates if record.quality_report else [])
            ],
            "dissertation_path": f"dissertations/live/HIL_v2_{topic.replace(' ', '_')[:30]}.md",
        }
    except Exception as e:
        return {"error": str(e), "status": "error", "mode": "turbo"}


async def blast_flash(question: str, with_sources: bool = False, deep: bool = False) -> dict[str, Any]:
    """Run BLAST flash mode -- quick LLM answer with optional USP cognitive analysis.

    Args:
        question: Question to answer
        with_sources: Include source citations
        deep: Run USP cognitive components (IMPACT, C4, MP, QZRF, CDI, TOTE)
    """
    try:
        _ = validate_tool_input("blast_flash", {"question": question})
        from src.knowledge.orchestrator import MultiSourceSearcher
        from src.llm.gateway import get_gateway
        from src.plugins.unified_registry import WebSearchPlugin

        llm = get_gateway()
        context = ""
        sources = []
        usp_context = {}

        if deep:
            from src.c4.engine import C4Space
            from src.core.cdi_engine import CDIEngine
            from src.metamodels.impact import ImpactEngine
            from src.metamodels.mp.library import MPLibrary
            from src.metamodels.mp.profiles import MPRotationEngine
            from src.metamodels.qzrf.operators import QzrfLibrary

            try:
                impact = ImpactEngine()
                impact_result = impact.identify(question)
                impact_mapped = impact.map(impact_result)
                usp_context["impact"] = f"{len(impact_mapped.get('entities', []))} entities"
            except (ImportError, AttributeError, RuntimeError):
                logger.debug("impact engine failed in flash mode", exc_info=True)
                pass

            try:
                c4_space = C4Space()
                c4_state = c4_space.fingerprint(question)
                usp_context["c4_state"] = str(c4_state)
            except (ImportError, AttributeError, RuntimeError):
                c4_state = "unknown"

            try:
                mp_lib = MPLibrary()
                mp_rotation = MPRotationEngine(mp_lib)
                perspectives = mp_rotation.rotate(question, state=str(c4_state))
                usp_context["perspectives"] = [p.get("name", "") for p in perspectives[:3]]
            except (ImportError, AttributeError, RuntimeError):
                logger.debug("mp rotation failed in flash mode", exc_info=True)
                pass

            try:
                qzrf = QzrfLibrary()
                operators = qzrf.select(str(c4_state))
                usp_context["qzrf"] = operators[:5]
            except (ImportError, AttributeError, RuntimeError):
                logger.debug("qzrf select failed in flash mode", exc_info=True)
                pass

            try:
                cdi = CDIEngine()
                cdi_result = cdi.analyze(question, context={"c4_state": str(c4_state)})
                usp_context["contradictions"] = len(cdi_result.get("contradictions", []))
            except (ImportError, AttributeError, RuntimeError):
                logger.debug("cdi engine failed in flash mode", exc_info=True)
                pass

        if with_sources or deep:
            searcher = MultiSourceSearcher()
            try:
                result = await searcher.search_all(question)
                papers = result.get("papers", [])[:5]
                sources = papers
                context = "\n".join(
                    [
                        f"- {p.get('title', '')}: {p.get('snippet', p.get('abstract', ''))[:250]}"
                        for p in papers
                    ]
                )
            except (ImportError, AttributeError, RuntimeError, ValueError):
                searcher = WebSearchPlugin()
                results = searcher.execute(question, max_results=3)
                sources = results

        prompt = f"""Answer concisely and accurately.

Context:
{context}

Cognitive Analysis:
{usp_context}

Question: {question}

Answer:"""

        response = await llm.generate(prompt, max_tokens=800, temperature=0.3)

        return {
            "status": "success",
            "mode": "flash",
            "answer": response.content,
            "sources": [{"title": s.get("title", ""), "url": s.get("url", "")} for s in sources[:5]],
            "usp_context": usp_context,
        }
    except Exception as e:
        return {"error": str(e), "status": "error", "mode": "flash"}


async def blast_turbofactory(domain: str, scale: str = "standard", max_concurrent: int = 5, pipeline_mode: str = "mixed") -> dict[str, Any]:
    """Run BLAST turbofactory mode -- parallel paradigm factory (5-100 pipelines).

    Args:
        domain: Domain or problem to research
        scale: mini(5)|standard(10)|mega(25)|giga(100)
        max_concurrent: Max concurrent pipelines
        pipeline_mode: solve|turbo|mixed -- which pipeline(s) to run per agent
    """
    try:
        _ = validate_tool_input("blast_turbofactory", {"domain": domain, "scale": scale, "pipeline_mode": pipeline_mode})
        SCALE_MAP = {"mini": 5, "standard": 10, "mega": 25, "giga": 100}
        n_pipelines = SCALE_MAP.get(scale, 10)

        from src.agents.pipeline import UniversalSolvePipeline
        from src.core.profile_manager import UserProfileManager
        from src.llm.gateway import get_gateway
        from src.pipeline.hil_pipeline import HILDiscoveryPipeline

        manager = UserProfileManager()
        user_profile = manager.load()
        config = manager.get_config()

        llm = get_gateway()
        prompt = f"Given the domain '{domain}', generate {n_pipelines} distinct research sub-problems. Format as numbered list."
        response = await llm.generate(prompt, max_tokens=1200, temperature=0.8)
        import re

        subproblems = []
        for line in response.content.split("\n"):
            m = re.match(r"^\s*\d+[\.\)]\s*(.+)", line.strip())
            if m and len(m.group(1)) > 10:
                subproblems.append(m.group(1).strip())
        while len(subproblems) < n_pipelines:
            subproblems.append(f"{domain} -- aspect {len(subproblems)+1}")
        subproblems = subproblems[:n_pipelines]

        import asyncio as _asyncio

        sem = _asyncio.Semaphore(max_concurrent)
        use_solve = pipeline_mode in ("solve", "mixed")
        use_turbo = pipeline_mode in ("turbo", "mixed")

        async def run_one(topic: str) -> dict[str, Any]:
            async with sem:
                result = {
                    "topic": topic,
                    "status": "success",
                    "pipeline_used": [],
                    "solve_result": None,
                    "turbo_result": None,
                }
                if use_solve:
                    try:
                        pipeline = UniversalSolvePipeline(config=config)
                        solve_record = await pipeline.solve(topic, mode="autopilot")
                        result["solve_result"] = {
                            "final_solution": solve_record.final_solution[:500],
                            "confidence": solve_record.confidence,
                            "sources": len(solve_record.sources),
                            "gaps": len(solve_record.gaps),
                        }
                        result["pipeline_used"].append("solve")
                    except (AttributeError, ImportError, RuntimeError, ValueError) as e:
                        result["solve_result"] = {"error": str(e)}
                if use_turbo:
                    try:
                        pipeline = HILDiscoveryPipeline(config=config, user_profile=user_profile)
                        turbo_record = await pipeline.discover(topic)
                        result["turbo_result"] = {
                            "hypotheses": len(turbo_record.hypotheses),
                            "sources": len(turbo_record.sources),
                            "quality_grade": turbo_record.quality_report.grade if turbo_record.quality_report else "N/A",
                            "quality_score": turbo_record.quality_report.overall_score if turbo_record.quality_report else 0,
                        }
                        result["pipeline_used"].append("turbo")
                    except (AttributeError, ImportError, RuntimeError, ValueError) as e:
                        result["turbo_result"] = {"error": str(e)}
                if not result["pipeline_used"]:
                    result["status"] = "error"
                    result["error"] = "All pipelines failed"
                return result

        tasks = [run_one(sp) for sp in subproblems]
        results = await _asyncio.gather(*tasks)

        successful = [r for r in results if r["status"] == "success"]
        total_hypotheses = sum(r.get("turbo_result", {}).get("hypotheses", 0) for r in successful)
        avg_quality = sum(r.get("turbo_result", {}).get("quality_score", 0) for r in successful) / max(len(successful), 1)

        return {
            "status": "success",
            "mode": "turbofactory",
            "domain": domain,
            "scale": scale,
            "pipeline_mode": pipeline_mode,
            "pipelines": n_pipelines,
            "successful": len(successful),
            "failed": len(results) - len(successful),
            "total_hypotheses": total_hypotheses,
            "avg_quality_score": round(avg_quality, 1),
            "results": results,
        }
    except Exception as e:
        return {"error": str(e), "status": "error", "mode": "turbofactory"}


async def blast_auto(query: str) -> dict[str, Any]:
    """Auto-route query to best BLAST mode and execute it.

    Uses keyword-based routing:
    - Scientific -> turbo
    - Paradigm/survey -> turbofactory
    - Short question -> flash
    - Default -> solve
    """
    try:
        _ = validate_tool_input("blast_auto", {"query": query})
        from src.cli.mode_router import auto_route, get_mode_description

        mode = auto_route(query)
        description = get_mode_description(mode)

        if mode == "solve":
            result = await blast_solve(problem=query)
        elif mode == "turbo":
            result = await blast_turbo(topic=query)
        elif mode == "flash":
            result = await blast_flash(question=query, with_sources=True)
        elif mode == "turbofactory":
            result = await blast_turbofactory(domain=query)
        else:
            result = await blast_solve(problem=query)

        result["auto_routed"] = True
        result["selected_mode"] = mode
        result["mode_description"] = description
        return result
    except Exception as e:
        return {"error": str(e), "status": "error", "mode": "auto"}
