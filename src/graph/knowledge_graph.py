"""
C4REQBER: Knowledge Graph v4.0
NetworkX-based unified graph replacing 4 SQLite databases

This module is a thin backward-compatible wrapper around the new split modules:
  - core.py      : KnowledgeGraph class and core methods
  - queries.py   : query operations (search, filter, traverse)
  - operations.py: graph mutations (add, remove, update)
  - io.py        : serialization/deserialization

Integrates: Patterns, Projects, Bibliography, Analogies into single graph structure
"""
from __future__ import annotations

from typing import Any

from . import io as _io
from . import operations as _operations
from . import queries as _queries
from .core import (
    HAS_NETWORKX,
    EdgeData,
    NodeData,
)
from .core import (
    KnowledgeGraph as _KnowledgeGraph,
)


class KnowledgeGraph(_KnowledgeGraph):
    """Backward-compatible KnowledgeGraph with all methods attached."""

    # -- queries --
    def get_nodes_by_tag(self, tag: str) -> list[dict[str, Any]]:
        return _queries.get_nodes_by_tag(self, tag)

    def get_discoveries_by_domain(self, domain: str) -> list[dict[str, Any]]:
        return _queries.get_discoveries_by_domain(self, domain)

    def get_neighbors(self, node_id: str, edge_type: str | None = None) -> list[str]:
        return _queries.get_neighbors(self, node_id, edge_type)

    def get_neighbors_with_edges(
        self, node_id: str, edge_type: str | None = None
    ) -> dict[str, dict[str, Any]]:
        return _queries.get_neighbors_with_edges(self, node_id, edge_type)

    def get_citations(self, discovery_id: str) -> list[dict[str, Any]]:
        return _queries.get_citations(self, discovery_id)

    def get_all_nodes(self) -> list[dict[str, Any]]:
        return _queries.get_all_nodes(self)

    def get_all_edges(self) -> list[dict[str, Any]]:
        return _queries.get_all_edges(self)

    def find_shortest_path(self, source: str, target: str) -> list[str] | None:
        return _queries.find_shortest_path(self, source, target)

    def find_clusters(self) -> list[list[str]]:
        return _queries.find_clusters(self)

    def bibliographic_coupling(self, ref_id: str, top_n: int = 5) -> list[tuple[str, int]]:
        return _queries.bibliographic_coupling(self, ref_id, top_n)

    def find_analogy_chains(
        self, source_domain: str, target_domain: str, max_length: int = 3
    ) -> list[list[str]]:
        return _queries.find_analogy_chains(self, source_domain, target_domain, max_length)

    def find_similar_nodes(
        self,
        query_embedding: list[float],
        node_type: str | None = None,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        return _queries.find_similar_nodes(self, query_embedding, node_type, top_k)

    # -- operations --
    def add_discovery(
        self,
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
        return _operations.add_discovery(
            self,
            problem,
            hypothesis,
            confidence_score,
            contradiction,
            c4_path,
            domain,
            falsifiability_criteria,
            llm_provider,
            llm_model,
            tags,
            embedding,
        )

    def add_project(
        self,
        name: str,
        description: str = "",
        domain: str = "general",
        objectives: list[str] | None = None,
        discovery_ids: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> str:
        return _operations.add_project(
            self, name, description, domain, objectives, discovery_ids, tags
        )

    def add_reference(
        self,
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
        return _operations.add_reference(
            self,
            title,
            authors,
            year,
            source,
            source_id,
            abstract,
            url,
            tags,
            embedding,
        )

    def add_analogy(
        self,
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
        return _operations.add_analogy(
            self,
            source_domain,
            target_domain,
            source_concept,
            target_concept,
            mapping_type,
            confidence,
            semantic_similarity,
            structural_similarity,
            evidence,
        )

    def add_operator_node(
        self,
        operator_name: str,
        from_state: tuple[int, int, int],
        to_state: tuple[int, int, int],
        description: str = "",
        usage_count: int = 0,
        success_rate: float = 0.0,
    ) -> str:
        return _operations.add_operator_node(
            self,
            operator_name,
            from_state,
            to_state,
            description,
            usage_count,
            success_rate,
        )

    def add_experiment_node(
        self,
        experiment_id: str,
        discovery_id: str,
        name: str,
        description: str = "",
        researcher: str = "",
        status: str = "design",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        return _operations.add_experiment_node(
            self,
            experiment_id,
            discovery_id,
            name,
            description,
            researcher,
            status,
            metadata,
        )

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        edge_type: str,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        return _operations.add_edge(self, from_id, to_id, edge_type, weight, metadata)

    def add_citation(self, from_id: str, to_ref_id: str, context: str = "") -> Any:
        return _operations.add_citation(self, from_id, to_ref_id, context)

    def add_derivation(self, from_id: str, to_id: str, operator: str = "") -> Any:
        return _operations.add_derivation(self, from_id, to_id, operator)

    def add_transformation(self, from_state: str, to_state: str, operator: str) -> Any:
        return _operations.add_transformation(self, from_state, to_state, operator)

    # -- io --
    def export_to_json(self, path: str) -> bool:
        return _io.export_to_json(self, path)

    def export_to_graphml(self, path: str) -> bool:
        return _io.export_to_graphml(self, path)


# ═══════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE (backed by DI container)
# ═══════════════════════════════════════════════════════════════════


def get_knowledge_graph(storage_path: str | None = None) -> KnowledgeGraph:
    """Get thread-safe singleton knowledge graph instance (backed by DI container)."""
    from src.di.container import get_container
    container = get_container()
    if container.has("knowledge_graph_v2"):
        return container.resolve("knowledge_graph_v2")
    kg = KnowledgeGraph(storage_path)
    container.register("knowledge_graph_v2", kg)
    return kg


__all__ = [
    "HAS_NETWORKX",
    "NodeData",
    "EdgeData",
    "KnowledgeGraph",
    "get_knowledge_graph",
]
