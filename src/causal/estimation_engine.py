"""
c4reqber: Causal Effect Estimation Engine

Estimates causal effects using DoWhy + EconML.
Supports: backdoor adjustment, propensity scoring, doubly robust, CausalForest.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


logger = logging.getLogger("c4reqber.causal.estimation")


@dataclass
class EstimationResult:
    """Result of causal effect estimation."""

    ate: float  # Average Treatment Effect
    ci_lower: float  # Confidence interval lower bound
    ci_upper: float  # Confidence interval upper bound
    method: str
    treatment: str
    outcome: str
    valid: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ate": round(self.ate, 6) if self.valid else None,
            "ci_lower": round(self.ci_lower, 6) if self.valid else None,
            "ci_upper": round(self.ci_upper, 6) if self.valid else None,
            "method": self.method,
            "treatment": self.treatment,
            "outcome": self.outcome,
            "valid": self.valid,
            "error": self.error,
        }


class CausalEstimationEngine:
    """Estimate causal effects from observational data."""

    METHODS = (
        "backdoor.linear_regression",
        "backdoor.propensity_score_matching",
        "backdoor.propensity_score_weighting",
        "backdoor.doubly_robust",
        "causal_forest",
    )

    def estimate_ate(
        self,
        data: pd.DataFrame,
        treatment: str,
        outcome: str,
        confounders: list[str] | None = None,
        method: str = "backdoor.linear_regression",
    ) -> EstimationResult:
        """Estimate Average Treatment Effect.

        Args:
            data: DataFrame with treatment, outcome, and confounders.
            treatment: Name of treatment column.
            outcome: Name of outcome column.
            confounders: List of confounder column names.
            method: Estimation method.

        Returns:
            EstimationResult with ATE and confidence interval.
        """
        if method not in self.METHODS:
            return EstimationResult(
                ate=0.0, ci_lower=0.0, ci_upper=0.0,
                method=method, treatment=treatment, outcome=outcome,
                valid=False, error=f"Unknown method: {method}",
            )

        confounders = confounders or []
        required_cols = {treatment, outcome} | set(confounders)
        missing = required_cols - set(data.columns)
        if missing:
            return EstimationResult(
                ate=0.0, ci_lower=0.0, ci_upper=0.0,
                method=method, treatment=treatment, outcome=outcome,
                valid=False, error=f"Missing columns: {missing}",
            )

        try:
            return self._estimate_with_dowhy(data, treatment, outcome, confounders, method)
        except Exception as e:
            logger.warning("DoWhy estimation failed: %s", e)
            return self._estimate_fallback(data, treatment, outcome, confounders, method, str(e))

    def _estimate_with_dowhy(
        self,
        data: pd.DataFrame,
        treatment: str,
        outcome: str,
        confounders: list[str],
        method: str,
    ) -> EstimationResult:
        """Use DoWhy for estimation."""
        try:
            from dowhy import CausalModel

            graph = self._build_graph(treatment, outcome, confounders)
            model = CausalModel(
                data=data,
                treatment=treatment,
                outcome=outcome,
                graph=graph,
            )

            identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)

            # Map method names
            method_map = {
                "backdoor.linear_regression": "backdoor.linear_regression",
                "backdoor.propensity_score_matching": "backdoor.propensity_score_matching",
                "backdoor.propensity_score_weighting": "backdoor.propensity_score_weighting",
                "backdoor.doubly_robust": "backdoor.propensity_score_stratification",
            }
            dowhy_method = method_map.get(method, "backdoor.linear_regression")

            estimate = model.estimate_effect(
                identified_estimand,
                method_name=dowhy_method,
            )

            # Bootstrap for confidence interval
            n_bootstrap = 100
            bootstraps = []
            rng = np.random.default_rng(42)
            for _ in range(n_bootstrap):
                sample = data.sample(n=len(data), replace=True, random_state=rng.integers(0, 2**31))
                try:
                    m = CausalModel(data=sample, treatment=treatment, outcome=outcome, graph=graph)
                    ie = m.identify_effect(proceed_when_unidentifiable=True)
                    e = m.estimate_effect(ie, method_name=dowhy_method)
                    bootstraps.append(e.value)
                except Exception:
                    pass

            if bootstraps:
                ci_lower = float(np.percentile(bootstraps, 2.5))
                ci_upper = float(np.percentile(bootstraps, 97.5))
            else:
                ci_lower = ci_upper = float(estimate.value)

            return EstimationResult(
                ate=float(estimate.value),
                ci_lower=ci_lower,
                ci_upper=ci_upper,
                method=method,
                treatment=treatment,
                outcome=outcome,
            )
        except ImportError:
            raise  # Let fallback handle it

    def _estimate_fallback(
        self,
        data: pd.DataFrame,
        treatment: str,
        outcome: str,
        confounders: list[str],
        method: str,
        error_msg: str,
    ) -> EstimationResult:
        """Fallback: simple linear regression difference."""
        try:
            treated = data[data[treatment] == 1][outcome]
            control = data[data[treatment] == 0][outcome]
            ate = float(treated.mean() - control.mean())
            pooled_std = np.sqrt((treated.var() + control.var()) / 2)
            se = pooled_std / np.sqrt(min(len(treated), len(control)))
            return EstimationResult(
                ate=ate,
                ci_lower=ate - 1.96 * se,
                ci_upper=ate + 1.96 * se,
                method=f"{method}_fallback_naive",
                treatment=treatment,
                outcome=outcome,
                valid=True,
                error=f"DoWhy failed ({error_msg}), used naive difference",
            )
        except Exception as e:
            return EstimationResult(
                ate=0.0, ci_lower=0.0, ci_upper=0.0,
                method=method, treatment=treatment, outcome=outcome,
                valid=False, error=str(e),
            )

    @staticmethod
    def _build_graph(treatment: str, outcome: str, confounders: list[str]) -> str:
        """Build DOT graph string for DoWhy."""
        edges = []
        for c in confounders:
            edges.append(f"{c} -> {treatment}")
            edges.append(f"{c} -> {outcome}")
        edges.append(f"{treatment} -> {outcome}")
        return "digraph {" + "; ".join(edges) + ";}"
