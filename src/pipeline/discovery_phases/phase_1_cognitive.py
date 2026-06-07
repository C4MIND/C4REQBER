"""Phase 1: Cognitive Framing — C4 navigation, FRA routing, C4 observer,
TRIZ contradiction resolution, UCOS analysis, QZRF operators, Matrix Dream.
"""
from __future__ import annotations

import logging


logger = logging.getLogger("c4_cdi_turbo.pipeline.discovery.phase1")


async def run_cognitive_framing(problem: str, results: dict) -> dict:
    """Run cognitive framing."""
    import time

    from src.discovery.pipeline_logic import (
        _domain_improving_param,
        _domain_worsening_param,
        navigate_c4,
        resolve_triz,
        run_c4_observer,
        run_fra_routing,
        run_matrix_dream,
    )

    domain = results["domain"]
    errors = results.setdefault("_errors", [])

    try:
        c4_path = navigate_c4(problem)
        results["c4_path"] = {"states": c4_path.get("states_visited", 0), "steps": c4_path.get("steps", 0), "operators": c4_path.get("operators", []), "summary": f"{c4_path.get('states_visited', 0)} states in {c4_path.get('steps', 0)} steps"}
        if c4_path.get("error"):
            errors.append(f"c4: {c4_path['error']}")
    except Exception as e:
        results["c4_path"] = {"states": 0, "steps": 0, "error": str(e)}
        errors.append(f"c4: {str(e)}")
    t_fra = time.perf_counter()
    try:
        results["fra_routing"] = run_fra_routing(problem)
    except Exception as e:
        results["fra_routing"] = {"error": str(e)}
        errors.append(f"fra_routing: {str(e)}")
    logger.info("FRA routing: %.3fs", time.perf_counter() - t_fra)
    t_obs = time.perf_counter()
    try:
        results["c4_observer"] = run_c4_observer(problem, results.get("c4_path", {}))
    except Exception as e:
        results["c4_observer"] = {"error": str(e)}
        errors.append(f"c4_observer: {str(e)}")
    logger.info("C4 observer: %.3fs", time.perf_counter() - t_obs)
    try:
        triz_principles = resolve_triz(problem, domain)
        results["triz"] = {"principles": triz_principles[:5], "count": len(triz_principles), "improving_param": _domain_improving_param(domain), "worsening_param": _domain_worsening_param(domain)}
    except Exception as e:
        results["triz"] = {"principles": [], "error": str(e)}
        errors.append(f"triz: {str(e)}")
    try:
        from src.pipeline.ucos_qzrf import UCOSAnalyzer
        ucos = UCOSAnalyzer()
        results["ucos"] = ucos.analyze({"problem": problem, "c4_path": results.get("c4_path", {}), "triz": results.get("triz", {}), "papers": results.get("papers", []), "isomorphisms": results.get("isomorphisms", {})}, "")
    except Exception as e:
        results["ucos"] = {"status": "error", "error": str(e)}
        errors.append(f"ucos: {str(e)}")
    try:
        from src.pipeline.ucos_qzrf import QZRFAnalyzer
        triz_list = results.get("triz", {}).get("principles", [])
        qzrf = QZRFAnalyzer()
        results["qzrf"] = qzrf.apply(problem, triz_list if isinstance(triz_list, list) else [], "")
    except Exception as e:
        results["qzrf"] = {"operators_applied": 0, "error": str(e)}
        errors.append(f"qzrf: {str(e)}")
    t_md = time.perf_counter()
    try:
        results["matrix_dream"] = run_matrix_dream(problem, results.get("c4_path", {}))
    except Exception as e:
        results["matrix_dream"] = {"error": str(e)}
        errors.append(f"matrix_dream: {str(e)}")
    logger.info("Matrix Dream: %.3fs", time.perf_counter() - t_md)
    return results
