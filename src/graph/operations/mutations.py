"""Graph mutation operations: analogy, operator, experiment, and edge mutations."""
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


def add_analogy(
    self: KnowledgeGraph,
    source_domain: str,
    target_domain: str,
    source_concept: str,
    target_concept: str,
    mapping_type: str,
    confidence: float,
    semantic_similarity: float | None = None,
    structural_similarity: float | None = None,
    evidence: list[str] | None = None,
) -> str:
    """Add an analogy mapping node."""
    with self.lock:
        self._node_counters["analogy"] += 1
        node_id = f"analogy_{self._node_counters['analogy']}"

        node_data = NodeData(
            node_id=node_id,
            node_type="analogy",
            metadata={
                "source_domain": source_domain,
                "target_domain": target_domain,
                "source_concept": source_concept,
                "target_concept": target_concept,
                "mapping_type": mapping_type,
                "confidence": confidence,
                "semantic_similarity": semantic_similarity,
                "structural_similarity": structural_similarity,
                "evidence": evidence or [],
                "verified": False,
                "usage_count": 0,
            },
            tags=[source_domain, target_domain],
        )

        edges_added = []
        if HAS_NETWORKX:
            self.graph.add_node(node_id, **node_data.to_dict())
            for domain in [source_domain, target_domain]:
                domain_id = f"domain_{domain}"
                if not self.graph.has_node(domain_id):
                    self.graph.add_node(
                        domain_id,
                        node_type="domain",
                        name=domain,
                        created_at=datetime.now().isoformat(),
                    )
                    edges_added.append({"to": domain_id, "type": "domain_node"})
            self.graph.add_edge(
                node_id,
                f"domain_{source_domain}",
                edge_type="maps_from",
                weight=confidence,
            )
            self.graph.add_edge(
                node_id,
                f"domain_{target_domain}",
                edge_type="maps_to",
                weight=confidence,
            )
            edges_added.extend(
                [
                    {
                        "to": f"domain_{source_domain}",
                        "type": "maps_from",
                        "weight": confidence,  # type: ignore[dict-item]
                    },
                    {
                        "to": f"domain_{target_domain}",
                        "type": "maps_to",
                        "weight": confidence,  # type: ignore[dict-item]
                    },
                ]
            )
        else:
            self.graph["nodes"][node_id] = node_data.to_dict()

        self._pending_changes.append(
            {
                "op": "add_node",
                "id": node_id,
                "type": "analogy",
                "data": node_data.to_dict(),
                "edges": edges_added,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._check_snapshot()

        return node_id


def add_operator_node(
    self: KnowledgeGraph,
    operator_name: str,
    from_state: tuple[int, int, int],
    to_state: tuple[int, int, int],
    description: str = "",
    usage_count: int = 0,
    success_rate: float = 0.0,
) -> str:
    """Add a C4 operator node with usage statistics."""
    with self.lock:
        self._node_counters["operator"] += 1
        node_id = f"operator_{self._node_counters['operator']}"

        node_data = NodeData(
            node_id=node_id,
            node_type="operator",
            metadata={
                "operator_name": operator_name,
                "from_state": from_state,
                "to_state": to_state,
                "description": description,
                "usage_count": usage_count,
                "success_rate": success_rate,
                "transform_vector": (
                    to_state[0] - from_state[0],
                    to_state[1] - from_state[1],
                    to_state[2] - from_state[2],
                ),
            },
            tags=[operator_name],
        )

        if HAS_NETWORKX:
            self.graph.add_node(node_id, **node_data.to_dict())
        else:
            self.graph["nodes"][node_id] = node_data.to_dict()

        self._pending_changes.append(
            {
                "op": "add_node",
                "id": node_id,
                "type": "operator",
                "data": node_data.to_dict(),
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._check_snapshot()

        return node_id


def add_experiment_node(
    self: KnowledgeGraph,
    experiment_id: str,
    discovery_id: str,
    name: str,
    description: str = "",
    researcher: str = "",
    status: str = "design",
    metadata: dict[str, Any] | None = None,
) -> str:
    """Add an experiment node for hypothesis validation."""
    with self.lock:
        node_data = NodeData(
            node_id=experiment_id,
            node_type="experiment",
            metadata={
                "discovery_id": discovery_id,
                "name": name,
                "description": description,
                "researcher": researcher,
                "status": status,
                **(metadata or {}),
            },
            tags=["experiment", discovery_id],
        )

        if HAS_NETWORKX:
            self.graph.add_node(experiment_id, **node_data.to_dict())
        else:
            self.graph["nodes"][experiment_id] = node_data.to_dict()

        self._pending_changes.append(
            {
                "op": "add_node",
                "id": experiment_id,
                "type": "experiment",
                "data": node_data.to_dict(),
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._check_snapshot()

        return experiment_id
