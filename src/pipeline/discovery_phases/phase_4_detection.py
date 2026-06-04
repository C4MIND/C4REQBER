"""Phase 4: Shift Detection — AlreadyShiftedDetector, paradigm shift, novelty validator,
falsification engine, DoE design, power analysis, reproducibility.
"""
from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger("c4_cdi_turbo.pipeline.discovery.phase4")


async def run_shift_detection(problem, domain, papers, results, citation_chase_result, thresholds, errors, abort_reasons) -> dict[str, Any]:
    """Run shift detection."""
    import asyncio
    import time

    from src.api.v8_routers.discovery.pipeline import (
        detect_paradigm_shift,
        run_doe_design,
        run_falsification_engine,
        run_power_analysis,
        run_reproducibility_check,
    )

    already_shifted_result: dict[str, Any] = {}
    try:
        from src.discovery.already_shifted import AlreadyShiftedDetector
        hypothesis_text = results.get("hypothesis", {}).get("text", "")
        shift_detector = AlreadyShiftedDetector()
        already_shifted_result = await asyncio.wait_for(shift_detector.check(hypothesis=hypothesis_text, papers=papers[:100], citation_timeline=citation_chase_result.get("timeline", []), domain=domain), timeout=15.0)
        if isinstance(already_shifted_result, dict) and already_shifted_result.get("already_shifted"):
            verdict = already_shifted_result.get("verdict", "ALREADY_SHIFTED")
            logger.warning("ALREADY_SHIFTED_GATE: adding abort reason. Verdict=%s Consensus=%s ShiftYear=%s", verdict, already_shifted_result.get('consensus_level'), already_shifted_result.get('shift_year'))
            abort_reasons.append(f"ALREADY_SHIFTED: This paradigm shift has ALREADY occurred. Seminal papers: {[p['title'][:60] for p in already_shifted_result.get('seminal_papers', [])[:3]]}. First detected: {already_shifted_result.get('shift_year')}. Consensus: {already_shifted_result.get('consensus_level', 0):.0%}.")
            logger.warning("abort_reasons now has %d items: %s", len(abort_reasons), abort_reasons)
    except TimeoutError:
        logger.warning("shift_detector.check timed out after 15s")
    except ImportError:
        pass
    t_ps = time.perf_counter()
    try:
        results["paradigm_shift"] = detect_paradigm_shift(papers, domain)
    except Exception as e:
        results["paradigm_shift"] = {"error": str(e)}
        errors.append(f"paradigm_shift: {str(e)}")
    logger.info("Paradigm shift: %.3fs", time.perf_counter() - t_ps)
    try:
        from src.discovery.novelty_validator import NoveltyValidator
        hypothesis_text = results.get("hypothesis", {}).get("text", "")
        async with NoveltyValidator() as validator:
            novelty_result = await validator.check(hypothesis_text, domain)
        results["novelty"] = novelty_result
        novelty_score_val = novelty_result.get("novelty_score", 0.5)
        if novelty_score_val < thresholds["min_novelty_score"]:
            closest = novelty_result.get("closest_papers", [])
            closest_title = closest[0].get("title", "unknown") if closest else "unknown"
            low_novelty_note = f"LOW_NOVELTY: hypothesis overlaps with existing literature. Closest: '{closest_title}' (similarity={novelty_result.get('max_similarity', 0):.2f}, score={novelty_score_val:.2f}). Consider reformulating."
            abort_reasons.append(low_novelty_note)
            results["novelty_warning"] = low_novelty_note
            logger.warning(low_novelty_note)
        elif novelty_score_val < 0.6:
            results["novelty_warning"] = f"MODERATE_NOVELTY: score={novelty_score_val:.2f}. Acceptable but borderline."
            logger.info("Moderate novelty: %.2f", novelty_score_val)
    except Exception as e:
        results["novelty"] = {"status": "unchecked", "novelty_score": 0.5, "error": str(e)}
        errors.append(f"novelty: {str(e)}")
    t_fals = time.perf_counter()
    try:
        results["falsification_engine"] = run_falsification_engine(results.get("hypothesis", {}), domain)
    except Exception as e:
        results["falsification_engine"] = {"error": str(e)}
        errors.append(f"falsification_engine: {str(e)}")
    logger.info("Falsification engine: %.3fs", time.perf_counter() - t_fals)
    t_doe = time.perf_counter()
    try:
        results["doe_design"] = run_doe_design(domain)
    except Exception as e:
        results["doe_design"] = {"error": str(e)}
        errors.append(f"doe_design: {str(e)}")
    logger.info("DoE design: %.3fs", time.perf_counter() - t_doe)
    t_power = time.perf_counter()
    try:
        results["power_analysis"] = run_power_analysis(results.get("hypothesis", {}))
    except Exception as e:
        results["power_analysis"] = {"error": str(e)}
        errors.append(f"power_analysis: {str(e)}")
    logger.info("Power analysis: %.3fs", time.perf_counter() - t_power)
    t_repro = time.perf_counter()
    try:
        results["reproducibility"] = run_reproducibility_check(problem)
    except Exception as e:
        results["reproducibility"] = {"error": str(e)}
        errors.append(f"reproducibility: {str(e)}")
    logger.info("Reproducibility: %.3fs", time.perf_counter() - t_repro)
    return already_shifted_result
