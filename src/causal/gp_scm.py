"""
c4reqber: Gaussian Process Structural Causal Model (GP-SCM)

Learns structural functions as Gaussian Processes for accurate counterfactual inference.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd


logger = logging.getLogger("c4reqber.causal.gp_scm")


@dataclass
class CounterfactualResult:
    factual_value: float
    counterfactual_value: float
    effect: float
    uncertainty: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "factual_value": round(self.factual_value, 4),
            "counterfactual_value": round(self.counterfactual_value, 4),
            "effect": round(self.effect, 4),
            "uncertainty": round(self.uncertainty, 4),
        }


class GPSCM:
    """Gaussian Process Structural Causal Model."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph | None = None
        self._models: dict[str, Any] = {}
        self._nodes: list[str] = []

    def fit(self, data: pd.DataFrame, graph: nx.DiGraph) -> None:
        """Fit GP models for each node given its parents.

        Args:
            data: Training data.
            graph: Causal DAG.
        """
        self._graph = graph
        self._nodes = list(nx.topological_sort(graph))
        self._models = {}

        try:
            from sklearn.gaussian_process import GaussianProcessRegressor
            from sklearn.gaussian_process.kernels import RBF, WhiteKernel
        except ImportError:
            logger.warning("sklearn GaussianProcess not available, using linear fallback")
            self._fit_linear(data, graph)
            return

        for node in self._nodes:
            parents = list(graph.predecessors(node))
            y = data[node].values

            if not parents:
                # Exogenous: just model as GP of index (represents time/observation)
                X = np.arange(len(y)).reshape(-1, 1)
                kernel = RBF(length_scale=1.0) + WhiteKernel(noise_level=0.1)
                gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=2)
                gp.fit(X, y)
                self._models[node] = {"type": "gp_exogenous", "model": gp}
            else:
                X = data[parents].values
                kernel = RBF(length_scale=1.0) + WhiteKernel(noise_level=0.1)
                gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=2)
                gp.fit(X, y)
                self._models[node] = {"type": "gp", "parents": parents, "model": gp}

    def _fit_linear(self, data: pd.DataFrame, graph: nx.DiGraph) -> None:
        """Fallback linear fit."""
        from sklearn.linear_model import LinearRegression

        for node in self._nodes:
            parents = list(graph.predecessors(node))
            y = data[node].values
            if not parents:
                self._models[node] = {"type": "mean", "mean": float(np.mean(y))}
            else:
                X = data[parents].values
                lr = LinearRegression().fit(X, y)
                self._models[node] = {"type": "linear", "parents": parents, "model": lr}

    def counterfactual(
        self,
        evidence: dict[str, float],
        intervention: dict[str, float],
        target: str,
    ) -> CounterfactualResult:
        """Compute counterfactual query.

        Args:
            evidence: Observed evidence values.
            intervention: do-intervention values.
            target: Target variable to predict.

        Returns:
            CounterfactualResult.
        """
        if self._graph is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        # Step 1: Abduction - infer exogenous noise from evidence
        noise = self._infer_noise(evidence)

        # Step 2 & 3: Action + Prediction - mutilate graph and forward simulate
        cf_values = self._forward_simulate(intervention, noise)
        factual_values = self._forward_simulate(evidence, noise)

        return CounterfactualResult(
            factual_value=factual_values.get(target, 0.0),
            counterfactual_value=cf_values.get(target, 0.0),
            effect=cf_values.get(target, 0.0) - factual_values.get(target, 0.0),
            uncertainty=0.0,  # Could be computed from GP variance
        )

    def _infer_noise(self, evidence: dict[str, float]) -> dict[str, float]:
        """Infer exogenous noise for each node from evidence."""
        noise: dict[str, float] = {}
        for node in self._nodes:
            model_info = self._models.get(node, {})
            observed = evidence.get(node)
            if observed is None:
                noise[node] = 0.0
                continue

            parents = list(self._graph.predecessors(node))  # type: ignore[union-attr]
            if not parents:
                # Exogenous: noise = observed - mean prediction
                if model_info.get("type") == "mean":
                    predicted = model_info["mean"]
                elif model_info.get("type") == "gp_exogenous":
                    predicted = float(model_info["model"].predict(np.array([[0]]))[0])
                else:
                    predicted = observed
                noise[node] = observed - predicted
            else:
                parent_values = np.array([[evidence.get(p, 0.0) for p in parents]])
                if model_info.get("type") == "gp":
                    predicted = float(model_info["model"].predict(parent_values)[0])
                elif model_info.get("type") == "linear":
                    predicted = float(model_info["model"].predict(parent_values)[0])
                else:
                    predicted = observed
                noise[node] = observed - predicted

        return noise

    def _forward_simulate(
        self,
        values: dict[str, float],
        noise: dict[str, float],
    ) -> dict[str, float]:
        """Forward simulate through the SCM."""
        simulated = dict(values)
        for node in self._nodes:
            if node in simulated:
                continue  # Already set (intervention or evidence)

            model_info = self._models.get(node, {})
            parents = list(self._graph.predecessors(node))  # type: ignore[union-attr]
            node_noise = noise.get(node, 0.0)

            if not parents:
                if model_info.get("type") == "mean":
                    base = model_info["mean"]
                elif model_info.get("type") == "gp_exogenous":
                    base = float(model_info["model"].predict(np.array([[0]]))[0])
                else:
                    base = 0.0
                simulated[node] = base + node_noise
            else:
                parent_values = np.array([[simulated.get(p, 0.0) for p in parents]])
                if model_info.get("type") == "gp":
                    base = float(model_info["model"].predict(parent_values)[0])
                elif model_info.get("type") == "linear":
                    base = float(model_info["model"].predict(parent_values)[0])
                else:
                    base = sum(simulated.get(p, 0.0) for p in parents)
                simulated[node] = base + node_noise

        return simulated
