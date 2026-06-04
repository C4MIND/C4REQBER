"""C4REQBER: A/B testing for pipeline configurations."""
from __future__ import annotations

import hashlib
import random
import statistics
from dataclasses import dataclass, field
from typing import Any

from src.pipeline.config import PipelineConfig


@dataclass
class Variant:
    """A single A/B test variant."""

    variant_id: str
    name: str
    config: PipelineConfig
    traffic_weight: float = 1.0
    metrics: dict[str, list[float]] = field(default_factory=dict)

    def record(self, metric: str, value: float) -> None:
        """Record a metric observation."""
        if metric not in self.metrics:
            self.metrics[metric] = []
        self.metrics[metric].append(value)

    def mean(self, metric: str) -> float | None:
        """Return mean for a metric."""
        vals = self.metrics.get(metric, [])
        return statistics.mean(vals) if vals else None

    def std(self, metric: str) -> float | None:
        """Return sample standard deviation for a metric."""
        vals = self.metrics.get(metric, [])
        return statistics.stdev(vals) if len(vals) > 1 else (0.0 if vals else None)

    def count(self, metric: str) -> int:
        return len(self.metrics.get(metric, []))

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "name": self.name,
            "traffic_weight": self.traffic_weight,
            "metrics": {k: {"count": len(v), "mean": self.mean(k)} for k, v in self.metrics.items()},
        }


class ABTestManager:
    """
    Manages A/B tests for pipeline configurations.

    Usage::

        ab = ABTestManager()
        ab.register_variant("control", control_config)
        ab.register_variant("treatment", treatment_config)

        variant = ab.assign_user("user-123")
        # run pipeline with variant.config ...
        ab.record_result(variant.variant_id, "solution_quality", 0.85)
    """

    def __init__(self) -> None:
        self._variants: dict[str, Variant] = {}
        self._user_assignments: dict[str, str] = {}

    def register_variant(
        self,
        name: str,
        config: PipelineConfig,
        traffic_weight: float = 1.0,
    ) -> str:
        """Register a variant and return its generated ID."""
        variant_id = hashlib.sha256(name.encode()).hexdigest()[:12]
        self._variants[variant_id] = Variant(
            variant_id=variant_id,
            name=name,
            config=config,
            traffic_weight=traffic_weight,
        )
        return variant_id

    def assign_user(self, user_id: str) -> Variant:
        """Assign a user to a variant (sticky + weighted random)."""
        if user_id in self._user_assignments:
            vid = self._user_assignments[user_id]
            return self._variants[vid]

        if not self._variants:
            raise ValueError("No variants registered")

        weights = [v.traffic_weight for v in self._variants.values()]
        total = sum(weights)
        if total == 0:
            raise ValueError("All variant weights are zero")

        # Deterministic but balanced assignment
        hash_val = int(hashlib.sha256(user_id.encode()).hexdigest(), 16)
        rnd = random.Random(hash_val)
        chosen = rnd.choices(list(self._variants.values()), weights=weights, k=1)[0]
        self._user_assignments[user_id] = chosen.variant_id
        return chosen

    def record_result(self, variant_id: str, metric: str, value: float) -> None:
        """Record a metric for a variant."""
        if variant_id not in self._variants:
            raise ValueError(f"Unknown variant: {variant_id}")
        self._variants[variant_id].record(metric, value)

    def get_results(self) -> dict[str, dict[str, Any]]:
        """Return statistics for all variants."""
        return {vid: v.to_dict() for vid, v in self._variants.items()}

    def is_significant(self, variant_a: str, variant_b: str, metric: str) -> bool:
        """
        Check whether the difference between two variants is statistically
        significant using Welch's t-test.

        Returns ``True`` if p < 0.05 and both variants have >= 2 observations.
        """
        try:
            from scipy import stats
        except ImportError as err:
            raise RuntimeError("scipy is required for significance testing") from err

        a = self._variants.get(variant_a)
        b = self._variants.get(variant_b)
        if not a or not b:
            raise ValueError("Both variants must exist")

        vals_a = a.metrics.get(metric, [])
        vals_b = b.metrics.get(metric, [])
        if len(vals_a) < 2 or len(vals_b) < 2:
            return False

        _, pvalue = stats.ttest_ind(vals_a, vals_b, equal_var=False)
        return bool(pvalue < 0.05)

    def best_variant(self, metric: str) -> Variant | None:
        """Return the variant with the highest mean for a metric."""
        candidates = [
            (v.mean(metric), v)
            for v in self._variants.values()
            if v.mean(metric) is not None
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0], reverse=True)  # type: ignore[arg-type, return-value]
        return candidates[0][1]

    def get_config_for_user(self, user_id: str) -> PipelineConfig:
        """Convenience: get the PipelineConfig assigned to a user."""
        return self.assign_user(user_id).config


def apply_ab_config(
    ab_manager: ABTestManager,
    user_id: str,
    base_config: PipelineConfig | None = None,
) -> PipelineConfig:
    """
    Resolve the final pipeline config for a user.

    If ``base_config`` is provided and no A/B variant overrides it,
    the base config is returned.
    """
    if not ab_manager._variants:
        if base_config is None:
            raise ValueError("No variants and no base config provided")
        return base_config
    return ab_manager.get_config_for_user(user_id)
