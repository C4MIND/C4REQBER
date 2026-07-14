"""
Tests for src/analogy/operations.py
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.analogy.operations import (
    ConceptNetBridge,
    SemanticEmbedder,
    Word2VecAnalogySolver,
)


class TestSemanticEmbedder:
    """Test SemanticEmbedder class."""

    @patch("src.analogy.operations.HAS_SENTENCE_TRANSFORMERS", False)
    @patch("src.analogy.operations.HAS_SKLEARN", False)
    def test_embed_with_fallback(self):
        embedder = SemanticEmbedder()
        embedding = embedder.embed("test text")
        assert isinstance(embedding, np.ndarray)
        assert len(embedding) > 0
        assert np.isclose(np.linalg.norm(embedding), 1.0) or np.linalg.norm(embedding) == 0

    @patch("src.analogy.operations.HAS_SENTENCE_TRANSFORMERS", False)
    @patch("src.analogy.operations.HAS_SKLEARN", False)
    def test_similarity_range(self):
        embedder = SemanticEmbedder()
        sim = embedder.similarity("hello world", "hello world")
        assert 0.0 <= sim <= 1.0

    @patch("src.analogy.operations.HAS_SENTENCE_TRANSFORMERS", False)
    @patch("src.analogy.operations.HAS_SKLEARN", False)
    def test_batch_embed(self):
        embedder = SemanticEmbedder()
        embeddings = embedder.batch_embed(["text one", "text two"])
        assert isinstance(embeddings, np.ndarray)
        assert len(embeddings) == 2

    @patch("src.analogy.operations.HAS_SENTENCE_TRANSFORMERS", False)
    @patch("src.analogy.operations.HAS_SKLEARN", False)
    def test_caching(self):
        embedder = SemanticEmbedder()
        e1 = embedder.embed("cached text")
        e2 = embedder.embed("cached text")
        assert np.array_equal(e1, e2)


class TestWord2VecAnalogySolver:
    """Test Word2VecAnalogySolver class."""

    def test_solve_with_no_model(self):
        solver = Word2VecAnalogySolver(model_path=None)
        solver.model = None
        result = solver.solve("king", "man", "woman")
        assert result == []

    def test_doesnt_match_with_no_model(self):
        solver = Word2VecAnalogySolver(model_path=None)
        solver.model = None
        result = solver.doesnt_match(["breakfast", "cereal", "dinner", "lunch"])
        assert result is None

    def test_similarity_with_no_model(self):
        solver = Word2VecAnalogySolver(model_path=None)
        solver.model = None
        result = solver.similarity("king", "queen")
        assert result == 0.0

    def test_solve_with_mock_model(self):
        solver = Word2VecAnalogySolver(model_path=None)
        mock_model = MagicMock()
        mock_model.most_similar.return_value = [
            ("queen", 0.75),
            ("princess", 0.60),
        ]
        solver.model = mock_model

        result = solver.solve("king", "man", "woman", topn=2)
        assert result == [("queen", 0.75), ("princess", 0.60)]
        mock_model.most_similar.assert_called_once_with(
            positive=["man", "woman"], negative=["king"], topn=2
        )

    def test_solve_keyerror_returns_empty(self):
        solver = Word2VecAnalogySolver(model_path=None)
        mock_model = MagicMock()
        mock_model.most_similar.side_effect = KeyError("word not found")
        solver.model = mock_model

        result = solver.solve("king", "man", "woman")
        assert result == []

    def test_solve_exception_returns_empty(self):
        solver = Word2VecAnalogySolver(model_path=None)
        mock_model = MagicMock()
        mock_model.most_similar.side_effect = RuntimeError("model error")
        solver.model = mock_model

        result = solver.solve("king", "man", "woman")
        assert result == []

    def test_doesnt_match_with_mock_model(self):
        solver = Word2VecAnalogySolver(model_path=None)
        mock_model = MagicMock()
        mock_model.doesnt_match.return_value = "cereal"
        solver.model = mock_model

        result = solver.doesnt_match(["breakfast", "cereal", "dinner", "lunch"])
        assert result == "cereal"

    def test_similarity_with_mock_model(self):
        solver = Word2VecAnalogySolver(model_path=None)
        mock_model = MagicMock()
        mock_model.similarity.return_value = 0.85
        solver.model = mock_model

        result = solver.similarity("king", "queen")
        assert result == 0.85


class TestConceptNetBridge:
    """Test ConceptNetBridge class."""

    @pytest.fixture
    def bridge(self):
        with patch("src.analogy.operations.get_knowledge_graph") as mock_kg:
            kg = MagicMock()
            kg.get_nodes_by_type.return_value = []
            kg.add_analogy.return_value = "analogy_id"
            mock_kg.return_value = kg

            bridge = ConceptNetBridge()
            bridge.knowledge_graph = kg
            yield bridge

    def test_get_domain_concepts(self, bridge):
        concepts = bridge.get_domain_concepts("biology")
        assert isinstance(concepts, list)
        assert "cell" in concepts
        assert "neuron" in concepts

    def test_get_domain_concepts_empty(self, bridge):
        concepts = bridge.get_domain_concepts("nonexistent_domain")
        assert concepts == []

    def test_find_conceptual_metaphors(self, bridge):
        results = bridge.find_conceptual_metaphors("biology", "computer_science")
        assert isinstance(results, list)
        assert ("neuron", "node") in results

    def test_find_conceptual_metaphors_reverse(self, bridge):
        results = bridge.find_conceptual_metaphors("computer_science", "biology")
        assert isinstance(results, list)

    def test_find_conceptual_metaphors_no_match(self, bridge):
        results = bridge.find_conceptual_metaphors("biology", "cooking")
        assert results == []

    def test_add_concept_new(self, bridge):
        result = bridge.add_concept("new_domain", "new_concept", auto_save=False)
        assert result is True
        assert "new_concept" in bridge.DOMAIN_CONCEPTS["new_domain"]

    def test_add_concept_duplicate(self, bridge):
        bridge.add_concept("biology", "cell", auto_save=False)
        result = bridge.add_concept("biology", "cell", auto_save=False)
        assert result is False

    def test_add_conceptual_metaphor_new(self, bridge):
        result = bridge.add_conceptual_metaphor(
            "domain_a", "concept_a", "domain_b", "concept_b", auto_save=False
        )
        assert result is True
        assert ("domain_a", "concept_a", "domain_b", "concept_b") in bridge.CONCEPTUAL_METAPHORS

    def test_add_conceptual_metaphor_duplicate(self, bridge):
        bridge.add_conceptual_metaphor(
            "domain_a", "concept_a", "domain_b", "concept_b", auto_save=False
        )
        result = bridge.add_conceptual_metaphor(
            "domain_a", "concept_a", "domain_b", "concept_b", auto_save=False
        )
        assert result is False

    def test_list_domains(self, bridge):
        domains = bridge.list_domains()
        assert isinstance(domains, list)
        assert "biology" in domains
        assert "physics" in domains

    def test_get_concept_stats(self, bridge):
        stats = bridge.get_concept_stats()
        assert isinstance(stats, dict)
        assert "biology" in stats
        assert stats["biology"] > 0

    def test_extract_concepts_from_text(self, bridge):
        with patch("src.analogy.utils.extract_concepts_from_text") as mock_extract:
            mock_extract.return_value = {"neural", "network", "learning"}
            result = bridge.extract_concepts_from_text(
                "Neural network learning", "computer_science"
            )
            assert isinstance(result, list)

    def test_auto_extract_from_hypothesis(self, bridge):
        with patch.object(bridge, "extract_concepts_from_text") as mock_extract:
            mock_extract.return_value = ["neuron", "network"]
            result = bridge.auto_extract_from_hypothesis(
                "Neural networks process information", "biology"
            )
            assert "concepts" in result
            assert "potential_analogies" in result
            assert result["concepts"] == ["neuron", "network"]

    def test_load_conceptual_metaphors_on_init(self):
        with patch("src.analogy.operations.get_knowledge_graph") as mock_kg:
            kg = MagicMock()
            kg.get_nodes_by_type.return_value = []
            kg.add_analogy.return_value = "analogy_id"
            mock_kg.return_value = kg

            bridge = ConceptNetBridge()
            kg.add_analogy.assert_called()

    def test_metaphor_exists_true(self, bridge):
        result = bridge._metaphor_exists("biology", "neuron", "computer_science", "node")
        assert result is True

    def test_metaphor_exists_false(self, bridge):
        result = bridge._metaphor_exists("biology", "cell", "cooking", "soup")
        assert result is False

    def test_save_concept_to_graph(self, bridge):
        bridge.knowledge_graph.has_node.return_value = False
        bridge._save_concept_to_graph("test_domain", "test_concept")
        bridge.knowledge_graph.graph.add_node.assert_called()
        bridge.knowledge_graph.add_edge.assert_called()
        bridge.knowledge_graph.save.assert_called_once()


class TestStructuralMapping:
    """Test structural mapping behavior via ConceptNetBridge."""

    @pytest.fixture
    def bridge(self):
        with patch("src.analogy.operations.get_knowledge_graph") as mock_kg:
            kg = MagicMock()
            kg.get_nodes_by_type.return_value = []
            mock_kg.return_value = kg
            yield ConceptNetBridge()

    def test_basic_mapping(self, bridge):
        mapping = bridge.find_conceptual_metaphors("biology", "computer_science")
        assert isinstance(mapping, list)
        assert len(mapping) > 0
        for item in mapping:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_empty_inputs(self, bridge):
        mapping = bridge.find_conceptual_metaphors("", "")
        assert mapping == []


class TestEvaluateSimilarity:
    """Test similarity evaluation via SemanticEmbedder."""

    @patch("src.analogy.operations.HAS_SENTENCE_TRANSFORMERS", False)
    @patch("src.analogy.operations.HAS_SKLEARN", False)
    def test_score_range(self):
        embedder = SemanticEmbedder()
        score = embedder.similarity("hello world", "hello world")
        assert 0.0 <= score <= 1.0

    @patch("src.analogy.operations.HAS_SENTENCE_TRANSFORMERS", False)
    @patch("src.analogy.operations.HAS_SKLEARN", False)
    def test_different_texts(self):
        embedder = SemanticEmbedder()
        score = embedder.similarity("hello world", "goodbye moon")
        assert 0.0 <= score <= 1.0

    @patch("src.analogy.operations.HAS_SENTENCE_TRANSFORMERS", False)
    @patch("src.analogy.operations.HAS_SKLEARN", False)
    def test_empty_mapping(self):
        embedder = SemanticEmbedder()
        score = embedder.similarity("", "")
        assert 0.0 <= score <= 1.0


class TestTransferSolution:
    """Test transfer_solution behavior via ConceptNetBridge."""

    @pytest.fixture
    def bridge(self):
        with patch("src.analogy.operations.get_knowledge_graph") as mock_kg:
            kg = MagicMock()
            kg.get_nodes_by_type.return_value = []
            mock_kg.return_value = kg
            yield ConceptNetBridge()

    def test_basic_transfer(self, bridge):
        mapping = bridge.find_conceptual_metaphors("biology", "computer_science")
        assert isinstance(mapping, list)
        if mapping:
            source, target = mapping[0]
            assert isinstance(source, str)
            assert isinstance(target, str)

    def test_invalid_analogy_empty_domains(self, bridge):
        mapping = bridge.find_conceptual_metaphors("nonexistent", "also_nonexistent")
        assert mapping == []


class TestValidateAnalogy:
    """Test validate_analogy behavior via ConceptNetBridge."""

    @pytest.fixture
    def bridge(self):
        with patch("src.analogy.operations.get_knowledge_graph") as mock_kg:
            kg = MagicMock()
            kg.get_nodes_by_type.return_value = []
            mock_kg.return_value = kg
            yield ConceptNetBridge()

    def test_valid_metaphor(self, bridge):
        exists = bridge._metaphor_exists("biology", "neuron", "computer_science", "node")
        assert exists is True

    def test_invalid_metaphor(self, bridge):
        exists = bridge._metaphor_exists("biology", "neuron", "cooking", "spoon")
        assert exists is False

    def test_valid_concept_in_domain(self, bridge):
        concepts = bridge.get_domain_concepts("biology")
        assert "cell" in concepts

    def test_invalid_concept_in_domain(self, bridge):
        concepts = bridge.get_domain_concepts("biology")
        assert "quark" not in concepts

    def test_add_concept_validates(self, bridge):
        result = bridge.add_concept("test_domain", "test_concept", auto_save=False)
        assert result is True
        result2 = bridge.add_concept("test_domain", "test_concept", auto_save=False)
        assert result2 is False
