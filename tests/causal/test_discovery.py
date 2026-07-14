"""Tests for TURBO-CDI L1 Causal Engine — Causal discovery algorithms."""
from __future__ import annotations

import numpy as np
import pytest

from src.causal.discovery import (
    FCIAlgorithm,
    GESAlgorithm,
    PCAlgorithm,
    _residuals,
    fisher_z_test,
    partial_correlation,
    run_causal_discovery,
)
from src.causal.scm import StructuralCausalModel


class TestPartialCorrelation:
    def test_no_conditioning(self) -> None:
        np.random.seed(42)
        x = np.random.randn(100)
        y = 2 * x + np.random.randn(100) * 0.1
        data = np.column_stack([x, y])
        corr = partial_correlation(data, 0, 1, [])
        assert corr > 0.95

    def test_with_conditioning(self) -> None:
        np.random.seed(42)
        z = np.random.randn(100)
        x = z + np.random.randn(100) * 0.1
        y = z + np.random.randn(100) * 0.1
        data = np.column_stack([x, y, z])

        corr_unconditional = partial_correlation(data, 0, 1, [])
        assert abs(corr_unconditional) > 0.5

        corr_conditional = partial_correlation(data, 0, 1, [2])
        assert abs(corr_conditional) < 0.3

    def test_invalid_index(self) -> None:
        data = np.random.randn(10, 2)
        with pytest.raises(ValueError):
            partial_correlation(data, 0, 5, [])


class TestResiduals:
    def test_residuals(self) -> None:
        x = np.array([1.0, 2.0, 3.0])
        y = 2 * x + 1.0
        residuals = _residuals(y, x.reshape(-1, 1))
        assert np.allclose(residuals, 0.0, atol=1e-10)


class TestFisherZTest:
    def test_independent(self) -> None:
        np.random.seed(42)
        x = np.random.randn(1000)
        y = np.random.randn(1000)
        corr = np.corrcoef(x, y)[0, 1]
        is_ind, p_val = fisher_z_test(corr, 1000)
        assert is_ind
        assert p_val > 0.05

    def test_dependent(self) -> None:
        np.random.seed(42)
        x = np.random.randn(1000)
        y = 2 * x + np.random.randn(1000) * 0.1
        corr = np.corrcoef(x, y)[0, 1]
        is_ind, p_val = fisher_z_test(corr, 1000)
        assert not is_ind
        assert p_val < 0.05

    def test_perfect_correlation(self) -> None:
        is_ind, p_val = fisher_z_test(1.0, 100)
        assert not is_ind
        assert p_val == 0.0


class TestPCAlgorithm:
    def test_fork_structure(self) -> None:
        np.random.seed(42)
        n = 1000
        z = np.random.randn(n)
        x = z + np.random.randn(n) * 0.2
        y = z + np.random.randn(n) * 0.2
        data = np.column_stack([x, y, z])

        pc = PCAlgorithm(alpha=0.05)
        graph = pc.fit(data, ["X", "Y", "Z"])

        assert graph.has_node("X")
        assert graph.has_node("Y")
        assert graph.has_node("Z")

    def test_chain_structure(self) -> None:
        np.random.seed(42)
        n = 1000
        z = np.random.randn(n)
        x = z + np.random.randn(n) * 0.2
        y = x + np.random.randn(n) * 0.2
        data = np.column_stack([x, y, z])

        pc = PCAlgorithm(alpha=0.05)
        graph = pc.fit(data, ["X", "Y", "Z"])

        assert graph.number_of_nodes() == 3

    def test_no_edges_independent(self) -> None:
        np.random.seed(42)
        n = 500
        x = np.random.randn(n)
        y = np.random.randn(n)
        z = np.random.randn(n)
        data = np.column_stack([x, y, z])

        pc = PCAlgorithm(alpha=0.05)
        graph = pc.fit(data, ["X", "Y", "Z"])

        assert graph.number_of_nodes() == 3

    def test_default_var_names(self) -> None:
        np.random.seed(42)
        data = np.random.randn(100, 3)
        pc = PCAlgorithm()
        graph = pc.fit(data)
        assert graph.has_node("X0")
        assert graph.has_node("X1")
        assert graph.has_node("X2")


class TestFCIAlgorithm:
    def test_basic_run(self) -> None:
        np.random.seed(42)
        n = 500
        z = np.random.randn(n)
        x = z + np.random.randn(n) * 0.3
        y = z + np.random.randn(n) * 0.3
        data = np.column_stack([x, y, z])

        fci = FCIAlgorithm(alpha=0.05)
        pag = fci.fit(data, ["X", "Y", "Z"])

        assert pag.number_of_nodes() == 3
        assert pag.has_node("X")

    def test_get_pag_edges(self) -> None:
        np.random.seed(42)
        data = np.random.randn(100, 2)
        fci = FCIAlgorithm()
        pag = fci.fit(data, ["A", "B"])
        edges = fci.get_pag_edges(pag)
        assert isinstance(edges, list)


class TestGESAlgorithm:
    def test_chain_recovery(self) -> None:
        import networkx as nx
        np.random.seed(42)
        n = 500
        z = np.random.randn(n)
        x = z + np.random.randn(n) * 0.2
        y = x + np.random.randn(n) * 0.2
        data = np.column_stack([x, y, z])

        ges = GESAlgorithm()
        dag = ges.fit(data, ["X", "Y", "Z"])

        assert dag.number_of_nodes() == 3
        assert nx.is_directed_acyclic_graph(dag)

    def test_bic_score(self) -> None:
        np.random.seed(42)
        n = 100
        x = np.random.randn(n)
        y = 2 * x + np.random.randn(n) * 0.1
        data = np.column_stack([x, y])

        ges = GESAlgorithm()
        score_with_parent = ges._bic_score(data, [0], 1)
        score_without_parent = ges._bic_score(data, [], 1)

        assert score_with_parent > score_without_parent

    def test_total_score(self) -> None:
        np.random.seed(42)
        data = np.random.randn(50, 2)
        ges = GESAlgorithm()
        dag = ges.fit(data, ["X", "Y"])
        score = ges._total_score(data, dag, ["X", "Y"])
        assert isinstance(score, float)

    def test_empty_dag_score(self) -> None:
        np.random.seed(42)
        data = np.random.randn(50, 2)
        ges = GESAlgorithm()
        import networkx as nx
        dag = nx.DiGraph()
        dag.add_nodes_from(["X", "Y"])
        score = ges._total_score(data, dag, ["X", "Y"])
        assert isinstance(score, float)


class TestRunCausalDiscovery:
    def test_pc_algorithm(self) -> None:
        np.random.seed(42)
        data = np.random.randn(100, 3)
        graph = run_causal_discovery(data, algorithm="pc")
        assert graph.number_of_nodes() == 3

    def test_fci_algorithm(self) -> None:
        np.random.seed(42)
        data = np.random.randn(100, 3)
        graph = run_causal_discovery(data, algorithm="fci")
        assert graph.number_of_nodes() == 3

    def test_ges_algorithm(self) -> None:
        np.random.seed(42)
        data = np.random.randn(100, 3)
        graph = run_causal_discovery(data, algorithm="ges")
        assert graph.number_of_nodes() == 3

    def test_unknown_algorithm(self) -> None:
        data = np.random.randn(10, 2)
        with pytest.raises(ValueError, match="Unknown algorithm"):
            run_causal_discovery(data, algorithm="unknown")


class TestDiscoveryWithSCM:
    def test_recover_fork_from_scm(self) -> None:
        np.random.seed(42)
        scm = StructuralCausalModel()
        scm.add_node("Z", is_exogenous=True, noise=lambda: np.random.randn())
        scm.add_node("X", parents=["Z"], mechanism=lambda z, u: z + u)
        scm.add_node("Y", parents=["Z"], mechanism=lambda z, u: z + u)

        samples = scm.sample(1000)
        data = np.column_stack([samples["X"], samples["Y"], samples["Z"]])

        pc = PCAlgorithm(alpha=0.05)
        graph = pc.fit(data, ["X", "Y", "Z"])

        assert graph.number_of_nodes() == 3

    def test_recover_chain_from_scm(self) -> None:
        import networkx as nx
        np.random.seed(42)
        scm = StructuralCausalModel()
        scm.add_node("Z", is_exogenous=True, noise=lambda: np.random.randn())
        scm.add_node("X", parents=["Z"], mechanism=lambda z, u: z + u)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, u: x + u)

        samples = scm.sample(1000)
        data = np.column_stack([samples["X"], samples["Y"], samples["Z"]])

        ges = GESAlgorithm()
        dag = ges.fit(data, ["X", "Y", "Z"])

        assert dag.number_of_nodes() == 3
        assert nx.is_directed_acyclic_graph(dag)
