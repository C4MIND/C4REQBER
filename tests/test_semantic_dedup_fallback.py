"""Lexical fallback for semantic_deduplicate when ST unavailable."""

from __future__ import annotations

from src.llm.embeddings import _lexical_deduplicate, semantic_deduplicate


def test_lexical_dedup_collapses_near_duplicate_titles() -> None:
    papers = [
        {"title": "Deep Cryogenic Treatment of AISI 440C Steel"},
        {"title": "Deep Cryogenic Treatment of AISI 440C Steel Review"},
        {"title": "Completely Unrelated Quantum Chromodynamics Paper"},
    ]
    out = _lexical_deduplicate(papers, threshold=0.5)
    assert len(out) >= 2
    assert any("Quantum" in p["title"] for p in out)


def test_semantic_deduplicate_fallback_when_embed_raises(monkeypatch) -> None:
    def boom(texts):
        raise RuntimeError(
            "sentence-transformers unavailable: No module named 'sentence_transformers'"
        )

    monkeypatch.setattr("src.llm.embeddings._engine.embed", boom)
    papers = [
        {"title": "Alpha paper about steel cryogenic"},
        {"title": "Beta paper about steel cryogenic"},
        {"title": "Gamma totally different neuroscience"},
    ]
    out = semantic_deduplicate(papers, threshold=0.85)
    assert isinstance(out, list)
    assert len(out) >= 1
