# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import importlib
import json
import logging
import pkgutil
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from src.plugins.persistence import PluginResultStore


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════


@dataclass
class ToolMetadata:
    """Metadata for a tool plugin (v1)."""

    name: str
    version: str
    description: str
    author: str
    requires: list[str]


@dataclass
class PluginInfo:
    """Plugin metadata (v2 — richer)."""

    id: str
    name: str
    description: str
    category: str
    execute_fn: Callable  # type: ignore[type-arg]
    icon: str = "puzzle"


# ═══════════════════════════════════════════════════════════════════
# ABSTRACT BASE CLASS (v1)
# ═══════════════════════════════════════════════════════════════════


class ToolPlugin(ABC):
    """Base class for tool plugins."""

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Return plugin metadata."""
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """Execute the tool."""
        pass

    def validate_input(self, **kwargs: Any) -> bool:
        """Validate input parameters."""
        return True

    def get_schema(self) -> dict[str, Any]:
        """Get JSON schema for tool parameters."""
        return {"type": "object", "properties": {}}


# ═══════════════════════════════════════════════════════════════════
# UNIFIED PLUGIN REGISTRY
# ═══════════════════════════════════════════════════════════════════


class PluginRegistry:
    """
    Unified registry for tool plugins and plugin infos.

    Supports both v1 (ToolPlugin registration) and v2 (PluginInfo dict-like
    access) APIs plus dict-compatible operations for backward compatibility
    with code that treats PLUGIN_REGISTRY as a plain dict.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, PluginInfo] = {}
        self._tool_plugins: dict[str, ToolPlugin] = {}
        self._hooks: dict[str, list[Callable]] = {}  # type: ignore[type-arg]
        self._store = PluginResultStore()

    def init_plugins(self) -> PluginRegistry:
        """Register all built-in plugins. Returns self for chaining."""
        self._register_builtin_tool_plugins()
        self._register_builtin_plugin_infos()
        return self

    def _init_plugins(self) -> None:
        """Register all built-in plugins."""
        self._register_builtin_tool_plugins()
        self._register_builtin_plugin_infos()

    def _register_builtin_tool_plugins(self) -> None:
        """Register v1-style tool plugins (WebSearch, Calculator)."""
        self.register(WebSearchPlugin())
        self.register(CalculatorPlugin())

    def _register_builtin_plugin_infos(self) -> None:
        """Register all v2-style PluginInfo entries."""
        _populate_plugin_infos_into(self)

    # ── dict-like access (for PLUGIN_REGISTRY dict API compat) ──

    def __getitem__(self, key: str) -> PluginInfo:
        return self._plugins[key]

    def __setitem__(self, key: str, value: PluginInfo) -> None:
        self._plugins[key] = value

    def __delitem__(self, key: str) -> None:
        del self._plugins[key]

    def __contains__(self, key: str) -> bool:
        return key in self._plugins

    def __len__(self) -> int:
        return len(self._plugins)

    def __iter__(self):
        return iter(self._plugins)

    def get(self, key: str, default: Any = None) -> PluginInfo | Any:
        return self._plugins.get(key, default)

    def items(self):
        return self._plugins.items()

    def values(self):
        return self._plugins.values()

    def keys(self):
        return self._plugins.keys()

    # ── v1 API: ToolPlugin management ──

    def register(self, plugin: ToolPlugin) -> None:
        """Register a ToolPlugin."""
        name = plugin.metadata.name
        self._tool_plugins[name] = plugin

    def unregister(self, name: str) -> None:
        """Unregister a ToolPlugin by name."""
        if name in self._tool_plugins:
            del self._tool_plugins[name]

    def get_plugin(self, name: str) -> ToolPlugin | None:
        """Get a ToolPlugin by name (v1 API)."""
        return self._tool_plugins.get(name)

    def list_tool_plugins(self) -> list[ToolMetadata]:
        """List all registered ToolPlugin metadata (v1 API)."""
        return [p.metadata for p in self._tool_plugins.values()]

    def list_plugins(self) -> list[dict[str, Any]]:
        """List all v2 PluginInfo entries as dicts."""
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "category": p.category,
            }
            for p in self._plugins.values()
        ]

    def execute(self, name: str, **kwargs: Any) -> Any:
        """Execute a ToolPlugin by name (v1 API)."""
        plugin = self._tool_plugins.get(name)
        if not plugin:
            raise ValueError(f"Plugin not found: {name}")
        if not plugin.validate_input(**kwargs):
            raise ValueError(f"Invalid input for plugin: {name}")
        return plugin.execute(**kwargs)

    def register_hook(self, event: str, callback: Callable) -> None:  # type: ignore[type-arg]
        """Register a hook for an event."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)

    def trigger_hook(self, event: str, **kwargs: Any) -> None:
        """Trigger all hooks for an event."""
        for callback in self._hooks.get(event, []):
            callback(**kwargs)

    def discover_plugins(self, package_name: str = "c4_cdi_turbo.plugins") -> None:
        """Auto-discover ToolPlugins in a package."""
        try:
            package = importlib.import_module(package_name)
            for _, name, _ in pkgutil.iter_modules(package.__path__):
                try:
                    module = importlib.import_module(f"{package_name}.{name}")
                    if hasattr(module, "Plugin"):
                        plugin_class = module.Plugin
                        plugin = plugin_class()
                        self.register(plugin)
                except Exception as e:
                    logger.warning("Failed to load plugin %s: %s", name, e)
        except ImportError:
            logger.debug("plugin registry import failed", exc_info=True)
            pass

    # ── v2 API: PluginInfo management ──

    def register_info(self, info: PluginInfo) -> None:
        """Register a PluginInfo entry."""
        self._plugins[info.id] = info

    def get_plugin_info(self, plugin_id: str) -> PluginInfo | None:
        """Get a PluginInfo by id (v2 API)."""
        return self._plugins.get(plugin_id)

    def list_by_category(self, category: str) -> list[dict[str, Any]]:
        """List PluginInfo entries in a category."""
        return [
            {"id": p.id, "name": p.name, "description": p.description}
            for p in self._plugins.values()
            if p.category == category
        ]

    def execute_plugin(
        self, plugin_id: str, use_cache: bool = True, **kwargs: Any
    ) -> dict[str, Any]:
        """Execute a plugin by ID with optional caching.

        Returns a result dict with status info.
        """
        plugin = self._plugins.get(plugin_id)
        if not plugin:
            return {"error": f"Plugin '{plugin_id}' not found"}

        problem_key = json.dumps(kwargs, sort_keys=True, ensure_ascii=False)

        if use_cache:
            cached = self._store.get(plugin_id, problem_key)
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

        self._store.save(
            plugin_id, problem_key, result, metadata={"source": "unified_registry"}
        )

        return {"cached": False, "plugin_id": plugin_id, "result": result}

    def select_plugins_for_problem(
        self, problem: str, domain_hint: str = "", auto_mode: str = ""
    ) -> list[str]:
        """Smart plugin selection based on problem complexity, domain, and mode."""
        return _select_plugins_for_problem(problem, domain_hint, auto_mode)

    def to_dict(self) -> dict[str, Any]:
        """Serialize registry (compat with pipeline/api PluginRegistry.to_dict)."""
        return {
            "plugins": self.list_plugins(),
            "total": len(self._plugins),
            "tool_plugins": len(self._tool_plugins),
        }


# ═══════════════════════════════════════════════════════════════════
# MODULE-LEVEL CONVENIENCE FUNCTIONS (v2 compat)
# ═══════════════════════════════════════════════════════════════════


def list_plugins() -> list[dict[str, Any]]:
    """List all registered plugins."""
    return PLUGIN_REGISTRY.list_plugins()  # noqa: F821


def list_plugins_by_category(category: str) -> list[dict[str, Any]]:
    """List plugins in a category."""
    return PLUGIN_REGISTRY.list_by_category(category)  # noqa: F821


def get_plugin(plugin_id: str) -> PluginInfo | None:
    """Get plugin by ID."""
    return PLUGIN_REGISTRY.get_plugin_info(plugin_id)  # noqa: F821


def execute_plugin(
    plugin_id: str, use_cache: bool = True, **kwargs: Any
) -> dict[str, Any]:
    """Execute a plugin by ID."""
    return PLUGIN_REGISTRY.execute_plugin(plugin_id, use_cache=use_cache, **kwargs)  # noqa: F821


def select_plugins_for_problem(
    problem: str, domain_hint: str = "", auto_mode: str = ""
) -> list[str]:
    """Smart plugin selection for a problem."""
    return PLUGIN_REGISTRY.select_plugins_for_problem(problem, domain_hint, auto_mode)  # noqa: F821


def get_plugin_registry() -> PluginRegistry:
    """Get singleton plugin registry."""
    return PLUGIN_REGISTRY  # noqa: F821


# ═══════════════════════════════════════════════════════════════════
# PLUGIN INFO POPULATION & SELECTION LOGIC
# ═══════════════════════════════════════════════════════════════════


def _register_plugin_info(
    registry: PluginRegistry,
    id: str,
    name: str,
    description: str,
    category: str,
    module_path: str,
    fn_name: str = "execute",
) -> None:
    """Register a plugin from module path."""
    try:
        try:
            module = importlib.import_module(module_path)
        except (ImportError, ModuleNotFoundError):
            if module_path.endswith("@wasm"):
                module = None
                logger.debug("WASM plugin %s — loaded via wasmtime, not Python import", name)
            else:
                raise
        fn = getattr(module, fn_name)
        registry.register_info(
            PluginInfo(
                id=id,
                name=name,
                description=description,
                category=category,
                execute_fn=fn,
            )
        )
    except Exception as e:
        logger.warning("Could not register plugin %s: %s", id, e)


def _populate_plugin_infos_into(registry: PluginRegistry) -> None:
    """Populate registry with all 28 built-in plugin infos."""

    _register_plugin_info(
        registry,
        "swot",
        "SWOT Analysis",
        "Strengths, Weaknesses, Opportunities, Threats",
        "strategy",
        "src.plugins.swot",
    )
    _register_plugin_info(
        registry,
        "five_whys",
        "5 Whys",
        "Root cause analysis through iterative questioning",
        "analysis",
        "src.plugins.five_whys",
    )
    _register_plugin_info(
        registry,
        "morphological",
        "Morphological Analysis",
        "Systematic exploration of all possible solutions",
        "creativity",
        "src.plugins.morphological",
    )
    _register_plugin_info(
        registry,
        "lateral_thinking",
        "Lateral Thinking",
        "De Bono's creative thinking techniques",
        "creativity",
        "src.plugins.lateral_thinking",
    )
    _register_plugin_info(
        registry,
        "scamper",
        "SCAMPER",
        "Substitute, Combine, Adapt, Modify, Put to other uses, Eliminate, Reverse",
        "creativity",
        "src.plugins.scamper",
    )
    _register_plugin_info(
        registry,
        "first_principles",
        "First Principles",
        "Decompose to fundamental truths and rebuild",
        "analysis",
        "src.plugins.first_principles",
    )
    _register_plugin_info(
        registry,
        "red_team",
        "Red Team",
        "Adversarial critique and vulnerability analysis",
        "analysis",
        "src.plugins.red_team",
    )
    _register_plugin_info(
        registry,
        "pre_mortem",
        "Pre-Mortem",
        "Imagine failure and work backwards to prevent it",
        "strategy",
        "src.plugins.pre_mortem",
    )
    _register_plugin_info(
        registry,
        "ooda",
        "OODA Loop",
        "Observe, Orient, Decide, Act cycle",
        "strategy",
        "src.plugins.ooda",
    )
    _register_plugin_info(
        registry,
        "six_hats",
        "Six Thinking Hats",
        "Parallel thinking with 6 perspectives",
        "creativity",
        "src.plugins.six_hats",
    )
    _register_plugin_info(
        registry,
        "bayesian_update",
        "Bayesian Update",
        "Probabilistic belief updating with evidence",
        "analysis",
        "src.plugins.bayesian_update",
    )
    _register_plugin_info(
        registry,
        "triz_bridge",
        "TRIZ Bridge",
        "40 inventive principles and contradiction matrix",
        "engineering",
        "src.plugins.triz_bridge",
    )
    _register_plugin_info(
        registry,
        "inversion",
        "Inversion",
        "Solve backwards from failure state",
        "analysis",
        "src.plugins.inversion",
    )
    _register_plugin_info(
        registry,
        "second_order",
        "Second-Order Thinking",
        "Consider consequences of consequences",
        "analysis",
        "src.plugins.second_order",
    )
    _register_plugin_info(
        registry,
        "constraint_relaxation",
        "Constraint Relaxation",
        "Remove constraints temporarily for creativity",
        "creativity",
        "src.plugins.constraint_relaxation",
    )
    _register_plugin_info(
        registry,
        "analogical_reasoning",
        "Analogical Reasoning",
        "Cross-domain analogy and transfer",
        "creativity",
        "src.plugins.analogical_reasoning",
    )
    _register_plugin_info(
        registry,
        "delphi",
        "Delphi Method",
        "Structured expert consensus forecasting",
        "strategy",
        "src.plugins.delphi",
    )
    _register_plugin_info(
        registry,
        "ishikawa",
        "Ishikawa Diagram",
        "Fishbone root cause analysis with 6 categories",
        "analysis",
        "src.plugins.ishikawa",
    )
    _register_plugin_info(
        registry,
        "pareto",
        "Pareto Analysis",
        "80/20 rule prioritization",
        "analysis",
        "src.plugins.pareto",
    )
    _register_plugin_info(
        registry,
        "design_thinking",
        "Design Thinking",
        "Empathize, Define, Ideate, Prototype, Test",
        "creativity",
        "src.plugins.design_thinking",
    )
    _register_plugin_info(
        registry,
        "stat_tests",
        "Statistical Tests",
        "Welch t-test, Mann-Whitney, chi-squared, Cohen's d",
        "statistics",
        "src.plugins.stat_tests",
    )
    _register_plugin_info(
        registry,
        "info_theory",
        "Information Theory",
        "Shannon entropy, mutual information, KL divergence, complexity",
        "analysis",
        "src.plugins.info_theory",
    )
    _register_plugin_info(
        registry,
        "dist_analyzer",
        "Distribution Analyzer",
        "KS test, bootstrap CI, power-law fit, outlier detection",
        "statistics",
        "src.plugins.dist_analyzer",
    )
    _register_plugin_info(
        registry,
        "timeseries",
        "Time Series Analysis",
        "Autocorrelation, stationarity, trend decomposition, growth rate",
        "analysis",
        "src.plugins.timeseries",
    )
    _register_plugin_info(
        registry,
        "graph_metrics",
        "Graph Metrics",
        "PageRank, degree centrality, clustering, connected components",
        "analysis",
        "src.plugins.graph_metrics",
    )
    _register_plugin_info(
        registry,
        "signal_processing",
        "Signal Processing",
        "DFT/FFT, convolution, peak detection, signal autocorrelation",
        "computation",
        "src.plugins.signal_processing",
    )
    _register_plugin_info(
        registry,
        "dim_reduction",
        "Dimension Reduction",
        "PCA, explained variance, eigenvalue decomposition",
        "computation",
        "src.plugins.dim_reduction",
    )
    _register_plugin_info(
        registry,
        "optimization",
        "Optimization",
        "Gradient descent, grid search, Nelder-Mead simplex",
        "computation",
        "src.plugins.optimization",
    )
    # WASM plugins (compiled from Rust, loaded via wasmtime)
    _register_plugin_info(
        registry, "monte_carlo_pi", "Monte Carlo π", "π estimation via Monte Carlo integration (WASM)", "computation", "wasm/plugins/monte_carlo_pi.wasm@wasm",
    )
    _register_plugin_info(
        registry, "matrix_mult", "Matrix Multiplication", "Fast matrix multiplication (WASM)", "computation", "wasm/plugins/matrix_mult.wasm@wasm",
    )
    _register_plugin_info(
        registry, "text_distance", "Text Distance", "Levenshtein, Jaccard, Cosine distance (WASM)", "analysis", "wasm/plugins/text_distance.wasm@wasm",
    )
    _register_plugin_info(
        registry, "hash_fingerprint", "Hash Fingerprint", "SHA256/BLAKE2b/MD5 fingerprinting (WASM)", "analysis", "wasm/plugins/hash_fingerprint.wasm@wasm",
    )


def _select_plugins_for_problem(
    problem: str, domain_hint: str = "", auto_mode: str = ""
) -> list[str]:
    """Smart plugin selection based on problem complexity, domain, and BLAST mode.

    Returns: list of plugin IDs to run
    """
    problem_lower = problem.lower()
    word_count = len(problem.split())
    selected: list[tuple[str, float]] = []

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

    if word_count >= 30:
        selected.append(("stat_tests", 0.5))
        selected.append(("info_theory", 0.5))
        selected.append(("swot", 0.3))
        selected.append(("delphi", 0.3))
    elif word_count >= 10:
        selected.append(("info_theory", 0.3))
        selected.append(("six_hats", 0.2))
    elif word_count <= 3 and auto_mode == "flash":
        pass

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
        pass

    best: dict[str, float] = {}
    for pid, score in selected:
        best[pid] = max(best.get(pid, 0.0), score)

    ranked = sorted(best.items(), key=lambda x: -x[1])
    result = [pid for pid, _ in ranked]

    max_plugins = {"turbo": 6, "solve": 4, "turbofactory": 8, "flash": 2}
    limit = max_plugins.get(auto_mode, 5)
    return result[:limit]


# ═══════════════════════════════════════════════════════════════════
# BUILT-IN TOOL PLUGINS
# ═══════════════════════════════════════════════════════════════════


class WebSearchPlugin(ToolPlugin):
    """Example plugin: Web search integration."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="web_search",
            version="1.0.0",
            description="Search the web for information",
            author="C4Reqber",
            requires=[],
        )

    def execute(self, query: str, max_results: int = 5) -> list[dict]:  # type: ignore[override, type-arg]
        return [
            {"title": f"Result {i}", "url": f"http://example.com/{i}"}
            for i in range(max_results)
        ]


class CalculatorPlugin(ToolPlugin):
    """Example plugin: Mathematical calculations."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="calculator",
            version="1.0.0",
            description="Perform mathematical calculations",
            author="C4Reqber",
            requires=[],
        )

    def execute(self, expression: str) -> float:  # type: ignore[override]
        """Execute."""
        from src.utils.safe_eval import safe_eval

        try:
            return safe_eval(expression.strip(), {
                "abs": abs,
                "max": max,
                "min": min,
                "pow": pow,
                "round": round,
            })
        except Exception:
            logger.warning("Calculator expression evaluation failed")
            raise


# ═══════════════════════════════════════════════════════════════════
# GLOBAL SINGLETON
# ═══════════════════════════════════════════════════════════════════

PLUGIN_REGISTRY: PluginRegistry = PluginRegistry().init_plugins()


__all__ = [
    "PluginRegistry",
    "PluginInfo",
    "ToolPlugin",
    "ToolMetadata",
    "PLUGIN_REGISTRY",
    "list_plugins",
    "list_plugins_by_category",
    "get_plugin",
    "execute_plugin",
    "select_plugins_for_problem",
    "get_plugin_registry",
    "WebSearchPlugin",
    "CalculatorPlugin",
    "PluginResultStore",
]
