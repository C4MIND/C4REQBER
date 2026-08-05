"""Suite 06 — Agenda questions must not invent novelty_score mid-range."""

from __future__ import annotations

import networkx as nx

from src.agenda.feasibility import FeasibilityResult
from src.agenda.generator import AgendaGenerator
from src.agenda.priority import PriorityScorer


def test_extension_and_conflict_novelty_null() -> None:
    gen = AgendaGenerator()
    recent = [
        {"hypothesis": {"text": "Hypothesis Alpha about cells"}},
        {"hypothesis": {"text": "Hypothesis Beta about genes"}},
    ]
    qs = gen.generate(nx.Graph(), recent, n_questions=5)
    assert qs
    for q in qs:
        assert q.novelty_score is None
        d = q.to_dict()
        assert d["novelty_score"] is None
        assert d["novelty_unchecked"] is True


def test_gap_driven_novelty_null() -> None:
    gen = AgendaGenerator()
    g = nx.Graph()
    g.add_nodes_from(["A", "B", "C", "D"])
    g.add_edge("A", "B")
    qs = gen.generate(g, [], n_questions=5)
    gap = [q for q in qs if q.strategy == "gap"]
    assert gap
    assert all(q.novelty_score is None for q in gap)


def test_priority_null_novelty_does_not_inflate() -> None:
    from src.agenda.generator import ResearchQuestion

    scorer = PriorityScorer()
    f = FeasibilityResult(True, 1.0, 10.0, 0.5)
    unchecked = ResearchQuestion("Q?", "gap", None, 0.7)
    invented = ResearchQuestion("Q?", "gap", 0.8, 0.7)
    assert scorer.score(unchecked, f) < scorer.score(invented, f)
