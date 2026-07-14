"""Graph Metrics Plugin — PageRank, degree centrality, clustering coefficient.

Does NOT duplicate: text_distance (token-level), matrix_mult (linear algebra).
UNIQUE: Graph-level analysis for knowledge graphs, citation networks, concept maps.
"""
from __future__ import annotations

from typing import Any


def degree_centrality(adjacency: dict[str, list[str]], directed: bool = False) -> dict[str, Any]:
    """Compute degree centrality for all nodes.

    Input: {"A": ["B","C"], "B": ["A"], "C": ["A","B"]}
    """
    if not adjacency:
        return {"error": "Empty adjacency dict"}

    n = len(adjacency)
    max_degree = n - 1 if n > 1 else 1

    centrality = {}
    for node, neighbors in adjacency.items():
        centrality[node] = round(len(neighbors) / max_degree, 4) if max_degree > 0 else 1.0

    ranked = sorted(centrality.items(), key=lambda x: -x[1])
    top3 = [(node, score) for node, score in ranked[:3]]

    return {
        "centrality": centrality,
        "top_nodes": [{"node": n, "score": s} for n, s in top3],
        "n_nodes": n,
        "max_degree": max_degree,
    }


def clustering_coefficient(adjacency: dict[str, list[str]]) -> dict[str, Any]:
    """Average clustering coefficient (undirected)."""
    if not adjacency:
        return {"error": "Empty adjacency dict"}

    node_to_idx = {node: i for i, node in enumerate(adjacency)}
    coefficients = {}

    for node, neighbors in adjacency.items():
        neighbor_set = set(neighbors)
        k = len(neighbor_set)
        if k < 2:
            coefficients[node] = 0.0
            continue

        # Count edges between neighbors
        edges = 0
        for n1 in neighbor_set:
            if n1 in adjacency:
                for n2 in adjacency[n1]:
                    if n2 in neighbor_set and node_to_idx.get(n2, 0) > node_to_idx.get(n1, -1):
                        edges += 1

        possible = k * (k - 1) / 2
        coefficients[node] = round(edges / possible, 4) if possible > 0 else 0.0

    avg = sum(coefficients.values()) / len(coefficients) if coefficients else 0.0

    return {
        "coefficients": coefficients,
        "average": round(avg, 4),
        "n_nodes": len(adjacency),
    }


def pagerank(adjacency: dict[str, list[str]], damping: float = 0.85, iterations: int = 50) -> dict[str, Any]:
    """Simple PageRank algorithm."""
    if not adjacency:
        return {"error": "Empty adjacency dict"}

    nodes = list(adjacency.keys())
    n = len(nodes)
    rank = {node: 1.0 / n for node in nodes}

    for _ in range(iterations):
        new_rank = {node: (1 - damping) / n for node in nodes}
        for node in nodes:
            if node in adjacency and adjacency[node]:
                out = len(adjacency[node])
                for target in adjacency[node]:
                    if target in new_rank:
                        new_rank[target] += damping * rank[node] / out

        # Handle dangling nodes
        dangling_sum = damping * sum(rank[n] for n in nodes if not adjacency.get(n)) / n
        for node in nodes:
            new_rank[node] += dangling_sum

        rank = new_rank

    ranked = sorted(rank.items(), key=lambda x: -x[1])
    top5 = [{"node": n, "score": round(s, 6)} for n, s in ranked[:5]]

    return {
        "pagerank": {n: round(s, 6) for n, s in rank.items()},
        "top_nodes": top5,
        "damping": damping,
        "n_nodes": n,
    }


def connected_components(adjacency: dict[str, list[str]]) -> dict[str, Any]:
    """Find connected components via BFS (undirected)."""
    if not adjacency:
        return {"error": "Empty adjacency dict"}

    visited: set[str] = set()
    components: list[list[str]] = []

    for node in adjacency:
        if node not in visited:
            comp = []
            queue = [node]
            visited.add(node)
            while queue:
                current = queue.pop(0)
                comp.append(current)
                for neighbor in adjacency.get(current, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(comp)

    sizes = [len(c) for c in components]

    return {
        "components": len(components),
        "largest_size": max(sizes) if sizes else 0,
        "sizes": sizes,
        "n_nodes": len(adjacency),
        "is_connected": len(components) == 1,
    }


# ── Pipeline interface ─────────────────────────────────────────────────

def execute(problem: str = "", hypothesis_text: str = "", **kwargs: Any) -> dict[str, Any]:
    """Run graph analysis on provided adjacency dict.

    metric: "centrality" | "clustering" | "pagerank" | "components"
    adjacency: dict of node → list of neighbors
    """
    metric = kwargs.get("metric", "centrality")
    adjacency = kwargs.get("adjacency", {})

    try:
        if metric == "pagerank":
            return pagerank(adjacency)
        elif metric == "clustering":
            return clustering_coefficient(adjacency)
        elif metric == "components":
            return connected_components(adjacency)
        else:
            return degree_centrality(adjacency)
    except Exception as e:
        return {"error": str(e), "metric": metric}
