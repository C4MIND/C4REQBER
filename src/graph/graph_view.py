"""
TURBO-CDI: Graph View Visualization
Obsidian-style interactive graph visualization
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json


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
    metadata: Dict[str, Any] = None


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

    def __init__(self, knowledge_graph=None):
        from src.graph.knowledge_graph import get_knowledge_graph

        self.kg = knowledge_graph or get_knowledge_graph()

    def build_visualization_graph(
        self,
        center_node: Optional[str] = None,
        depth: int = 2,
        node_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
    ) -> Tuple[List[GraphNode], List[GraphEdge]]:
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
        nodes: Dict[str, GraphNode] = {}
        edges: List[GraphEdge] = []

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
                    nodes[node_id] = self._create_graph_node(node_id, node_data)

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
                node_id = node_data.get("node_id")
                node_type = node_data.get("node_type", "unknown")

                if node_types and node_type not in node_types:
                    continue

                confidence = node_data.get("metadata", {}).get("confidence_score", 1.0)
                if confidence < min_confidence:
                    continue

                nodes[node_id] = self._create_graph_node(node_id, node_data)

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
        self._apply_force_layout(list(nodes.values()), edges)

        return list(nodes.values()), edges

    def _create_graph_node(self, node_id: str, node_data: Dict) -> GraphNode:
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
            color=self.TYPE_COLORS.get(node_type, self.TYPE_COLORS["default"]),
            metadata=metadata,
        )

    def _apply_force_layout(
        self, nodes: List[GraphNode], edges: List[GraphEdge], iterations: int = 100
    ):
        """
        Simple force-directed layout algorithm.

        Uses repulsion between nodes and attraction along edges.
        """
        import random
        import math

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

    def export_to_html(
        self,
        output_path: str,
        center_node: Optional[str] = None,
        title: str = "TURBO-CDI Knowledge Graph",
    ):
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
        <h1>🔬 TURBO-CDI Graph View</h1>
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
        self, center_node: Optional[str] = None, width: int = 60, height: int = 20
    ) -> str:
        """
        Render ASCII preview of the graph.

        Quick terminal-based visualization.
        """
        nodes, edges = self.build_visualization_graph(center_node=center_node, depth=1)

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


# Singleton
_renderer: Optional[GraphViewRenderer] = None


def get_graph_renderer(kg=None) -> GraphViewRenderer:
    """Get singleton graph renderer."""
    global _renderer
    if _renderer is None:
        _renderer = GraphViewRenderer(kg)
    return _renderer
