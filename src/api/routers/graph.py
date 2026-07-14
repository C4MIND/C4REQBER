"""
C4REQBER API: Knowledge Graph Router
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from src.graph.knowledge_graph import get_knowledge_graph


router = APIRouter(prefix="/api/v1/graph", tags=["graph"])

_MAX_GRAPH_LIMIT = 2000


@router.get("/stats")
async def graph_stats() -> dict[str, Any]:
    """Graph stats."""
    kg = get_knowledge_graph()
    return kg.get_stats()


@router.get("/nodes")
async def graph_nodes(
    node_type: str | None = None, limit: int = 100, offset: int = 0
) -> list[Any]:
    """Graph nodes."""
    limit = min(max(limit, 0), _MAX_GRAPH_LIMIT)
    offset = max(offset, 0)
    kg = get_knowledge_graph()
    if node_type:
        nodes = kg.get_nodes_by_type(node_type)
    else:
        nodes = kg.get_all_nodes()
    return nodes[offset : offset + limit]


@router.get("/edges")
async def graph_edges(limit: int = 500, offset: int = 0) -> list[Any]:
    """Graph edges."""
    limit = min(max(limit, 0), _MAX_GRAPH_LIMIT)
    offset = max(offset, 0)
    kg = get_knowledge_graph()
    edges = kg.get_all_edges()
    return edges[offset : offset + limit]


@router.get("/central")
async def graph_central_nodes(n: int = 10) -> list[dict[str, Any]]:
    """Graph central nodes."""
    n = min(max(n, 1), 100)
    kg = get_knowledge_graph()
    return [
        {"node_id": nid, "centrality": float(c)}
        for nid, c in kg.get_central_nodes(n)
    ]
