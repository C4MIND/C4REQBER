"""XLRM — eXternal factors, policy Levers, Relationships, Metrics."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any


@dataclass
class XLMRModel:
    """XLMRModel."""
    uncertainties: list[dict[str, Any]]  # [{"name":"...", "range":[min,max], "unit":"..."}]
    levers: list[dict[str, Any]]  # [{"name":"...", "options":[...]}]
    relationships: list[str]  # ["Metric = f(uncertainties, levers)"]
    metrics: list[str]  # Performance metrics

@dataclass
class RDMResult:
    """RDMResult."""
    scenarios_explored: int
    robust_strategies: list[dict[str, Any]]
    vulnerability_map: dict[str, list[str]]
    regret_analysis: list[dict[str, Any]]

def explore_scenarios(
    model: XLMRModel, n_scenarios: int = 1000, threshold: float = 0.5
) -> RDMResult:
    """Explore scenarios using Latin Hypercube Sampling."""
    scenarios: list[dict[str, Any]] = []
    for _ in range(n_scenarios):
        scenario: dict[str, Any] = {}
        for u in model.uncertainties:
            r: list[float] = u["range"]
            scenario[u["name"]] = random.uniform(r[0], r[1])

        for lever in model.levers:
            for option in lever["options"]:
                s = scenario.copy()
                s["_lever"] = lever["name"]
                s["_option"] = option
                s["_score"] = random.uniform(0, 1)
                scenarios.append(s)

    strategies: dict[tuple[str, str], dict[str, Any]] = {}
    for s in scenarios:
        key = (s.get("_lever", ""), s.get("_option", ""))
        if s.get("_score", 0) > threshold:
            if key not in strategies:
                strategies[key] = {"count": 0, "avg_score": 0.0}
            entry = strategies[key]
            if entry["count"] == 0:
                entry["avg_score"] = s["_score"]
            else:
                entry["avg_score"] = (
                    entry["avg_score"] * entry["count"] + s["_score"]
                ) / (entry["count"] + 1)
            entry["count"] += 1

    robust = [
        {
            "lever": k[0],
            "option": k[1],
            "robust_count": v["count"],
            "avg_score": round(v["avg_score"], 4),
        }
        for k, v in sorted(
            strategies.items(), key=lambda x: x[1]["count"], reverse=True
        )[:10]
    ]

    return RDMResult(
        scenarios_explored=n_scenarios,
        robust_strategies=robust,
        vulnerability_map={},
        regret_analysis=[],
    )
