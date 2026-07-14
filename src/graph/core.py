"""Core data structures and KnowledgeGraph class."""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from src.compat import UTC


try:
    import networkx as nx
    from networkx import DiGraph

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    print("⚠️  NetworkX not installed. Using fallback dict-based graph.")


@dataclass
class NodeData:
    """Base node data structure."""

    node_id: str
    node_type: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    embedding: list[float] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "tags": self.tags,
            "embedding": self.embedding,
        }


@dataclass
class EdgeData:
    """Base edge data structure."""

    edge_type: str
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_type": self.edge_type,
            "weight": self.weight,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class KnowledgeGraph:
    """Unified knowledge graph for C4REQBER."""

    SNAPSHOT_INTERVAL = 100

    def __init__(self, storage_path: str | None = None) -> None:
        self.storage_dir = Path(storage_path) if storage_path else Path("data")
        self.graphml_path = self.storage_dir / "knowledge_graph.graphml"
        self.metadata_path = self.storage_dir / "knowledge_graph_metadata.json"
        self.changelog_path = self.storage_dir / "knowledge_graph_changelog.jsonl"
        self.lock = threading.RLock()

        if HAS_NETWORKX:
            self.graph: DiGraph = DiGraph()
        else:
            self.graph = {"nodes": {}, "edges": []}

        self._node_counters: dict[str, int] = {
            "discovery": 0,
            "project": 0,
            "reference": 0,
            "analogy": 0,
            "operator": 0,
            "experiment": 0,
        }

        self._pending_changes: list[dict[str, Any]] = []
        self._last_snapshot_size = 0

        self._load()

        if self.graph.number_of_nodes() == 0:
            try:
                from src.graph.seed_data import seed_knowledge_graph
                seed_knowledge_graph(self)  # type: ignore[arg-type]
            except (ImportError, RuntimeError):
                pass

    def _load(self) -> None:
        """Load graph from JSON if exists."""
        if not HAS_NETWORKX:
            return

        json_path = self.storage_dir / "knowledge_graph.json"
        if json_path.exists():
            try:
                with open(json_path) as f:
                    data = json.load(f)

                self.graph = DiGraph()

                for node_data in data.get("nodes", []):
                    node_id = node_data.pop("id")
                    self.graph.add_node(node_id, **node_data)

                for edge_data in data.get("edges", []):
                    source = edge_data.pop("source")
                    target = edge_data.pop("target")
                    self.graph.add_edge(source, target, **edge_data)

                self._node_counters = data.get("metadata", {}).get(
                    "counters", self._node_counters
                )

                print(
                    f"📊 Loaded knowledge graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges"
                )
            except Exception as e:
                print(f"⚠️  Failed to load graph from JSON: {e}")
                self.graph = DiGraph()

        elif (self.storage_dir / "knowledge_graph.pkl").exists():
            print(
                "⚠️  Legacy pickle format detected but disabled for security. Convert to JSON."
            )
            self.graph = DiGraph()

        self._load_changelog()

    def _load_changelog(self) -> None:
        """Load and apply incremental changes from changelog."""
        if not HAS_NETWORKX or not self.changelog_path.exists():
            return

        try:
            applied = 0
            with open(self.changelog_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        change = json.loads(line)
                        op = change.get("op")

                        if op == "add_node":
                            node_id = change.get("id")
                            data = change.get("data", {})
                            self.graph.add_node(node_id, **data)
                            for edge_info in change.get("edges", []):
                                if self.graph.has_node(edge_info.get("to")):
                                    self.graph.add_edge(
                                        node_id,
                                        edge_info["to"],
                                        edge_type=edge_info.get("type", "related"),
                                        weight=edge_info.get("weight", 1.0),
                                    )

                        elif op == "add_edge":
                            src = change.get("src")
                            tgt = change.get("tgt")
                            if self.graph.has_node(src) and self.graph.has_node(tgt):
                                self.graph.add_edge(
                                    src,
                                    tgt,
                                    edge_type=change.get("type", "related"),
                                    weight=change.get("weight", 1.0),
                                    metadata=change.get("metadata", {}),
                                    timestamp=change.get("timestamp"),
                                )
                        applied += 1
                    except Exception as e:
                        print(f"⚠️  Failed to apply changelog entry: {e}")

            if applied > 0:
                print(f"📝 Applied {applied} incremental changes from changelog")
        except Exception as e:
            print(f"⚠️  Failed to load changelog: {e}")

    def _check_snapshot(self) -> None:
        """Check if full snapshot is needed based on change count."""
        if len(self._pending_changes) >= self.SNAPSHOT_INTERVAL:
            self.save(incremental=False)

    def save(self, incremental: bool = True) -> None:
        """Save graph to JSON with optional incremental append-only mode."""
        if not HAS_NETWORKX:
            return

        with self.lock:
            try:
                self.storage_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                print(f"⚠️  Failed to create storage directory: {e}")
                return

            if incremental and self._pending_changes:
                try:
                    with open(self.changelog_path, "a") as f:
                        for change in self._pending_changes:
                            f.write(json.dumps(change, default=str) + "\n")
                    self._pending_changes.clear()
                    return
                except OSError as e:
                    print(f"⚠️  Failed to write changelog: {e}")
                    return

            data = {
                "nodes": [],
                "edges": [],
                "metadata": {
                    "counters": self._node_counters,
                    "saved_at": datetime.now(UTC).isoformat(),
                    "node_count": self.graph.number_of_nodes(),
                    "edge_count": self.graph.number_of_edges(),
                },
            }

            for node_id, node_data in self.graph.nodes(data=True):
                node_dict = {"id": node_id}
                node_dict.update(node_data)
                data["nodes"].append(node_dict)  # type: ignore[attr-defined]

            for source, target, edge_data in self.graph.edges(data=True):
                edge_dict = {"source": source, "target": target}
                edge_dict.update(edge_data)
                data["edges"].append(edge_dict)  # type: ignore[attr-defined]

            json_path = self.storage_dir / "knowledge_graph.json"
            temp_path = self.storage_dir / "knowledge_graph.json.tmp"
            try:
                with open(temp_path, "w") as f:
                    json.dump(data, f, indent=2, default=str)
                temp_path.replace(json_path)
            except OSError as e:
                print(f"⚠️  Failed to save graph: {e}")
                if temp_path.exists():
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass
                return

            if self.changelog_path.exists():
                try:
                    self.changelog_path.unlink()
                except OSError as e:
                    print(f"⚠️  Failed to clear changelog: {e}")
            self._last_snapshot_size = len(data["nodes"]) + len(data["edges"])

    def has_node(self, node_id: str) -> bool:
        """Check if node exists."""
        if HAS_NETWORKX:
            return self.graph.has_node(node_id)  # type: ignore[no-any-return]
        return node_id in self.graph["nodes"]

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Get node data."""
        if not self.has_node(node_id):
            return None

        if HAS_NETWORKX:
            return dict(self.graph.nodes[node_id])
        return self.graph["nodes"].get(node_id)  # type: ignore[no-any-return]

    def get_stats(self) -> dict[str, Any]:
        """Get graph statistics."""
        if HAS_NETWORKX:
            node_count = self.graph.number_of_nodes()
            edge_count = self.graph.number_of_edges()
            return {
                "nodes": node_count,
                "edges": edge_count,
                "density": nx.density(self.graph) if node_count > 1 else 0.0,
                "is_connected": nx.is_weakly_connected(self.graph)
                if node_count > 0
                else False,
                "node_types": {
                    nt: len(self.get_nodes_by_type(nt))
                    for nt in [
                        "discovery",
                        "project",
                        "reference",
                        "analogy",
                        "operator",
                    ]
                },
                "central_nodes": self.get_central_nodes(5) if node_count > 0 else [],
            }
        else:
            return {
                "nodes": len(self.graph["nodes"]),
                "edges": len(self.graph["edges"]),
                "node_types": {},
            }

    def get_nodes_by_type(self, node_type: str) -> list[dict[str, Any]]:
        """Get all nodes of a specific type."""
        if HAS_NETWORKX:
            return [
                dict(data)
                for _, data in self.graph.nodes(data=True)
                if data.get("node_type") == node_type
            ]
        return [
            data
            for data in self.graph["nodes"].values()
            if data.get("node_type") == node_type
        ]

    def get_central_nodes(self, n: int = 10) -> list[tuple[str, float]]:
        """Get most central nodes by PageRank."""
        if not HAS_NETWORKX or self.graph.number_of_nodes() == 0:
            return []

        pagerank = nx.pagerank(self.graph)
        return sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:n]


def get_knowledge_graph(storage_path: str | None = None) -> KnowledgeGraph:
    """Get thread-safe singleton knowledge graph instance (backed by DI container)."""
    from src.di.container import get_container
    container = get_container()
    if container.has("knowledge_graph"):
        return container.resolve("knowledge_graph")
    kg = KnowledgeGraph(storage_path)
    container.register("knowledge_graph", kg)
    return kg
