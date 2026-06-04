from __future__ import annotations


"""
Reqber v8.0: Turbo Discovery + Paradigm Shift API Router
POST /api/v8/discover/turbo — multi-agent turbo discovery
POST /api/v8/discover/paradigm — paradigm shift detection (100+ agents)
"""
import asyncio
import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator


logger = logging.getLogger("reqber.api.v8.turbo")

router = APIRouter(prefix="/turbo", tags=["v8-turbo"])


class TurboRequest(BaseModel):
    """TurboRequest."""
    problem: str
    domain: str = "science"
    level: str = "complex"
    vector: str = "discover"
    agent_count: int = 25

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate level."""
        allowed = {"simple", "hard", "complex", "epic"}
        if v not in allowed:
            raise ValueError(f"level must be one of {allowed}")
        return v

    @field_validator("vector")
    @classmethod
    def validate_vector(cls, v: str) -> str:
        """Validate vector."""
        allowed = {"discover", "invent", "transform"}
        if v not in allowed:
            raise ValueError(f"vector must be one of {allowed}")
        return v


class ParadigmRequest(BaseModel):
    """ParadigmRequest."""
    problem: str
    domain: str = "science"


def _agent_count_for_level(level: str, override: int) -> int:
    defaults = {"simple": 1, "hard": 5, "complex": 25, "epic": 120}
    return override if override != 25 else defaults.get(level, 25)


def _vector_output(vector: str, problem: str, domain: str, agent_results: list[dict[str, Any]]) -> dict[str, Any]:
    if vector == "discover":
        return {
            "type": "hypothesis",
            "problem": problem,
            "domain": domain,
            "hypothesis": _synthesize_hypothesis(problem, domain, agent_results),
            "article_outline": _generate_article_outline(problem, agent_results),
            "supporting_evidence": len(agent_results),
        }
    elif vector == "invent":
        return {
            "type": "blueprint",
            "problem": problem,
            "domain": domain,
            "blueprint": _synthesize_blueprint(problem, domain, agent_results),
            "schema": _generate_schema(problem, agent_results),
            "components": len(agent_results),
        }
    else:
        return {
            "type": "dissertation",
            "problem": problem,
            "domain": domain,
            "theory": _synthesize_theory(problem, domain, agent_results),
            "paradigm_shift_score": _compute_paradigm_shift_score(agent_results),
            "axiomatic_contradictions": _extract_contradictions(agent_results),
        }


def _synthesize_hypothesis(problem: str, domain: str, results: list[dict[str, Any]]) -> str:
    perspectives = [r.get("insight", "") for r in results if r.get("insight")]
    joined = "; ".join(perspectives[:5])
    return f"Integrated hypothesis for '{problem}' in {domain}: {joined}. Synthesis of {len(results)} agent perspectives suggests a novel explanatory model."


def _generate_article_outline(problem: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "title": f"On the Resolution of {problem}: A Multi-Agent Discovery Approach",
        "sections": ["Abstract", "Introduction", "Methodology", "Agent Analysis", "Synthesis", "Discussion", "Conclusion"],
        "agent_count": len(results),
    }


def _synthesize_blueprint(problem: str, domain: str, results: list[dict[str, Any]]) -> str:
    return f"Blueprint solving '{problem}' in {domain} via {len(results)} concurrent functional transformations."


def _generate_schema(problem: str, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"component": r.get("agent", f"agent_{i}"), "role": r.get("operation", "analysis"), "output": r.get("insight", "")}
        for i, r in enumerate(results[:10])
    ]


def _synthesize_theory(problem: str, domain: str, results: list[dict[str, Any]]) -> str:
    contradictions = len([r for r in results if r.get("contradiction")])
    return f"Theory for '{problem}' in {domain}: identified {contradictions} axiomatic tensions resolved through {len(results)} functional transformations."


def _compute_paradigm_shift_score(results: list[dict[str, Any]]) -> float:
    contradiction_count = sum(1 for r in results if r.get("contradiction"))
    novelty_count = sum(1 for r in results if r.get("novel", False))
    if not results:
        return 0.0
    return round((contradiction_count * 0.6 + novelty_count * 0.4) / len(results), 3)


def _extract_contradictions(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "agent": r.get("agent", "unknown"),
            "contradiction": r["contradiction"],
            "resolution": r.get("resolution", "unresolved"),
        }
        for r in results
        if r.get("contradiction")
    ]


# ---------------------------------------------------------------------------
# Turbo Discovery Endpoint
# ---------------------------------------------------------------------------

@router.post("/turbo")
async def turbo_discovery(request: TurboRequest) -> dict[str, Any]:
    """
    Turbo discovery: multiple functor-agents explore a problem in parallel.

    Level → agent count: simple (1), hard (5), complex (25), epic (100+).
    Vector → output type: discover (hypothesis+article), invent (blueprint+schema), transform (dissertation+theory).
    """
    problem = request.problem
    domain = request.domain
    level = request.level
    vector = request.vector
    agent_count = _agent_count_for_level(level, request.agent_count)
    errors: list[str] = []
    start_total = time.perf_counter()

    results: dict[str, Any] = {
        "problem": problem,
        "domain": domain,
        "level": level,
        "vector": vector,
        "agent_count": agent_count,
        "pipeline_version": "v8.0-turbo",
    }

    # Run turbo via FunctorOrchestrator
    try:
        from src.agents.functor_orchestrator import FunctorOrchestrator

        orchestrator = FunctorOrchestrator()
        turbo_output = await asyncio.wait_for(
            orchestrator.run_turbo(problem=problem, agent_count=agent_count, vector=vector),
            timeout=7200.0,
        )
        results["turbo"] = turbo_output
        results["agent_results"] = turbo_output.get("agent_results", [])
        results["output"] = turbo_output.get("synthesis", {})
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Turbo engine unavailable: {e}") from e
    except (AttributeError, RuntimeError, TimeoutError) as e:
        logger.error("Turbo discovery error: %s", e)
        raise HTTPException(status_code=502, detail=f"Turbo execution failed: {e}") from e

    total_time = time.perf_counter() - start_total
    results["errors"] = errors
    results["total_time_seconds"] = round(total_time, 2)
    results["status"] = "partial" if errors else "complete"

    return results


# ---------------------------------------------------------------------------
# Paradigm Shift Endpoint
# ---------------------------------------------------------------------------

@router.post("/paradigm")
async def paradigm_shift(request: ParadigmRequest) -> dict[str, Any]:
    """
    Paradigm shift detection: 100+ agents search for axiomatic contradictions
    in the given problem domain, identifying potential paradigm shifts.
    """
    problem = request.problem
    domain = request.domain
    errors: list[str] = []
    start_total = time.perf_counter()

    results: dict[str, Any] = {
        "problem": problem,
        "domain": domain,
        "agent_count": 120,
        "mode": "paradigm_shift",
        "pipeline_version": "v8.0-paradigm",
    }

    try:
        from src.agents.paradigm_coordinator import ParadigmCoordinator

        coordinator = ParadigmCoordinator()
        paradigm_output = await asyncio.wait_for(
            coordinator.run(problem=problem, domain=domain),
            timeout=7200.0,
        )
        paradigm_dict = paradigm_output.to_dict()
        results["paradigm"] = paradigm_dict
        results["axiomatic_contradictions"] = paradigm_dict.get("contradictions", [])
        results["paradigm_shift_score"] = paradigm_dict.get("shift_score", 0.0)
        results["recommended_paradigm"] = paradigm_dict.get("recommended_paradigm", "")
        results["manifesto"] = paradigm_dict.get("manifesto", "")
    except ImportError as e:
        raise HTTPException(status_code=503, detail=f"Paradigm engine unavailable: {e}") from e
    except (AttributeError, RuntimeError, TimeoutError) as e:
        logger.error("Paradigm shift error: %s", e)
        raise HTTPException(status_code=502, detail=f"Paradigm execution failed: {e}") from e

    total_time = time.perf_counter() - start_total
    results["errors"] = errors
    results["total_time_seconds"] = round(total_time, 2)
    results["status"] = "partial" if errors else "complete"

    return results

