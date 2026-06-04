# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class HistoryNode:
    """HistoryNode."""
    id: str
    query: str
    result_summary: str
    c4_state: tuple[int, int, int]
    timestamp: float = field(default_factory=time.time)
    hypotheses: list[str] = field(default_factory=list)
    conclusions: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # node IDs this depends on


class HistoryGraph:
    """HistoryGraph."""
    def __init__(self) -> None:
        self._nodes: dict[str, HistoryNode] = {}
        self._reverse_index: dict[str, list[str]] = {}  # dependency → dependent nodes

    def add(self, node: HistoryNode) -> None:
        """Add."""
        self._nodes[node.id] = node
        for dep in node.dependencies:
            if dep not in self._reverse_index:
                self._reverse_index[dep] = []
            self._reverse_index[dep].append(node.id)

    def find_dependents(self, node_id: str) -> list[HistoryNode]:
        """Find dependents."""
        dep_ids = self._reverse_index.get(node_id, [])
        return [self._nodes[rid] for rid in dep_ids if rid in self._nodes]

    def find_by_conclusion(self, text: str) -> list[HistoryNode]:
        """Find by conclusion."""
        lower = text.lower()
        return [n for n in self._nodes.values() if lower in " ".join(n.conclusions).lower()]

    def find_by_hypothesis(self, text: str) -> list[HistoryNode]:
        """Find by hypothesis."""
        lower = text.lower()
        return [n for n in self._nodes.values() if any(lower in h.lower() for h in n.hypotheses)]

    def find_by_state(self, state: tuple[int, int, int]) -> list[HistoryNode]:
        return [n for n in self._nodes.values() if n.c4_state == state]

    def ancestors(self, node_id: str, max_depth: int = 5) -> list[HistoryNode]:
        """Ancestors."""
        result = []
        visited = set()
        queue = [node_id]
        for _ in range(max_depth):
            if not queue:
                break
            current = queue.pop(0)
            if current in visited or current not in self._nodes:
                continue
            visited.add(current)
            node = self._nodes[current]
            result.append(node)
            queue.extend(node.dependencies)
        return result

    @property
    def nodes(self) -> list[HistoryNode]:
        return sorted(self._nodes.values(), key=lambda n: n.timestamp, reverse=True)

    def __len__(self) -> int:
        return len(self._nodes)
