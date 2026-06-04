"""
C4REQBER: Plugin Registry v2
Unified registry for all 20 metamodel plugins.
"""

from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from typing import Any, Callable

from src.plugins.persistence import PluginResultStore


@dataclass
class PluginInfo:
    """Plugin metadata."""

    id: str
    name: str
    description: str
    category: str
    execute_fn: Callable  # type: ignore[type-arg]
    icon: str = "puzzle"


# All 20 plugins
PLUGIN_REGISTRY: dict[str, PluginInfo] = {}

# Shared persistence store (eager init to avoid global)
_persistence_store = PluginResultStore()


def _get_store() -> PluginResultStore:
    return _persistence_store


def _register_plugin(
    id: str, name: str, description: str, category: str, module_path: str, fn_name: str = "execute"
) -> None:
    """Register a plugin from module path."""
    try:
        module = importlib.import_module(module_path)
        fn = getattr(module, fn_name)
        PLUGIN_REGISTRY[id] = PluginInfo(
            id=id,
            name=name,
            description=description,
            category=category,
            execute_fn=fn,
        )
    except Exception as e:
        print(f"Warning: Could not register plugin {id}: {e}")


# Register all plugins
_register_plugin(
    "swot",
    "SWOT Analysis",
    "Strengths, Weaknesses, Opportunities, Threats",
    "strategy",
    "src.plugins.swot",
)
_register_plugin(
    "five_whys",
    "5 Whys",
    "Root cause analysis through iterative questioning",
    "analysis",
    "src.plugins.five_whys",
)
_register_plugin(
    "morphological",
    "Morphological Analysis",
    "Systematic exploration of all possible solutions",
    "creativity",
    "src.plugins.morphological",
)
_register_plugin(
    "lateral_thinking",
    "Lateral Thinking",
    "De Bono's creative thinking techniques",
    "creativity",
    "src.plugins.lateral_thinking",
)
_register_plugin(
    "scamper",
    "SCAMPER",
    "Substitute, Combine, Adapt, Modify, Put to other uses, Eliminate, Reverse",
    "creativity",
    "src.plugins.scamper",
)
_register_plugin(
    "first_principles",
    "First Principles",
    "Decompose to fundamental truths and rebuild",
    "analysis",
    "src.plugins.first_principles",
)
_register_plugin(
    "red_team",
    "Red Team",
    "Adversarial critique and vulnerability analysis",
    "analysis",
    "src.plugins.red_team",
)
_register_plugin(
    "pre_mortem",
    "Pre-Mortem",
    "Imagine failure and work backwards to prevent it",
    "strategy",
    "src.plugins.pre_mortem",
)
_register_plugin(
    "ooda", "OODA Loop", "Observe, Orient, Decide, Act cycle", "strategy", "src.plugins.ooda"
)
_register_plugin(
    "six_hats",
    "Six Thinking Hats",
    "Parallel thinking with 6 perspectives",
    "creativity",
    "src.plugins.six_hats",
)
_register_plugin(
    "bayesian_update",
    "Bayesian Update",
    "Probabilistic belief updating with evidence",
    "analysis",
    "src.plugins.bayesian_update",
)
_register_plugin(
    "triz_bridge",
    "TRIZ Bridge",
    "40 inventive principles and contradiction matrix",
    "engineering",
    "src.plugins.triz_bridge",
)
_register_plugin(
    "inversion",
    "Inversion",
    "Solve backwards from failure state",
    "analysis",
    "src.plugins.inversion",
)
_register_plugin(
    "second_order",
    "Second-Order Thinking",
    "Consider consequences of consequences",
    "analysis",
    "src.plugins.second_order",
)
_register_plugin(
    "constraint_relaxation",
    "Constraint Relaxation",
    "Remove constraints temporarily for creativity",
    "creativity",
    "src.plugins.constraint_relaxation",
)
_register_plugin(
    "analogical_reasoning",
    "Analogical Reasoning",
    "Cross-domain analogy and transfer",
    "creativity",
    "src.plugins.analogical_reasoning",
)
_register_plugin(
    "delphi",
    "Delphi Method",
    "Structured expert consensus forecasting",
    "strategy",
    "src.plugins.delphi",
)
_register_plugin(
    "ishikawa",
    "Ishikawa Diagram",
    "Fishbone root cause analysis with 6 categories",
    "analysis",
    "src.plugins.ishikawa",
)
_register_plugin(
    "pareto", "Pareto Analysis", "80/20 rule prioritization", "analysis", "src.plugins.pareto"
)
_register_plugin(
    "design_thinking",
    "Design Thinking",
    "Empathize, Define, Ideate, Prototype, Test",
    "creativity",
    "src.plugins.design_thinking",
)
_register_plugin("stat_tests", "Statistical Tests", "Welch t-test, Mann-Whitney, chi-squared, Cohen's d", "statistics", "src.plugins.stat_tests")
_register_plugin("info_theory", "Information Theory", "Shannon entropy, mutual information, KL divergence, complexity", "analysis", "src.plugins.info_theory")
_register_plugin("dist_analyzer", "Distribution Analyzer", "KS test, bootstrap CI, power-law fit, outlier detection", "statistics", "src.plugins.dist_analyzer")
_register_plugin("timeseries", "Time Series Analysis", "Autocorrelation, stationarity, trend decomposition, growth rate", "analysis", "src.plugins.timeseries")
_register_plugin("graph_metrics", "Graph Metrics", "PageRank, degree centrality, clustering, connected components", "analysis", "src.plugins.graph_metrics")
_register_plugin("signal_processing", "Signal Processing", "DFT/FFT, convolution, peak detection, signal autocorrelation", "computation", "src.plugins.signal_processing")
_register_plugin("dim_reduction", "Dimension Reduction", "PCA, explained variance, eigenvalue decomposition", "computation", "src.plugins.dim_reduction")
_register_plugin("optimization", "Optimization", "Gradient descent, grid search, Nelder-Mead simplex", "computation", "src.plugins.optimization")


def list_plugins() -> list[dict[str, Any]]:
    """List all registered plugins."""
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "category": p.category,
        }
        for p in PLUGIN_REGISTRY.values()
    ]


def list_plugins_by_category(category: str) -> list[dict[str, Any]]:
    """List plugins in a category."""
    return [
        {"id": p.id, "name": p.name, "description": p.description}
        for p in PLUGIN_REGISTRY.values()
        if p.category == category
    ]


def get_plugin(plugin_id: str) -> PluginInfo | None:
    """Get plugin by ID."""
    return PLUGIN_REGISTRY.get(plugin_id)


def execute_plugin(plugin_id: str, use_cache: bool = True, **kwargs: Any) -> dict[str, Any]:
    """Execute a plugin by ID.

    If use_cache is True and a cached result exists for the same plugin+problem,
    returns the cached result instead of re-executing.
    """
    plugin = PLUGIN_REGISTRY.get(plugin_id)
    if not plugin:
        return {"error": f"Plugin '{plugin_id}' not found"}

    # Build a stable problem key from kwargs
    problem_key = json.dumps(kwargs, sort_keys=True, ensure_ascii=False)

    store = _get_store()
    if use_cache:
        cached = store.get(plugin_id, problem_key)
        if cached is not None:
            return {
                "cached": True,
                "plugin_id": plugin_id,
                "result": cached["result"],
                "metadata": cached.get("metadata"),
            }

    try:
        result = plugin.execute_fn(**kwargs)
    except Exception as e:
        return {"error": str(e), "plugin_id": plugin_id}

    # Persist result
    store.save(plugin_id, problem_key, result, metadata={"source": "v2_registry"})

    return {"cached": False, "plugin_id": plugin_id, "result": result}


def select_plugins_for_problem(problem: str, domain_hint: str = "", auto_mode: str = "") -> list[str]:
    """Smart plugin selection based on problem complexity, domain, and BLAST mode.

    Args:
        problem: The problem/topic text
        domain_hint: Known domain (physics, biology, etc.)
        auto_mode: BLAST mode — "turbo", "solve", "flash", "turbofactory"

    Returns: list of plugin IDs to run
    """
    problem_lower = problem.lower()
    word_count = len(problem.split())
    selected: list[tuple[str, float]] = []

    # ═══════════════════════════════════════════════════════════════════
    # Keyword-based selection (existing)
    # ═══════════════════════════════════════════════════════════════════
    keywords = {
        "swot": ["strength", "weakness", "opportunity", "threat", "competitive"],
        "five_whys": ["root cause", "why", "underlying", "fundamental cause"],
        "scamper": ["innovate", "improve", "modify", "creative solution"],
        "first_principles": ["fundamental", "basic", "from scratch", "decompose"],
        "red_team": ["risk", "vulnerability", "attack", "weakness", "critique"],
        "pre_mortem": ["prevent failure", "what if fail", "risk mitigation"],
        "ooda": ["rapid decision", "fast response", "tactical", "agile"],
        "six_hats": ["perspective", "viewpoint", "multiple angles", "parallel thinking"],
        "delphi": ["expert opinion", "consensus", "forecast", "prediction"],
        "ishikawa": ["cause", "fishbone", "root cause analysis"],
        "design_thinking": ["user", "experience", "empathy", "prototype"],
        "morphological": ["explore all", "combinations", "systematic"],
        "lateral_thinking": ["out of the box", "unconventional", "breakthrough"],
        "stat_tests": ["p-value", "statistical significance", "hypothesis test", "t-test", "anova"],
        "info_theory": ["entropy", "information theory", "complexity measure", "uncertainty"],
        "dist_analyzer": ["distribution", "outlier", "power law", "fit", "confidence interval"],
    }

    for plugin_id, plugin_keywords in keywords.items():
        kw_score = sum(1 for kw in plugin_keywords if kw in problem_lower)
        if kw_score > 0:
            selected.append((plugin_id, float(kw_score)))

    # ═══════════════════════════════════════════════════════════════════
    # Complexity-based tier selection
    # ═══════════════════════════════════════════════════════════════════
    if word_count >= 30:
        # Deep analysis: always include stats + info theory
        selected.append(("stat_tests", 0.5))
        selected.append(("info_theory", 0.5))
        selected.append(("swot", 0.3))
        selected.append(("delphi", 0.3))
    elif word_count >= 10:
        selected.append(("info_theory", 0.3))
        selected.append(("six_hats", 0.2))
    elif word_count <= 3 and auto_mode == "flash":
        # Very short: skip analysis plugins, just answer
        pass

    # ═══════════════════════════════════════════════════════════════════
    # Domain-based selection
    # ═══════════════════════════════════════════════════════════════════
    domain_lower = domain_hint.lower() if domain_hint else ""
    if any(kw in domain_lower for kw in ["physics", "engineering", "material"]):
        selected.append(("dist_analyzer", 0.4))
        selected.append(("stat_tests", 0.3))
    elif any(kw in domain_lower for kw in ["biology", "genetics", "neuroscience", "medicine"]):
        selected.append(("stat_tests", 0.5))
        selected.append(("info_theory", 0.3))
    elif any(kw in domain_lower for kw in ["data", "statistics", "machine learning"]):
        selected.append(("dist_analyzer", 0.5))
        selected.append(("stat_tests", 0.5))

    # ═══════════════════════════════════════════════════════════════════
    # BLAST mode defaults
    # ═══════════════════════════════════════════════════════════════════
    if auto_mode == "turbo":
        selected.append(("swot", 0.2))
        selected.append(("delphi", 0.2))
        selected.append(("red_team", 0.2))
        selected.append(("info_theory", 0.3))
    elif auto_mode == "solve":
        selected.append(("first_principles", 0.2))
        selected.append(("five_whys", 0.2))
        selected.append(("stat_tests", 0.2))
    elif auto_mode == "turbofactory":
        selected.append(("delphi", 0.3))
        selected.append(("info_theory", 0.3))
        selected.append(("dist_analyzer", 0.3))
        selected.append(("stat_tests", 0.3))
    elif auto_mode == "flash":
        pass  # No auto-plugins for quick mode

    # ═══════════════════════════════════════════════════════════════════
    # Deduplicate + sort by score
    # ═══════════════════════════════════════════════════════════════════
    best: dict[str, float] = {}
    for pid, score in selected:
        best[pid] = max(best.get(pid, 0.0), float(score))

    ranked = sorted(best.items(), key=lambda x: -x[1])
    result = [pid for pid, _ in ranked]

    # Cap at reasonable number
    max_plugins = {"turbo": 6, "solve": 4, "turbofactory": 8, "flash": 2}
    limit = max_plugins.get(auto_mode, 5)
    return result[:limit]


__all__ = [
    "PLUGIN_REGISTRY",
    "list_plugins",
    "list_plugins_by_category",
    "get_plugin",
    "execute_plugin",
    "select_plugins_for_problem",
    "PluginInfo",
    "PluginResultStore",
]
