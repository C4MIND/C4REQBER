# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GraphNode:
    """GraphNode."""
    id: str
    label: str
    layer: int  # 1-3
    verified: bool = False
    falsified: bool = False

    @property
    def symbol(self) -> str:
        """Symbol."""
        if self.falsified:
            return "✗"
        if self.verified:
            return "✓"
        return "○"

    @property
    def color(self) -> str:
        """Color."""
        if self.falsified:
            return "red"
        if self.verified:
            return "green"
        return {1: "cyan", 2: "yellow", 3: "magenta"}.get(self.layer, "white")


@dataclass
class GraphEdge:
    """GraphEdge."""
    source: str
    target: str
    verified: bool = False


class ProofGraph:
    """ProofGraph."""
    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[GraphEdge] = []

    def add_node(self, id: str, label: str, layer: int = 1, verified: bool = False) -> None:
        self.nodes[id] = GraphNode(id=id, label=label, layer=layer, verified=verified)

    def add_edge(self, source: str, target: str, verified: bool = False) -> None:
        self.edges.append(GraphEdge(source=source, target=target, verified=verified))

    def render_ascii(self, width: int = 50) -> str:
        """Render ascii."""
        if not self.nodes:
            return "(empty graph)"
        lines = []
        roots = [nid for nid in self.nodes if not any(e.target == nid for e in self.edges)]
        if not roots:
            roots = list(self.nodes.keys())[:1]
        for root in roots:
            lines.extend(self._render_tree(root, "", True, set(), width))
        return "\n".join(lines)

    def _render_tree(self, node_id: str, prefix: str, is_last: bool, visited: set, width: int) -> list[str]:
        if node_id in visited:
            return [f"{prefix}{'└─' if is_last else '├─'} [{node_id}] (cycle)"]
        visited.add(node_id)
        node = self.nodes.get(node_id)
        if not node:
            return [f"{prefix}{'└─' if is_last else '├─'} {node_id}?"]
        connector = "└─" if is_last else "├─"
        {True: "══", False: "----", None: "····"}.get(
            next((e.verified for e in self.edges if e.target == node_id), None), "····"
        )
        lines = [f"{prefix}{connector} {node.symbol} {node.label}"]
        children = [e.target for e in self.edges if e.source == node_id]
        for i, child in enumerate(children):
            child_is_last = (i == len(children) - 1)
            child_prefix = prefix + ("   " if is_last else "│  ")
            lines.extend(self._render_tree(child, child_prefix, child_is_last, visited.copy(), width))
        return lines

    @property
    def stats(self) -> dict:
        """Stats."""
        total = len(self.nodes)
        verified = sum(1 for n in self.nodes.values() if n.verified)
        falsified = sum(1 for n in self.nodes.values() if n.falsified)
        layers: dict[int, int] = {}
        for n in self.nodes.values():
            layers[n.layer] = layers.get(n.layer, 0) + 1
        return {"total": total, "verified": verified, "falsified": falsified, "layers": layers, "edges": len(self.edges)}
