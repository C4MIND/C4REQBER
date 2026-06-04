"""
Plugin Stage Router — maps each plugin to its correct pipeline stage.

WASM/compute plugins are NOT generic cognitive tools — they serve specific
pipeline stages where their computation has impact:

  Phase A (Cognitive Framing) → info_theory (C4 complexity scoring)
  Phase B (Knowledge Search)  → text_distance (paper dedup)
  Phase C (Gap Analysis)      → text_distance (abstract similarity), info_theory (gap complexity)
  Phase D (Hypothesis Gen)    → cognitive plugins (SWOT, Delphi, etc.)
  Phase E (Simulation)        → monte_carlo_pi, matrix_mult, dist_analyzer
  Phase F (Dissertation)      → hash_fingerprint (DiscoveryMemory)
  Phase G (Quality)           → stat_tests (p-value), dist_analyzer (KS test), info_theory
"""
from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)

# Each phase gets specific plugins that are USEFUL at that stage
PHASE_PLUGINS: dict[str, list[str]] = {
    "A": ["info_theory", "dim_reduction"],           # C4 framing → complexity + PCA
    "B": ["text_distance", "graph_metrics"],          # Knowledge → dedup + graph analysis
    "C": ["text_distance", "info_theory", "timeseries", "graph_metrics"],  # Gaps → similarity + entropy + trends
    "D": [                                             # Hypothesis gen → cognitive reasoning
        "swot", "delphi", "red_team", "six_hats", "scamper",
        "first_principles", "five_whys", "lateral_thinking",
        "ooda", "design_thinking", "ishikawa", "morphological",
    ],
    "E": ["monte_carlo_pi", "matrix_mult", "dist_analyzer",
          "signal_processing", "optimization", "timeseries"],  # Simulation → all compute
    "F": ["hash_fingerprint", "dim_reduction"],        # Dissertation → fingerprint + PCA
    "G": ["stat_tests", "dist_analyzer", "info_theory",
          "signal_processing", "optimization"],         # Quality → validation
}

ALL_COMPUTE_PLUGINS = {"monte_carlo_pi", "hash_fingerprint", "modular_math", "matrix_mult",
                        "text_distance", "stat_tests", "dist_analyzer", "info_theory",
                        "timeseries", "graph_metrics", "signal_processing", "dim_reduction",
                        "optimization"}

ALL_COGNITIVE_PLUGINS = set(PHASE_PLUGINS["D"])


def get_plugins_for_phase(phase: str) -> list[str]:
    """Return plugin IDs that should run during a specific pipeline phase."""
    return PHASE_PLUGINS.get(phase, [])


def execute_phase_plugins(phase: str, **kwargs: Any) -> dict[str, Any]:
    """Execute all plugins for a given pipeline phase.

    Returns: {plugin_id: result, ...}
    Graceful: failed plugins log warning and return error dict.
    """
    results: dict[str, Any] = {}
    plugin_ids = PHASE_PLUGINS.get(phase, [])

    for pid in plugin_ids:
        try:
            from src.plugins.v2_registry import execute_plugin
            result = execute_plugin(pid, **kwargs)
            results[pid] = result
        except Exception as e:
            logger.warning("Plugin %s failed in phase %s: %s", pid, phase, e)
            results[pid] = {"error": str(e)}

    return results


def get_stage_description(phase: str) -> str:
    """Human-readable description of what plugins do in this phase."""
    descriptions = {
        "A": "C4 complexity scoring (info_theory) + PCA (dim_reduction)",
        "B": "Paper dedup (text_distance) + graph analysis (graph_metrics)",
        "C": "Abstract similarity + gap complexity + trends (text_distance, info_theory, timeseries, graph_metrics)",
        "D": "Cognitive reasoning — SWOT, Delphi, 5Whys, Six Hats, SCAMPER...",
        "E": "Simulation validation — Monte Carlo, matrix, KS test, FFT, optimization, trends",
        "F": "Discovery fingerprinting (hash_fingerprint) + PCA of results (dim_reduction)",
        "G": "Statistical validation — t-test, KS, entropy, signal analysis, optimization",
    }
    return descriptions.get(phase, "unknown")


__all__ = ["get_plugins_for_phase", "execute_phase_plugins", "get_stage_description", "PHASE_PLUGINS", "ALL_COMPUTE_PLUGINS", "ALL_COGNITIVE_PLUGINS"]
