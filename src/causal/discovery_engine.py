"""
c4reqber: Causal Discovery Engine

Implements causal discovery algorithms on tabular data:
- PC (Peter-Clark): constraint-based
- FCI: Fast Causal Inference (handles latent confounders)
- NOTEARS: continuous optimization for DAGs
- ANM: Additive Noise Model (nonlinear)
"""
from __future__ import annotations

import logging
from typing import Any

import networkx as nx
import numpy as np
import pandas as pd

logger = logging.getLogger("c4reqber.causal.discovery")


class CausalDiscoveryEngine:
    """Run causal discovery algorithms on data."""

    ALGORITHMS = ("pc", "fci", "notears", "anm", "correlation")

    def discover(
        self,
        data: pd.DataFrame,
        algorithm: str = "pc",
    ) -> nx.DiGraph:
        """Discover causal graph from data.

        Args:
            data: DataFrame with numeric columns.
            algorithm: One of "pc", "fci", "notears", "anm", "correlation".

        Returns:
            Directed graph representing discovered causal structure.
        """
        algorithm = algorithm.lower()
        if algorithm not in self.ALGORITHMS:
            raise ValueError(f"Unknown algorithm: {algorithm}. Choose from: {self.ALGORITHMS}")

        # Ensure numeric data only
        numeric_data = data.select_dtypes(include=[np.number])
        if numeric_data.empty:
            raise ValueError("No numeric columns found in data")

        if algorithm == "pc":
            return self._pc(numeric_data)
        if algorithm == "fci":
            return self._fci(numeric_data)
        if algorithm == "notears":
            return self._notears(numeric_data)
        if algorithm == "anm":
            return self._anm(numeric_data)
        return self._correlation(numeric_data)

    def _pc(self, data: pd.DataFrame) -> nx.DiGraph:
        """Peter-Clark algorithm (constraint-based)."""
        try:
            from castle.algorithms import PC

            pc = PC()
            pc.learn(data.values)
            adj = pc.causal_matrix
            return self._matrix_to_graph(adj, data.columns)
        except ImportError:
            logger.warning("gcastle not installed, falling back to correlation")
            return self._correlation(data)
        except Exception as e:
            logger.warning("PC algorithm failed: %s", e)
            return self._correlation(data)

    def _fci(self, data: pd.DataFrame) -> nx.DiGraph:
        """Fast Causal Inference (handles latent confounders)."""
        try:
            from castle.algorithms import FCI

            fci = FCI()
            fci.learn(data.values)
            adj = fci.causal_matrix
            return self._matrix_to_graph(adj, data.columns)
        except ImportError:
            logger.warning("gcastle not installed, falling back to correlation")
            return self._correlation(data)
        except Exception as e:
            logger.warning("FCI algorithm failed: %s", e)
            return self._correlation(data)

    def _notears(self, data: pd.DataFrame) -> nx.DiGraph:
        """NOTEARS: continuous optimization for DAGs."""
        try:
            from castle.algorithms import Notears

            nt = Notears()
            nt.learn(data.values)
            adj = nt.causal_matrix
            return self._matrix_to_graph(adj, data.columns)
        except ImportError:
            logger.warning("gcastle not installed, falling back to correlation")
            return self._correlation(data)
        except Exception as e:
            logger.warning("NOTEARS algorithm failed: %s", e)
            return self._correlation(data)

    def _anm(self, data: pd.DataFrame) -> nx.DiGraph:
        """Additive Noise Model for pairwise direction discovery."""
        columns = list(data.columns)
        n = len(columns)
        g = nx.DiGraph()
        g.add_nodes_from(columns)

        for i in range(n):
            for j in range(i + 1, n):
                x = data[columns[i]].values
                y = data[columns[j]].values
                direction = self._anm_direction(x, y)
                if direction == 1:
                    g.add_edge(columns[i], columns[j])
                elif direction == -1:
                    g.add_edge(columns[j], columns[i])

        return g

    def _anm_direction(self, x: np.ndarray, y: np.ndarray) -> int:
        """Determine causal direction using ANM.

        Returns:
            1 if x -> y, -1 if y -> x, 0 if undetermined.
        """
        try:
            from sklearn.linear_model import LinearRegression
            from sklearn.preprocessing import PolynomialFeatures

            # Fit x -> y (nonlinear via polynomial features)
            poly = PolynomialFeatures(degree=2, include_bias=False)
            x_poly = poly.fit_transform(x.reshape(-1, 1))
            model_xy = LinearRegression().fit(x_poly, y)
            resid_xy = y - model_xy.predict(x_poly)
            # Test independence of x and resid_xy using correlation
            corr_xy = np.corrcoef(x, resid_xy)[0, 1]

            # Fit y -> x
            y_poly = poly.fit_transform(y.reshape(-1, 1))
            model_yx = LinearRegression().fit(y_poly, x)
            resid_yx = x - model_yx.predict(y_poly)
            corr_yx = np.corrcoef(y, resid_yx)[0, 1]

            # Lower correlation with residual indicates correct direction
            if abs(corr_xy) < abs(corr_yx) - 0.05:
                return 1
            if abs(corr_yx) < abs(corr_xy) - 0.05:
                return -1
            return 0
        except Exception:
            return 0

    def _correlation(self, data: pd.DataFrame) -> nx.DiGraph:
        """Fallback: correlation-based undirected graph."""
        columns = list(data.columns)
        corr = data.corr().abs()
        g = nx.DiGraph()
        g.add_nodes_from(columns)

        threshold = 0.3
        for i, col1 in enumerate(columns):
            for col2 in columns[i + 1:]:
                if corr.loc[col1, col2] > threshold:
                    # Arbitrary direction for fallback
                    g.add_edge(col1, col2)

        return g

    @staticmethod
    def _matrix_to_graph(adj: np.ndarray, columns: pd.Index | list[str]) -> nx.DiGraph:
        """Convert adjacency matrix to NetworkX DiGraph."""
        g = nx.DiGraph()
        g.add_nodes_from(columns)
        for i in range(len(columns)):
            for j in range(len(columns)):
                if adj[i, j] != 0:
                    g.add_edge(columns[i], columns[j])
        return g
