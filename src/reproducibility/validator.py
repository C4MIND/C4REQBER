"""Reproducibility validator for C4REQBER experiments."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


@dataclass
class ReproducibilityReport:
    """ReproducibilityReport."""
    experiment_id: str
    checks: list[dict[str, Any]]
    is_reproducible: bool
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "checks": self.checks,
            "is_reproducible": self.is_reproducible,
            "score": self.score,
        }

def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def compute_experiment_hash(data: Any) -> str:
    return hashlib.sha256(_canonical(data).encode()).hexdigest()[:8]

def verify_result_match(
    results: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    tolerance: float = 1e-6,
) -> tuple[bool, str]:
    """Verify result match."""
    if len(results) != len(expected):
        return False, f"Count mismatch: {len(results)} vs {len(expected)}"

    for i, (r, e) in enumerate(zip(results, expected)):  # noqa: B905
        common_keys = set(r) & set(e)
        if not common_keys:
            continue
        for k in sorted(common_keys):
            rv, ev = r.get(k), e.get(k)
            if isinstance(rv, (int, float)) and isinstance(ev, (int, float)):
                if abs(rv - ev) >= tolerance:
                    return False, f"Mismatch at run {i}, key {k}: {rv} != {ev}"
            elif rv != ev:
                return False, f"Mismatch at run {i}, key {k}: {rv!r} != {ev!r}"
    return True, "All results match within tolerance"

def validate_experiment(
    experiment_config: dict[str, Any],
    results: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    tolerance: float = 1e-6,
) -> ReproducibilityReport:
    """Validate experiment."""
    config_hash = compute_experiment_hash(experiment_config)

    checks: list[dict[str, Any]] = []
    issues = 0
    total = 0

    has_seed = "seed" in experiment_config or "random_state" in experiment_config
    checks.append({"name": "config_deterministic", "passed": has_seed})
    total += 1
    if not has_seed:
        issues += 1

    if expected:
        total += 1
        match, detail = verify_result_match(results, expected, tolerance)
        checks.append({
            "name": "results_match",
            "passed": match,
            "detail": detail,
        })
        if not match:
            issues += 1

    if results:
        total += 1
        result_hash = compute_experiment_hash(results)
        checks.append({
            "name": "result_hash",
            "passed": result_hash != "",
            "detail": result_hash,
        })
        if not result_hash:
            issues += 1

    score = round(100 * (1 - issues / max(total, 1)), 2)

    return ReproducibilityReport(
        experiment_id=config_hash,
        checks=checks,
        is_reproducible=score >= 80,
        score=score,
    )

def compare_runs(
    run_a: list[dict[str, Any]],
    run_b: list[dict[str, Any]],
    tolerance: float = 1e-6,
) -> dict[str, Any]:
    """Compare two independent runs for reproducibility."""
    match, detail = verify_result_match(run_a, run_b, tolerance)
    run_a_hash = compute_experiment_hash(run_a)
    run_b_hash = compute_experiment_hash(run_b)
    return {
        "match": match,
        "detail": detail,
        "run_a_hash": run_a_hash,
        "run_b_hash": run_b_hash,
        "identical_hashes": run_a_hash == run_b_hash,
    }
