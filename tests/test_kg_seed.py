"""
TURBO-CDI Graph: Knowledge Graph Seed Tests
"""
from __future__ import annotations

import tempfile

import pytest

from src.graph.knowledge_graph import KnowledgeGraph
from src.graph.seed_data import SEED_DOMAINS, SEED_PROBLEMS, seed_knowledge_graph


class TestSeedKnowledgeGraph:
    def test_seeds_empty_graph(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            graph = KnowledgeGraph(storage_path=tmpdir)
            # Clear auto-seed for this test
            graph.graph.clear()
            assert graph.graph.number_of_nodes() == 0

            seed_knowledge_graph(graph)

            assert graph.graph.number_of_nodes() > 0
            # Domain nodes + discovery nodes
            assert graph.graph.number_of_nodes() == len(SEED_DOMAINS) + len(SEED_PROBLEMS)

    def test_skips_non_empty_graph(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            graph = KnowledgeGraph(storage_path=tmpdir)
            # Clear auto-seed and add our own node
            graph.graph.clear()
            graph.graph.add_node("existing_node", node_type="test")

            seed_knowledge_graph(graph)

            # Should not add seed data
            assert graph.graph.number_of_nodes() == 1

    def test_domain_nodes_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            graph = KnowledgeGraph(storage_path=tmpdir)
            seed_knowledge_graph(graph)

            for domain in SEED_DOMAINS:
                node_id = f"domain_{domain['name']}"
                assert graph.has_node(node_id)
                node = graph.get_node(node_id)
                assert node["node_type"] == "domain"
                assert node["name"] == domain["name"]

    def test_discovery_nodes_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            graph = KnowledgeGraph(storage_path=tmpdir)
            seed_knowledge_graph(graph)

            discoveries = graph.get_nodes_by_type("discovery")
            assert len(discoveries) == len(SEED_PROBLEMS)

    def test_domain_edges_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            graph = KnowledgeGraph(storage_path=tmpdir)
            seed_knowledge_graph(graph)

            edges = graph.get_all_edges()
            assert len(edges) > 0
            # At least some edges should connect domains
            domain_edges = [e for e in edges if e.get("edge_type") == "isomorphic_to"]
            assert len(domain_edges) >= 2

    def test_c4_states_in_problems(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            graph = KnowledgeGraph(storage_path=tmpdir)
            seed_knowledge_graph(graph)

            for problem_data in SEED_PROBLEMS:
                domain = problem_data["domain"]
                domain_discoveries = graph.get_discoveries_by_domain(domain)
                assert len(domain_discoveries) >= 1
                # Check that C4 path is present
                discovery = domain_discoveries[0]
                assert "c4_path" in discovery.get("metadata", {})
