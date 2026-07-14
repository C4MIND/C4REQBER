"""Graph mutation operations: core node additions."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any


try:
    import networkx as nx

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False

from src.graph.core import NodeData


if TYPE_CHECKING:
    from src.graph.core import KnowledgeGraph


def add_discovery(
    self: KnowledgeGraph,
    problem: str,
    hypothesis: str,
    confidence_score: float,
    contradiction: dict[str, Any] | None = None,
    c4_path: list[str] | None = None,
    domain: str = "general",
    falsifiability_criteria: list[dict] | None = None,  # type: ignore[type-arg]
    llm_provider: str | None = None,
    llm_model: str | None = None,
    tags: list[str] | None = None,
    embedding: list[float] | None = None,
) -> str:
    """Add a discovery/hypothesis node."""
    with self.lock:
        self._node_counters["discovery"] += 1
        node_id = f"discovery_{self._node_counters['discovery']}"

        node_data = NodeData(
            node_id=node_id,
            node_type="discovery",
            metadata={
                "problem": problem,
                "hypothesis": hypothesis,
                "contradiction": contradiction,
                "c4_path": c4_path,
                "confidence_score": confidence_score,
                "domain": domain,
                "falsifiability_criteria": falsifiability_criteria or [],
                "status": "pending",
                "llm_provider": llm_provider,
                "llm_model": llm_model,
            },
            tags=tags or [],
            embedding=embedding,
        )

        if HAS_NETWORKX:
            self.graph.add_node(node_id, **node_data.to_dict())
        else:
            self.graph["nodes"][node_id] = node_data.to_dict()

        self._pending_changes.append(
            {
                "op": "add_node",
                "id": node_id,
                "type": "discovery",
                "data": node_data.to_dict(),
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._check_snapshot()

        return node_id


def add_project(
    self: KnowledgeGraph,
    name: str,
    description: str = "",
    domain: str = "general",
    objectives: list[str] | None = None,
    discovery_ids: list[str] | None = None,
    tags: list[str] | None = None,
) -> str:
    """Add a research project node."""
    with self.lock:
        self._node_counters["project"] += 1
        node_id = f"project_{self._node_counters['project']}"

        node_data = NodeData(
            node_id=node_id,
            node_type="project",
            metadata={
                "name": name,
                "description": description,
                "domain": domain,
                "objectives": objectives or [],
                "discovery_ids": discovery_ids or [],
                "status": "active",
            },
            tags=tags or [],
        )

        if HAS_NETWORKX:
            self.graph.add_node(node_id, **node_data.to_dict())
            for disc_id in discovery_ids or []:
                if self.has_node(disc_id):
                    self.graph.add_edge(
                        node_id, disc_id, edge_type="contains", weight=1.0
                    )
        else:
            self.graph["nodes"][node_id] = node_data.to_dict()

        self._pending_changes.append(
            {
                "op": "add_node",
                "id": node_id,
                "type": "project",
                "data": node_data.to_dict(),
                "edges": [
                    {"to": d, "type": "contains"} for d in (discovery_ids or [])
                ],
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._check_snapshot()

        return node_id


def add_reference(
    self: KnowledgeGraph,
    title: str,
    authors: list[str],
    year: int,
    source: str,
    source_id: str,
    abstract: str = "",
    url: str = "",
    tags: list[str] | None = None,
    embedding: list[float] | None = None,
) -> str:
    """Add a bibliographic reference node."""
    with self.lock:
        self._node_counters["reference"] += 1
        node_id = f"reference_{self._node_counters['reference']}"

        node_data = NodeData(
            node_id=node_id,
            node_type="reference",
            metadata={
                "title": title,
                "authors": authors,
                "year": year,
                "source": source,
                "source_id": source_id,
                "abstract": abstract,
                "url": url,
                "citation_count": 0,
            },
            tags=tags or [],
            embedding=embedding,
        )

        if HAS_NETWORKX:
            self.graph.add_node(node_id, **node_data.to_dict())
        else:
            self.graph["nodes"][node_id] = node_data.to_dict()

        self._pending_changes.append(
            {
                "op": "add_node",
                "id": node_id,
                "type": "reference",
                "data": node_data.to_dict(),
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._check_snapshot()

        return node_id
