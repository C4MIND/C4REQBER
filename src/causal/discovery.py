"""C4REQBER L1 Causal Engine — Causal discovery algorithms."""
from __future__ import annotations

from itertools import combinations

import networkx as nx
import numpy as np
from scipy import stats


def partial_correlation(data: np.ndarray, x: int, y: int, z: list[int]) -> float:
    """
    Compute partial correlation between variables x and y controlling for z.

    Uses the recursive formula: ρ(xy|z) from residuals of linear regression.
    """
    n_vars = data.shape[1]
    if x >= n_vars or y >= n_vars:
        raise ValueError("Variable index out of range")

    if not z:
        return float(np.corrcoef(data[:, x], data[:, y])[0, 1])

    z = list(set(z))
    z_data = data[:, z]

    x_resid = _residuals(data[:, x], z_data)
    y_resid = _residuals(data[:, y], z_data)

    if np.std(x_resid) < 1e-10 or np.std(y_resid) < 1e-10:
        return 0.0

    return float(np.corrcoef(x_resid, y_resid)[0, 1])


def _residuals(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Compute residuals of y after regressing on x."""
    x_with_intercept = np.column_stack([np.ones(x.shape[0]), x])
    try:
        coeffs = np.linalg.lstsq(x_with_intercept, y, rcond=None)[0]
        predicted = x_with_intercept @ coeffs
        return y - predicted
    except np.linalg.LinAlgError:
        return y - np.mean(y)


def fisher_z_test(correlation: float, n: int, k: int = 0, alpha: float = 0.05) -> tuple[bool, float]:
    """
    Fisher's Z-test for conditional independence.

    H0: partial correlation = 0 (conditional independence)
    Returns (is_independent, p_value).
    """
    if abs(correlation) >= 1.0:
        return False, 0.0

    n_eff = n - k - 3
    if n_eff <= 0:
        return False, 1.0

    z_stat = 0.5 * np.log((1 + correlation) / (1 - correlation))
    se = 1.0 / np.sqrt(n_eff)
    z_score = z_stat / se

    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    is_independent = p_value > alpha

    return is_independent, float(p_value)


class PCAlgorithm:
    """
    PC Algorithm (Peter-Clark) for causal discovery.

    Constraint-based algorithm that learns a CPDAG (Completed Partially
    Directed Acyclic Graph) from observational data using conditional
    independence tests.

    Steps:
    1. Skeleton discovery: Start with complete undirected graph, remove edges
       based on conditional independence tests with increasing conditioning set size
    2. Orientation: Apply Meek orientation rules to direct edges
    """

    def __init__(self, alpha: float = 0.05) -> None:
        self.alpha = alpha
        self.separation_sets: dict[tuple[int, int], set[int]] = {}

    def fit(self, data: np.ndarray, var_names: list[str] | None = None) -> nx.DiGraph:
        """
        Run PC algorithm on data.

        Args:
            data: n_samples x n_variables array
            var_names: Optional names for variables

        Returns:
            A CPDAG represented as a DiGraph (bidirectional edges indicate undirected)
        """
        n_samples, n_vars = data.shape
        var_names = var_names or [f"X{i}" for i in range(n_vars)]

        skeleton = nx.Graph()
        skeleton.add_nodes_from(range(n_vars))
        for i, j in combinations(range(n_vars), 2):
            skeleton.add_edge(i, j)

        self.separation_sets = {}
        max_depth = n_vars - 2

        for depth in range(max_depth + 1):
            edges_to_remove = []
            for i, j in list(skeleton.edges()):
                if skeleton.degree(i) - 1 < depth:
                    continue

                neighbors_i = set(skeleton.neighbors(i)) - {j}
                if len(neighbors_i) < depth:
                    continue

                for z_subset in combinations(neighbors_i, depth):
                    z_list = list(z_subset)
                    corr = partial_correlation(data, i, j, z_list)
                    is_ind, p_val = fisher_z_test(corr, n_samples, len(z_list), self.alpha)

                    if is_ind:
                        edges_to_remove.append((i, j))
                        self.separation_sets[(i, j)] = set(z_subset)
                        self.separation_sets[(j, i)] = set(z_subset)
                        break

            for edge in edges_to_remove:
                if skeleton.has_edge(*edge):
                    skeleton.remove_edge(*edge)

            if not edges_to_remove:
                break

        cpdag = self._orient_edges(skeleton, n_vars)

        labeled_graph = nx.DiGraph()
        labeled_graph.add_nodes_from(var_names)
        for u, v in cpdag.edges():
            if cpdag.has_edge(v, u):
                if not labeled_graph.has_edge(var_names[u], var_names[v]):
                    labeled_graph.add_edge(var_names[u], var_names[v])
                    labeled_graph.add_edge(var_names[v], var_names[u])
            else:
                labeled_graph.add_edge(var_names[u], var_names[v])

        return labeled_graph

    def _orient_edges(self, skeleton: nx.Graph, n_vars: int) -> nx.DiGraph:
        """Apply PC orientation rules to the skeleton."""
        cpdag = nx.DiGraph()
        cpdag.add_nodes_from(range(n_vars))
        for u, v in skeleton.edges():
            cpdag.add_edge(u, v)
            cpdag.add_edge(v, u)

        for i, j in combinations(range(n_vars), 2):
            if not skeleton.has_edge(i, j):
                continue

            for k in range(n_vars):
                if k == i or k == j:
                    continue
                if not skeleton.has_edge(i, k) or not skeleton.has_edge(j, k):
                    continue

                if (i, j) in self.separation_sets:
                    sep_set = self.separation_sets[(i, j)]
                    if k not in sep_set:
                        if cpdag.has_edge(i, k) and cpdag.has_edge(k, i):
                            cpdag.remove_edge(k, i)
                        if cpdag.has_edge(j, k) and cpdag.has_edge(k, j):
                            pass

        changed = True
        while changed:
            changed = False
            for i, j, k in self._triples(cpdag):
                if cpdag.has_edge(i, j) and not cpdag.has_edge(j, i):
                    if cpdag.has_edge(j, k) and cpdag.has_edge(k, j):
                        if cpdag.has_edge(i, k) and cpdag.has_edge(k, i):
                            cpdag.remove_edge(k, j)
                            changed = True

            for i, j, k in self._triples(cpdag):
                if cpdag.has_edge(i, j) and not cpdag.has_edge(j, i):
                    if cpdag.has_edge(j, k) and not cpdag.has_edge(k, j):
                        if cpdag.has_edge(i, k) and cpdag.has_edge(k, i):
                            cpdag.remove_edge(k, i)
                            changed = True

        return cpdag

    def _triples(self, g: nx.DiGraph) -> list[tuple[int, int, int]]:
        """Generate all triples (i, j, k) where i -> j and j -- k."""
        triples = []
        nodes = sorted(g.nodes())
        for j in nodes:
            for i in g.predecessors(j):
                if not g.has_edge(j, i):
                    for k in g.successors(j):
                        if k != i:
                            triples.append((i, j, k))
        return triples


class FCIAlgorithm:
    """
    Fast Causal Inference (FCI) algorithm.

    Extends PC to handle latent confounders. Returns a PAG (Partial Ancestral Graph)
    with additional edge types: ->, <-, o->, <-o, o-o.

    Edge types in PAG:
    - A -> B: A is a direct cause of B
    - A o-> B: A may be a cause of B
    - A o-o B: A and B may be connected by a latent confounder
    """

    def __init__(self, alpha: float = 0.05) -> None:
        self.alpha = alpha
        self.separation_sets: dict[tuple[int, int], set[int]] = {}

    def fit(self, data: np.ndarray, var_names: list[str] | None = None) -> nx.DiGraph:
        """
        Run FCI algorithm (simplified version).

        Returns a PAG as a DiGraph with edge attributes indicating type.
        """
        n_samples, n_vars = data.shape
        var_names = var_names or [f"X{i}" for i in range(n_vars)]

        pc = PCAlgorithm(alpha=self.alpha)
        skeleton_graph = pc.fit(data, var_names)

        pag = nx.DiGraph()
        pag.add_nodes_from(var_names)

        for u, v in skeleton_graph.edges():
            if skeleton_graph.has_edge(v, u):
                if not pag.has_edge(u, v):
                    pag.add_edge(u, v, edge_type="o-o")
                    pag.add_edge(v, u, edge_type="o-o")
            else:
                pag.add_edge(u, v, edge_type="->")

        self._orient_fci(pag, var_names)

        return pag

    def _orient_fci(self, pag: nx.DiGraph, var_names: list[str]) -> None:
        """Apply FCI-specific orientation rules."""
        changed = True
        while changed:
            changed = False
            for i in var_names:
                for j in var_names:
                    if i == j:
                        continue
                    if not pag.has_edge(i, j):
                        continue

                    edge_type = pag.edges[i, j].get("edge_type", "o-o")
                    if edge_type == "o-o":
                        for k in var_names:
                            if k == i or k == j:
                                continue
                            if pag.has_edge(i, k) and pag.has_edge(k, i):
                                ik_type = pag.edges[i, k].get("edge_type", "o-o")
                                if ik_type == "->":
                                    if pag.edges[k, i].get("edge_type") != "->":
                                        if pag.has_edge(k, j) and pag.has_edge(j, k):
                                            pag.edges[j, k]["edge_type"] = "o->"
                                            changed = True

    def get_pag_edges(self, pag: nx.DiGraph) -> list[tuple[str, str, str]]:
        """Return edges with their PAG types."""
        edges = []
        seen = set()
        for u, v, data in pag.edges(data=True):
            if (v, u) not in seen:
                edge_type = data.get("edge_type", "o-o")
                edges.append((u, v, edge_type))
                seen.add((u, v))
        return edges


class GESAlgorithm:
    """
    Greedy Equivalence Search (GES) algorithm.

    Score-based causal discovery that searches over Markov equivalence classes
    of DAGs using a greedy hill-climbing approach with two phases:
    1. Forward phase: Add edges to maximize score
    2. Backward phase: Remove edges to maximize score

    Uses BIC (Bayesian Information Criterion) as the scoring function.
    """

    def __init__(self, penalty: float = 2.0) -> None:
        self.penalty = penalty

    def _bic_score(self, data: np.ndarray, parents: list[int], child: int) -> float:
        """
        Compute BIC score for a child variable given its parents.

        BIC = -2 * log_likelihood + k * log(n)
        where k is the number of parameters.
        """
        n_samples = data.shape[0]
        child_data = data[:, child]

        if not parents:
            ll = -0.5 * n_samples * np.log(np.var(child_data) + 1e-10)
            k = 1
        else:
            parent_data = data[:, parents]
            x_with_intercept = np.column_stack([np.ones(n_samples), parent_data])
            try:
                coeffs = np.linalg.lstsq(x_with_intercept, child_data, rcond=None)[0]
                residuals = child_data - x_with_intercept @ coeffs
                sigma2 = np.var(residuals) + 1e-10
                ll = -0.5 * n_samples * np.log(sigma2)
                k = len(parents) + 1
            except np.linalg.LinAlgError:
                ll = -1e10
                k = len(parents) + 1

        bic = -2 * ll + self.penalty * k * np.log(n_samples)
        return -bic

    def _total_score(self, data: np.ndarray, dag: nx.DiGraph, var_names: list[str]) -> float:
        """Compute total BIC score for a DAG."""
        name_to_idx = {name: i for i, name in enumerate(var_names)}
        total = 0.0
        for node in dag.nodes():
            parents = [name_to_idx[p] for p in dag.predecessors(node)]
            total += self._bic_score(data, parents, name_to_idx[node])
        return total

    def fit(self, data: np.ndarray, var_names: list[str] | None = None) -> nx.DiGraph:
        """
        Run GES algorithm on data.

        Returns the highest-scoring DAG found.
        """
        n_samples, n_vars = data.shape
        var_names = var_names or [f"X{i}" for i in range(n_vars)]

        dag = nx.DiGraph()
        dag.add_nodes_from(var_names)

        best_score = self._total_score(data, dag, var_names)

        changed = True
        while changed:
            changed = False

            for i, j in combinations(range(n_vars), 2):
                for u, v in [(i, j), (j, i)]:
                    if dag.has_edge(var_names[u], var_names[v]):
                        continue

                    test_dag = dag.copy()
                    test_dag.add_edge(var_names[u], var_names[v])

                    if not nx.is_directed_acyclic_graph(test_dag):
                        continue

                    score = self._total_score(data, test_dag, var_names)
                    if score > best_score:
                        dag = test_dag
                        best_score = score
                        changed = True
                        break
                if changed:
                    break

        changed = True
        while changed:
            changed = False
            for u, v in list(dag.edges()):
                test_dag = dag.copy()
                test_dag.remove_edge(u, v)

                score = self._total_score(data, test_dag, var_names)
                if score > best_score:
                    dag = test_dag
                    best_score = score
                    changed = True
                    break

        return dag

    def fit_cpdaG(self, data: np.ndarray, var_names: list[str] | None = None) -> nx.DiGraph:
        """Run GES and return a CPDAG representation."""
        dag = self.fit(data, var_names)
        cpdag = self._dag_to_cpdaG(dag)
        return cpdag

    def _dag_to_cpdaG(self, dag: nx.DiGraph) -> nx.DiGraph:
        """Convert DAG to CPDAG (simplified — just return DAG for now)."""
        return dag


def run_causal_discovery(
    data: np.ndarray,
    algorithm: str = "pc",
    var_names: list[str] | None = None,
    alpha: float = 0.05,
) -> nx.DiGraph:
    """
    Run a causal discovery algorithm on data.

    Args:
        data: n_samples x n_variables array
        algorithm: "pc", "fci", or "ges"
        var_names: Optional variable names
        alpha: Significance level for conditional independence tests

    Returns:
        Discovered causal graph
    """
    if algorithm == "pc":
        algo = PCAlgorithm(alpha=alpha)
    elif algorithm == "fci":
        algo = FCIAlgorithm(alpha=alpha)  # type: ignore[assignment]
    elif algorithm == "ges":
        algo = GESAlgorithm()  # type: ignore[assignment]
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    return algo.fit(data, var_names)
