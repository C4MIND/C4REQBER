"""
c4reqber: Ensemble Runner

Runs PatternRunnerV2 (or an injected runner) for each ensemble member.
Noise fallback is OFF by default — closed-loop must not invent evidence.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

import numpy as np

from src.discovery.closed_loop.experiment_designer import ExperimentDesign


logger = logging.getLogger("c4reqber.discovery.closed_loop")

# ExperimentDesigner names → PatternRunnerV2 pattern ids
_SIMULATOR_TO_PATTERN: dict[str, str] = {
    "physics": "newtonian",
    "monte_carlo": "monte_carlo",
    "acoustic": "acoustic_waves",
    "newtonian": "newtonian",
    "openmm": "openmm",
    "lammps": "lammps",
}


class _Runner(Protocol):
    def run(
        self,
        pattern_id: str,
        hypothesis: dict | None = None,
        engine: str | None = None,
        force_cpu: bool = False,
    ) -> Any: ...


def _extract_scalar(result: Any) -> float | None:
    """Pull a numeric observable from a PatternRunner result. No string-hash theater."""
    if not isinstance(result, dict):
        return None
    status = str(result.get("status", "")).lower()
    if (
        status in {"failed", "unavailable", "error", "skipped", "partial", "simulated"}
        or result.get("stub") is True
        or result.get("executed") is False
    ):
        return None
    if result.get("heuristic") is True:
        return None

    candidates: list[Any] = [
        result.get("potential_energy"),
        result.get("mean"),
        result.get("predicted"),
        result.get("value"),
        result.get("score"),
    ]
    data = result.get("data")
    if isinstance(data, dict):
        candidates.extend(
            [
                data.get("potential_energy"),
                data.get("mean"),
                data.get("mean_temperature"),
                data.get("total_energy_ry"),
                data.get("final_separation_au"),
                data.get("natoms"),
                data.get("t2_mean"),
            ]
        )
        nested = data.get("result")
        if isinstance(nested, dict):
            candidates.append(nested.get("potential_energy"))

    meta = result.get("metadata")
    if isinstance(meta, dict):
        candidates.append(meta.get("potential_energy"))

    for c in candidates:
        if isinstance(c, (int, float)) and not isinstance(c, bool):
            return float(c)
        if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
            return float(np.mean(c))

    # Refuse inventing scalars from note/output hashes
    return None


class EnsembleRunner:
    """Run simulator ensemble via PatternRunnerV2."""

    def __init__(
        self,
        runner: _Runner | None = None,
        *,
        allow_heuristic_fallback: bool = False,
    ) -> None:
        self._runner = runner
        self.allow_heuristic_fallback = allow_heuristic_fallback

    def _get_runner(self) -> _Runner:
        if self._runner is not None:
            return self._runner
        from src.simulations.runner_v2 import get_runner_v2

        return get_runner_v2()

    async def run_ensemble(
        self,
        design: ExperimentDesign,
        hypothesis: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run ensemble of simulations against a real pattern runner.

        Returns dict with predicted, observed, uncertainty.
        """
        pattern_id = _SIMULATOR_TO_PATTERN.get(design.simulator.lower(), design.simulator.lower())
        seed0 = int(design.params.get("seed", 42))
        rng = np.random.default_rng(seed0)
        scale = float(design.params.get("scale", 1.0))
        perturbation = float(design.params.get("perturbation", 0.0))

        runner = self._get_runner()
        scalars: list[float] = []
        raw_runs: list[dict[str, Any]] = []
        called = 0

        for i in range(max(1, design.n_runs)):
            hyp = dict(hypothesis or {})
            hyp.setdefault("text", hyp.get("text", f"ensemble:{pattern_id}"))
            hyp["seed"] = seed0 + i
            hyp["scale"] = scale
            hyp["perturbation"] = perturbation
            hyp["ensemble_index"] = i
            try:
                result = runner.run(pattern_id, hyp, force_cpu=True)
                called += 1
            except Exception as exc:
                logger.warning("Ensemble run %d failed: %s", i, exc)
                raw_runs.append({"error": str(exc), "index": i})
                continue

            if not isinstance(result, dict):
                result = {"output": str(result)}
            raw_runs.append(
                {"index": i, "status": result.get("status"), "engine": result.get("engine")}
            )
            scalar = _extract_scalar(result)
            if scalar is not None:
                scalars.append(scalar * scale + perturbation)

        # Need ≥2 independent scalars for predicted vs observed split
        if len(scalars) >= 2:
            arr = np.array(scalars, dtype=float)
            mid = len(arr) // 2
            predicted = float(np.mean(arr[:mid]))
            observed = float(np.mean(arr[mid:]))
            return {
                "predicted": predicted,
                "observed": observed,
                "uncertainty": float(np.std(arr)),
                "n_runs": design.n_runs,
                "n_successful": len(scalars),
                "runner_calls": called,
                "simulator": design.simulator,
                "pattern_id": pattern_id,
                "heuristic": False,
                "status": "ok",
                "note": "Ensemble from PatternRunnerV2 numeric observables",
                "run_summaries": raw_runs[:20],
            }

        if scalars:
            return {
                "predicted": None,
                "observed": None,
                "uncertainty": None,
                "n_runs": design.n_runs,
                "n_successful": len(scalars),
                "runner_calls": called,
                "simulator": design.simulator,
                "pattern_id": pattern_id,
                "heuristic": False,
                "status": "unavailable",
                "note": (
                    f"Only {len(scalars)} numeric observable(s) — "
                    "need ≥2 for predicted/observed comparison"
                ),
                "run_summaries": raw_runs[:20],
            }

        if not self.allow_heuristic_fallback:
            return {
                "predicted": None,
                "observed": None,
                "uncertainty": None,
                "n_runs": design.n_runs,
                "n_successful": 0,
                "runner_calls": called,
                "simulator": design.simulator,
                "pattern_id": pattern_id,
                "heuristic": False,
                "status": "unavailable",
                "note": "All PatternRunnerV2 ensemble members failed — no noise fallback",
                "run_summaries": raw_runs[:20],
            }

        # Explicit opt-in noise — observed jittered so Bayes never sees predicted==observed
        noise = []
        base = 1.0 + perturbation
        for _ in range(design.n_runs):
            noise.append(base * scale + rng.normal(0, design.target_uncertainty))
        arr = np.asarray(noise, dtype=float)
        observed_arr = arr + rng.normal(0, design.target_uncertainty, size=arr.shape)
        return {
            "predicted": float(np.mean(arr)),
            "observed": float(np.mean(observed_arr)),
            "uncertainty": float(np.std(arr)),
            "n_runs": design.n_runs,
            "n_successful": 0,
            "runner_calls": called,
            "simulator": design.simulator,
            "pattern_id": pattern_id,
            "heuristic": True,
            "status": "heuristic_fallback",
            "note": "FALLBACK noise only — PatternRunnerV2 produced no scalars",
            "run_summaries": raw_runs[:20],
        }
