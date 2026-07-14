"""
C4REQBER: Knowledge Graph Seed Data
Initial domains, problems, and C4 states for bootstrapping the graph.
"""
from __future__ import annotations

from typing import Any

from src.c4.state import C4State
from src.graph.knowledge_graph import KnowledgeGraph


SEED_DOMAINS: list[dict[str, Any]] = [
    {"name": "physics", "description": "Fundamental laws of nature and physical systems"},
    {"name": "biology", "description": "Living organisms, ecosystems, and life processes"},
    {"name": "economics", "description": "Production, distribution, and consumption of goods"},
    {"name": "cs", "description": "Computation, algorithms, and information processing"},
    {"name": "mathematics", "description": "Abstract structures, patterns, and logical reasoning"},
]

SEED_DOMAIN_EDGES: list[tuple[str, str, str, float]] = [
    # (from_domain, to_domain, relation_type, weight)
    ("physics", "mathematics", "isomorphic_to", 0.95),
    ("cs", "mathematics", "isomorphic_to", 0.90),
    ("biology", "cs", "analogous_to", 0.75),
    ("economics", "physics", "analogous_to", 0.70),
    ("mathematics", "cs", "isomorphic_to", 0.92),
    ("physics", "cs", "analogous_to", 0.80),
]

SEED_PROBLEMS: list[dict[str, Any]] = [
    {
        "problem": "Optimize traffic flow in a dense urban environment",
        "hypothesis": "Agent-based modeling with adaptive signal timing reduces congestion by 30%",
        "domain": "cs",
        "c4_state": C4State(T=2, S=1, A=2),
        "confidence_score": 0.82,
        "tags": ["optimization", "urban", "simulation"],
    },
    {
        "problem": "Predict protein folding dynamics for novel sequences",
        "hypothesis": "Energy landscape minimization via graph neural networks",
        "domain": "biology",
        "c4_state": C4State(T=2, S=2, A=1),
        "confidence_score": 0.78,
        "tags": ["protein", "ml", "prediction"],
    },
    {
        "problem": "Model systemic risk in interconnected financial networks",
        "hypothesis": "Percolation theory captures cascade thresholds in banking systems",
        "domain": "economics",
        "c4_state": C4State(T=1, S=2, A=2),
        "confidence_score": 0.85,
        "tags": ["finance", "networks", "risk"],
    },
    {
        "problem": "Design efficient quantum error correction codes",
        "hypothesis": "Topological codes outperform surface codes at low error rates",
        "domain": "physics",
        "c4_state": C4State(T=2, S=2, A=0),
        "confidence_score": 0.74,
        "tags": ["quantum", "error-correction", "topology"],
    },
    {
        "problem": "Prove bounds on graph coloring with local algorithms",
        "hypothesis": "Lovasz theta function provides tight bounds for random graphs",
        "domain": "mathematics",
        "c4_state": C4State(T=1, S=2, A=0),
        "confidence_score": 0.88,
        "tags": ["graphs", "algorithms", "bounds"],
    },
]


def seed_knowledge_graph(graph: KnowledgeGraph | None = None) -> KnowledgeGraph:
    """
    Seed the knowledge graph with initial domains, mappings, and problems.

    If the graph already contains nodes, seeding is skipped to avoid duplicates.
    Returns the (possibly newly seeded) graph instance.
    """
    if graph is None:
        from src.graph.knowledge_graph import get_knowledge_graph

        graph = get_knowledge_graph()

    # Skip if already seeded
    if graph.graph.number_of_nodes() > 0:
        return graph

    # Add domain nodes
    for domain in SEED_DOMAINS:
        domain_id = f"domain_{domain['name']}"
        graph.graph.add_node(
            domain_id,
            node_type="domain",
            name=domain["name"],
            description=domain["description"],
            created_at="",
            updated_at="",
            metadata={},
            tags=[domain["name"]],
            embedding=None,
        )

    # Add cross-domain edges
    for from_domain, to_domain, relation, weight in SEED_DOMAIN_EDGES:
        from_id = f"domain_{from_domain}"
        to_id = f"domain_{to_domain}"
        if graph.has_node(from_id) and graph.has_node(to_id):
            graph.add_edge(from_id, to_id, edge_type=relation, weight=weight)

    # Add seed problems as discovery nodes
    for problem_data in SEED_PROBLEMS:
        c4_path = [str(problem_data["c4_state"])]
        graph.add_discovery(
            problem=problem_data["problem"],
            hypothesis=problem_data["hypothesis"],
            contradiction={},
            c4_path=c4_path,
            confidence_score=problem_data["confidence_score"],
            domain=problem_data["domain"],
            tags=problem_data["tags"],
        )

    graph.save(incremental=False)
    return graph
