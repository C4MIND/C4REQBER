from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.mcp_server.tool_dependencies import (
    HAS_TOOLS,
    DoCalculus,
    ExportManager,
    run_bma,
)


logger = logging.getLogger(__name__)


async def c4_transfer(problem: str, source_domain: str, target_domain: str) -> dict[str, Any]:
    """Execute cross-domain structural isomorphism transfer."""
    try:
        from src.c4_analysis.transfer_pipeline import TransferPipeline

        pipeline = TransferPipeline()
        result = pipeline.transfer(problem, source_domain, target_domain)
        return result.to_dict()
    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e), "status": "error"}


async def c4_simulate(pattern_id: str, hypothesis: dict[str, Any]) -> dict[str, Any]:
    """Run physics simulation via PatternRunnerV2 (pattern_id selects engine)."""
    try:
        if not HAS_TOOLS:
            return {"status": "error", "errors": ["Simulation modules not available"]}
        from src.simulations.runner_v2 import get_runner_v2

        runner = get_runner_v2()
        result = await asyncio.to_thread(runner.run, pattern_id, hypothesis or {})
        return {"status": "success", "data": {"pattern": pattern_id, "result": result}}
    except (AttributeError, ImportError, TypeError, ValueError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"status": "error", "errors": [str(e)]}


async def c4_bayesian(
    models: list[dict[str, Any]] | dict[str, float],
    samples: int = 1000,
) -> dict[str, Any]:
    """Run Bayesian inference (MCMC/BMA) on competing models."""
    try:
        if not HAS_TOOLS:
            return {"status": "error", "errors": ["Bayesian module not available"]}

        if isinstance(models, dict):
            if not models:
                raise ValueError("models must not be empty")
            if any(probability < 0 for probability in models.values()):
                raise ValueError("model probabilities must be non-negative")
            total = sum(models.values())
            if total <= 0:
                raise ValueError("at least one model probability must be positive")
            ranked = [
                {"name": name, "posterior_prob": probability / total}
                for name, probability in models.items()
            ]
            ranked.sort(key=lambda model: model["posterior_prob"], reverse=True)
            return {
                "status": "success",
                "data": {
                    "method": "prior_ranking",
                    "models": ranked,
                    "best_model": ranked[0]["name"],
                    "samples": samples,
                },
                "warnings": [
                    "Predictions were not supplied; returning normalized prior ranking, not BMA."
                ],
            }

        from src.bayesian.router import BMARequest

        result = await run_bma(BMARequest(models=models))
        return {
            "status": "success",
            "data": {**result, "method": "bayesian_model_averaging", "samples": samples},
        }
    except (AttributeError, ImportError, KeyError, TypeError, ValueError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"status": "error", "errors": [str(e)]}


async def c4_causal(nodes: list[dict[str, Any]], treatment: str, outcome: str) -> dict[str, Any]:
    """Determine whether an SCM causal effect is identifiable via do-calculus."""
    try:
        if not HAS_TOOLS:
            return {"status": "error", "errors": ["Causal module not available"]}

        from src.causal.scm import StructuralCausalModel

        if not nodes:
            raise ValueError("nodes must not be empty")
        pending = {node["name"]: node for node in nodes}
        if len(pending) != len(nodes):
            raise ValueError("node names must be unique")

        scm = StructuralCausalModel()
        while pending:
            progressed = False
            for name, node in list(pending.items()):
                parents = list(node.get("parents", []))
                if all(parent in scm.nodes for parent in parents):
                    scm.add_node(
                        name=name,
                        parents=parents,
                        is_exogenous=bool(node.get("is_exogenous", False)),
                        domain=node.get("domain"),
                    )
                    del pending[name]
                    progressed = True
            if not progressed:
                unresolved = ", ".join(sorted(pending))
                raise ValueError(
                    f"SCM contains a cycle or references missing parents: {unresolved}"
                )

        dc = DoCalculus(scm)
        identifiable, formula, adjustment_set = dc.get_adjustment_formula(treatment, outcome)
        reason = dc.is_identifiable(treatment, outcome)[1]
        return {
            "status": "success",
            "data": {
                "treatment": treatment,
                "outcome": outcome,
                "identifiable": identifiable,
                "formula": formula,
                "adjustment_set": sorted(adjustment_set or set()),
                "reason": reason,
            },
        }
    except (AttributeError, ImportError, KeyError, TypeError, ValueError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"status": "error", "errors": [str(e)]}


async def c4_export(discovery: dict[str, Any], format: str = "markdown") -> dict[str, Any]:
    """Export discovery to LaTeX/Markdown/JSON/HTML/PDF/BibTeX."""
    try:
        if not HAS_TOOLS:
            return {"error": "Export module not available"}
        manager = ExportManager()
        if format == "markdown":
            content = manager.export_discovery_markdown(discovery)
        elif format == "json":
            import json

            content = json.dumps(discovery, indent=2)
        else:
            content = str(discovery)
        return {"status": "exported", "format": format, "content": content[:1000]}
    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e)}
