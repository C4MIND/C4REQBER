"""
Tests for src/analogy/engine.py (backward-compatibility re-exports).
"""
from __future__ import annotations

from src.analogy.engine import (
    AnalogyEngine,
    AnalogyResult,
    ConceptNetBridge,
    SemanticEmbedder,
    Word2VecAnalogySolver,
    get_analogy_engine,
)


class TestEngineReExports:
    def test_analogy_engine_is_class(self):
        assert isinstance(AnalogyEngine, type)

    def test_analogy_result_is_dataclass(self):
        r = AnalogyResult(
            source_concept="a",
            target_concept="b",
            source_domain="x",
            target_domain="y",
            mapping_type="semantic",
            confidence=0.5,
        )
        assert r.source_concept == "a"

    def test_conceptnet_bridge_is_class(self):
        assert isinstance(ConceptNetBridge, type)

    def test_semantic_embedder_is_class(self):
        assert isinstance(SemanticEmbedder, type)

    def test_word2vec_solver_is_class(self):
        assert isinstance(Word2VecAnalogySolver, type)

    def test_get_analogy_engine_callable(self):
        assert callable(get_analogy_engine)

    def test_all_exports_present(self):
        from src.analogy import engine

        assert hasattr(engine, "AnalogyEngine")
        assert hasattr(engine, "get_analogy_engine")
        assert hasattr(engine, "AnalogyResult")
        assert hasattr(engine, "SemanticEmbedder")
        assert hasattr(engine, "Word2VecAnalogySolver")
        assert hasattr(engine, "ConceptNetBridge")
