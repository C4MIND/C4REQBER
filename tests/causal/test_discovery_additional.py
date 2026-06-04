"""Additional tests for causal discovery algorithms to improve coverage."""
from __future__ import annotations

import networkx as nx
import numpy as np
import pytest

from causal.discovery import (
    FCIAlgorithm,
    GESAlgorithm,
    PCAlgorithm,
    _residuals,
    fisher_z_test,
    partial_correlation,
    run_causal_discovery,
)


class TestPartialCorrelationEdgeCases:
    """Edge case tests for partial_correlation."""

    def test_zero_std_residuals_returns_zero(self):
        np.random.seed(42)
        # Create data where x and y are perfectly predicted by z
        z = np.ones(10)
        x = z.copy()
        y = z.copy()
        data = np.column_stack([x, y, z])
        corr = partial_correlation(data, 0, 1, [2])
        assert corr == 0.0

    def test_single_conditioning_variable(self):
        np.random.seed(42)
        z = np.random.randn(100)
        x = z + np.random.randn(100) * 0.1
        y = z + np.random.randn(100) * 0.1
        data = np.column_stack([x, y, z])
        corr = partial_correlation(data, 0, 1, [2])
        assert abs(corr) < 0.3

    def test_multiple_conditioning_variables(self):
        np.random.seed(42)
        z1 = np.random.randn(100)
        z2 = np.random.randn(100)
        x = z1 + z2 + np.random.randn(100) * 0.1
        y = z1 + z2 + np.random.randn(100) * 0.1
        data = np.column_stack([x, y, z1, z2])
        corr = partial_correlation(data, 0, 1, [2, 3])
        assert abs(corr) < 0.3

    def test_duplicate_z_removed(self):
        np.random.seed(42)
        z = np.random.randn(100)
        x = z + np.random.randn(100) * 0.1
        y = z + np.random.randn(100) * 0.1
        data = np.column_stack([x, y, z])
        # Pass duplicate z indices
        corr = partial_correlation(data, 0, 1, [2, 2, 2])
        assert abs(corr) < 0.3


class TestResidualsEdgeCases:
    """Edge case tests for _residuals."""

    def test_residuals_collinear_x(self):
        # When x columns are collinear, lstsq should still work
        x = np.column_stack([np.ones(10), np.ones(10)])
        y = np.arange(10)
        resid = _residuals(y, x)
        assert len(resid) == 10

    def test_residuals_single_point(self):
        x = np.array([[1.0]])
        y = np.array([2.0])
        resid = _residuals(y, x)
        assert len(resid) == 1

    def test_residuals_zero_variance(self):
        x = np.ones((10, 1))
        y = np.ones(10) * 5.0
        resid = _residuals(y, x)
        # All predictions should be 5.0, residuals ~0
        assert np.allclose(resid, 0.0, atol=1e-10)


class TestFisherZTestEdgeCases:
    """Edge case tests for fisher_z_test."""

    def test_negative_correlation(self):
        is_ind, p_val = fisher_z_test(-0.5, 100)
        assert isinstance(is_ind, (bool, np.bool_))
        assert 0.0 <= p_val <= 1.0

    def test_zero_correlation(self):
        is_ind, p_val = fisher_z_test(0.0, 100)
        assert is_ind == True
        assert p_val > 0.05

    def test_small_sample_size(self):
        is_ind, p_val = fisher_z_test(0.3, 5, k=2)
        # With n_eff <= 0, returns (False, 1.0)
        assert p_val == 1.0
        assert not is_ind

    def test_extreme_correlation(self):
        is_ind, p_val = fisher_z_test(0.99, 1000)
        assert is_ind == False
        assert p_val < 0.05

    def test_negative_n_eff(self):
        is_ind, p_val = fisher_z_test(0.3, 3, k=2)
        assert is_ind is False
        assert p_val == 1.0


class TestPCAlgorithmEdgeCases:
    """Edge case tests for PCAlgorithm."""

    def test_two_variables(self):
        np.random.seed(42)
        n = 200
        x = np.random.randn(n)
        y = 2 * x + np.random.randn(n) * 0.1
        data = np.column_stack([x, y])

        pc = PCAlgorithm(alpha=0.05)
        graph = pc.fit(data, ["X", "Y"])

        assert graph.number_of_nodes() == 2

    def test_four_variable_chain(self):
        np.random.seed(42)
        n = 500
        w = np.random.randn(n)
        x = w + np.random.randn(n) * 0.2
        y = x + np.random.randn(n) * 0.2
        z = y + np.random.randn(n) * 0.2
        data = np.column_stack([w, x, y, z])

        pc = PCAlgorithm(alpha=0.05)
        graph = pc.fit(data, ["W", "X", "Y", "Z"])

        assert graph.number_of_nodes() == 4
        assert "W" in graph
        assert "Z" in graph

    def test_orient_edges_empty_skeleton(self):
        pc = PCAlgorithm()
        import networkx as nx
        skeleton = nx.Graph()
        skeleton.add_nodes_from([0, 1, 2])
        cpdag = pc._orient_edges(skeleton, 3)
        assert cpdag.number_of_nodes() == 3

    def test_triples_no_valid(self):
        pc = PCAlgorithm()
        import networkx as nx
        g = nx.DiGraph()
        g.add_nodes_from([0, 1, 2])
        # No directed edges
        triples = pc._triples(g)
        assert triples == []

    def test_triples_with_directed_edges(self):
        pc = PCAlgorithm()
        import networkx as nx
        g = nx.DiGraph()
        g.add_edges_from([(0, 1), (1, 2)])
        triples = pc._triples(g)
        assert len(triples) >= 1
        assert (0, 1, 2) in triples


class TestFCIAlgorithmEdgeCases:
    """Edge case tests for FCIAlgorithm."""

    def test_three_variables_fork(self):
        np.random.seed(42)
        n = 300
        z = np.random.randn(n)
        x = z + np.random.randn(n) * 0.3
        y = z + np.random.randn(n) * 0.3
        data = np.column_stack([x, y, z])

        fci = FCIAlgorithm(alpha=0.05)
        pag = fci.fit(data, ["X", "Y", "Z"])

        assert pag.number_of_nodes() == 3
        assert "X" in pag
        assert "Y" in pag
        assert "Z" in pag

    def test_get_pag_edges_empty(self):
        fci = FCIAlgorithm()
        import networkx as nx
        pag = nx.DiGraph()
        pag.add_nodes_from(["A", "B"])
        edges = fci.get_pag_edges(pag)
        assert edges == []

    def test_get_pag_edges_with_types(self):
        fci = FCIAlgorithm()
        import networkx as nx
        pag = nx.DiGraph()
        pag.add_nodes_from(["A", "B"])
        pag.add_edge("A", "B", edge_type="->")
        edges = fci.get_pag_edges(pag)
        assert len(edges) == 1
        assert edges[0] == ("A", "B", "->")

    def test_orient_fci_no_changes(self):
        fci = FCIAlgorithm()
        import networkx as nx
        pag = nx.DiGraph()
        pag.add_nodes_from(["A", "B", "C"])
        pag.add_edge("A", "B", edge_type="->")
        pag.add_edge("B", "C", edge_type="->")
        fci._orient_fci(pag, ["A", "B", "C"])
        assert pag.edges["A", "B"]["edge_type"] == "->"


class TestGESAlgorithmEdgeCases:
    """Edge case tests for GESAlgorithm."""

    def test_single_variable(self):
        np.random.seed(42)
        data = np.random.randn(50, 1)
        ges = GESAlgorithm()
        dag = ges.fit(data, ["X"])
        assert dag.number_of_nodes() == 1
        assert nx.is_directed_acyclic_graph(dag)

    def test_bic_score_with_collinear_parents(self):
        np.random.seed(42)
        n = 50
        x = np.random.randn(n)
        # y depends on x but parents list includes duplicate info
        y = 2 * x + np.random.randn(n) * 0.1
        data = np.column_stack([x, y])

        ges = GESAlgorithm()
        # Test with parent that actually predicts child well
        score = ges._bic_score(data, [0], 1)
        assert isinstance(score, float)
        assert score > -1e10

    def test_bic_score_linalg_error(self):
        np.random.seed(42)
        n = 5
        # Create collinear data that triggers LinAlgError
        x = np.ones((n, 2))
        y = np.ones(n)
        data = np.column_stack([x[:, 0], y])

        ges = GESAlgorithm()
        score = ges._bic_score(data, [0], 1)
        assert isinstance(score, float)

    def test_fit_cpdaG(self):
        np.random.seed(42)
        data = np.random.randn(50, 2)
        ges = GESAlgorithm()
        cpdag = ges.fit_cpdaG(data, ["X", "Y"])
        assert cpdag.number_of_nodes() == 2

    def test_dag_to_cpdaG(self):
        ges = GESAlgorithm()
        import networkx as nx
        dag = nx.DiGraph()
        dag.add_nodes_from(["A", "B"])
        dag.add_edge("A", "B")
        cpdag = ges._dag_to_cpdaG(dag)
        assert cpdag is dag  # Currently returns as-is


class TestRunCausalDiscoveryEdgeCases:
    """Edge case tests for run_causal_discovery."""

    def test_pc_with_two_vars(self):
        np.random.seed(42)
        x = np.random.randn(100)
        y = 2 * x + np.random.randn(100) * 0.1
        data = np.column_stack([x, y])
        graph = run_causal_discovery(data, algorithm="pc", var_names=["X", "Y"])
        assert graph.number_of_nodes() == 2

    def test_fci_with_two_vars(self):
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        data = np.column_stack([x, y])
        graph = run_causal_discovery(data, algorithm="fci", var_names=["X", "Y"])
        assert graph.number_of_nodes() == 2

    def test_ges_with_two_vars(self):
        np.random.seed(42)
        x = np.random.randn(100)
        y = 2 * x + np.random.randn(100) * 0.1
        data = np.column_stack([x, y])
        graph = run_causal_discovery(data, algorithm="ges", var_names=["X", "Y"])
        assert graph.number_of_nodes() == 2
        assert nx.is_directed_acyclic_graph(graph)

    def test_default_var_names(self):
        np.random.seed(42)
        data = np.random.randn(50, 2)
        graph = run_causal_discovery(data, algorithm="pc")
        assert graph.has_node("X0")
        assert graph.has_node("X1")

    def test_unknown_algorithm_raises(self):
        data = np.random.randn(10, 2)
        with pytest.raises(ValueError, match="Unknown algorithm"):
            run_causal_discovery(data, algorithm="unknown_algo")
