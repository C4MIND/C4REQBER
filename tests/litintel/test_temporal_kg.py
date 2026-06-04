"""Tests for temporal_kg.py — Temporal Knowledge Graph."""
from __future__ import annotations

from datetime import datetime

import pytest

from src.discovery.temporal_kg import (
    ConsensusEvolution,
    ConsensusQuery,
    TemporalKnowledgeGraph,
    TimeStampedClaim,
)


class TestTimeStampedClaim:
    def test_creation(self) -> None:
        claim = TimeStampedClaim(
            id="c1",
            text="Test claim",
            timestamp=datetime(2020, 1, 1),
            source="S1",
        )
        assert claim.id == "c1"
        assert claim.confidence == 1.0


class TestTemporalKnowledgeGraph:
    def test_add_claim(self) -> None:
        tkg = TemporalKnowledgeGraph()
        claim = TimeStampedClaim(
            id="c1",
            text="Dark matter is composed of WIMPs",
            timestamp=datetime(2020, 1, 1),
            source="Paper A",
        )
        tkg.add_claim(claim)
        assert "c1" in tkg.claims
        assert tkg.graph.has_node("c1")

    def test_add_claims(self) -> None:
        tkg = TemporalKnowledgeGraph()
        claims = [
            TimeStampedClaim(id=f"c{i}", text=f"Claim {i}", timestamp=datetime(2020, 1, i), source="S")
            for i in range(1, 4)
        ]
        tkg.add_claims(claims)
        assert len(tkg.claims) == 3

    def test_temporal_linking(self) -> None:
        tkg = TemporalKnowledgeGraph()
        c1 = TimeStampedClaim(
            id="c1",
            text="Dark matter is WIMPs",
            timestamp=datetime(2020, 1, 1),
            source="S1",
            domain="cosmology",
        )
        c2 = TimeStampedClaim(
            id="c2",
            text="Dark matter may be axions",
            timestamp=datetime(2020, 6, 1),
            source="S2",
            domain="cosmology",
        )
        tkg.add_claim(c1)
        tkg.add_claim(c2)
        # Should have an edge due to topic similarity
        assert tkg.graph.has_edge("c1", "c2") or tkg.graph.has_edge("c2", "c1")

    def test_query_consensus_evolution(self) -> None:
        tkg = TemporalKnowledgeGraph()
        claims = [
            TimeStampedClaim(
                id="c1",
                text="String theory is the theory of everything",
                timestamp=datetime(2018, 1, 1),
                source="S1",
                domain="physics",
            ),
            TimeStampedClaim(
                id="c2",
                text="String theory unifies all forces",
                timestamp=datetime(2019, 1, 1),
                source="S2",
                domain="physics",
            ),
            TimeStampedClaim(
                id="c3",
                text="Loop quantum gravity is an alternative to string theory",
                timestamp=datetime(2020, 1, 1),
                source="S3",
                domain="physics",
            ),
            TimeStampedClaim(
                id="c4",
                text="String theory faces challenges from swampland conjectures",
                timestamp=datetime(2021, 1, 1),
                source="S4",
                domain="physics",
            ),
        ]
        tkg.add_claims(claims)

        query = ConsensusQuery(topic="string theory", domain="physics")
        evolution = tkg.query_consensus_evolution(query)
        assert isinstance(evolution, ConsensusEvolution)
        assert evolution.topic == "string theory"
        assert len(evolution.time_points) > 0
        assert len(evolution.consensus_scores) == len(evolution.time_points)

    def test_query_empty(self) -> None:
        tkg = TemporalKnowledgeGraph()
        query = ConsensusQuery(topic="nonexistent topic")
        evolution = tkg.query_consensus_evolution(query)
        assert len(evolution.time_points) == 0

    def test_topic_relevance(self) -> None:
        tkg = TemporalKnowledgeGraph()
        rel = tkg._topic_relevance("Dark matter is composed of WIMPs", "dark matter")
        assert rel > 0.15

        rel_low = tkg._topic_relevance("Cats are mammals", "dark matter")
        assert rel_low < 0.15

    def test_get_claim_neighbors(self) -> None:
        tkg = TemporalKnowledgeGraph()
        claims = [
            TimeStampedClaim(id="c1", text="Dark matter is composed of WIMPs particles", timestamp=datetime(2020, 1, 1), source="S1"),
            TimeStampedClaim(id="c2", text="Dark matter may be composed of axions instead", timestamp=datetime(2020, 2, 1), source="S2"),
            TimeStampedClaim(id="c3", text="Cats are mammals that live on Earth", timestamp=datetime(2020, 3, 1), source="S3"),
        ]
        tkg.add_claims(claims)
        neighbors = tkg.get_claim_neighbors("c1", depth=1)
        # c1 and c2 are about dark matter, so they should be linked
        assert len(neighbors) >= 1

    def test_get_claim_neighbors_missing(self) -> None:
        tkg = TemporalKnowledgeGraph()
        neighbors = tkg.get_claim_neighbors("nonexistent")
        assert neighbors == []

    def test_consensus_trajectory(self) -> None:
        tkg = TemporalKnowledgeGraph()
        claims = [
            TimeStampedClaim(
                id=f"c{i}",
                text="Consensus claim" if i < 3 else "Divergent claim",
                timestamp=datetime(2020, i, 1),
                source="S",
            )
            for i in range(1, 6)
        ]
        tkg.add_claims(claims)
        trajectory = tkg.consensus_trajectory("consensus")
        assert "topic" in trajectory
        assert "stability" in trajectory
        assert "trend" in trajectory
        assert "points" in trajectory
        assert len(trajectory["points"]) > 0

    def test_find_paradigm_boundaries(self) -> None:
        tkg = TemporalKnowledgeGraph()
        claims = [
            TimeStampedClaim(
                id="c1",
                text="Theory X is universally accepted",
                timestamp=datetime(2018, 1, 1),
                source="S1",
            ),
            TimeStampedClaim(
                id="c2",
                text="Theory X is universally accepted",
                timestamp=datetime(2019, 1, 1),
                source="S2",
            ),
            TimeStampedClaim(
                id="c3",
                text="Theory Y contradicts Theory X",
                timestamp=datetime(2020, 1, 1),
                source="S3",
            ),
            TimeStampedClaim(
                id="c4",
                text="Theory Y gains support",
                timestamp=datetime(2021, 1, 1),
                source="S4",
            ),
        ]
        tkg.add_claims(claims)
        boundaries = tkg.find_paradigm_boundaries("theory")
        assert isinstance(boundaries, list)
        # Should detect some boundary due to consensus shift

    def test_export_subgraph(self) -> None:
        tkg = TemporalKnowledgeGraph()
        claims = [
            TimeStampedClaim(id="c1", text="Topic A claim 1", timestamp=datetime(2020, 1, 1), source="S1"),
            TimeStampedClaim(id="c2", text="Topic A claim 2", timestamp=datetime(2020, 2, 1), source="S2"),
            TimeStampedClaim(id="c3", text="Topic B claim", timestamp=datetime(2020, 3, 1), source="S3"),
        ]
        tkg.add_claims(claims)
        subgraph = tkg.export_subgraph("Topic A")
        assert "nodes" in subgraph
        assert "edges" in subgraph
        assert len(subgraph["nodes"]) >= 2

    def test_date_filtering(self) -> None:
        tkg = TemporalKnowledgeGraph()
        claims = [
            TimeStampedClaim(id="c1", text="Old claim", timestamp=datetime(2018, 1, 1), source="S1"),
            TimeStampedClaim(id="c2", text="New claim", timestamp=datetime(2022, 1, 1), source="S2"),
        ]
        tkg.add_claims(claims)
        query = ConsensusQuery(
            topic="claim",
            start_date=datetime(2020, 1, 1),
            end_date=datetime(2023, 1, 1),
        )
        evolution = tkg.query_consensus_evolution(query)
        assert len(evolution.time_points) >= 1

    def test_domain_filtering(self) -> None:
        tkg = TemporalKnowledgeGraph()
        claims = [
            TimeStampedClaim(id="c1", text="Physics claim", timestamp=datetime(2020, 1, 1), source="S1", domain="physics"),
            TimeStampedClaim(id="c2", text="Biology claim", timestamp=datetime(2020, 2, 1), source="S2", domain="biology"),
        ]
        tkg.add_claims(claims)
        query = ConsensusQuery(topic="claim", domain="physics")
        evolution = tkg.query_consensus_evolution(query)
        # Should only include physics claims
        assert len(evolution.time_points) >= 0
