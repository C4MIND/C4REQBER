"""
C4REQBER: Graph View Visualization
Obsidian-style interactive graph visualization

DEPRECATED: This module has been split. Use src.graph.view.core and src.graph.view.renderers instead.
This file remains as a backward-compatibility wrapper.
"""
from __future__ import annotations


__all__ = [
    "GraphNode",
    "GraphEdge",
    "GraphViewRenderer",
    "get_graph_renderer",
]

from src.graph.view.core import GraphEdge, GraphNode, GraphViewRenderer, get_graph_renderer
