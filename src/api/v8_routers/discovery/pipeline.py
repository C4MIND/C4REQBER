from __future__ import annotations


"""Discovery API endpoints + request models.

Domain logic lives in src.discovery.pipeline_logic and is re-exported here for
backward compatibility (so existing `...discovery.pipeline` imports keep working).
"""
import asyncio
import json
import logging
import re
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from src.api.v8_routers.discovery.jobs import get_job_store
from src.api.v8_routers.discovery.search import search_knowledge
from src.discovery.pipeline_logic import (
    _build_dissertation,
    _domain_improving_param,
    _domain_worsening_param,
    _escape_latex,
    _refine_hypothesis_llm,
    _run_self_critique,
    _sanitize_for_prompt,
    build_temporal_kg,
    detect_paradigm_shift,
    generate_competing_hypotheses,
    generate_hypothesis,
    generate_lean4_proof,
    generate_paper,
    mine_contradictions,
    navigate_c4,
    resolve_triz,
    run_abduction,
    run_autoscanner,
    run_bayesian_conjugate_update,
    run_bayesian_model_averaging,
    run_c4_observer,
    run_causal_do_calculus,
    run_cognitive_plugins,
    run_consensus_meter,
    run_counterfactual,
    run_dempster_shafer,
    run_doe_design,
    run_empirical_validation,
    run_falsification_engine,
    run_fra_routing,
    run_matrix_dream,
    run_power_analysis,
    run_relevant_simulation,
    run_reproducibility_check,
    run_strong_inference,
    search_isomorphisms,
)
from src.llm.gateway import get_gateway
from src.pipeline.discovery_config import (
    minimum_discovery_papers,
    minimum_paradigm_shift_papers,
    simulation_timeout_seconds,
)


logger = logging.getLogger("c4_cdi_turbo.api.v8.discovery")


__all__ = [
    "DissertationRequest",
    "FlashRequest",
    "MultiHypothesisRequest",
    "OneClickRequest",
    "_build_dissertation",
    "_domain_improving_param",
    "_domain_worsening_param",
    "_escape_latex",
    "_refine_hypothesis_llm",
    "_run_self_critique",
    "_sanitize_for_prompt",
    "_update_phase",
    "build_temporal_kg",
    "detect_paradigm_shift",
    "dissertation_mode",
    "flash_discovery",
    "generate_competing_hypotheses",
    "generate_hypothesis",
    "generate_lean4_proof",
    "generate_paper",
    "mine_contradictions",
    "multi_hypothesis_discovery",
    "navigate_c4",
    "one_click_discovery",
    "resolve_triz",
    "run_abduction",
    "run_autoscanner",
    "run_bayesian_conjugate_update",
    "run_bayesian_model_averaging",
    "run_c4_observer",
    "run_causal_do_calculus",
    "run_cognitive_plugins",
    "run_consensus_meter",
    "run_counterfactual",
    "run_dempster_shafer",
    "run_doe_design",
    "run_empirical_validation",
    "run_falsification_engine",
    "run_fra_routing",
    "run_matrix_dream",
    "run_power_analysis",
    "run_relevant_simulation",
    "run_reproducibility_check",
    "run_strong_inference",
    "search_isomorphisms",
]


class OneClickRequest(BaseModel):
    problem: str
    domain: str = "science"
    llm_tier: str = "C2"
    output_mode: str = "human"  # "human" (clean paper) or "explain" (with pipeline internals)


class MultiHypothesisRequest(BaseModel):
    problem: str
    domain: str = "science"
    count: int = 3


class FlashRequest(BaseModel):
    problem: str
    domain: str = "science"
    level: str = "simple"


class DissertationRequest(BaseModel):
    problem: str
    domain: str = "general"
    max_iterations: int = 10
    min_quality: str = "PUBLISHABLE"


async def _update_phase(
    job_id: str | None,
    phase_name: str,
    detail: str = "",
    progress: float | None = None,
) -> None:
    if job_id:
        store = get_job_store()
        await store.update_phase(job_id, phase_name, detail, progress)
        job = await store.get(job_id)
        status = job.status.value if job else "running"
        await store.push_event(
            job_id,
            "phase_progress",
            {
                "type": "phase_progress",
                "phase": phase_name,
                "detail": detail,
                "progress": progress if progress is not None else (job.progress if job else 0.0),
                "status": status,
            },
        )


async def one_click_discovery(
    request: OneClickRequest,
    *,
    job_id: str | None = None,
) -> dict[str, Any]:
    problem = request.problem
    domain = request.domain
    errors: list[str] = []
    start_total = time.perf_counter()
    results: dict[str, Any] = {
        "problem": problem,
        "domain": domain,
        "pipeline_version": "v8.0",
        "warnings": [],
    }
    thresholds = {
        "min_papers_for_discovery": minimum_discovery_papers(),
        "min_papers_for_paradigm_shift": minimum_paradigm_shift_papers(),
        "min_gap_miner_potential": 0.15,
        "min_novelty_score": 0.5,
        "min_contradictions_found": 3,
        "recursive_search_depth": 2,
        "cross_validate_sources_min": 5,
        "require_already_shifted_check": True,
        "require_self_critique": True,
        # Per-stage LLM model tier — user can override in TUI settings.
        # Maps pipeline phase → quality level (local/cheap/balanced/premium).
        # C1 → cheap, C2 → balanced, C3 → premium. Local requires MLX.
        "llm_tier": request.llm_tier,
        "output_mode": request.output_mode,
    }
    abort_reasons: list[str] = []
    results["_errors"] = errors
    results["_abort_reasons"] = abort_reasons
    results["_thresholds"] = thresholds
    results["_llm_stage"] = {
        "A": "local",  # Framing — MLX, free
        "B": "balanced",  # Search — Qwen, free
        "C": "balanced",  # Gap analysis — Qwen, free
        "D": "premium",  # Hypothesis — Claude Sonnet $3
        "E": "local",  # Simulation — no LLM (compute plugins)
        "F": "premium",  # Dissertation — Claude Sonnet $3
        "G": "cheap",  # Quality — GPT-4o-mini $0.15
    }

    await _update_phase(job_id, "A: Framing", "Cognitive framing", 0.0)
    from src.pipeline.discovery_phases.phase_1_cognitive import run_cognitive_framing

    results = await run_cognitive_framing(problem, results)

    await _update_phase(job_id, "B: Search", "Knowledge acquisition", 0.15)
    from src.pipeline.discovery_phases.phase_2_knowledge import run_knowledge_acquisition

    logger.info("PHASE_B starting search...")
    papers, papers_found, sources_used, citation_chase_result = await run_knowledge_acquisition(
        problem, domain, thresholds, results, errors
    )
    logger.info("PHASE_B done: %d papers from %d sources", papers_found, sources_used)

    await _update_phase(job_id, "C: Gaps", "Deep analysis & gap mining", 0.30)
    from src.pipeline.discovery_phases.phase_3_analysis import run_deep_analysis

    logger.info("PHASE_C starting...")
    try:
        gap_potential, hypothesis = await asyncio.wait_for(
            run_deep_analysis(problem, domain, papers, results, thresholds, errors),
            timeout=300.0,
        )
    except TimeoutError:
        errors.append("Phase C (gap analysis) timed out after 300s")
        gap_potential = 0.0
        logger.warning("PHASE_C timed out after 300s")
    results["_gap_potential"] = gap_potential
    results["_papers_list"] = papers
    results["_papers_found"] = papers_found
    results["_sources_used"] = sources_used
    results["_citation_chase_result"] = citation_chase_result

    await _update_phase(job_id, "D: Hyps", "Hypothesis generation", 0.45)
    from src.pipeline.discovery_phases.phase_4_detection import run_shift_detection

    already_shifted_result = await run_shift_detection(
        problem, domain, papers, results, citation_chase_result, thresholds, errors, abort_reasons
    )
    results["_already_shifted_result"] = already_shifted_result

    await _update_phase(job_id, "E: Sim", "Simulation & verification", 0.60)
    from src.pipeline.discovery_phases.phase_5_verification import run_verification_suite

    results = await run_verification_suite(problem, domain, results, errors, job_id=job_id)

    await _update_phase(job_id, "F: Dissertation", "Quality assessment", 0.75)
    from src.pipeline.discovery_phases.phase_6_quality import run_quality_and_output

    results = await run_quality_and_output(results, errors, abort_reasons)

    await _update_phase(job_id, "G: Quality", "Finalizing", 0.90)
    total_time = time.perf_counter() - start_total
    results["errors"] = errors
    results["total_time_seconds"] = round(total_time, 2)
    await _update_phase(job_id, "G: Quality", "Complete", 1.0)
    return results


async def flash_discovery(
    request: FlashRequest,
    *,
    job_id: str | None = None,
) -> dict[str, Any]:
    """Lightweight discovery: C4 -> TRIZ -> Knowledge -> 1 hypothesis."""
    import time

    start_total = time.perf_counter()
    problem = request.problem
    domain = request.domain
    errors: list[str] = []
    results: dict[str, Any] = {
        "problem": problem,
        "domain": domain,
        "pipeline_version": "v8.0-flash",
        "warnings": [],
    }

    await _update_phase(job_id, "A: Framing", "C4 navigation", 0.0)
    c4_path = navigate_c4(problem)
    results["c4_path"] = c4_path

    await _update_phase(job_id, "B: Search", "TRIZ principles", 0.20)
    triz_principles = resolve_triz(problem, domain)
    results["triz_principles"] = triz_principles

    await _update_phase(job_id, "C: Gaps", "Knowledge search", 0.40)
    papers = await search_knowledge(problem)
    results["papers"] = papers

    await _update_phase(job_id, "D: Hyps", "Hypothesis generation", 0.60)
    try:
        h = await generate_hypothesis(problem, c4_path, triz_principles, papers)
        results["hypothesis"] = h
    except Exception as e:
        errors.append(f"hypothesis: {e}")
        results["hypothesis"] = {"text": f"Failed: {e}", "source": "error"}

    await _update_phase(job_id, "G: Quality", "Finalizing", 0.90)
    results["errors"] = errors
    results["total_time_seconds"] = round(time.perf_counter() - start_total, 2)
    await _update_phase(job_id, "G: Quality", "Complete", 1.0)
    return results


async def multi_hypothesis_discovery(request: MultiHypothesisRequest) -> dict[str, Any]:
    problem = request.problem
    domain = request.domain
    count = max(1, min(request.count, 5))
    errors: list[str] = []
    start_total = time.perf_counter()
    c4_path = navigate_c4(problem)
    triz_principles = resolve_triz(problem, domain)
    papers = await search_knowledge(problem)
    hypotheses: list[dict[str, Any]] = []
    for i in range(count):
        try:
            h = await generate_hypothesis(
                problem=problem, c4_path=c4_path, triz_principles=triz_principles, papers=papers
            )
            h["index"] = i
            h["variant"] = f"variant_{i}"
            hypotheses.append(h)
        except Exception as e:
            errors.append(f"hypothesis[{i}]: {str(e)}")
            hypotheses.append(
                {
                    "index": i,
                    "variant": f"variant_{i}",
                    "source": "error",
                    "text": f"Failed: {str(e)}",
                    "error": str(e),
                }
            )

    # P2.5: Rank hypotheses before simulation using MCDM
    valid_hypotheses = [
        h for h in hypotheses if h.get("text") and "Failed" not in h.get("text", "")
    ]
    ranked: list[dict[str, Any]] = []
    try:
        from src.discovery.ranking.orchestrator import rank_hypotheses

        ranked_objs = await rank_hypotheses(
            valid_hypotheses,
            context={"literature": papers or [], "domain": domain},
            max_simulations=3,
        )
        ranked = [rh.hypothesis for rh in ranked_objs]
        # Preserve rank info on hypothesis dicts for response
        for _i, rh in enumerate(ranked_objs):
            rh.hypothesis["_rank_info"] = rh.to_dict()
    except Exception as e:
        logger.warning("rank_hypotheses failed, falling back to generation order: %s", e)
        errors.append(f"ranking: {str(e)}")
        ranked = valid_hypotheses

    # Run simulation only on top-ranked hypotheses (budget-aware)
    for h in ranked:
        try:
            sim = await asyncio.wait_for(
                run_relevant_simulation(domain, h),
                timeout=simulation_timeout_seconds(),
            )
            h["simulation"] = sim
        except TimeoutError:
            h["simulation"] = {"status": "timeout", "note": "exceeded time budget"}
            errors.append(f"simulation[{h.get('index')}]: timeout")
        except Exception as e:
            h["simulation"] = {"status": "error", "error": str(e)}
            errors.append(f"simulation[{h.get('index')}]: {str(e)}")

    # Novelty check for top-ranked hypotheses
    try:
        from src.novelty.validator import NoveltyValidator

        async with NoveltyValidator() as validator:
            for h in ranked:
                h_text = h.get("text", "")
                if h_text and "Failed" not in h_text:
                    h["novelty"] = await validator.check_novelty(h_text, domain)
                else:
                    h["novelty"] = {"status": "skipped", "reason": "no hypothesis text"}
    except ImportError:
        for h in ranked:
            h["novelty"] = {"status": "unchecked", "reason": "novelty module unavailable"}
    except Exception as e:
        logger.error("Novelty batch check error: %s", e)
        for h in ranked:
            h.setdefault("novelty", {"status": "unchecked", "reason": str(e)})

    # Build comparison view
    comparison: list[dict[str, Any]] = []
    for h in ranked:
        n = h.get("novelty", {})
        rank_info = h.get("_rank_info", {})
        comparison.append(
            {
                "variant": h.get("variant", "?"),
                "index": h.get("index", -1),
                "source": h.get("source", "?"),
                "score": rank_info.get("total_score", 0.0),
                "criteria_scores": rank_info.get("criteria_scores", {}),
                "cost_estimate": rank_info.get("cost_estimate", {}),
                "novel": n.get("novel"),
                "max_similarity": n.get("max_similarity"),
                "simulation_status": h.get("simulation", {}).get("status", "unknown"),
            }
        )

    best = ranked[0] if ranked else {}
    total_time = time.perf_counter() - start_total
    return {
        "problem": problem,
        "domain": domain,
        "pipeline_version": "v8.0",
        "hypotheses_count": count,
        "best_hypothesis": best,
        "c4_path": {
            "states": c4_path.get("states_visited", 0),
            "steps": c4_path.get("steps", 0),
            "operators": c4_path.get("operators", []),
        },
        "triz_principles": triz_principles[:5] if isinstance(triz_principles, list) else [],
        "ranked_hypotheses": comparison,
        "errors": errors,
        "total_time_seconds": round(total_time, 2),
        "status": "partial" if errors else "complete",
    }


async def dissertation_mode(request: DissertationRequest) -> dict[str, Any]:
    start_total = time.perf_counter()
    errors: list[str] = []
    attempts: list[dict] = []
    best_result = None
    best_score = -1.0
    current_problem = request.problem
    for iteration in range(1, request.max_iterations + 1):
        t_iter = time.perf_counter()
        try:
            discovery_result = await one_click_discovery(
                OneClickRequest(problem=current_problem, domain=request.domain)
            )
        except Exception as e:
            errors.append(f"Discovery failed (iteration {iteration}): {str(e)}")
            continue
        status = discovery_result.get("status", "error")
        abort_reasons = discovery_result.get("abort_reasons", [])
        gap_potential = discovery_result.get("gap_miner", {}).get("discovery_potential", 0)
        self_critique = discovery_result.get("self_critique", {})
        critique_rec = self_critique.get("recommendation", "?")
        novelty = discovery_result.get("novelty", {}).get(
            "novelty_score", discovery_result.get("novelty_check", {}).get("novelty_score", 0)
        )
        hypothesis = discovery_result.get("hypothesis", {})
        hyp_text = hypothesis.get("text", "")[:300]
        quality = (
            gap_potential * 0.3
            + novelty * 0.3
            + (0.7 if critique_rec in ("PUBLISH", "NEEDS_MORE_EVIDENCE") else 0.2) * 0.4
        )
        attempt = {
            "iteration": iteration,
            "status": status,
            "gap_potential": gap_potential,
            "novelty": round(novelty, 3),
            "critique_recommendation": critique_rec,
            "quality_score": round(quality, 3),
            "abort_reasons": abort_reasons,
            "hypothesis": hyp_text,
            "time_seconds": round(time.perf_counter() - t_iter, 1),
        }
        attempts.append(attempt)
        if quality > best_score:
            best_score = quality
            best_result = discovery_result
        gates_passed = (
            status != "aborted"
            and gap_potential >= 0.3
            and (critique_rec in ("PUBLISH", "NEEDS_MORE_EVIDENCE"))
        )
        if gates_passed:
            dissertation = _build_dissertation(best_result or discovery_result, attempts)
            dissertation["total_attempts"] = iteration
            dissertation["total_time"] = round(time.perf_counter() - start_total, 2)
            dissertation["status"] = "dissertation_complete"
            try:
                from src.export.manager import ExportManager

                export_dir = Path("discovery/batch_v5/exports")
                export_dir.mkdir(parents=True, exist_ok=True)
                ExportManager(str(export_dir))
                exports: dict[str, str] = {}
                safe_slug = re.sub(r"[^a-zA-Z0-9_-]", "_", request.problem[:50].lower())
                # Avoid Windows reserved names
                reserved = {
                    "con",
                    "prn",
                    "aux",
                    "nul",
                    "com1",
                    "com2",
                    "com3",
                    "com4",
                    "com5",
                    "com6",
                    "com7",
                    "com8",
                    "com9",
                    "lpt1",
                    "lpt2",
                    "lpt3",
                    "lpt4",
                    "lpt5",
                    "lpt6",
                    "lpt7",
                    "lpt8",
                    "lpt9",
                }
                if safe_slug.lower() in reserved:
                    safe_slug = f"_{safe_slug}"
                try:
                    md_file = export_dir / f"{safe_slug}.md"
                    md_file.write_text(
                        f"# {dissertation.get('title', 'Untitled')}\n\n## Abstract\n{dissertation.get('abstract', '')}\n\n## Hypothesis\n{discovery_result.get('hypothesis', {}).get('text', '')}\n\nGenerated by C4-CDI-Turbo v8.2 | Citation: Selyutin I., Kovalev N.I. (2026)\n",
                        encoding="utf-8",
                    )
                    exports["markdown"] = str(md_file)
                except OSError:
                    exports["markdown"] = "failed"
                try:
                    json_file = export_dir / f"{safe_slug}.json"
                    json_file.write_text(
                        json.dumps(discovery_result, indent=2, ensure_ascii=False), encoding="utf-8"
                    )
                    exports["json"] = str(json_file)
                except (OSError, TypeError, ValueError):
                    exports["json"] = "failed"
                try:
                    vrf_file = export_dir / f"{safe_slug}_verification.txt"
                    vrf_content = (
                        f"Verification: {discovery_result.get('verification_summary', 'N/A')}\n"
                    )
                    for prover, pv in discovery_result.get("verification", {}).items():
                        vrf_content += f"  {prover}: {pv.get('verified', False)}\n"
                    vrf_file.write_text(vrf_content, encoding="utf-8")
                    exports["verification"] = str(vrf_file)
                except OSError:
                    exports["verification"] = "failed"
            except (ImportError, ModuleNotFoundError, OSError) as e:
                exports = {"error": str(e)[:200]}
            dissertation["exports"] = exports
            return dissertation
        if iteration < request.max_iterations:
            try:
                refine_prompt = f"Iteration {iteration}/{request.max_iterations}. Current hypothesis rejected. Reasons: {'; '.join(abort_reasons[:2])}. Critique: {critique_rec}. Refine the research question to find a genuine unexplored angle. Original problem: {request.problem[:300]}. Current: {current_problem[:300]}. Output ONLY a new one-sentence problem statement."
                refined = await get_gateway().chat(
                    [{"role": "user", "content": refine_prompt}], temperature=0.7, max_tokens=200
                )
                if refined and len(refined) > 20:
                    current_problem = refined.strip()
                else:
                    strategies = [
                        lambda p: f"What is the mechanistic basis of {p}?",
                        lambda p: f"How does {p} vary across scales (molecular to ecological)?",
                        lambda p: f"What is the evolutionary origin of {p}?",
                        lambda p: f"How can we computationally model {p} to predict outcomes?",
                        lambda p: f"What overlooked variable explains contradictions in {p}?",
                    ]
                    current_problem = strategies[(iteration - 1) % len(strategies)](request.problem)
            except (ImportError, ModuleNotFoundError, RuntimeError, OSError):
                current_problem = (
                    f"New perspective on {request.problem[:100]}: iteration {iteration}"
                )
    return {
        "status": "dissertation_failed",
        "message": f"Unable to find publishable hypothesis after {request.max_iterations} iterations. Best quality: {best_score:.2f}",
        "attempts": attempts,
        "best_result": best_result,
        "total_time_seconds": round(time.perf_counter() - start_total, 2),
    }
