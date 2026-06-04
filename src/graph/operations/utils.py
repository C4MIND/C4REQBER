"""Graph mutation operations: edge utilities."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any


try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

if TYPE_CHECKING:
    from .core import KnowledgeGraph  # type: ignore[attr-defined]


def add_edge(
    self: KnowledgeGraph,
    from_id: str,
    to_id: str,
    edge_type: str,
    weight: float = 1.0,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Add an edge between two nodes."""
    with self.lock:
        if not self.has_node(from_id) or not self.has_node(to_id):
            return False

        if HAS_NETWORKX:
            self.graph.add_edge(
                from_id,
                to_id,
                edge_type=edge_type,
                weight=weight,
                metadata=metadata or {},
                timestamp=datetime.now().isoformat(),
            )
        else:
            self.graph["edges"].append(
                {
                    "from": from_id,
                    "to": to_id,
                    "edge_type": edge_type,
                    "weight": weight,
                    "metadata": metadata or {},
                }
            )

        self._pending_changes.append(
            {
                "op": "add_edge",
                "src": from_id,
                "tgt": to_id,
                "type": edge_type,
                "weight": weight,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._check_snapshot()

        return True


def add_citation(self: KnowledgeGraph, from_id: str, to_ref_id: str, context: str = "") -> Any:
    """Add a citation edge from discovery/project to reference."""
    return add_edge(
        self, from_id, to_ref_id, edge_type="cites", metadata={"context": context}
    )


def add_derivation(self: KnowledgeGraph, from_id: str, to_id: str, operator: str = "") -> Any:
    """Add derivation edge: to_id was derived from from_id."""
    return add_edge(
        self, from_id, to_id, edge_type="derived_from", metadata={"operator": operator}
    )


def add_transformation(self: KnowledgeGraph, from_state: str, to_state: str, operator: str) -> Any:
    """Add C4 state transformation edge."""
    return add_edge(
        self,
        from_state,
        to_state,
        edge_type="transformed_by",
        metadata={"operator": operator},
    )
