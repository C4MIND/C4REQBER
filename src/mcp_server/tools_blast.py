from __future__ import annotations

from typing import Any


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

        return {
            "status": "success",
            "mode": "turbo",
            "topic": record.topic,
            "sources": len(record.sources),
            "gaps": len(record.gaps),
            "hypotheses": len(record.hypotheses),
            "simulation": record.simulation.status if record.simulation else "N/A",
            "verification": record.verification.status if record.verification else "N/A",
            "quality_grade": record.quality_report.grade if record.quality_report else "N/A",
            "quality_score": record.quality_report.overall_score if record.quality_report else 0,
            "quality_gates": [
                {
                    "step": g.step,
                    "passed": g.passed,
                    "score": round(g.score, 2),
                    "message": g.message,
                }
                for g in (record.quality_report.gates if record.quality_report else [])
            ],
            "dissertation_path": f"dissertations/live/HIL_v2_{topic.replace(' ', '_')[:30]}.md",
        }
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
        from src.knowledge.orchestrator import MultiSourceSearcher
        from src.llm.gateway import get_gateway
        from src.plugins.unified_registry import WebSearchPlugin

        llm = get_gateway()
        context = ""
        sources = []
        usp_context = {}

        if deep:
            # Run USP cognitive components
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
                pass

            try:
                qzrf = QzrfLibrary()
                operators = qzrf.select(str(c4_state))
                usp_context["qzrf"] = operators[:5]
            except (ImportError, AttributeError, RuntimeError):
                pass

            try:
                cdi = CDIEngine()
                cdi_result = cdi.analyze(question, context={"c4_state": str(c4_state)})
                usp_context["contradictions"] = len(cdi_result.get("contradictions", []))
            except (ImportError, AttributeError, RuntimeError):
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
            "sources": [
                {"title": s.get("title", ""), "url": s.get("url", "")} for s in sources[:5]
            ],
            "usp_context": usp_context,
        }
    except Exception as e:
        return {"error": str(e), "status": "error", "mode": "flash"}
