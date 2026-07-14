from __future__ import annotations

from typing import Any

from src.mcp_server.tools_blast import blast_flash, blast_solve, blast_turbo


async def blast_turbofactory(
    domain: str, scale: str = "standard", max_concurrent: int = 5, pipeline_mode: str = "mixed"
) -> dict[str, Any]:
    """Run BLAST turbofactory mode — parallel paradigm factory (5-100 pipelines).

    Args:
        domain: Domain or problem to research
        scale: mini(5)|standard(10)|mega(25)|giga(100)
        max_concurrent: Max concurrent pipelines
        pipeline_mode: solve|turbo|mixed — which pipeline(s) to run per agent
    """
    try:
        SCALE_MAP = {"mini": 5, "standard": 10, "mega": 25, "giga": 100}
        n_pipelines = SCALE_MAP.get(scale, 10)

        from src.agents.pipeline import UniversalSolvePipeline
        from src.core.profile_manager import UserProfileManager
        from src.llm.gateway import get_gateway
        from src.pipeline.hil_pipeline import HILDiscoveryPipeline

        manager = UserProfileManager()
        user_profile = manager.load()
        config = manager.get_config()

        # Generate sub-problems
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
            subproblems.append(f"{domain} — aspect {len(subproblems) + 1}")
        subproblems = subproblems[:n_pipelines]

        # Run pipelines
        import asyncio

        sem = asyncio.Semaphore(max_concurrent)
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
                            "quality_grade": turbo_record.quality_report.grade
                            if turbo_record.quality_report
                            else "N/A",
                            "quality_score": turbo_record.quality_report.overall_score
                            if turbo_record.quality_report
                            else 0,
                        }
                        result["pipeline_used"].append("turbo")
                    except (AttributeError, ImportError, RuntimeError, ValueError) as e:
                        result["turbo_result"] = {"error": str(e)}
                if not result["pipeline_used"]:
                    result["status"] = "error"
                    result["error"] = "All pipelines failed"
                return result

        tasks = [run_one(sp) for sp in subproblems]
        results = await asyncio.gather(*tasks)

        successful = [r for r in results if r["status"] == "success"]
        total_hypotheses = sum(r.get("turbo_result", {}).get("hypotheses", 0) for r in successful)
        avg_quality = sum(
            r.get("turbo_result", {}).get("quality_score", 0) for r in successful
        ) / max(len(successful), 1)

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
    - Scientific → turbo
    - Paradigm/survey → turbofactory
    - Short question → flash
    - Default → solve
    """
    try:
        from src.cli.mode_router import auto_route, get_mode_description

        mode = auto_route(query)
        description = get_mode_description(mode)

        # Execute the routed mode
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
