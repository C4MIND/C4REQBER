"""Temporal Knowledge Graph for scientific claims."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import networkx as nx
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class TimeStampedClaim:
    """A scientific claim with temporal metadata."""

    id: str
    text: str
    timestamp: datetime
    source: str
    confidence: float = 1.0
    citations: int = 0
    domain: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsensusEvolution:
    """Evolution of consensus on a topic over time."""

    topic: str
    time_points: list[datetime] = field(default_factory=list)
    consensus_scores: list[float] = field(default_factory=list)
    claim_counts: list[int] = field(default_factory=list)
    dominant_claims: list[str] = field(default_factory=list)
    variance: list[float] = field(default_factory=list)


@dataclass
class ConsensusQuery:
    """Query for consensus evolution."""

    topic: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    domain: str = ""
    min_confidence: float = 0.0


class TemporalKnowledgeGraph:
    """Temporal Knowledge Graph for tracking scientific claims over time."""

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self.claims: dict[str, TimeStampedClaim] = {}
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self._texts_fitted: bool = False

    def add_claim(self, claim: TimeStampedClaim) -> None:
        """Add a claim to the temporal graph."""
        self.graph.add_node(
            claim.id,
            text=claim.text,
            timestamp=claim.timestamp.isoformat(),
            source=claim.source,
            confidence=claim.confidence,
            citations=claim.citations,
            domain=claim.domain,
            **claim.metadata,
        )
        self.claims[claim.id] = claim
        self._texts_fitted = False

        # Link to temporally adjacent claims on similar topics
        self._link_temporal_neighbors(claim)

    def add_claims(self, claims: list[TimeStampedClaim]) -> None:
        """Add multiple claims."""
        for claim in claims:
            self.add_claim(claim)

    def _link_temporal_neighbors(self, claim: TimeStampedClaim, threshold: float = 0.25) -> None:
        """Create edges to claims on similar topics within temporal proximity."""
        if not self.claims:
            return

        texts = [claim.text]
        ids: list[str] = []
        for cid, other in self.claims.items():
            if cid == claim.id:
                continue
            # Time proximity: within 2 years
            time_diff = abs((claim.timestamp - other.timestamp).days)
            if time_diff <= 730:
                texts.append(other.text)
                ids.append(cid)

        if len(texts) < 2:
            return

        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            X = vectorizer.fit_transform(texts)
            sims = cosine_similarity(X[0:1], X[1:])[0]
            for i, cid in enumerate(ids):
                if sims[i] > threshold:
                    self.graph.add_edge(
                        claim.id,
                        cid,
                        weight=float(sims[i]),
                        time_diff_days=abs((claim.timestamp - self.claims[cid].timestamp).days),
                        relation="temporal_similarity",
                    )
        except ValueError:
            pass

    def query_consensus_evolution(self, query: ConsensusQuery) -> ConsensusEvolution:
        """Query how consensus on a topic has changed over time."""
        # Filter claims by topic relevance
        relevant_claims = self._filter_by_topic(query)
        if not relevant_claims:
            return ConsensusEvolution(topic=query.topic)

        # Sort by time
        sorted_claims = sorted(relevant_claims, key=lambda c: c.timestamp)

        # Create time windows
        start = query.start_date or sorted_claims[0].timestamp
        end = query.end_date or sorted_claims[-1].timestamp
        window_days = max(30, (end - start).days // 6)

        time_points: list[datetime] = []
        consensus_scores: list[float] = []
        claim_counts: list[int] = []
        dominant_claims: list[str] = []
        variances: list[float] = []

        current = start
        while current <= end:
            window_end = current + timedelta(days=window_days)
            window_claims = [
                c for c in sorted_claims
                if current <= c.timestamp < window_end
            ]

            if window_claims:
                score, dominant, var = self._compute_window_consensus(window_claims)
                time_points.append(current)
                consensus_scores.append(score)
                claim_counts.append(len(window_claims))
                dominant_claims.append(dominant)
                variances.append(var)

            current = window_end

        return ConsensusEvolution(
            topic=query.topic,
            time_points=time_points,
            consensus_scores=consensus_scores,
            claim_counts=claim_counts,
            dominant_claims=dominant_claims,
            variance=variances,
        )

    def _filter_by_topic(self, query: ConsensusQuery) -> list[TimeStampedClaim]:
        """Filter claims by topic relevance and query constraints."""
        results: list[TimeStampedClaim] = []

        for claim in self.claims.values():
            # Domain filter
            if query.domain and claim.domain != query.domain:
                continue

            # Confidence filter
            if claim.confidence < query.min_confidence:
                continue

            # Date filter
            if query.start_date and claim.timestamp < query.start_date:
                continue
            if query.end_date and claim.timestamp > query.end_date:
                continue

            # Topic relevance
            if self._topic_relevance(claim.text, query.topic) > 0.15:
                results.append(claim)

        return results

    def _topic_relevance(self, text: str, topic: str) -> float:
        """Compute relevance of text to topic."""
        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            X = vectorizer.fit_transform([text, topic])
            return float(cosine_similarity(X[0:1], X[1:2])[0, 0])
        except ValueError:
            # Fallback: keyword overlap
            text_words = set(text.lower().split())
            topic_words = set(topic.lower().split())
            if not topic_words:
                return 0.0
            return len(text_words & topic_words) / len(topic_words)

    def _compute_window_consensus(
        self, claims: list[TimeStampedClaim]
    ) -> tuple[float, str, float]:
        """Compute consensus metrics for a time window."""
        if len(claims) == 1:
            return 1.0, claims[0].text[:100], 0.0

        texts = [c.text for c in claims]
        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            X = vectorizer.fit_transform(texts)
            sim_matrix = cosine_similarity(X)
        except ValueError:
            return 0.5, texts[0][:100], 0.5

        # Consensus = mean pairwise similarity
        mask = ~np.eye(sim_matrix.shape[0], dtype=bool)
        mean_sim = float(sim_matrix[mask].mean()) if mask.any() else 1.0

        # Variance in similarity
        var = float(np.var(sim_matrix[mask])) if mask.any() else 0.0

        # Dominant claim = highest average similarity to others
        avg_sims = sim_matrix.mean(axis=1)
        dominant_idx = int(np.argmax(avg_sims))
        dominant = texts[dominant_idx][:100]

        return mean_sim, dominant, var

    def get_claim_neighbors(self, claim_id: str, depth: int = 1) -> list[TimeStampedClaim]:
        """Get temporally connected claims."""
        if claim_id not in self.claims:
            return []

        nodes: set[str] = {claim_id}
        for _ in range(depth):
            new_nodes: set[str] = set()
            for node in nodes:
                new_nodes.update(self.graph.predecessors(node))
                new_nodes.update(self.graph.successors(node))
            nodes.update(new_nodes)

        nodes.discard(claim_id)
        return [self.claims[n] for n in nodes if n in self.claims]

    def consensus_trajectory(self, topic: str, window_days: int = 180) -> dict[str, Any]:
        """Get full consensus trajectory for a topic."""
        query = ConsensusQuery(topic=topic)
        evolution = self.query_consensus_evolution(query)

        if not evolution.time_points:
            return {
                "topic": topic,
                "stability": 0.0,
                "trend": "insufficient_data",
                "points": [],
            }

        # Stability = inverse of variance in consensus scores
        if len(evolution.consensus_scores) > 1:
            stability = 1.0 - min(float(np.var(evolution.consensus_scores)), 1.0)
            trend = (
                "converging"
                if evolution.consensus_scores[-1] > evolution.consensus_scores[0]
                else "diverging"
            )
        else:
            stability = 1.0
            trend = "stable"

        points = []
        for i, tp in enumerate(evolution.time_points):
            points.append({
                "date": tp.isoformat(),
                "consensus_score": evolution.consensus_scores[i],
                "claim_count": evolution.claim_counts[i],
                "dominant_claim": evolution.dominant_claims[i],
                "variance": evolution.variance[i],
            })

        return {
            "topic": topic,
            "stability": stability,
            "trend": trend,
            "points": points,
        }

    def find_paradigm_boundaries(self, topic: str) -> list[dict[str, Any]]:
        """Find potential paradigm shift boundaries in consensus evolution."""
        trajectory = self.consensus_trajectory(topic)
        points = trajectory.get("points", [])

        if len(points) < 3:
            return []

        boundaries: list[dict[str, Any]] = []
        scores = [p["consensus_score"] for p in points]

        for i in range(1, len(scores) - 1):
            # Significant drop in consensus
            if scores[i - 1] - scores[i] > 0.2 and scores[i + 1] < scores[i - 1]:
                boundaries.append({
                    "date": points[i]["date"],
                    "type": "consensus_drop",
                    "magnitude": scores[i - 1] - scores[i],
                    "before_score": scores[i - 1],
                    "after_score": scores[i],
                })

            # High variance point
            if points[i]["variance"] > 0.1:
                boundaries.append({
                    "date": points[i]["date"],
                    "type": "high_variance",
                    "magnitude": points[i]["variance"],
                    "claim_count": points[i]["claim_count"],
                })

        return boundaries

    def export_subgraph(self, topic: str) -> dict[str, Any]:
        """Export a topic-specific subgraph."""
        relevant = self._filter_by_topic(ConsensusQuery(topic=topic))
        ids = {c.id for c in relevant}

        sub = self.graph.subgraph(ids)
        return {
            "nodes": [
                {
                    "id": n,
                    "text": sub.nodes[n].get("text", ""),
                    "timestamp": sub.nodes[n].get("timestamp", ""),
                    "source": sub.nodes[n].get("source", ""),
                }
                for n in sub.nodes()
            ],
            "edges": [
                {
                    "source": u,
                    "target": v,
                    "weight": d.get("weight", 0.0),
                    "relation": d.get("relation", ""),
                }
                for u, v, d in sub.edges(data=True)
            ],
        }
