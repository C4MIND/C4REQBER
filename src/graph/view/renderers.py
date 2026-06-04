"""
C4REQBER: Graph View — Renderers
"""
from __future__ import annotations


__all__ = [
    "_apply_force_layout",
    "_create_graph_node",
    "render_ascii_preview",
]

import math
import random
from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from src.graph.view.core import GraphEdge, GraphNode


def _create_graph_node(node_id: str, node_data: dict[str, Any], type_colors: dict[str, str]) -> GraphNode:
    """Create a GraphNode from knowledge graph data."""
    node_type = node_data.get("node_type", "unknown")
    metadata = node_data.get("metadata", {})

    # Determine label
    label = node_id
    if "name" in metadata:
        label = metadata["name"]
    elif "problem" in metadata:
        label = metadata["problem"][:30] + "..."
    elif "hypothesis" in metadata:
        label = metadata["hypothesis"][:30] + "..."
    elif "title" in metadata:
        label = metadata["title"][:30] + "..."

    # Determine size based on importance
    size = 10.0
    if "confidence_score" in metadata:
        size = 10 + metadata["confidence_score"] * 20
    if "citation_count" in metadata:
        size += min(metadata["citation_count"] / 100, 20)

    return GraphNode(
        id=node_id,
        label=label,
        type=node_type,
        size=size,
        color=type_colors.get(node_type, type_colors["default"]),
        metadata=metadata,
    )


def _apply_force_layout(
    nodes: list[GraphNode], edges: list[GraphEdge], iterations: int = 100
) -> None:
    """
    Simple force-directed layout algorithm.

    Uses repulsion between nodes and attraction along edges.
    """
    # Initialize random positions
    for node in nodes:
        node.x = random.uniform(-100, 100)
        node.y = random.uniform(-100, 100)

    # Create node lookup
    node_map = {n.id: n for n in nodes}

    # Force-directed iterations
    for _ in range(iterations):
        # Calculate forces
        forces = {n.id: [0.0, 0.0] for n in nodes}

        # Repulsion between all nodes
        for i, n1 in enumerate(nodes):
            for n2 in nodes[i + 1 :]:
                dx = n1.x - n2.x
                dy = n1.y - n2.y
                dist = math.sqrt(dx * dx + dy * dy) + 0.1

                # Repulsion force (inverse square)
                force = 5000 / (dist * dist)
                fx = (dx / dist) * force
                fy = (dy / dist) * force

                forces[n1.id][0] += fx
                forces[n1.id][1] += fy
                forces[n2.id][0] -= fx
                forces[n2.id][1] -= fy

        # Attraction along edges
        for edge in edges:
            if edge.source in node_map and edge.target in node_map:
                n1 = node_map[edge.source]
                n2 = node_map[edge.target]

                dx = n2.x - n1.x
                dy = n2.y - n1.y
                dist = math.sqrt(dx * dx + dy * dy) + 0.1

                # Spring force (Hooke's law)
                target_dist = 100
                force = (dist - target_dist) * 0.01
                fx = (dx / dist) * force
                fy = (dy / dist) * force

                forces[n1.id][0] += fx
                forces[n1.id][1] += fy
                forces[n2.id][0] -= fx
                forces[n2.id][1] -= fy

        # Apply forces
        for node in nodes:
            node.x += forces[node.id][0] * 0.1
            node.y += forces[node.id][1] * 0.1


def render_ascii_preview(
    nodes: list[GraphNode], edges: list[GraphEdge], width: int = 60, height: int = 20
) -> str:
    """
    Render ASCII preview of the graph.

    Quick terminal-based visualization.
    """
    if not nodes:
        return "No nodes to display."

    # Normalize positions to grid
    min_x = min(n.x for n in nodes)
    max_x = max(n.x for n in nodes)
    min_y = min(n.y for n in nodes)
    max_y = max(n.y for n in nodes)

    x_range = max_x - min_x or 1
    y_range = max_y - min_y or 1

    # Create grid
    grid = [[" " for _ in range(width)] for _ in range(height)]

    # Draw edges (simplified)
    node_map = {n.id: n for n in nodes}
    for edge in edges[:20]:  # Limit edges for clarity
        if edge.source in node_map and edge.target in node_map:
            n1 = node_map[edge.source]
            n2 = node_map[edge.target]

            x1 = int((n1.x - min_x) / x_range * (width - 1))
            y1 = int((n1.y - min_y) / y_range * (height - 1))
            x2 = int((n2.x - min_x) / x_range * (width - 1))
            y2 = int((n2.y - min_y) / y_range * (height - 1))

            # Simple line drawing
            dx = abs(x2 - x1)
            dy = abs(y2 - y1)
            steps = max(dx, dy)
            if steps > 0:
                for i in range(steps):
                    x = x1 + (x2 - x1) * i // steps
                    y = y1 + (y2 - y1) * i // steps
                    if 0 <= y < height and 0 <= x < width:
                        if grid[y][x] == " ":
                            grid[y][x] = "·"

    # Draw nodes
    for node in nodes[:15]:  # Limit nodes for clarity
        x = int((node.x - min_x) / x_range * (width - 1))
        y = int((node.y - min_y) / y_range * (height - 1))

        if 0 <= y < height and 0 <= x < width:
            symbol = node.type[0].upper() if node.type else "?"
            grid[y][x] = f"[bold]{symbol}[/bold]"

    # Render grid
    lines = [
        "",
        "Knowledge Graph Preview (ASCII)",
        "─" * width,
    ]
    for row in grid:
        lines.append("".join(row))
    lines.extend(
        [
            "─" * width,
            f"Showing {len(nodes)} nodes, {len(edges)} edges",
            "Legend: D=Discovery, P=Project, C=Concept, A=Analogy, O=Operator",
            "",
        ]
    )

    return "\n".join(lines)
