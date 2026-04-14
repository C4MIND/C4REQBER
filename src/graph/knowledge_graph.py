"""
TURBO-CDI: Knowledge Graph v4.0
NetworkX-based unified graph replacing 4 SQLite databases

Integrates: Patterns, Projects, Bibliography, Analogies into single graph structure
"""

import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
import threading

try:
    import networkx as nx
    from networkx import DiGraph, Graph

    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    print("⚠️  NetworkX not installed. Using fallback dict-based graph.")


@dataclass
class NodeData:
    """Base node data structure."""

    node_id: str
    node_type: str  # discovery, project, reference, analogy, operator
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    embedding: Optional[List[float]] = None  # For semantic search

    def to_dict(self) -> Dict[str, Any]:
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

    edge_type: str  # derived_from, uses, cites, analogous_to, transformed_by
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "edge_type": self.edge_type,
            "weight": self.weight,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class KnowledgeGraph:
    """
    Unified knowledge graph for TURBO-CDI.

    Replaces 4 SQLite databases:
    - patterns.db → discovery nodes
    - projects.db → project nodes
    - bibliography.db → reference nodes
    - Analogies → analogy nodes + edges

    Provides:
    - Graph traversal for C4 path finding
    - Semantic similarity search (with embeddings)
    - Cross-domain analogy discovery
    - Bibliographic coupling analysis
    """

    # ═══════════════════════════════════════════════════════════════
    # INCREMENTAL SAVE CONFIG
    # ═══════════════════════════════════════════════════════════════
    SNAPSHOT_INTERVAL = 100  # Full snapshot every 100 changes

    def __init__(self, storage_path: Optional[str] = None):
        # Use GraphML for graph structure, JSON for metadata
        self.storage_dir = Path(storage_path) if storage_path else Path("data")
        self.graphml_path = self.storage_dir / "knowledge_graph.graphml"
        self.metadata_path = self.storage_dir / "knowledge_graph_metadata.json"
        self.changelog_path = self.storage_dir / "knowledge_graph_changelog.jsonl"
        self.lock = threading.RLock()

        if HAS_NETWORKX:
            self.graph: DiGraph = DiGraph()
        else:
            # Fallback: simple adjacency list
            self.graph = {"nodes": {}, "edges": []}

        self._node_counters: Dict[str, int] = {
            "discovery": 0,
            "project": 0,
            "reference": 0,
            "analogy": 0,
            "operator": 0,
            "experiment": 0,
        }

        # Incremental save state
        self._pending_changes: List[Dict[str, Any]] = []
        self._last_snapshot_size = 0

        self._load()

    def _load(self):
        """Load graph from JSON (human-readable, secure) if exists."""
        if not HAS_NETWORKX:
            return

        # Try JSON first (new format)
        json_path = self.storage_dir / "knowledge_graph.json"
        if json_path.exists():
            try:
                with open(json_path) as f:
                    data = json.load(f)

                # Reconstruct graph
                self.graph = DiGraph()

                # Add nodes
                for node_data in data.get("nodes", []):
                    node_id = node_data.pop("id")
                    self.graph.add_node(node_id, **node_data)

                # Add edges
                for edge_data in data.get("edges", []):
                    source = edge_data.pop("source")
                    target = edge_data.pop("target")
                    self.graph.add_edge(source, target, **edge_data)

                # Load metadata
                self._node_counters = data.get("metadata", {}).get(
                    "counters", self._node_counters
                )

                print(
                    f"📊 Loaded knowledge graph: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges"
                )
            except Exception as e:
                print(f"⚠️  Failed to load graph from JSON: {e}")
                self.graph = DiGraph()

        # Fallback to pickle (legacy format)
        elif (self.storage_dir / "knowledge_graph.pkl").exists():
            try:
                with open(self.storage_dir / "knowledge_graph.pkl", "rb") as f:
                    self.graph = pickle.load(f)
                print(
                    f"📊 Loaded knowledge graph (legacy pickle): {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges"
                )
            except Exception as e:
                print(f"⚠️  Failed to load graph: {e}")
                self.graph = DiGraph()

        # Load any pending incremental changes from changelog
        self._load_changelog()

    def _load_changelog(self):
        """Load and apply incremental changes from changelog."""
        if not HAS_NETWORKX or not self.changelog_path.exists():
            return

        try:
            applied = 0
            with open(self.changelog_path, "r") as f:
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
                            # Also add any tracked edges
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

    def _check_snapshot(self):
        """Check if full snapshot is needed based on change count."""
        if len(self._pending_changes) >= self.SNAPSHOT_INTERVAL:
            self.save(incremental=False)

    def save(self, incremental: bool = True):
        """Save graph to JSON with optional incremental append-only mode.

        Args:
            incremental: If True and there are pending changes, only append
                        changes to changelog. If False or no changelog exists,
                        perform full snapshot.
        """
        if not HAS_NETWORKX:
            return

        with self.lock:
            self.storage_dir.mkdir(parents=True, exist_ok=True)

            # Incremental append-only save
            if incremental and self._pending_changes:
                # Append changes to changelog (fast O(k) where k = changes)
                with open(self.changelog_path, "a") as f:
                    for change in self._pending_changes:
                        f.write(json.dumps(change, default=str) + "\n")
                self._pending_changes.clear()
                return

            # Full snapshot (slow O(n+m) but needed periodically)
            data = {
                "nodes": [],
                "edges": [],
                "metadata": {
                    "counters": self._node_counters,
                    "saved_at": datetime.now().isoformat(),
                    "node_count": self.graph.number_of_nodes(),
                    "edge_count": self.graph.number_of_edges(),
                },
            }

            # Serialize nodes
            for node_id, node_data in self.graph.nodes(data=True):
                node_dict = {"id": node_id}
                node_dict.update(node_data)
                data["nodes"].append(node_dict)

            # Serialize edges
            for source, target, edge_data in self.graph.edges(data=True):
                edge_dict = {"source": source, "target": target}
                edge_dict.update(edge_data)
                data["edges"].append(edge_dict)

            # Save to JSON
            json_path = self.storage_dir / "knowledge_graph.json"
            with open(json_path, "w") as f:
                json.dump(data, f, indent=2, default=str)

            # Clear changelog after full snapshot
            if self.changelog_path.exists():
                self.changelog_path.unlink()
            self._last_snapshot_size = len(data["nodes"]) + len(data["edges"])

    # ═══════════════════════════════════════════════════════════════
    # NODE OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    def add_discovery(
        self,
        problem: str,
        hypothesis: str,
        contradiction: Dict[str, Any],
        c4_path: List[str],
        confidence_score: float,
        domain: str = "general",
        falsifiability_criteria: Optional[List[Dict]] = None,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        tags: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None,
    ) -> str:
        """Add a discovery/hypothesis node."""
        with self.lock:
            self._node_counters["discovery"] += 1
            node_id = f"discovery_{self._node_counters['discovery']}"

            node_data = NodeData(
                node_id=node_id,
                node_type="discovery",
                metadata={
                    "problem": problem,
                    "hypothesis": hypothesis,
                    "contradiction": contradiction,
                    "c4_path": c4_path,
                    "confidence_score": confidence_score,
                    "domain": domain,
                    "falsifiability_criteria": falsifiability_criteria or [],
                    "status": "pending",
                    "llm_provider": llm_provider,
                    "llm_model": llm_model,
                },
                tags=tags or [],
                embedding=embedding,
            )

            if HAS_NETWORKX:
                self.graph.add_node(node_id, **node_data.to_dict())
            else:
                self.graph["nodes"][node_id] = node_data.to_dict()

            # Track for incremental save
            self._pending_changes.append(
                {
                    "op": "add_node",
                    "id": node_id,
                    "type": "discovery",
                    "data": node_data.to_dict(),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            self._check_snapshot()

            return node_id

    def add_project(
        self,
        name: str,
        description: str = "",
        domain: str = "general",
        objectives: Optional[List[str]] = None,
        discovery_ids: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Add a research project node."""
        with self.lock:
            self._node_counters["project"] += 1
            node_id = f"project_{self._node_counters['project']}"

            node_data = NodeData(
                node_id=node_id,
                node_type="project",
                metadata={
                    "name": name,
                    "description": description,
                    "domain": domain,
                    "objectives": objectives or [],
                    "discovery_ids": discovery_ids or [],
                    "status": "active",
                },
                tags=tags or [],
            )

            if HAS_NETWORKX:
                self.graph.add_node(node_id, **node_data.to_dict())
                # Link discoveries to project
                for disc_id in discovery_ids or []:
                    if self.has_node(disc_id):
                        self.graph.add_edge(
                            node_id, disc_id, edge_type="contains", weight=1.0
                        )
            else:
                self.graph["nodes"][node_id] = node_data.to_dict()

            # Track for incremental save
            self._pending_changes.append(
                {
                    "op": "add_node",
                    "id": node_id,
                    "type": "project",
                    "data": node_data.to_dict(),
                    "edges": [
                        {"to": d, "type": "contains"} for d in (discovery_ids or [])
                    ],
                    "timestamp": datetime.now().isoformat(),
                }
            )
            self._check_snapshot()

            return node_id

    def add_reference(
        self,
        title: str,
        authors: List[str],
        year: int,
        source: str,  # arxiv, pubmed, doi, etc.
        source_id: str,
        abstract: str = "",
        url: str = "",
        tags: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None,
    ) -> str:
        """Add a bibliographic reference node."""
        with self.lock:
            self._node_counters["reference"] += 1
            node_id = f"reference_{self._node_counters['reference']}"

            node_data = NodeData(
                node_id=node_id,
                node_type="reference",
                metadata={
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "source": source,
                    "source_id": source_id,
                    "abstract": abstract,
                    "url": url,
                    "citation_count": 0,
                },
                tags=tags or [],
                embedding=embedding,
            )

            if HAS_NETWORKX:
                self.graph.add_node(node_id, **node_data.to_dict())
            else:
                self.graph["nodes"][node_id] = node_data.to_dict()

            # Track for incremental save
            self._pending_changes.append(
                {
                    "op": "add_node",
                    "id": node_id,
                    "type": "reference",
                    "data": node_data.to_dict(),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            self._check_snapshot()

            return node_id

    def add_analogy(
        self,
        source_domain: str,
        target_domain: str,
        source_concept: str,
        target_concept: str,
        mapping_type: str,  # horizontal, vertical, semantic, structural
        confidence: float,
        semantic_similarity: Optional[float] = None,
        structural_similarity: Optional[float] = None,
        evidence: Optional[List[str]] = None,
    ) -> str:
        """Add an analogy mapping node."""
        with self.lock:
            self._node_counters["analogy"] += 1
            node_id = f"analogy_{self._node_counters['analogy']}"

            node_data = NodeData(
                node_id=node_id,
                node_type="analogy",
                metadata={
                    "source_domain": source_domain,
                    "target_domain": target_domain,
                    "source_concept": source_concept,
                    "target_concept": target_concept,
                    "mapping_type": mapping_type,
                    "confidence": confidence,
                    "semantic_similarity": semantic_similarity,
                    "structural_similarity": structural_similarity,
                    "evidence": evidence or [],
                    "verified": False,
                    "usage_count": 0,
                },
                tags=[source_domain, target_domain],
            )

            edges_added = []
            if HAS_NETWORKX:
                self.graph.add_node(node_id, **node_data.to_dict())
                # Create domain nodes if not exist
                for domain in [source_domain, target_domain]:
                    domain_id = f"domain_{domain}"
                    if not self.graph.has_node(domain_id):
                        self.graph.add_node(
                            domain_id,
                            node_type="domain",
                            name=domain,
                            created_at=datetime.now().isoformat(),
                        )
                        edges_added.append({"to": domain_id, "type": "domain_node"})
                # Link analogy to domains
                self.graph.add_edge(
                    node_id,
                    f"domain_{source_domain}",
                    edge_type="maps_from",
                    weight=confidence,
                )
                self.graph.add_edge(
                    node_id,
                    f"domain_{target_domain}",
                    edge_type="maps_to",
                    weight=confidence,
                )
                edges_added.extend(
                    [
                        {
                            "to": f"domain_{source_domain}",
                            "type": "maps_from",
                            "weight": confidence,
                        },
                        {
                            "to": f"domain_{target_domain}",
                            "type": "maps_to",
                            "weight": confidence,
                        },
                    ]
                )
            else:
                self.graph["nodes"][node_id] = node_data.to_dict()

            # Track for incremental save
            self._pending_changes.append(
                {
                    "op": "add_node",
                    "id": node_id,
                    "type": "analogy",
                    "data": node_data.to_dict(),
                    "edges": edges_added,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            self._check_snapshot()

            return node_id

    def add_operator_node(
        self,
        operator_name: str,
        from_state: Tuple[int, int, int],
        to_state: Tuple[int, int, int],
        description: str = "",
        usage_count: int = 0,
        success_rate: float = 0.0,
    ) -> str:
        """Add a C4 operator node with usage statistics."""
        with self.lock:
            self._node_counters["operator"] += 1
            node_id = f"operator_{self._node_counters['operator']}"

            node_data = NodeData(
                node_id=node_id,
                node_type="operator",
                metadata={
                    "operator_name": operator_name,
                    "from_state": from_state,
                    "to_state": to_state,
                    "description": description,
                    "usage_count": usage_count,
                    "success_rate": success_rate,
                    "transform_vector": (
                        to_state[0] - from_state[0],
                        to_state[1] - from_state[1],
                        to_state[2] - from_state[2],
                    ),
                },
                tags=[operator_name],
            )

            if HAS_NETWORKX:
                self.graph.add_node(node_id, **node_data.to_dict())
            else:
                self.graph["nodes"][node_id] = node_data.to_dict()

            # Track for incremental save
            self._pending_changes.append(
                {
                    "op": "add_node",
                    "id": node_id,
                    "type": "operator",
                    "data": node_data.to_dict(),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            self._check_snapshot()

            return node_id

    def add_experiment_node(
        self,
        experiment_id: str,
        discovery_id: str,
        name: str,
        description: str = "",
        researcher: str = "",
        status: str = "design",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add an experiment node for hypothesis validation."""
        with self.lock:
            node_data = NodeData(
                node_id=experiment_id,
                node_type="experiment",
                metadata={
                    "discovery_id": discovery_id,
                    "name": name,
                    "description": description,
                    "researcher": researcher,
                    "status": status,
                    **(metadata or {}),
                },
                tags=["experiment", discovery_id],
            )

            if HAS_NETWORKX:
                self.graph.add_node(experiment_id, **node_data.to_dict())
            else:
                self.graph["nodes"][experiment_id] = node_data.to_dict()

            # Track for incremental save
            self._pending_changes.append(
                {
                    "op": "add_node",
                    "id": experiment_id,
                    "type": "experiment",
                    "data": node_data.to_dict(),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            self._check_snapshot()

            return experiment_id

    # ═══════════════════════════════════════════════════════════════
    # EDGE OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        edge_type: str,
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add an edge between two nodes."""
        with self.lock:
            if not self.has_node(from_id) or not self.has_node(to_id):
                return False

            if HAS_NETWORKX:
                self.graph.add_edge(
                    from_id,
                    to_id,
                    edge_type=edge_type,
                    weight=weight,
                    metadata=metadata or {},
                    timestamp=datetime.now().isoformat(),
                )
            else:
                self.graph["edges"].append(
                    {
                        "from": from_id,
                        "to": to_id,
                        "edge_type": edge_type,
                        "weight": weight,
                        "metadata": metadata or {},
                    }
                )

            # Track for incremental save
            self._pending_changes.append(
                {
                    "op": "add_edge",
                    "src": from_id,
                    "tgt": to_id,
                    "type": edge_type,
                    "weight": weight,
                    "metadata": metadata or {},
                    "timestamp": datetime.now().isoformat(),
                }
            )
            self._check_snapshot()

            return True

    def add_citation(self, from_id: str, to_ref_id: str, context: str = ""):
        """Add a citation edge from discovery/project to reference."""
        return self.add_edge(
            from_id, to_ref_id, edge_type="cites", metadata={"context": context}
        )

    def add_derivation(self, from_id: str, to_id: str, operator: str = ""):
        """Add derivation edge: to_id was derived from from_id."""
        return self.add_edge(
            from_id, to_id, edge_type="derived_from", metadata={"operator": operator}
        )

    def add_transformation(self, from_state: str, to_state: str, operator: str):
        """Add C4 state transformation edge."""
        return self.add_edge(
            from_state,
            to_state,
            edge_type="transformed_by",
            metadata={"operator": operator},
        )

    # ═══════════════════════════════════════════════════════════════
    # QUERY OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    def has_node(self, node_id: str) -> bool:
        """Check if node exists."""
        if HAS_NETWORKX:
            return self.graph.has_node(node_id)
        return node_id in self.graph["nodes"]

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node data."""
        if not self.has_node(node_id):
            return None

        if HAS_NETWORKX:
            return dict(self.graph.nodes[node_id])
        return self.graph["nodes"].get(node_id)

    def get_nodes_by_type(self, node_type: str) -> List[Dict[str, Any]]:
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

    def get_nodes_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get all nodes with a specific tag."""
        if HAS_NETWORKX:
            return [
                dict(data)
                for _, data in self.graph.nodes(data=True)
                if tag in data.get("tags", [])
            ]
        return [
            data for data in self.graph["nodes"].values() if tag in data.get("tags", [])
        ]

    def get_discoveries_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Get all discoveries in a domain."""
        return [
            node
            for node in self.get_nodes_by_type("discovery")
            if node.get("metadata", {}).get("domain") == domain
        ]

    def get_neighbors(self, node_id: str, edge_type: Optional[str] = None) -> List[str]:
        """Get neighboring nodes."""
        if not self.has_node(node_id):
            return []

        if HAS_NETWORKX:
            neighbors = list(self.graph.neighbors(node_id))
            if edge_type:
                neighbors = [
                    n
                    for n in neighbors
                    if self.graph.edges[node_id, n].get("edge_type") == edge_type
                ]
            return neighbors

        # Fallback
        neighbors = []
        for edge in self.graph["edges"]:
            if edge["from"] == node_id:
                if edge_type is None or edge.get("edge_type") == edge_type:
                    neighbors.append(edge["to"])
        return neighbors

    def get_neighbors_with_edges(
        self, node_id: str, edge_type: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Get neighboring nodes with their edge data as a dictionary."""
        if not self.has_node(node_id):
            return {}

        result = {}
        if HAS_NETWORKX:
            for neighbor in self.graph.neighbors(node_id):
                edge_data = self.graph.edges[node_id, neighbor]
                if edge_type is None or edge_data.get("edge_type") == edge_type:
                    result[neighbor] = dict(edge_data)
            return result

        # Fallback
        for edge in self.graph["edges"]:
            if edge["from"] == node_id:
                if edge_type is None or edge.get("edge_type") == edge_type:
                    result[edge["to"]] = edge
        return result

    def get_citations(self, discovery_id: str) -> List[Dict[str, Any]]:
        """Get all references cited by a discovery."""
        ref_ids = self.get_neighbors(discovery_id, edge_type="cites")
        return [self.get_node(rid) for rid in ref_ids if self.get_node(rid)]

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """Get all nodes in the graph."""
        if HAS_NETWORKX:
            return [dict(data) for _, data in self.graph.nodes(data=True)]
        return list(self.graph["nodes"].values())

    def get_all_edges(self) -> List[Dict[str, Any]]:
        """Get all edges in the graph."""
        if HAS_NETWORKX:
            return [
                {"source": u, "target": v, **data}
                for u, v, data in self.graph.edges(data=True)
            ]
        return [
            {"source": edge["from"], "target": edge["to"], **edge}
            for edge in self.graph["edges"]
        ]

    # ═══════════════════════════════════════════════════════════════
    # ANALYSIS OPERATIONS
    # ═══════════════════════════════════════════════════════════════

    def find_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """Find shortest path between two nodes."""
        if not HAS_NETWORKX:
            return None

        try:
            return nx.shortest_path(self.graph, source, target)
        except nx.NetworkXNoPath:
            return None

    def get_central_nodes(self, n: int = 10) -> List[Tuple[str, float]]:
        """Get most central nodes by PageRank."""
        if not HAS_NETWORKX or self.graph.number_of_nodes() == 0:
            return []

        pagerank = nx.pagerank(self.graph)
        return sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:n]

    def find_clusters(self) -> List[List[str]]:
        """Find communities/clusters in the graph."""
        if not HAS_NETWORKX:
            return []

        # Convert to undirected for community detection
        undirected = self.graph.to_undirected()
        from networkx.algorithms import community

        communities = community.greedy_modularity_communities(undirected)
        return [list(c) for c in communities]

    def bibliographic_coupling(
        self, ref_id: str, top_n: int = 5
    ) -> List[Tuple[str, int]]:
        """Find papers that cite the same papers as ref_id."""
        if not HAS_NETWORKX:
            return []

        # Get papers citing ref_id
        citing_ref = list(self.graph.predecessors(ref_id))

        # For each other reference, count shared citations
        coupling_scores = {}
        for other_ref in self.get_nodes_by_type("reference"):
            other_id = other_ref["node_id"]
            if other_id == ref_id:
                continue

            citing_other = set(self.graph.predecessors(other_id))
            shared = len(set(citing_ref) & citing_other)
            if shared > 0:
                coupling_scores[other_id] = shared

        return sorted(coupling_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    def find_analogy_chains(
        self, source_domain: str, target_domain: str, max_length: int = 3
    ) -> List[List[str]]:
        """Find chains of analogies between domains."""
        if not HAS_NETWORKX:
            return []

        source_node = f"domain_{source_domain}"
        target_node = f"domain_{target_domain}"

        if not self.graph.has_node(source_node) or not self.graph.has_node(target_node):
            return []

        try:
            paths = list(
                nx.all_simple_paths(
                    self.graph,
                    source_node,
                    target_node,
                    cutoff=max_length * 2,  # Each analogy adds 2 edges
                )
            )
            return paths
        except nx.NetworkXNoPath:
            return []

    # ═══════════════════════════════════════════════════════════════
    # SEMANTIC SEARCH (requires embeddings)
    # ═══════════════════════════════════════════════════════════════

    def find_similar_nodes(
        self,
        query_embedding: List[float],
        node_type: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Tuple[str, float]]:
        """Find nodes by cosine similarity to query embedding."""
        import numpy as np

        query_vec = np.array(query_embedding)
        similarities = []

        nodes = (
            self.get_nodes_by_type(node_type)
            if node_type
            else list(self.graph["nodes"].values())
            if not HAS_NETWORKX
            else [data for _, data in self.graph.nodes(data=True)]
        )

        for node in nodes:
            emb = node.get("embedding")
            if emb:
                node_vec = np.array(emb)
                sim = np.dot(query_vec, node_vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(node_vec)
                )
                similarities.append((node["node_id"], float(sim)))

        return sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]

    # ═══════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════

    def get_stats(self) -> Dict[str, Any]:
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

    def export_to_json(self, path: str):
        """Export graph to JSON for visualization."""
        if HAS_NETWORKX:
            data = {
                "nodes": [{"id": n, **data} for n, data in self.graph.nodes(data=True)],
                "edges": [
                    {"source": u, "target": v, **data}
                    for u, v, data in self.graph.edges(data=True)
                ],
            }
        else:
            data = self.graph

        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def export_to_graphml(self, path: str):
        """Export to GraphML for Gephi/Cytoscape."""
        if HAS_NETWORKX:
            nx.write_graphml(self.graph, path)


# ═══════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════

_knowledge_graph: Optional[KnowledgeGraph] = None


def get_knowledge_graph(storage_path: Optional[str] = None) -> KnowledgeGraph:
    """Get singleton knowledge graph instance."""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph(storage_path)
    return _knowledge_graph
