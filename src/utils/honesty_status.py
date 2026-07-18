"""Outer-status helpers — align with docs/HONESTY_CONTRACT.md.

Shared by MCP tools, discovery plugin runners, and API utilities.

Success requires **positive provenance** (real engine / LLM / compute ran).
Do not invent ``success`` for wrapper-only or bare self-declared status.
Do not demote real work to stub/unavailable — keep payloads and engines intact.
"""

from __future__ import annotations

from typing import Any


# Simulation / engine statuses that must not surface as outer MCP success.
_SIM_ERROR = frozenset({"error", "failed"})
_SIM_UNAVAILABLE = frozenset(
    {
        "unavailable",
        "skipped",
        "not_implemented",
        "simulated",  # legacy fake path
    }
)
_SIM_PARTIAL = frozenset({"partial", "stub", "timeout", "incomplete"})

# Named engines that may claim success when status is ok and not a fallback.
_REAL_ENGINES = frozenset(
    {
        "schr",
        "jaxsim",
        "newton",
        "newton_physics",
        "torchsim",
        "openfoam",
        "gromacs",
        "lammps",
        "fenicsx",
        "mujoco",
        "rebound",
        "amuse",
    }
)

# Numeric / structural evidence that a compute plugin actually ran.
_COMPUTE_EVIDENCE_KEYS = frozenset(
    {
        "p_value",
        "t_statistic",
        "entropy",
        "kl_divergence",
        "cohens_d",
        "chi2",
        "acf",
        "fft",
        "eigenvalues",
        "n_components",
        "posterior",
        "posterior_prob",
        "weighted_prediction",
        "best_x",
        "best_y",
    }
)


def outer_status_from_sim_payload(result: Any) -> str:
    """Map PatternRunner / bridge payload → outer status."""
    if not isinstance(result, dict):
        return "partial"

    stub = bool(result.get("stub"))
    heuristic = bool(result.get("heuristic"))
    raw_data = result.get("data")
    data: dict[str, Any] = raw_data if isinstance(raw_data, dict) else {}
    stub = stub or bool(data.get("stub"))
    heuristic = heuristic or bool(data.get("heuristic"))

    inner = str(result.get("status") or data.get("status") or "").lower()
    engine_truth = str(result.get("engine_truth") or data.get("engine_truth") or "")
    accelerated = result.get("accelerated")
    if accelerated is None:
        accelerated = data.get("accelerated")

    engine = str(result.get("engine") or data.get("engine") or "").lower()
    backend = str(result.get("backend") or data.get("backend") or "").lower()

    if stub or inner in _SIM_ERROR:
        return "error" if inner in _SIM_ERROR else "unavailable"
    if inner in _SIM_UNAVAILABLE:
        return "unavailable"
    if heuristic or inner in _SIM_PARTIAL or engine_truth.startswith("not_"):
        return "partial"
    if accelerated is False and any(
        tok in f"{engine} {backend}" for tok in ("fallback", "numpy", "cpu_stub", "heuristic")
    ):
        return "partial"
    if inner in {"success", "completed", "ok"}:
        # Positive provenance: explicit engine_truth, or named real engine
        # without fallback tokens (bridges should set engine_truth on success).
        if engine_truth and not engine_truth.startswith("not_"):
            return "success"
        if any(tok in f"{engine} {backend}" for tok in ("fallback", "numpy", "stub")):
            return "partial"
        if engine in _REAL_ENGINES or result.get("executed") is True:
            return "success"
        # Ambiguous bare success — refuse to invent green.
        return "partial"
    if not inner:
        return "partial"
    return "partial"


def outer_status_from_plugin_result(result: Any) -> str:
    """Plugin execute() returning without exception ≠ success of claimed analysis.

    Success needs positive provenance: ``llm_backed``, ``executed``, or compute
    evidence keys. Bare ``status: success`` alone is refused (not demoted to stub).
    """
    if result is None:
        return "partial"
    if isinstance(result, dict):
        if result.get("error") or result.get("status") in {"error", "failed"}:
            return "error"
        if result.get("abstained") is True or result.get("passed") is False:
            return "partial"
        st = str(result.get("status", "")).lower()
        if st in {"partial", "unavailable", "skipped", "ran"}:
            return st if st != "ran" else "partial"
        has_llm = result.get("llm_backed") is True
        has_exec = result.get("executed") is True or bool(result.get("backend"))
        has_compute = any(k in result for k in _COMPUTE_EVIDENCE_KEYS)
        # Positive provenance wins even if llm_backed is explicitly False
        # (numeric plugins are not LLM claims).
        if has_llm or has_exec or has_compute:
            if st in {"", "success", "completed", "ok", "passed"}:
                return "success"
            return "partial"
        # LLM explicitly missing and no other provenance — keep payload, not success.
        if result.get("llm_backed") is False:
            return "partial"
        # Opaque / bare self-declared success — refuse invented green.
        if st in {"success", "completed", "ok", "passed"}:
            return "partial"
        return "partial"
    return "partial"


def outer_status_from_hil_like(
    *,
    quality_passed_all: bool | None,
    quality_score: float | int | None,
    sim_status: str | None,
    gate_any_failed: bool = False,
    min_score: float = 40.0,
) -> str:
    """Shared HIL / turbo / solve outer status."""
    sim_s = str(sim_status or "").lower()
    if gate_any_failed or quality_passed_all is False:
        return "partial"
    if sim_s in _SIM_ERROR | _SIM_UNAVAILABLE | _SIM_PARTIAL | {"stub"}:
        return "partial"
    if isinstance(quality_score, (int, float)) and quality_score < min_score:
        return "partial"
    return "success"


def search_outer_status(*, total_found: int, sources_requested: bool) -> str:
    """Empty literature hit is partial (not success)."""
    if total_found <= 0:
        return "partial"
    return "success"


def record_field_status(obj: Any, default: str = "N/A") -> str:
    """Safe status from DiscoveryRecord fields (dict or object)."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return str(obj.get("status", default))
    return str(getattr(obj, "status", default))


def record_field_get(obj: Any, key: str, default: Any = None) -> Any:
    """Safe attribute/dict get for DiscoveryRecord nested payloads."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def bma_outer_status(result: Any) -> str:
    """BMA success only when weighted prediction / model posteriors exist."""
    if not isinstance(result, dict):
        return "partial"
    if result.get("error") or result.get("status") in {"error", "failed"}:
        return "error"
    if result.get("heuristic") is True or result.get("stub") is True:
        return "partial"
    models = result.get("models")
    has_weighted = "weighted_prediction" in result
    has_posteriors = isinstance(models, list) and any(
        isinstance(m, dict) and "posterior_prob" in m for m in models
    )
    if has_weighted and has_posteriors:
        return "success"
    return "partial"


def causal_outer_status(*, identifiable: bool | None, formula: Any) -> str:
    """Do-calculus success when the identifiability query actually completed.

    ``identifiable=False`` is still a real answer (not a green-fake).
    """
    if identifiable is None:
        return "partial"
    # Formula may be None when not identifiable — that is honest completion.
    return "success"
