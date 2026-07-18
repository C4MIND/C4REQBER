"""
c4reqber: Agenda Generator

Generates research questions from knowledge graph and open gaps.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import networkx as nx
import numpy as np


logger = logging.getLogger("c4reqber.agenda")


@dataclass
class ResearchQuestion:
    """A generated research question."""

    text: str
    strategy: str  # 'gap', 'conflict', 'extension', 'surprise'
    novelty_score: float
    impact_potential: float
    user_alignment: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "strategy": self.strategy,
            "novelty_score": round(self.novelty_score, 3),
            "impact_potential": round(self.impact_potential, 3),
            "user_alignment": round(self.user_alignment, 3),
            "heuristic": True,
            "note": "novelty/impact scores are fixed heuristics, not model estimates",
        }


class AgendaGenerator:
    """Generate research questions from knowledge state."""

    def generate(
        self,
        knowledge_graph: nx.Graph,
        recent_results: list[dict],
        n_questions: int = 5,
    ) -> list[ResearchQuestion]:
        """Generate research questions.

        Args:
            knowledge_graph: Graph of known concepts and relationships.
            recent_results: Recent discovery results.
            n_questions: Number of questions to generate.

        Returns:
            List of ResearchQuestion.
        """
        questions: list[ResearchQuestion] = []

        # Strategy 1: Gap-driven
        gap_questions = self._gap_driven(knowledge_graph)
        questions.extend(gap_questions)

        # Strategy 2: Extension-driven
        ext_questions = self._extension_driven(knowledge_graph, recent_results)
        questions.extend(ext_questions)

        # Strategy 3: Conflict-driven
        conflict_questions = self._conflict_driven(recent_results)
        questions.extend(conflict_questions)

        # Sort by composite score and return top N
        questions.sort(
            key=lambda q: q.novelty_score * 0.4 + q.impact_potential * 0.4 + q.user_alignment * 0.2,
            reverse=True,
        )
        return questions[:n_questions]

    def _gap_driven(self, graph: nx.Graph) -> list[ResearchQuestion]:
        """Find disconnected components and ask about their relationships."""
        questions: list[ResearchQuestion] = []
        if graph.number_of_nodes() < 4:
            return questions

        nodes = list(graph.nodes)
        rng = np.random.default_rng(42)
        # Sample pairs with no edge
        for _ in range(20):
            i, j = rng.choice(len(nodes), 2, replace=False)
            n1, n2 = nodes[i], nodes[j]
            if not graph.has_edge(n1, n2):
                questions.append(
                    ResearchQuestion(
                        text=f"What is the relationship between {n1} and {n2}?",
                        strategy="gap",
                        novelty_score=0.7,
                        impact_potential=0.6,
                    )
                )
        return questions

    def _extension_driven(
        self,
        graph: nx.Graph,
        recent_results: list[dict],
    ) -> list[ResearchQuestion]:
        """Extend recent findings to new domains or conditions."""
        questions = []
        for result in recent_results[:3]:
            hyp = result.get("hypothesis", {}).get("text", "")
            if not hyp:
                continue
            questions.append(
                ResearchQuestion(
                    text=f"Does the finding '{hyp[:80]}...' generalize to other populations or contexts?",
                    strategy="extension",
                    novelty_score=0.5,
                    impact_potential=0.7,
                )
            )
        return questions

    def _conflict_driven(self, recent_results: list[dict]) -> list[ResearchQuestion]:
        """Find contradictions and propose resolutions."""
        questions = []
        # Simple heuristic: if multiple hypotheses exist, ask about reconciliation
        hypotheses = [
            r.get("hypothesis", {}).get("text", "") for r in recent_results if r.get("hypothesis")
        ]
        if len(hypotheses) >= 2:
            questions.append(
                ResearchQuestion(
                    text=f"How can we reconcile the hypotheses: '{hypotheses[0][:60]}...' and '{hypotheses[1][:60]}...'?",
                    strategy="conflict",
                    novelty_score=0.8,
                    impact_potential=0.7,
                )
            )
        return questions
