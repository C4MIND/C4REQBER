"""C4REQBER: Plugin DAG execution with dependency resolution."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PluginNode:
    """A node in the plugin DAG."""

    plugin_id: str
    config: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)


class PluginDAG:
    """
    Directed acyclic graph for plugin execution.

    Plugins are nodes, edges represent data dependencies.
    Results from upstream plugins are passed to downstream plugins
    via the ``context`` dict.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, PluginNode] = {}
        self._edges: dict[str, list[str]] = {}  # from -> [to]
        self._in_degree: dict[str, int] = {}

    def add_node(self, plugin_id: str, config: dict[str, Any] | None = None) -> None:
        """Add a plugin node."""
        if plugin_id not in self._nodes:
            self._nodes[plugin_id] = PluginNode(plugin_id=plugin_id, config=config or {})
            self._edges[plugin_id] = []
            self._in_degree[plugin_id] = 0

    def add_edge(self, from_plugin: str, to_plugin: str) -> None:
        """Add a dependency edge (from_plugin must run before to_plugin)."""
        self.add_node(from_plugin)
        self.add_node(to_plugin)
        self._edges[from_plugin].append(to_plugin)
        self._in_degree[to_plugin] += 1
        self._nodes[to_plugin].dependencies.append(from_plugin)

    def validate(self) -> bool:
        """Return True if the graph has no cycles."""
        in_deg = dict(self._in_degree)
        queue = deque([n for n, d in in_deg.items() if d == 0])
        visited = 0
        while queue:
            node = queue.popleft()
            visited += 1
            for neighbor in self._edges[node]:
                in_deg[neighbor] -= 1
                if in_deg[neighbor] == 0:
                    queue.append(neighbor)
        return visited == len(self._nodes)

    def topological_sort(self) -> list[str]:
        """Return plugins in topological order.

        Raises ValueError if a cycle is detected.
        """
        if not self.validate():
            raise ValueError("Plugin DAG contains a cycle")

        in_deg = dict(self._in_degree)
        queue = deque([n for n, d in in_deg.items() if d == 0])
        order: list[str] = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in self._edges[node]:
                in_deg[neighbor] -= 1
                if in_deg[neighbor] == 0:
                    queue.append(neighbor)

        return order

    def execute(
        self,
        problem: str,
        executor: Any | None = None,
    ) -> dict[str, Any]:
        """
        Execute plugins in topological order.

        Parameters
        ----------
        problem: str
            The problem text passed to every plugin.
        executor:
            Callable with signature ``(plugin_id, problem, context) -> result``.
            Defaults to ``src.plugins.unified_registry.execute_plugin``.

        Returns
        -------
        dict mapping plugin_id -> result.  The special key ``_context``
        contains the accumulated context after all plugins have run.
        """
        if executor is None:
            from src.plugins.unified_registry import execute_plugin as default_executor

            executor = default_executor

        order = self.topological_sort()
        context: dict[str, Any] = {"problem": problem}
        results: dict[str, Any] = {"_context": context}

        for plugin_id in order:
            node = self._nodes[plugin_id]
            # Merge upstream results into context
            for dep in node.dependencies:
                context[f"{dep}_result"] = results.get(dep)

            try:
                call_kwargs = {**node.config, **context}
                call_kwargs.setdefault("problem", problem)
                result = executor(plugin_id, **call_kwargs)
                results[plugin_id] = result
                context[f"{plugin_id}_result"] = result
            except Exception as exc:
                results[plugin_id] = {"error": str(exc), "plugin_id": plugin_id}
                context[f"{plugin_id}_result"] = results[plugin_id]

        return results

    def to_dict(self) -> dict[str, Any]:
        """Serialize DAG structure."""
        return {
            "nodes": [
                {
                    "plugin_id": n.plugin_id,
                    "config": n.config,
                    "dependencies": n.dependencies,
                }
                for n in self._nodes.values()
            ],
            "valid": self.validate(),
        }

    @classmethod
    def from_list(cls, plugin_ids: list[str]) -> PluginDAG:
        """Create a linear DAG from a list (no dependencies)."""
        dag = cls()
        for pid in plugin_ids:
            dag.add_node(pid)
        return dag

    @classmethod
    def from_edges(
        cls,
        edges: list[tuple[str, str]],
        configs: dict[str, dict[str, Any]] | None = None,
    ) -> PluginDAG:
        """Create a DAG from edge tuples."""
        dag = cls()
        for from_p, to_p in edges:
            dag.add_edge(from_p, to_p)
        if configs:
            for pid, cfg in configs.items():
                if pid in dag._nodes:
                    dag._nodes[pid].config = cfg
        return dag
