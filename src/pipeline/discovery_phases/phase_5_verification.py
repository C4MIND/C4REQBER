"""Phase 5: Verification Suite — Simulation, Monte Carlo, Bayesian averaging,
Dempster-Shafer, Bayesian conjugate, causal do-calculus, counterfactual, proof generation.
"""
from __future__ import annotations

import logging


logger = logging.getLogger("c4_cdi_turbo.pipeline.discovery.phase5")


async def run_verification_suite(problem, domain, results, errors) -> dict:
    """Run verification suite."""
    import asyncio
    import time

    from src.discovery.pipeline_logic import (
        generate_lean4_proof,
        run_bayesian_conjugate_update,
        run_bayesian_model_averaging,
        run_causal_do_calculus,
        run_counterfactual,
        run_dempster_shafer,
        run_relevant_simulation,
    )

    try:
        hypothesis_for_sim = results.get("hypothesis", {})
        simulation = await asyncio.wait_for(run_relevant_simulation(domain, hypothesis_for_sim), timeout=2.0)
        results["simulation"] = simulation
    except TimeoutError:
        results["simulation"] = {"status": "timeout", "note": "Simulation exceeded time budget", "domain": domain}
        errors.append("simulation: timeout")
    except Exception as e:
        results["simulation"] = {"status": "error", "error": str(e), "domain": domain}
        errors.append(f"simulation: {str(e)}")
    try:
        from src.validation.monte_carlo import MonteCarloValidator
        mc = MonteCarloValidator(trials=100)
        mc_result = mc.validate(hypothesis_metrics={'mean': results.get('accuracy', 0.78)}, baseline_metrics={'mean': 0.45, 'std': 0.1})
        results["monte_carlo"] = mc_result
    except Exception as e:
        results["monte_carlo"] = {"error": str(e)}
    t_bma = time.perf_counter()
    try:
        results["bayesian_averaging"] = run_bayesian_model_averaging(results.get("hypothesis", {}), results.get("monte_carlo", {}))
    except Exception as e:
        results["bayesian_averaging"] = {"error": str(e)}
        errors.append(f"bayesian_averaging: {str(e)}")
    logger.info("Bayesian averaging: %.3fs", time.perf_counter() - t_bma)
    t_ds = time.perf_counter()
    try:
        results["dempster_shafer"] = run_dempster_shafer(results.get("hypothesis", {}), results.get("_papers_list", []))
    except Exception as e:
        results["dempster_shafer"] = {"error": str(e)}
        errors.append(f"dempster_shafer: {str(e)}")
    logger.info("Dempster-Shafer: %.3fs", time.perf_counter() - t_ds)
    t_bayes = time.perf_counter()
    try:
        results["bayesian_conjugate"] = run_bayesian_conjugate_update(results.get("monte_carlo", {}))
    except Exception as e:
        results["bayesian_conjugate"] = {"error": str(e)}
        errors.append(f"bayesian_conjugate: {str(e)}")
    logger.info("Bayesian conjugate: %.3fs", time.perf_counter() - t_bayes)
    t_causal = time.perf_counter()
    try:
        results["causal_do_calculus"] = run_causal_do_calculus(problem, domain)
    except Exception as e:
        results["causal_do_calculus"] = {"error": str(e)}
        errors.append(f"causal_do_calculus: {str(e)}")
    logger.info("Causal do-calculus: %.3fs", time.perf_counter() - t_causal)
    t_cf = time.perf_counter()
    try:
        results["counterfactual"] = run_counterfactual(results.get("hypothesis", {}), domain)
    except Exception as e:
        results["counterfactual"] = {"error": str(e)}
        errors.append(f"counterfactual: {str(e)}")
    logger.info("Counterfactual: %.3fs", time.perf_counter() - t_cf)
    try:
        hypothesis_for_proof = results.get("hypothesis", {})
        import asyncio
        proof = await asyncio.wait_for(generate_lean4_proof(hypothesis_for_proof), timeout=60.0)
        results["proof"] = proof
    except TimeoutError:
        results["proof"] = {"generated": False, "error": "Proof generation timed out after 60s"}
        errors.append("proof: timed out after 60s")
    except Exception as e:
        results["proof"] = {"generated": False, "error": str(e)}
        errors.append(f"proof: {str(e)}")
    return results
