"""Graph query operations: search, filter, traverse."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any


try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

if TYPE_CHECKING:
    from .core import KnowledgeGraph


def get_nodes_by_tag(self: KnowledgeGraph, tag: str) -> list[dict[str, Any]]:
    """Get all nodes with a specific tag."""
    if HAS_NETWORKX:
        return [
            dict(data)
            for _, data in self.graph.nodes(data=True)
            if tag in data.get("tags", [])
        ]
    return [
        data for data in self.graph["nodes"].values() if tag in data.get("tags", [])
    ]


def get_discoveries_by_domain(self: KnowledgeGraph, domain: str) -> list[dict[str, Any]]:
    """Get all discoveries in a domain."""
    return [
        node
        for node in self.get_nodes_by_type("discovery")
        if node.get("metadata", {}).get("domain") == domain
    ]


def get_neighbors(
    self: KnowledgeGraph, node_id: str, edge_type: str | None = None
) -> list[str]:
    """Get neighboring nodes."""
    if not self.has_node(node_id):
        return []

    if HAS_NETWORKX:
        neighbors = list(self.graph.neighbors(node_id))
        if edge_type:
            neighbors = [
                n
                for n in neighbors
                if self.graph.edges[node_id, n].get("edge_type") == edge_type
            ]
        return neighbors

    neighbors = []
    for edge in self.graph["edges"]:
        if edge["from"] == node_id:
            if edge_type is None or edge.get("edge_type") == edge_type:
                neighbors.append(edge["to"])
    return neighbors


def get_neighbors_with_edges(
    self: KnowledgeGraph, node_id: str, edge_type: str | None = None
) -> dict[str, dict[str, Any]]:
    """Get neighboring nodes with their edge data as a dictionary."""
    if not self.has_node(node_id):
        return {}

    result = {}
    if HAS_NETWORKX:
        for neighbor in self.graph.neighbors(node_id):
            edge_data = self.graph.edges[node_id, neighbor]
            if edge_type is None or edge_data.get("edge_type") == edge_type:
                result[neighbor] = dict(edge_data)
        return result

    for edge in self.graph["edges"]:
        if edge["from"] == node_id:
            if edge_type is None or edge.get("edge_type") == edge_type:
                result[edge["to"]] = edge
    return result


def get_citations(self: KnowledgeGraph, discovery_id: str) -> list[dict[str, Any]]:
    """Get all references cited by a discovery."""
    ref_ids = get_neighbors(self, discovery_id, edge_type="cites")
    return [self.get_node(rid) for rid in ref_ids if self.get_node(rid)]  # type: ignore[misc]


def get_all_nodes(self: KnowledgeGraph) -> list[dict[str, Any]]:
    """Get all nodes in the graph."""
    if HAS_NETWORKX:
        return [dict(data) for _, data in self.graph.nodes(data=True)]
    return list(self.graph["nodes"].values())


def get_all_edges(self: KnowledgeGraph) -> list[dict[str, Any]]:
    """Get all edges in the graph."""
    if HAS_NETWORKX:
        return [
            {"source": u, "target": v, **data}
            for u, v, data in self.graph.edges(data=True)
        ]
    return [
        {"source": edge["from"], "target": edge["to"], **edge}
        for edge in self.graph["edges"]
    ]


def find_shortest_path(
    self: KnowledgeGraph, source: str, target: str
) -> list[str] | None:
    """Find shortest path between two nodes."""
    if not HAS_NETWORKX:
        return None

    try:
        return nx.shortest_path(self.graph, source, target)  # type: ignore[no-any-return]
    except nx.NetworkXNoPath:
        return None


def find_clusters(self: KnowledgeGraph) -> list[list[str]]:
    """Find communities/clusters in the graph."""
    if not HAS_NETWORKX:
        return []

    undirected = self.graph.to_undirected()
    from networkx.algorithms import community

    communities = community.greedy_modularity_communities(undirected)
    return [list(c) for c in communities]


def bibliographic_coupling(
    self: KnowledgeGraph, ref_id: str, top_n: int = 5
) -> list[tuple[str, int]]:
    """Find papers that cite the same papers as ref_id."""
    if not HAS_NETWORKX:
        return []

    citing_ref = list(self.graph.predecessors(ref_id))

    coupling_scores = {}
    for other_ref in self.get_nodes_by_type("reference"):
        other_id = other_ref["node_id"]
        if other_id == ref_id:
            continue

        citing_other = set(self.graph.predecessors(other_id))
        shared = len(set(citing_ref) & citing_other)
        if shared > 0:
            coupling_scores[other_id] = shared

    return sorted(coupling_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]


def find_analogy_chains(
    self: KnowledgeGraph, source_domain: str, target_domain: str, max_length: int = 3
) -> list[list[str]]:
    """Find chains of analogies between domains."""
    if not HAS_NETWORKX:
        return []

    source_node = f"domain_{source_domain}"
    target_node = f"domain_{target_domain}"

    if not self.graph.has_node(source_node) or not self.graph.has_node(target_node):
        return []

    try:
        paths = list(
            nx.all_simple_paths(
                self.graph,
                source_node,
                target_node,
                cutoff=max_length * 2,
            )
        )
        return paths
    except nx.NetworkXNoPath:
        return []


def find_similar_nodes(
    self: KnowledgeGraph,
    query_embedding: list[float],
    node_type: str | None = None,
    top_k: int = 5,
) -> list[tuple[str, float]]:
    """Find nodes by cosine similarity to query embedding."""
    import numpy as np

    query_vec = np.array(query_embedding)
    similarities = []

    nodes = (
        self.get_nodes_by_type(node_type)
        if node_type
        else list(self.graph["nodes"].values())
        if not HAS_NETWORKX
        else [data for _, data in self.graph.nodes(data=True)]
    )

    for node in nodes:
        emb = node.get("embedding")
        if emb:
            node_vec = np.array(emb)
            sim = np.dot(query_vec, node_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(node_vec)
            )
            similarities.append((node["node_id"], float(sim)))

    return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]
