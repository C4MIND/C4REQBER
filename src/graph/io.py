"""Serialization and deserialization for the knowledge graph."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING


try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

if TYPE_CHECKING:
    from .core import KnowledgeGraph


def export_to_json(self: KnowledgeGraph, path: str) -> bool:
    """Export graph to JSON for visualization. Returns True on success."""
    if HAS_NETWORKX:
        data = {
            "nodes": [{"id": n, **data} for n, data in self.graph.nodes(data=True)],
            "edges": [
                {"source": u, "target": v, **data}
                for u, v, data in self.graph.edges(data=True)
            ],
        }
    else:
        data = self.graph

    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except OSError as e:
        print(f"⚠️  Failed to export JSON: {e}")
        return False


def export_to_graphml(self: KnowledgeGraph, path: str) -> bool:
    """Export to GraphML for Gephi/Cytoscape. Returns True on success."""
    if not HAS_NETWORKX:
        return False
    try:
        nx.write_graphml(self.graph, path)
        return True
    except OSError as e:
        print(f"⚠️  Failed to export GraphML: {e}")
        return False
