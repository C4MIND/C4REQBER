"""Tests for GPSCM."""
from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd
import pytest

from src.causal.gp_scm import GPSCM


class TestGPSCM:
    @pytest.fixture
    def chain_data(self) -> pd.DataFrame:
        rng = np.random.default_rng(42)
        n = 300
        x0 = rng.normal(0, 1, n)
        x1 = 2 * x0 + rng.normal(0, 0.5, n)
        x2 = 1.5 * x1 + rng.normal(0, 0.5, n)
        return pd.DataFrame({"X0": x0, "X1": x1, "X2": x2})

    @pytest.fixture
    def chain_graph(self) -> nx.DiGraph:
        g = nx.DiGraph()
        g.add_edges_from([("X0", "X1"), ("X1", "X2")])
        return g

    def test_fit_and_counterfactual(self, chain_data: pd.DataFrame, chain_graph: nx.DiGraph) -> None:
        gp = GPSCM()
        gp.fit(chain_data, chain_graph)

        evidence = {"X0": 1.0, "X1": 2.0, "X2": 3.0}
        intervention = {"X0": 2.0}
        result = gp.counterfactual(evidence, intervention, "X2")

        assert isinstance(result.factual_value, float)
        assert isinstance(result.counterfactual_value, float)
        assert isinstance(result.effect, float)

    def test_counterfactual_not_fitted_raises(self) -> None:
        gp = GPSCM()
        with pytest.raises(RuntimeError, match="not fitted"):
            gp.counterfactual({}, {}, "X")

    def test_fit_linear_fallback(self, chain_data: pd.DataFrame, chain_graph: nx.DiGraph) -> None:
        # Test that _fit_linear produces valid models
        gp = GPSCM()
        gp._fit_linear(chain_data, chain_graph)
        assert all(m["type"] in ("mean", "linear") for m in gp._models.values())

    def test_forward_simulate_propagates(self, chain_data: pd.DataFrame, chain_graph: nx.DiGraph) -> None:
        gp = GPSCM()
        gp.fit(chain_data, chain_graph)
        noise = {node: 0.0 for node in chain_graph.nodes}
        values = {"X0": 1.0}
        result = gp._forward_simulate(values, noise)
        assert "X1" in result
        assert "X2" in result
