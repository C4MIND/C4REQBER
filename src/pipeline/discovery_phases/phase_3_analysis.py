"""Phase 3: Deep Analysis — Contradiction mining, temporal KG, isomorphism,
gap miner, hypothesis generation, competing hypotheses, cognitive plugins,
auto-scanner, strong inference, abduction.
"""
from __future__ import annotations

import logging


logger = logging.getLogger("c4_cdi_turbo.pipeline.discovery.phase3")


async def run_deep_analysis(problem, domain, papers, results, thresholds, errors) -> tuple:
    """Run deep analysis."""
    import asyncio
    import time

    from src.discovery.pipeline_logic import (
        build_temporal_kg,
        generate_competing_hypotheses,
        generate_hypothesis,
        mine_contradictions,
        run_abduction,
        run_autoscanner,
        run_cognitive_plugins,
        run_strong_inference,
        search_isomorphisms,
    )

    t_contra = time.perf_counter()
    try:
        results["contradiction_mining"] = mine_contradictions(papers)
    except Exception as e:
        results["contradiction_mining"] = {"error": str(e)}
        errors.append(f"contradiction_mining: {str(e)}")
    logger.info("Contradiction mining: %.3fs", time.perf_counter() - t_contra)
    t_tkg = time.perf_counter()
    try:
        results["temporal_kg"] = build_temporal_kg(papers, problem)
    except Exception as e:
        results["temporal_kg"] = {"error": str(e)}
        errors.append(f"temporal_kg: {str(e)}")
    logger.info("Temporal KG: %.3fs", time.perf_counter() - t_tkg)
    try:
        triz_list = results.get("triz", {}).get("principles", [])
        iso_results = await search_isomorphisms(problem=problem, papers=papers if isinstance(papers, list) else [], triz_principles=triz_list if isinstance(triz_list, list) else [])
        results["isomorphisms"] = iso_results
    except Exception as e:
        results["isomorphisms"] = {"found": 0, "error": str(e)}
        errors.append(f"isomorphism: {str(e)}")
    try:
        from src.discovery.gap_miner import GapMiner
        gm = GapMiner()
        gap_result = await gm.mine_for_discovery(problem=problem, papers=papers if isinstance(papers, list) else [])
        results["gap_miner"] = gap_result
    except Exception as e:
        results["gap_miner"] = {"discovery_potential": 0, "error": str(e)}
        errors.append(f"gap_miner: {str(e)}")
    gap_potential: float = results.get("gap_miner", {}).get("discovery_potential", 0)
    if gap_potential < thresholds["min_gap_miner_potential"]:
        abort_reasons = results.setdefault("_abort_reasons", [])
        abort_reasons.append(f"LOW_DISCOVERY_POTENTIAL: GapMiner score = {gap_potential:.2f} (minimum {thresholds['min_gap_miner_potential']}). Research opportunity not supported by literature.")
    try:
        hypothesis = await asyncio.wait_for(generate_hypothesis(problem=problem, c4_path=results.get("c4_path", {}), triz_principles=results.get("triz", {}).get("principles", []), papers=papers if isinstance(papers, list) else []), timeout=20.0)
        results["hypothesis"] = hypothesis
        try:
            competing = await generate_competing_hypotheses(
                problem=problem,
                primary_hypothesis=hypothesis.get("text", "")[:300],
                triz_principles=results.get("triz", {}).get("principles", []),
                papers=papers[:20] if isinstance(papers, list) else [],
                count=2,
            )
            results["competing_hypotheses"] = competing
            logger.info("Generated %d competing hypotheses", len(competing))
        except Exception:
            logger.exception("one_click_discovery generate_competing_hypotheses failed")
    except Exception as e:
        results["hypothesis"] = {"source": "none", "text": str(e), "error": str(e)}
        errors.append(f"hypothesis: {str(e)}")
    t_plugins = time.perf_counter()
    try:
        hypothesis_text = hypothesis.get("text", "") if isinstance(hypothesis, dict) else str(hypothesis)
        results["cognitive_plugins"] = run_cognitive_plugins(problem=problem, hypothesis_text=hypothesis_text[:300], domain=domain)
    except Exception as e:
        results["cognitive_plugins"] = {"plugins_run": 0, "error": str(e)}
        errors.append(f"cognitive_plugins: {str(e)}")
    logger.info("Cognitive plugins: %.3fs", time.perf_counter() - t_plugins)
    t_auto = time.perf_counter()
    try:
        results["autoscanner"] = await run_autoscanner(papers)
    except Exception as e:
        results["autoscanner"] = {"error": str(e)}
        errors.append(f"autoscanner: {str(e)}")
    logger.info("AutoScanner: %.3fs", time.perf_counter() - t_auto)
    t_si = time.perf_counter()
    try:
        results["strong_inference"] = run_strong_inference(problem, domain, results.get("hypothesis", {}))
    except Exception as e:
        results["strong_inference"] = {"error": str(e)}
        errors.append(f"strong_inference: {str(e)}")
    logger.info("Strong Inference: %.3fs", time.perf_counter() - t_si)
    t_abd = time.perf_counter()
    try:
        results["abduction_ibe"] = run_abduction(problem, domain, papers)
    except Exception as e:
        results["abduction_ibe"] = {"error": str(e)}
        errors.append(f"abduction_ibe: {str(e)}")
    logger.info("Abduction IBE: %.3fs", time.perf_counter() - t_abd)
    return gap_potential, hypothesis
