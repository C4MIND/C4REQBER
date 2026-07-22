from __future__ import annotations

from typing import Any

from src.knowledge.flash_contract import source_cards_from_papers
from src.mcp_server.honesty import outer_status_from_hil_like, record_field_status
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
                result: dict[str, Any] = {
                    "topic": topic,
                    "status": "success",
                    "pipeline_used": [],
                    "solve_result": None,
                    "turbo_result": None,
                }
                child_partial = False
                if use_solve:
                    try:
                        pipeline = UniversalSolvePipeline(config=config)
                        solve_record = await pipeline.solve(topic, mode="autopilot")
                        conf = float(solve_record.confidence or 0)
                        solve_report = source_cards_from_papers(solve_record.sources)
                        result["solve_result"] = {
                            "final_solution": solve_record.final_solution[:500],
                            "confidence": conf,
                            "sources": solve_report["sources"],
                            "verified_count": solve_report["verified_count"],
                            "found_count": solve_report["found_count"],
                            "gaps": len(solve_record.gaps),
                        }
                        result["pipeline_used"].append("solve")
                        if conf < 0.3:
                            child_partial = True
                    except (AttributeError, ImportError, RuntimeError, ValueError) as e:
                        result["solve_result"] = {"error": str(e)}
                if use_turbo:
                    try:
                        pipeline = HILDiscoveryPipeline(config=config, user_profile=user_profile)
                        turbo_record = await pipeline.discover(topic)
                        qscore = (
                            turbo_record.quality_report.overall_score
                            if turbo_record.quality_report
                            else 0
                        )
                        sim_st = record_field_status(turbo_record.simulation)
                        turbo_report = source_cards_from_papers(turbo_record.sources)
                        result["turbo_result"] = {
                            "hypotheses": len(turbo_record.hypotheses),
                            "sources": turbo_report["sources"],
                            "verified_count": turbo_report["verified_count"],
                            "found_count": turbo_report["found_count"],
                            "quality_grade": turbo_record.quality_report.grade
                            if turbo_record.quality_report
                            else "N/A",
                            "quality_score": qscore,
                            "simulation": sim_st,
                        }
                        result["pipeline_used"].append("turbo")
                        child_st = outer_status_from_hil_like(
                            quality_passed_all=(
                                bool(turbo_record.quality_report.passed_all)
                                if turbo_record.quality_report
                                else None
                            ),
                            quality_score=qscore,
                            sim_status=str(sim_st),
                            sources_requested=bool(turbo_record.sources),
                            verified_count=turbo_report["verified_count"],
                            quality_report_missing=turbo_record.quality_report is None,
                        )
                        if child_st != "success":
                            child_partial = True
                    except (AttributeError, ImportError, RuntimeError, ValueError) as e:
                        result["turbo_result"] = {"error": str(e)}
                if not result["pipeline_used"]:
                    result["status"] = "error"
                    result["error"] = "All pipelines failed"
                elif (
                    child_partial
                    or (result.get("solve_result", {}) or {}).get("error")
                    or (result.get("turbo_result", {}) or {}).get("error")
                ):
                    # Mixed: some ran but weak / one side errored
                    if result["pipeline_used"] and (
                        (result.get("solve_result") or {}).get("error")
                        and (result.get("turbo_result") or {}).get("error")
                    ):
                        result["status"] = "error"
                    else:
                        result["status"] = "partial"
                return result

        tasks = [run_one(sp) for sp in subproblems]
        results = await asyncio.gather(*tasks)

        successful = [r for r in results if r["status"] == "success"]
        partial_n = sum(1 for r in results if r["status"] == "partial")
        failed_n = sum(1 for r in results if r["status"] == "error")
        total_hypotheses = sum(
            (r.get("turbo_result") or {}).get("hypotheses", 0)
            for r in results
            if r["status"] in {"success", "partial"}
        )
        scored = [
            (r.get("turbo_result") or {}).get("quality_score", 0)
            for r in results
            if r["status"] in {"success", "partial"}
        ]
        avg_quality = sum(scored) / max(len(scored), 1)

        if failed_n == len(results):
            outer_status = "error"
        elif failed_n > 0 or partial_n > 0:
            outer_status = "partial"
        else:
            outer_status = "success"

        return {
            "status": outer_status,
            "mode": "turbofactory",
            "domain": domain,
            "scale": scale,
            "pipeline_mode": pipeline_mode,
            "pipelines": n_pipelines,
            "successful": len(successful),
            "partial": partial_n,
            "failed": failed_n,
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
