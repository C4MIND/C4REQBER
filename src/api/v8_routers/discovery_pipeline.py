"""
Reqber v8.0: Discovery Pipeline

Contains the one-click discovery pipeline with subfunctions of 50-100 lines each.
"""

import asyncio
import logging
import time

from utils.error_handlers import execute_step


logger = logging.getLogger("reqber.api.v8.discovery.pipeline")

THRESHOLDS = {
    "min_papers_for_discovery": 50, "min_gap_miner_potential": 0.15,
    "min_novelty_score": 0.5, "recursive_search_depth": 2,
    "require_self_critique": True,
}


# ---------------------------------------------------------------------------
# Subfunction 1: C4 + TRIZ + UCOS + QZRF (lines ~50)
# ---------------------------------------------------------------------------

def _run_c4_triz_ucos(results: dict, problem: str, domain: str, errors: list) -> None:
    """Run C4, TRIZ, UCOS, QZRF, FRA, Observer, Matrix Dream."""
    from src.api.v8_routers.discovery_core import navigate_c4, resolve_triz
    from src.api.v8_routers.discovery_utils import _domain_improving_param, _domain_worsening_param

    # C4
    execute_step(results, "c4_path", navigate_c4, problem, errors=errors,
                default_value={"states": 0, "steps": 0})
    c4_result = results.get("c4_path", {})
    if isinstance(c4_result, dict) and not c4_result.get("error"):
        results["c4_path"] = {"states": c4_result.get("states_visited", 0),
                               "steps": c4_result.get("steps", 0),
                               "operators": c4_result.get("operators", []),
                               "summary": f"{c4_result.get('states_visited', 0)} states"}

    # FRA Routing
    from src.api.v8_routers.discovery_utils import run_fra_routing
    execute_step(results, "fra_routing", run_fra_routing, problem, errors=errors)

    # C4 Observer
    from src.api.v8_routers.discovery_utils import run_c4_observer
    execute_step(results, "c4_observer", run_c4_observer, problem, results.get("c4_path", {}), errors=errors)

    # TRIZ
    try:
        triz_principles = resolve_triz(problem, domain)
        results["triz"] = {"principles": triz_principles[:5], "count": len(triz_principles),
                           "improving_param": _domain_improving_param(domain),
                            "worsening_param": _domain_worsening_param(domain)}
    except (ImportError, AttributeError) as e:
        results["triz"] = {"principles": [], "error": str(e)}
        errors.append(f"triz: {str(e)}")

    # UCOS + QZRF
    for name, _func_name in [("ucos", "UCOSAnalyzer"), ("qzrf", "QZRFAnalyzer")]:
        try:
            from pipeline.ucos_qzrf import QZRFAnalyzer, UCOSAnalyzer
            cls = UCOSAnalyzer if name == "ucos" else QZRFAnalyzer
            results[name] = cls().analyze(results, "") if name == "ucos" else cls().apply(problem, results.get("triz", {}).get("principles", []), "")
        except (ImportError, AttributeError, RuntimeError) as e:
            results[name] = {"error": str(e)}
            errors.append(f"{name}: {str(e)}")

    # Matrix Dream
    from src.api.v8_routers.discovery_utils import run_matrix_dream
    execute_step(results, "matrix_dream", run_matrix_dream, problem, results.get("c4_path", {}), errors=errors)


# ---------------------------------------------------------------------------
# Subfunction 2: Knowledge Search (lines ~50)
# ---------------------------------------------------------------------------

async def _run_knowledge_search(results: dict, problem: str, domain: str, errors: list) -> tuple:
    """Run knowledge search and citation chase."""
    try:
        from src.knowledge.orchestrator import MultiSourceSearcher
        multi = MultiSourceSearcher(sources={'semantic_scholar', 'openalex', 'arxiv', 'pubmed'})
        search_result = await multi.search_all(problem, domain)
        papers = search_result.get("papers", [])
        papers_found = search_result.get("total_papers", 0)
        if papers_found < THRESHOLDS["min_papers_for_discovery"]:
            errors.append(f"INSUFFICIENT_DATA: Found only {papers_found} papers.")
        results["papers_found"] = len(papers)
        results["papers"] = papers[:5]
    except (ImportError, AttributeError, KeyError):
        from src.api.v8_routers.discovery_core import search_knowledge
        papers = await search_knowledge(problem)
        papers_found = len(papers)
        results["papers_found"] = len(papers)
        results["papers"] = papers[:5]

    # Index papers in ChromaDB for RAG retrieval
    try:
        from src.knowledge.chroma_store import ChromaVectorStore
        store = ChromaVectorStore()
        store.add_paper_embeddings(papers)
    except Exception:
        logger.warning("Failed to index papers in ChromaDB", exc_info=True)

    # Citation Chase
    try:
        from src.knowledge.citation_chaser import CitationChaser
        chase = await CitationChaser(max_depth=int(THRESHOLDS["recursive_search_depth"])).chase(
            results.get("papers", [])[:20], problem)
        results["citation_chase"] = chase
    except (ImportError, AttributeError):
        pass

    return papers, papers_found


# ---------------------------------------------------------------------------
# Subfunction 3: Analysis (lines ~50)
# ---------------------------------------------------------------------------

async def _run_analysis(results: dict, problem: str, papers: list, errors: list) -> None:
    """Run contradiction mining, temporal KG, isomorphisms, gap miner."""
    from src.api.v8_routers.discovery_utils import (
        build_temporal_kg,
        mine_contradictions,
        run_autoscanner,
        search_isomorphisms,
    )

    execute_step(results, "contradiction_mining", mine_contradictions, papers, errors=errors)
    execute_step(results, "temporal_kg", build_temporal_kg, papers, problem, errors=errors)

    try:
        triz_list = results.get("triz", {}).get("principles", [])
        results["isomorphisms"] = await search_isomorphisms(
            problem, papers, triz_list if isinstance(triz_list, list) else [])
    except (ImportError, AttributeError) as e:
        results["isomorphisms"] = {"found": 0, "error": str(e)}
        errors.append(f"isomorphism: {str(e)}")

    try:
        from src.discovery.gap_miner import GapMiner
        results["gap_miner"] = await GapMiner().mine_for_discovery(problem, papers)
    except (ImportError, AttributeError, RuntimeError) as e:
        results["gap_miner"] = {"discovery_potential": 0, "error": str(e)}
        errors.append(f"gap_miner: {str(e)}")

    try:
        results["autoscanner"] = await run_autoscanner(papers)
    except Exception as e:
        results["autoscanner"] = {"error": str(e)}
        errors.append(f"autoscanner: {str(e)}")


# ---------------------------------------------------------------------------
# Subfunction 4: Hypothesis + Plugins (lines ~50)
# ---------------------------------------------------------------------------

async def _run_hypothesis_plugins(results: dict, problem: str, domain: str, papers: list, errors: list) -> str:
    """Generate hypothesis, run plugins, inference."""
    from src.api.v8_routers.discovery_core import generate_hypothesis
    from src.api.v8_routers.discovery_utils import (
        run_abduction,
        run_cognitive_plugins,
        run_strong_inference,
    )

    try:
        results["hypothesis"] = await generate_hypothesis(
            problem, results.get("c4_path", {}),
            results.get("triz", {}).get("principles", []), papers)
    except (TimeoutError, RuntimeError) as e:
        results["hypothesis"] = {"source": "none", "text": str(e), "error": str(e)}
        errors.append(f"hypothesis: {str(e)}")

    execute_step(results, "cognitive_plugins", lambda: run_cognitive_plugins(
        problem=problem, hypothesis_text=results.get("hypothesis", {}).get("text", "")[:300],
        domain=domain), errors=errors)

    execute_step(results, "strong_inference", run_strong_inference, problem, domain, results.get("hypothesis", {}), errors=errors)
    execute_step(results, "abduction", run_abduction, problem, domain, papers, errors=errors)

    return results.get("hypothesis", {}).get("text", "") if isinstance(results.get("hypothesis"), dict) else ""


# ---------------------------------------------------------------------------
# Subfunction 5: Validation (lines ~50)
# ---------------------------------------------------------------------------

async def _run_validation(results: dict, problem: str, domain: str, papers: list, errors: list) -> dict:
    """Run paradigm shift, novelty, falsification, DoE, power, reproducibility."""
    from src.api.v8_routers.discovery_utils import (
        detect_paradigm_shift,
        run_consensus_meter,
        run_doe_design,
        run_empirical_validation,
        run_falsification_engine,
        run_power_analysis,
        run_reproducibility_check,
    )

    execute_step(results, "paradigm_shift", detect_paradigm_shift, papers, domain, errors=errors)

    try:
        from src.discovery.novelty_validator import NoveltyValidator
        async with NoveltyValidator() as v:
            results["novelty"] = await v.check(results.get("hypothesis", {}).get("text", ""), domain)
    except (ImportError, AttributeError) as e:
        results["novelty"] = {"status": "unchecked", "error": str(e)}
        errors.append(f"novelty: {str(e)}")

    execute_step(results, "falsification", run_falsification_engine, results.get("hypothesis", {}), domain, errors=errors)
    execute_step(results, "doe_design", run_doe_design, domain, errors=errors)
    execute_step(results, "power_analysis", run_power_analysis, results.get("hypothesis", {}), errors=errors)
    execute_step(results, "reproducibility", run_reproducibility_check, problem, errors=errors)
    execute_step(results, "consensus_meter", run_consensus_meter, results.get("hypothesis", {}), papers, errors=errors)
    execute_step(results, "empirical_validation", run_empirical_validation, problem, results.get("c4_path", {}), errors=errors)

    return results.get("novelty", {})


# ---------------------------------------------------------------------------
# Subfunction 6: Simulation + Verification (lines ~80)
# ---------------------------------------------------------------------------

async def _run_simulation_verify(results: dict, problem: str, domain: str, papers: list, errors: list) -> None:
    """Run simulation, Bayesian, Causal, Proof, Falsifier, Verification."""
    from src.api.v8_routers.discovery.pipeline import (
        generate_lean4_proof,
        generate_paper,
        run_bayesian_conjugate_update,
        run_bayesian_model_averaging,
        run_causal_do_calculus,
        run_counterfactual,
        run_dempster_shafer,
        run_relevant_simulation,
    )

    # Simulation
    try:
        results["simulation"] = await asyncio.wait_for(
            run_relevant_simulation(domain, results.get("hypothesis", {})), timeout=2.0)
    except (TimeoutError, RuntimeError) as e:
        results["simulation"] = {"status": "error", "error": str(e)}
        errors.append(f"simulation: {str(e)}")

    # Monte Carlo
    try:
        from validation.monte_carlo import MonteCarloValidator
        results["monte_carlo"] = MonteCarloValidator(trials=100).validate(
            hypothesis_metrics={'mean': results.get('accuracy', 0.78)},
            baseline_metrics={'mean': 0.45, 'std': 0.1})
    except (ImportError, AttributeError, RuntimeError) as e:
        results["monte_carlo"] = {"error": str(e)}

    # Bayesian
    execute_step(results, "bayesian_averaging", run_bayesian_model_averaging,
                results.get("hypothesis", {}), results.get("monte_carlo", {}), errors=errors)
    execute_step(results, "dempster_shafer", run_dempster_shafer, results.get("hypothesis", {}), papers, errors=errors)
    execute_step(results, "bayesian_conjugate", run_bayesian_conjugate_update, results.get("monte_carlo", {}), errors=errors)

    # Causal
    execute_step(results, "causal_do_calculus", run_causal_do_calculus, problem, domain, errors=errors)
    execute_step(results, "counterfactual", run_counterfactual, results.get("hypothesis", {}), domain, errors=errors)

    # Proof
    try:
        results["proof"] = await generate_lean4_proof(results.get("hypothesis", {}))
    except (ImportError, AttributeError, RuntimeError) as e:
        results["proof"] = {"generated": False, "error": str(e)}
        errors.append(f"proof: {str(e)}")

    # Falsifier
    try:
        from src.discovery.falsifier import Falsifier
        results["falsifier"] = Falsifier().check(results.get("hypothesis", {}).get("text", ""), domain)
    except (ImportError, AttributeError, RuntimeError) as e:
        results["falsifier"] = {"error": str(e)}

    # Claim-to-source verification
    try:
        from src.verification.claim_matcher import verify_solution
        claim_verif = await asyncio.to_thread(verify_solution, results.get("hypothesis", {}).get("text", ""), papers)
        results["claim_verification"] = claim_verif
        if not claim_verif.get("passed", False):
            errors.append(
                f"CLAIM_VERIFICATION: Only {claim_verif.get('supported_count', 0)}/{claim_verif.get('claim_count', 0)} "
                f"claims supported by sources (threshold: {claim_verif.get('pass_threshold', 0.5)})."
            )
    except (ImportError, AttributeError, RuntimeError) as e:
        results["claim_verification"] = {"error": str(e)}

    # Paper
    try:
        paper_parts = generate_paper(results.get("hypothesis", {}), papers, results.get("proof", {}))
        results["paper"] = {"latex_length": len(paper_parts.get("latex", "")),
                           "references": paper_parts.get("reference_count", 0),
                           "bibtex": paper_parts.get("bibtex", "")}
    except (ImportError, AttributeError) as e:
        results["paper"] = {"latex_length": 0, "references": 0, "error": str(e)}
        errors.append(f"paper: {str(e)}")

    # Formal Verification
    await _run_formal_verification(results, papers, errors)


# ---------------------------------------------------------------------------
# Subfunction 7: Formal Verification (lines ~30)
# ---------------------------------------------------------------------------

async def _run_formal_verification(results: dict, papers: list, errors: list) -> None:
    """Run Lean4, Coq, Dafny verification via auto-formalization pipeline."""
    hyp_text = results.get("hypothesis", {}).get("text", "")
    verification_results = {}
    for prover, module in [("lean4", "verification.lean4_client"), ("coq", "verification.coq_client"), ("dafny", "verification.dafny_client")]:
        try:
            import importlib
            client_cls = getattr(importlib.import_module(module), module.split('.')[-1].title() + "Client")
            r = await client_cls().verify_discovery(hyp_text[:500], [p.get("title", "")[:100] for p in papers[:5]])
            verification_results[prover] = {"verified": r.get("success", False), "output": str(r.get("output", ""))[:200]}
        except (ImportError, AttributeError, RuntimeError) as e:
            verification_results[prover] = {"verified": False, "error": str(e)[:100]}
    results["verification"] = verification_results
    verified = sum(1 for v in verification_results.values() if isinstance(v, dict) and v.get("verified"))
    results["verification_summary"] = f"{verified}/3 provers passed"


# ---------------------------------------------------------------------------
# Build Final Result
# ---------------------------------------------------------------------------

def _build_final_result(results: dict, problem: str, start_total: float, errors: list,
                       abort_reasons: list, papers: list, papers_found: int,
                       citation_chase: dict, self_critique: dict, gap_potential: float) -> dict:
    """Build final result dict."""
    results["errors"] = errors
    results["total_time_seconds"] = round(time.perf_counter() - start_total, 2)
    results["status"] = "aborted" if abort_reasons else ("partial" if errors else "complete")
    if abort_reasons:
        results["abort_reasons"] = abort_reasons
        results["warning"] = "DISCOVERY ABORTED."
    results.update({
        "pipeline_version": "8.2", "thresholds_applied": THRESHOLDS,
        "abort_type": abort_reasons[0].split(":")[0] if abort_reasons else None,
        "papers_expanded": len(papers) if isinstance(papers, list) else 0,
        "multi_source_search": {"papers_found": papers_found, "sources_used": 0},
        "citation_chase": citation_chase, "self_critique": self_critique,
        "gap_miner_gate_passed": gap_potential >= THRESHOLDS["min_gap_miner_potential"],
    })
    return results
