"""
Causal Loop Diagrams (CLD) for System Dynamics.

Supports node/link representation, automatic construction from a
knowledge-graph-like structure, and polarity / loop analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np
from numpy.typing import NDArray


# ---------------------------------------------------------------------------
# Enums and base classes
# ---------------------------------------------------------------------------


class Polarity(Enum):
    """Polarity."""
    POSITIVE = "+"
    NEGATIVE = "-"


class LoopType(Enum):
    """LoopType."""
    REINFORCING = "reinforcing"   # even number of negative links
    BALANCING = "balancing"       # odd number of negative links


@dataclass
class CLDNode:
    """A variable node in a causal loop diagram."""

    name: str
    description: str = ""
    category: str = ""            # e.g. "stock", "flow", "auxiliary"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("CLDNode name must be non-empty")


@dataclass
class CLDLink:
    """A directed causal link between two nodes."""

    source: str
    target: str
    polarity: Polarity
    delay: float = 0.0            # time delay in same units as model
    label: str = ""

    def __post_init__(self) -> None:
        if not self.source or not self.target:
            raise ValueError("Link source and target must be non-empty")


# ---------------------------------------------------------------------------
# CLD container
# ---------------------------------------------------------------------------


class CausalLoopDiagram:
    """Graph of causal relationships with loop-detection utilities."""

    def __init__(self, name: str = "cld") -> None:
        self.name = name
        self.nodes: dict[str, CLDNode] = {}
        self.links: list[CLDLink] = []
        self._adj: dict[str, list[tuple[str, Polarity]]] = {}

    # -- builders -----------------------------------------------------------

    def add_node(
        self, name: str, description: str = "", category: str = ""
    ) -> CausalLoopDiagram:
        """Add node."""
        if name in self.nodes:
            raise ValueError(f"Node '{name}' already exists")
        self.nodes[name] = CLDNode(name, description, category)
        self._adj.setdefault(name, [])
        return self

    def add_link(
        self,
        source: str,
        target: str,
        polarity: Polarity,
        delay: float = 0.0,
        label: str = "",
    ) -> CausalLoopDiagram:
        """Add link."""
        if source not in self.nodes:
            raise ValueError(f"Source node '{source}' not found")
        if target not in self.nodes:
            raise ValueError(f"Target node '{target}' not found")
        link = CLDLink(source, target, polarity, delay, label)
        self.links.append(link)
        self._adj[source].append((target, polarity))
        return self

    # -- auto-build from knowledge graph ------------------------------------

    @classmethod
    def from_knowledge_graph(
        cls,
        kg: dict[str, dict[str, Any]],
        name: str = "cld",
    ) -> CausalLoopDiagram:
        """Build a CLD from a dict-of-dicts knowledge graph.

        Expected *kg* shape::

            {
                "node_name": {
                    "description": "...",
                    "category": "...",
                    "links": [
                        {"target": "other", "polarity": "+", "delay": 0.0},
                        ...
                    ]
                },
                ...
            }
        """
        cld = cls(name)
        for node_name, data in kg.items():
            cld.add_node(
                node_name,
                data.get("description", ""),
                data.get("category", ""),
            )
        for node_name, data in kg.items():
            for link_data in data.get("links", []):
                pol = (
                    Polarity.POSITIVE
                    if link_data.get("polarity", "+") == "+"
                    else Polarity.NEGATIVE
                )
                cld.add_link(
                    node_name,
                    link_data["target"],
                    pol,
                    link_data.get("delay", 0.0),
                    link_data.get("label", ""),
                )
        return cld

    # -- loop analysis ------------------------------------------------------

    def find_loops(self, max_length: int = 10) -> list[tuple[list[str], LoopType]]:
        """Return all simple cycles with their loop type.

        Each loop is represented as (node_sequence, loop_type).
        """
        loops: list[tuple[list[str], LoopType]] = []
        visited_global: set[str] = set()

        def dfs(
            start: str, current: str, path: list[str], polarities: list[Polarity]
        ) -> None:
            for nxt, pol in self._adj.get(current, []):
                if nxt == start and len(path) >= 2:
                    neg_count = sum(1 for p in polarities + [pol] if p == Polarity.NEGATIVE)
                    ltype = LoopType.BALANCING if neg_count % 2 else LoopType.REINFORCING
                    loops.append((path[:] + [nxt], ltype))
                    continue
                if nxt in path:
                    continue
                if len(path) >= max_length:
                    continue
                dfs(start, nxt, path + [nxt], polarities + [pol])

        for node in self.nodes:
            if node not in visited_global:
                dfs(node, node, [node], [])
                visited_global.add(node)

        # deduplicate rotations
        unique: dict[tuple[str, ...], tuple[list[str], LoopType]] = {}
        for seq, ltype in loops:
            key = tuple(sorted(seq))
            if key not in unique:
                unique[key] = (seq, ltype)
        return list(unique.values())

    def loop_polarity_matrix(self) -> tuple[list[str], NDArray[np.int64]]:
        """Return (node_names, matrix) where M[i,j] = +1/-1/0 causal effect."""
        names = sorted(self.nodes.keys())
        idx = {n: i for i, n in enumerate(names)}
        mat = np.zeros((len(names), len(names)), dtype=np.int64)
        for link in self.links:
            i, j = idx[link.source], idx[link.target]
            val = 1 if link.polarity == Polarity.POSITIVE else -1
            # if multiple links, keep the strongest (sum)
            mat[i, j] += val
        return names, mat

    def reinforcing_loops(self, max_length: int = 10) -> list[list[str]]:
        return [seq for seq, lt in self.find_loops(max_length) if lt == LoopType.REINFORCING]

    def balancing_loops(self, max_length: int = 10) -> list[list[str]]:
        return [seq for seq, lt in self.find_loops(max_length) if lt == LoopType.BALANCING]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def adjacency_matrix(cld: CausalLoopDiagram) -> tuple[list[str], NDArray[np.float64]]:
    """Weighted adjacency matrix (positive=1, negative=-1)."""
    names = sorted(cld.nodes.keys())
    idx = {n: i for i, n in enumerate(names)}
    mat = np.zeros((len(names), len(names)), dtype=np.float64)
    for link in cld.links:
        mat[idx[link.source], idx[link.target]] = (
            1.0 if link.polarity == Polarity.POSITIVE else -1.0
        )
    return names, mat


def eigenvalue_analysis(cld: CausalLoopDiagram) -> tuple[NDArray[np.complex128], NDArray[np.complex128]]:
    """Return (eigenvalues, eigenvectors) of the weighted adjacency matrix."""
    _, mat = adjacency_matrix(cld)
    w, v = np.linalg.eig(mat)
    return w, v


# ---------------------------------------------------------------------------
# __init__ exports
# ---------------------------------------------------------------------------

__all__ = [
    "Polarity",
    "LoopType",
    "CLDNode",
    "CLDLink",
    "CausalLoopDiagram",
    "adjacency_matrix",
    "eigenvalue_analysis",
]
