"""Phase 6: Quality and Output — Falsifier, gate re-evaluation, consensus meter,
empirical validation, quality evaluation, dissertation generation, self-critique, export.
"""
from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger("c4_cdi_turbo.pipeline.discovery.phase6")


async def run_quality_and_output(results, errors, abort_reasons) -> dict:
    """Run quality and output."""
    import time

    from src.api.v8_routers.discovery.pipeline import (
        _refine_hypothesis_llm,
        _run_self_critique,
        generate_paper,
        run_consensus_meter,
        run_empirical_validation,
    )

    domain = results["domain"]
    problem = results["problem"]
    thresholds = results["_thresholds"]
    papers = results.get("_papers_list", [])
    papers_found = results.get("_papers_found", 0)
    sources_used = results.get("_sources_used", 0)
    citation_chase_result = results.get("_citation_chase_result", {})
    already_shifted_result = results.get("_already_shifted_result", {})
    gap_potential = results.get("_gap_potential", 0)

    hypothesis_text = results.get("hypothesis", {}).get("text", "")
    try:
        from src.discovery.falsifier import Falsifier
        f = Falsifier()
        falsify = f.check(hypothesis_text, domain)
        results["falsifier"] = falsify
        if not falsify.falsifiable:
            results["warnings"].append(f"Falsifier REJECT: {falsify.recommendation[:200]}")
    except Exception as e:
        results["falsifier"] = {"error": str(e)}
    t_cm = time.perf_counter()
    try:
        results["consensus_meter"] = run_consensus_meter(results.get("hypothesis", {}), papers)
    except Exception as e:
        results["consensus_meter"] = {"error": str(e)}
        errors.append(f"consensus_meter: {str(e)}")
    logger.info("Consensus meter: %.3fs", time.perf_counter() - t_cm)
    t_emp = time.perf_counter()
    try:
        results["empirical_validation"] = run_empirical_validation(problem, results.get("c4_path", {}))
    except Exception as e:
        results["empirical_validation"] = {"error": str(e)}
        errors.append(f"empirical_validation: {str(e)}")
    logger.info("Empirical validation: %.3fs", time.perf_counter() - t_emp)
    hypothesis_text = results.get("hypothesis", {}).get("text", "")
    t_verify = time.perf_counter()
    verification_results: dict[str, object] = {}
    from src.verification.llm_prover import LLMProver

    prover = LLMProver()
    for lang in ("lean4", "coq", "dafny", "agda", "z3", "hoare"):
        try:
            result = await prover.prove(hypothesis_text[:500], lang, max_iterations=3)
            verification_results[lang] = {
                "verified": result.valid,
                "iterations": len(result.iterations),
                "time_ms": round(result.total_time_ms, 1),
                "proof": result.proof[:300] if result.proof else "",
                "error": result.error[:200] if result.error else None,
            }
            logger.info(
                "LLM proof %s for %s: %s (%d iters, %.1fms)",
                "SUCCEEDED" if result.valid else "FAILED",
                lang,
                hypothesis_text[:50],
                len(result.iterations),
                result.total_time_ms,
            )
        except Exception as e:
            verification_results[lang] = {"verified": False, "error": str(e)[:200]}
    results["verification"] = verification_results
    verified_count = sum(1 for v in verification_results.values() if isinstance(v, dict) and v.get("verified"))
    results["verification_summary"] = f"{verified_count}/{len(verification_results)} provers passed"
    logger.info("Formal verification: %d/6 passed in %.3fs", verified_count, time.perf_counter() - t_verify)
    try:
        paper_parts = generate_paper(hypothesis=results.get("hypothesis", {}), papers=papers if isinstance(papers, list) else [], proof=results.get("proof", {}))
        results["paper"] = {"latex_length": len(paper_parts.get("latex", "")), "references": paper_parts.get("reference_count", 0), "bibtex": paper_parts.get("bibtex", "")}
    except Exception as e:
        results["paper"] = {"latex_length": 0, "references": 0, "error": str(e)}
        errors.append(f"paper: {str(e)}")
    self_critique_result: dict[str, object] = {}
    hypothesis_text = results.get("hypothesis", {}).get("text", "")
    novelty_result = results.get("novelty", {})
    if thresholds.get("require_self_critique") and hypothesis_text:
        try:
            self_critique_result = await _run_self_critique(hypothesis_text, papers[:10], novelty_result.to_dict() if hasattr(novelty_result, 'to_dict') else novelty_result)
            if self_critique_result.get("recommendation") == "REJECT":
                abort_reasons.append(f"SELF_CRITIQUE_REJECT: {self_critique_result.get('explanation', 'No explanation')}")
        except Exception as e:
            self_critique_result = {"error": str(e)}
    max_iterations = 3
    iteration = 0
    refinement_history: list[dict[str, object]] = []
    abort_reasons_all: list[str] = list(abort_reasons)
    papers_found_all: list[int] = [papers_found]
    sources_used_all: list[int] = [sources_used]
    while abort_reasons and iteration < max_iterations:
        iteration += 1
        refinement_history.append({"iteration": iteration, "hypothesis": hypothesis_text[:300], "abort_reasons": list(abort_reasons), "gap_miner_score": gap_potential, "papers_found": papers_found})
        competing_hypotheses_data = results.get("competing_hypotheses", [])
        competing_texts = [h.get("text", "")[:200] for h in competing_hypotheses_data]
        refined = await _refine_hypothesis_llm(problem=problem, hypothesis=hypothesis_text, abort_reasons=abort_reasons, top_papers=papers[:15] if isinstance(papers, list) else [], iteration=iteration, max_iterations=max_iterations, competing_hypotheses=competing_texts)
        if refined.get("no_improvement"):
            break
        new_hypothesis = refined.get("refined_hypothesis", hypothesis_text)
        new_problem = refined.get("refined_problem", problem)
        try:
            from src.knowledge.orchestrator import MultiSourceSearcher
            multi2 = MultiSourceSearcher(sources={'semantic_scholar', 'openalex', 'crossref', 'arxiv', 'pubmed', 'europe_pmc'})
            search_result2 = await multi2.search_all(new_problem, domain)
            if search_result2 is not None:
                papers = search_result2.get("papers", papers)
                papers_found = search_result2.get("total_papers", papers_found)
                sources_used = search_result2.get("sources_used", sources_used)
            papers_found_all.append(papers_found)
            sources_used_all.append(sources_used)
        except (ImportError, ModuleNotFoundError, RuntimeError, OSError) as e:
            logger.debug("MultiSourceSearcher unavailable in refinement: %s", e)
        try:
            from src.discovery.gap_miner import GapMiner
            gm2 = GapMiner()
            gm2_result = await gm2.mine_for_discovery(new_problem, papers[:30] if isinstance(papers, list) else [])
            gap_potential = gm2_result.get("discovery_potential", gap_potential)
        except (ImportError, ModuleNotFoundError, RuntimeError, OSError) as e:
            logger.debug("GapMiner unavailable in refinement: %s", e)
        hypothesis_text = new_hypothesis
        recheck_result: dict[str, Any] | None = None
        try:
            from src.discovery.already_shifted import AlreadyShiftedDetector
            shift_detector_loop = AlreadyShiftedDetector()
            recheck_result = await shift_detector_loop.check(
                hypothesis=hypothesis_text,
                papers=papers[:100] if isinstance(papers, list) else [],
                citation_timeline=citation_chase_result.get("timeline", []),
                domain=domain,
            )
        except TimeoutError:
            logger.warning("shift_detector.check timed out after 15s")
        except ImportError as e:
            logger.debug("AlreadyShiftedDetector unavailable: %s", e)
        if recheck_result is not None and recheck_result.get("already_shifted"):
            abort_reasons[:] = [
                f"ALREADY_SHIFTED(iter{iteration}): {recheck_result.get('verdict', 'ALREADY_SHIFTED')}. "
                f"Seminal: {[p['title'][:60] for p in recheck_result.get('seminal_papers', [])[:2]]}. "
                f"Consensus: {recheck_result.get('consensus_level', 0):.0%}."
            ]
            try:
                from src.discovery.paradigm_shift import detect_paradigm_shift  # type: ignore[attr-defined]
                ps_result = detect_paradigm_shift(papers, domain)  # type: ignore[attr-defined]
                results["paradigm_shift"] = ps_result
                shift_entry = dict(refinement_history[-1]) if refinement_history else {}
                shift_entry.update({"paradigm_shift_rechecked": True, "ps_probability": ps_result.get("probability")})
                refinement_history.append(shift_entry)
            except Exception:
                logger.exception("paradigm_shift detection in refinement loop failed")
            break
        elif recheck_result is not None:
            abort_reasons = [r for r in abort_reasons if "ALREADY_SHIFTED" not in r]
            # P0.3: Domain stability check after LLM refinement
            original_words = set(problem.lower().split())
            refined_words = set(new_problem.lower().split())
            all_words = original_words | refined_words
            if all_words:
                domain_similarity = len(original_words & refined_words) / len(all_words)
                if domain_similarity < 0.3:
                    logger.warning("Domain drift detected: similarity=%.2f between '%s' and '%s'", domain_similarity, problem[:50], new_problem[:50])
                    results["domain_drift"] = {"similarity": round(domain_similarity, 3), "original": problem, "refined": new_problem}
                refinement_history.append({
                    "iteration": iteration, "domain_similarity": round(domain_similarity, 3),
                } if refinement_history else {"iteration": iteration, "domain_similarity": round(domain_similarity, 3)})
            # P0.2: Re-run FalsificationEngine on refined hypothesis
            try:
                from src.discovery.falsification import FalsificationEngine
                engine = FalsificationEngine()
                refined_hypothesis_dict = results.get("hypothesis", {}).copy() if isinstance(results.get("hypothesis"), dict) else {}
                refined_hypothesis_dict["text"] = hypothesis_text
                falsification_result = engine.check_falsifiability(refined_hypothesis_dict["text"])
                results[f"falsification_iter{iteration}"] = falsification_result
                is_falsifiable, reason = falsification_result
                if not is_falsifiable:
                    abort_reasons.append(f"NOT_FALSIFIABLE(iter{iteration}): {reason}")
                logger.info("Falsification re-checked: iter=%d, falsifiable=%s", iteration, is_falsifiable)
            except Exception:
                logger.exception("falsification re-check in refinement loop failed")
            # P0.2: Re-run SelfCritique on refined hypothesis
            try:
                critique = await _run_self_critique(hypothesis_text, papers[:10] if isinstance(papers, list) else [], novelty_result if isinstance(novelty_result, dict) else {})
                results[f"self_critique_iter{iteration}"] = critique
                if critique.get("verdict") == "REJECT":
                    abort_reasons.append(f"SELF_CRITIQUE_REJECT(iter{iteration}): {critique.get('rationale', '')[:120]}")
                logger.info("SelfCritique re-checked: iter=%d, verdict=%s", iteration, critique.get("verdict"))
            except Exception:
                logger.exception("self_critique re-check in refinement loop failed")
        if gap_potential < thresholds["min_gap_miner_potential"]:
            reason = f"LOW_DISCOVERY_POTENTIAL(iter{iteration}): GapMiner score = {gap_potential:.2f} (minimum {thresholds['min_gap_miner_potential']})."
            if not any("LOW_DISCOVERY_POTENTIAL" in r for r in abort_reasons):
                abort_reasons.append(reason)
        if papers_found < thresholds["min_papers_for_discovery"]:
            reason = f"INSUFFICIENT_DATA(iter{iteration}): Found only {papers_found} papers."
            if not any("INSUFFICIENT_DATA" in r for r in abort_reasons):
                abort_reasons.append(reason)
    if abort_reasons:
        results["status"] = "aborted"
        results["abort_reasons"] = abort_reasons
        results["abort_reasons_original"] = abort_reasons_all
        results["abort_type"] = abort_reasons[0].split(":")[0]
        results["refinement_iterations"] = iteration
        results["refinement_history"] = refinement_history
        results["warning"] = f"DISCOVERY ABORTED after {iteration} refinement attempts. System detected insufficient evidence to claim discovery. See abort_reasons and refinement_history for details."
    if results.get("status") != "aborted":
        results["status"] = "partial" if errors else "complete"
    results.update({"pipeline_version": "8.2", "thresholds_applied": thresholds, "abort_reasons": abort_reasons, "abort_type": abort_reasons[0].split(":")[0] if abort_reasons else None, "papers_expanded": len(papers) if isinstance(papers, list) else 0, "multi_source_search": {"papers_found": papers_found, "sources_used": sources_used}, "citation_chase": citation_chase_result, "already_shifted": already_shifted_result, "self_critique": self_critique_result, "gap_miner_gate_passed": gap_potential >= thresholds["min_gap_miner_potential"]})
    return results
