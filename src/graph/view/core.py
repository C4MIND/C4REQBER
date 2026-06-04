"""
C4REQBER: Graph View — Core Renderer
"""
from __future__ import annotations


__all__ = [
    "GraphNode",
    "GraphEdge",
    "GraphViewRenderer",
    "get_graph_renderer",
]

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.graph.view.renderers import (
    _apply_force_layout,
    _create_graph_node,
    render_ascii_preview,
)


@dataclass
class GraphNode:
    """A node in the graph visualization."""

    id: str
    label: str
    type: str  # discovery, project, concept, analogy, etc.
    x: float = 0.0
    y: float = 0.0
    size: float = 10.0
    color: str = "#4ECDC4"
    metadata: dict[str, Any] = None  # type: ignore[assignment]


@dataclass
class GraphEdge:
    """An edge in the graph visualization."""

    source: str
    target: str
    label: str = ""
    weight: float = 1.0
    color: str = "#888888"
    type: str = "default"


class GraphViewRenderer:
    """
    Obsidian-style graph visualization renderer.

    Creates interactive force-directed graph representations
    of the knowledge graph for visual exploration.
    """

    # Color scheme by node type
    TYPE_COLORS = {
        "discovery": "#4ECDC4",  # Teal
        "project": "#FF6B6B",  # Red
        "concept": "#FFE66D",  # Yellow
        "analogy": "#95E1D3",  # Mint
        "operator": "#F38181",  # Coral
        "experiment": "#AA96DA",  # Purple
        "reference": "#FCBAD3",  # Pink
        "default": "#A8D8EA",  # Light blue
    }

    def __init__(self, knowledge_graph: Any=None) -> None:
        from src.graph.knowledge_graph import get_knowledge_graph

        self.kg = knowledge_graph or get_knowledge_graph()

    def build_visualization_graph(
        self,
        center_node: str | None = None,
        depth: int = 2,
        node_types: list[str] | None = None,
        min_confidence: float = 0.0,
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        """
        Build graph for visualization.

        Args:
            center_node: Start from this node (None = all nodes)
            depth: How many hops to include
            node_types: Filter by node types
            min_confidence: Minimum confidence threshold

        Returns:
            (nodes, edges) for visualization
        """
        nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []

        # Get relevant nodes
        if center_node:
            # BFS from center
            to_visit = [(center_node, 0)]
            visited = {center_node}

            while to_visit:
                node_id, current_depth = to_visit.pop(0)

                if current_depth > depth:
                    continue

                node_data = self.kg.get_node(node_id)
                if not node_data:
                    continue

                # Check filters
                node_type = node_data.get("node_type", "unknown")
                if node_types and node_type not in node_types:
                    continue

                confidence = node_data.get("metadata", {}).get("confidence_score", 1.0)
                if confidence < min_confidence:
                    continue

                # Add node
                if node_id not in nodes:
                    nodes[node_id] = _create_graph_node(node_id, node_data, self.TYPE_COLORS)

                # Get neighbors
                if current_depth < depth:
                    neighbors = self.kg.get_neighbors_with_edges(node_id)
                    for neighbor_id, edge_data in neighbors.items():
                        if neighbor_id not in visited:
                            visited.add(neighbor_id)
                            to_visit.append((neighbor_id, current_depth + 1))

                        # Add edge
                        edge = GraphEdge(
                            source=node_id,
                            target=neighbor_id,
                            label=edge_data.get("edge_type", ""),
                            type=edge_data.get("edge_type", "default"),
                        )
                        edges.append(edge)
        else:
            # Get all nodes
            all_nodes = self.kg.get_all_nodes()
            for node_data in all_nodes:
                node_id = node_data.get("node_id")  # type: ignore[assignment]
                node_type = node_data.get("node_type", "unknown")

                if node_types and node_type not in node_types:
                    continue

                confidence = node_data.get("metadata", {}).get("confidence_score", 1.0)
                if confidence < min_confidence:
                    continue

                nodes[node_id] = _create_graph_node(node_id, node_data, self.TYPE_COLORS)

            # Get all edges
            all_edges = self.kg.get_all_edges()
            for edge_data in all_edges:
                source = edge_data.get("source")
                target = edge_data.get("target")

                if source in nodes and target in nodes:
                    edges.append(
                        GraphEdge(
                            source=source,
                            target=target,
                            label=edge_data.get("edge_type", ""),
                            type=edge_data.get("edge_type", "default"),
                        )
                    )

        # Apply force-directed layout
        _apply_force_layout(list(nodes.values()), edges)

        return list(nodes.values()), edges

    def export_to_html(
        self,
        output_path: str,
        center_node: str | None = None,
        title: str = "C4REQBER Knowledge Graph",
    ) -> Any:
        """
        Export interactive graph to HTML.

        Uses D3.js for visualization.
        """
        nodes, edges = self.build_visualization_graph(center_node=center_node)

        # Convert to JSON-serializable format
        nodes_json = [
            {
                "id": n.id,
                "label": n.label,
                "type": n.type,
                "x": n.x,
                "y": n.y,
                "size": n.size,
                "color": n.color,
            }
            for n in nodes
        ]

        edges_json = [
            {"source": e.source, "target": e.target, "label": e.label, "type": e.type}
            for e in edges
        ]

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ margin: 0; overflow: hidden; background: #1a1a2e; font-family: system-ui, sans-serif; }}
        #graph {{ width: 100vw; height: 100vh; }}
        .node {{ cursor: pointer; }}
        .node circle {{ stroke: #fff; stroke-width: 2px; }}
        .node text {{ fill: #fff; font-size: 12px; pointer-events: none; text-shadow: 0 1px 3px rgba(0,0,0,0.8); }}
        .link {{ stroke: #444; stroke-opacity: 0.6; }}
        #info {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.8);
            color: #fff;
            padding: 15px;
            border-radius: 8px;
            max-width: 300px;
        }}
        #legend {{
            position: absolute;
            bottom: 10px;
            right: 10px;
            background: rgba(0,0,0,0.8);
            color: #fff;
            padding: 15px;
            border-radius: 8px;
        }}
        .legend-item {{ display: flex; align-items: center; margin: 5px 0; }}
        .legend-color {{ width: 16px; height: 16px; border-radius: 50%; margin-right: 8px; }}
        h1 {{ margin: 0 0 10px 0; font-size: 18px; }}
        .stats {{ color: #aaa; font-size: 12px; }}
    </style>
</head>
<body>
    <div id="graph"></div>
    <div id="info">
        <h1>🔬 C4REQBER Graph View</h1>
        <div class="stats">
            Nodes: {len(nodes)} | Edges: {len(edges)}<br>
            Drag to pan, scroll to zoom
        </div>
    </div>
    <div id="legend">
        <h3 style="margin: 0 0 10px 0;">Node Types</h3>
        {"".join(f'<div class="legend-item"><div class="legend-color" style="background: {color}"></div>{node_type}</div>' for node_type, color in self.TYPE_COLORS.items() if node_type != "default")}
    </div>
    <script>
        const nodes = {json.dumps(nodes_json)};
        const links = {json.dumps(edges_json)};

        const width = window.innerWidth;
        const height = window.innerHeight;

        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .call(d3.zoom().on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }}));

        const g = svg.append("g");

        // Arrow markers
        svg.append("defs").selectAll("marker")
            .data(["end"])
            .enter().append("marker")
            .attr("id", "end")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 25)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#444");

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(150))
            .force("charge", d3.forceManyBody().strength(-500))
            .force("center", d3.forceCenter(width / 2, height / 2));

        const link = g.append("g")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("class", "link")
            .attr("stroke-width", 2);

        const node = g.append("g")
            .selectAll("g")
            .data(nodes)
            .enter().append("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("circle")
            .attr("r", d => d.size)
            .attr("fill", d => d.color);

        node.append("text")
            .attr("dx", d => d.size + 5)
            .attr("dy", 4)
            .text(d => d.label);

        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        }});

        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
    </script>
</body>
</html>"""

        Path(output_path).write_text(html)
        return output_path

    def render_ascii_preview(
        self, center_node: str | None = None, width: int = 60, height: int = 20
    ) -> str:
        """
        Render ASCII preview of the graph.

        Quick terminal-based visualization.
        """
        nodes, edges = self.build_visualization_graph(center_node=center_node, depth=1)
        return render_ascii_preview(nodes, edges, width, height)


def get_graph_renderer(kg: Any = None) -> GraphViewRenderer:
    """Get singleton graph renderer (backed by DI container)."""
    from src.di.container import get_container
    container = get_container()
    if not container.has("graph_renderer"):
        container.register("graph_renderer", GraphViewRenderer(kg))
    return container.resolve("graph_renderer")
