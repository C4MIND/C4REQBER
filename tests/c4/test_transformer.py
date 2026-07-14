"""
Comprehensive tests for src/c4/transformer.py

Covers: DomainTransformer initialization, fingerprinting, isomorphism search,
        FRA adaptation, memory storage/retrieval, and edge cases.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from c4.engine import C4Space, C4State
from c4.transformer import (
    DomainFingerprint,
    DomainTransformer,
    IsomorphismResult,
    IsomorphismType,
    StructuralMemoryEntry,
)


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_c4_space():
    """Return a mocked C4Space with configurable shortest_path."""
    space = MagicMock(spec=C4Space)
    path_mock = MagicMock()
    path_mock.operators = ["tau+", "lambda+"]
    space.shortest_path.return_value = path_mock
    return space


@pytest.fixture
def transformer_default():
    """DomainTransformer with default (real) C4Space."""
    return DomainTransformer()


@pytest.fixture
def transformer_mocked(mock_c4_space):
    """DomainTransformer with mocked C4Space."""
    return DomainTransformer(c4_space=mock_c4_space)


@pytest.fixture
def sample_fingerprint():
    """A sample domain fingerprint for testing."""
    return DomainFingerprint(
        domain="physics",
        entities=["particle", "field", "energy"],
        relations=[("particle", "interacts_with", "field"), ("field", "generates", "energy")],
        constraints=["conservation_of_energy", "gauge_invariance"],
    )


@pytest.fixture
def similar_fingerprint():
    """A fingerprint structurally similar to sample_fingerprint."""
    return DomainFingerprint(
        domain="economics",
        entities=["particle", "market", "energy"],
        relations=[("particle", "interacts_with", "market"), ("market", "generates", "energy")],
        constraints=["conservation_of_energy", "equilibrium"],
    )


@pytest.fixture
def different_fingerprint():
    """A fingerprint with no overlap to sample_fingerprint."""
    return DomainFingerprint(
        domain="biology",
        entities=["cell", "organism", "ecosystem"],
        relations=[("cell", "part_of", "organism")],
        constraints=["homeostasis"],
    )


@pytest.fixture
def sample_state():
    """A sample C4State."""
    return C4State(T=0, S=0, A=0)


@pytest.fixture
def target_state():
    """Another sample C4State."""
    return C4State(T=1, S=1, A=1)


@pytest.fixture
def sample_isomorphism_result(sample_state, target_state):
    """A sample IsomorphismResult."""
    return IsomorphismResult(
        source_domain="physics",
        target_domain="economics",
        source_state=sample_state,
        target_state=target_state,
        mapping={"particle": "market", "field": "economy"},
        confidence=0.85,
        isomorphism_type=IsomorphismType.PARTIAL,
        path=["tau+", "lambda+"],
        description="Test isomorphism",
    )


# ═══════════════════════════════════════════════════════════════════
# __init__
# ═══════════════════════════════════════════════════════════════════


class TestInit:
    def test_default_c4_space(self, transformer_default):
        """When no c4_space is provided, a fresh C4Space is created."""
        assert transformer_default.c4_space is not None
        assert isinstance(transformer_default.c4_space, C4Space)

    def test_custom_c4_space(self, mock_c4_space):
        """When a custom c4_space is provided, it is stored as-is."""
        transformer = DomainTransformer(c4_space=mock_c4_space)
        assert transformer.c4_space is mock_c4_space

    def test_empty_memory_on_init(self, transformer_default):
        """Structural memory should be empty on instantiation."""
        assert transformer_default._structural_memory == []


# ═══════════════════════════════════════════════════════════════════
# fingerprint
# ═══════════════════════════════════════════════════════════════════


class TestFingerprint:
    def test_basic_call(self, transformer_default):
        """fingerprint should return a DomainFingerprint with correct fields."""
        fp = transformer_default.fingerprint(
            domain="test_domain",
            entities=["a", "b"],
            relations=[("a", "rel", "b")],
            constraints=["c1"],
        )
        assert isinstance(fp, DomainFingerprint)
        assert fp.domain == "test_domain"
        assert fp.entities == ["a", "b"]
        assert fp.relations == [("a", "rel", "b")]
        assert fp.constraints == ["c1"]
        assert fp.c4_state is None

    def test_empty_entities(self, transformer_default):
        """fingerprint should handle empty entities gracefully."""
        fp = transformer_default.fingerprint(
            domain="empty",
            entities=[],
            relations=[],
            constraints=[],
        )
        assert fp.entities == []
        assert fp.relations == []
        assert fp.constraints == []
        assert fp.spectral_hash != ""

    def test_with_relations_and_constraints(self, transformer_default):
        """fingerprint should preserve relations and constraints."""
        relations = [
            ("entity1", "depends_on", "entity2"),
            ("entity2", "implements", "entity3"),
        ]
        constraints = ["limit1", "limit2", "limit3"]
        fp = transformer_default.fingerprint(
            domain="complex",
            entities=["entity1", "entity2", "entity3"],
            relations=relations,
            constraints=constraints,
        )
        assert fp.relations == relations
        assert fp.constraints == constraints

    def test_with_c4_state(self, transformer_default, sample_state):
        """fingerprint should accept and store an optional C4State."""
        fp = transformer_default.fingerprint(
            domain="with_state",
            entities=["x"],
            relations=[],
            constraints=[],
            c4_state=sample_state,
        )
        assert fp.c4_state == sample_state

    def test_spectral_hash_computed(self, transformer_default):
        """spectral_hash should be auto-computed in __post_init__."""
        fp = transformer_default.fingerprint(
            domain="hash_test",
            entities=["a", "b"],
            relations=[("a", "r", "b")],
            constraints=["c"],
        )
        assert len(fp.spectral_hash) == 16
        assert fp.spectral_hash == fp.compute_hash()


# ═══════════════════════════════════════════════════════════════════
# find_isomorphism
# ═══════════════════════════════════════════════════════════════════


class TestFindIsomorphism:
    def test_same_domain_high_confidence(self, transformer_default, sample_fingerprint):
        """Identical fingerprints in the same domain should yield high confidence."""
        candidates = [sample_fingerprint]
        result = transformer_default.find_isomorphism(
            source=sample_fingerprint,
            target_domain="physics",
            candidates=candidates,
        )
        assert result.confidence > 0.9
        assert result.isomorphism_type == IsomorphismType.VERIFIED
        assert result.mapping == {"particle": "particle", "field": "field", "energy": "energy"}

    def test_different_domains_partial_match(self, transformer_default, sample_fingerprint, similar_fingerprint):
        """Similar fingerprints across domains yield PARTIAL match."""
        candidates = [similar_fingerprint]
        result = transformer_default.find_isomorphism(
            source=sample_fingerprint,
            target_domain="economics",
            candidates=candidates,
        )
        assert result.confidence > 0.0
        assert result.confidence <= 1.0
        assert result.isomorphism_type in (IsomorphismType.PARTIAL, IsomorphismType.VERIFIED)
        assert result.mapping == {"particle": "particle", "energy": "energy"}

    def test_no_match(self, transformer_default, sample_fingerprint, different_fingerprint):
        """When no candidate matches the target domain, result should be FAILED."""
        candidates = [different_fingerprint]
        result = transformer_default.find_isomorphism(
            source=sample_fingerprint,
            target_domain="nonexistent",
            candidates=candidates,
        )
        assert result.confidence == 0.0
        assert result.isomorphism_type == IsomorphismType.FAILED
        assert result.mapping == {}

    def test_no_candidates(self, transformer_default, sample_fingerprint):
        """Empty candidates list should return FAILED result."""
        result = transformer_default.find_isomorphism(
            source=sample_fingerprint,
            target_domain="any",
            candidates=[],
        )
        assert result.confidence == 0.0
        assert result.isomorphism_type == IsomorphismType.FAILED

    def test_multiple_candidates_best_selected(self, transformer_default, sample_fingerprint, similar_fingerprint, different_fingerprint):
        """When multiple candidates match target_domain, the best-scoring one wins."""
        similar_fingerprint.domain = "physics"  # Make it match target_domain
        different_fingerprint.domain = "physics"
        candidates = [different_fingerprint, similar_fingerprint]
        result = transformer_default.find_isomorphism(
            source=sample_fingerprint,
            target_domain="physics",
            candidates=candidates,
        )
        assert result.confidence > 0.0
        # similar_fingerprint should win over different_fingerprint
        assert result.mapping == {"particle": "particle", "energy": "energy"}

    def test_candidates_filtered_by_domain(self, transformer_default, sample_fingerprint, similar_fingerprint, different_fingerprint):
        """Candidates with non-matching domains should be ignored."""
        similar_fingerprint.domain = "other"
        different_fingerprint.domain = "other"
        candidates = [similar_fingerprint, different_fingerprint]
        result = transformer_default.find_isomorphism(
            source=sample_fingerprint,
            target_domain="physics",
            candidates=candidates,
        )
        assert result.confidence == 0.0
        assert result.isomorphism_type == IsomorphismType.FAILED


# ═══════════════════════════════════════════════════════════════════
# fra_adapt
# ═══════════════════════════════════════════════════════════════════


class TestFraAdapt:
    def test_basic_adaptation(self, transformer_mocked, sample_fingerprint, sample_isomorphism_result):
        """fra_adapt should return a dict with fingerprint, route, mapping, and rules."""
        result = transformer_mocked.fra_adapt(
            source=sample_fingerprint,
            analog=sample_isomorphism_result,
        )
        assert result["fingerprint"] == sample_fingerprint.spectral_hash
        assert result["route"] == sample_isomorphism_result.path
        assert result["mapping"] == sample_isomorphism_result.mapping
        assert result["confidence"] == sample_isomorphism_result.confidence
        assert isinstance(result["adaptation_rules"], list)
        assert len(result["adaptation_rules"]) > 0

    def test_adaptation_rules_content(self, transformer_mocked, sample_fingerprint, sample_isomorphism_result):
        """Adaptation rules should include entity mappings."""
        result = transformer_mocked.fra_adapt(
            source=sample_fingerprint,
            analog=sample_isomorphism_result,
        )
        rules = result["adaptation_rules"]
        assert any("particle" in rule for rule in rules)
        assert any("market" in rule for rule in rules)

    def test_same_state_no_path(self, transformer_default, sample_fingerprint):
        """When source and analog share the same state, path may be empty."""
        same_state = C4State(T=0, S=0, A=0)
        analog = IsomorphismResult(
            source_domain="physics",
            target_domain="physics",
            source_state=same_state,
            target_state=same_state,
            mapping={},
            confidence=1.0,
            isomorphism_type=IsomorphismType.VERIFIED,
            path=[],
            description="Same state",
        )
        result = transformer_default.fra_adapt(
            source=sample_fingerprint,
            analog=analog,
        )
        assert result["route"] == []
        assert result["confidence"] == 1.0


# ═══════════════════════════════════════════════════════════════════
# store_memory + search_memory
# ═══════════════════════════════════════════════════════════════════


class TestMemory:
    def test_store_and_search_roundtrip(self, transformer_default, sample_fingerprint, sample_isomorphism_result):
        """Storing an entry and searching should retrieve it."""
        entry = StructuralMemoryEntry(
            id="entry_1",
            source_fingerprint=sample_fingerprint,
            target_fingerprint=None,
            result=sample_isomorphism_result,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        transformer_default.store_memory(entry)
        results = transformer_default.search_memory(sample_fingerprint)
        assert len(results) == 1
        assert results[0].id == "entry_1"

    def test_multiple_entries(self, transformer_default, sample_fingerprint, similar_fingerprint, sample_isomorphism_result):
        """Multiple entries should all be searchable."""
        entry1 = StructuralMemoryEntry(
            id="e1",
            source_fingerprint=sample_fingerprint,
            target_fingerprint=None,
            result=sample_isomorphism_result,
        )
        entry2 = StructuralMemoryEntry(
            id="e2",
            source_fingerprint=similar_fingerprint,
            target_fingerprint=None,
            result=sample_isomorphism_result,
        )
        transformer_default.store_memory(entry1)
        transformer_default.store_memory(entry2)
        results = transformer_default.search_memory(sample_fingerprint)
        assert len(results) == 2

    def test_search_sorted_by_confidence(self, transformer_default, sample_fingerprint, similar_fingerprint):
        """search_memory should sort results by result.confidence descending."""
        high_conf = IsomorphismResult(
            source_domain="a",
            target_domain="b",
            source_state=None,
            target_state=None,
            confidence=0.95,
            isomorphism_type=IsomorphismType.VERIFIED,
        )
        low_conf = IsomorphismResult(
            source_domain="a",
            target_domain="b",
            source_state=None,
            target_state=None,
            confidence=0.3,
            isomorphism_type=IsomorphismType.PARTIAL,
        )
        entry1 = StructuralMemoryEntry(
            id="high",
            source_fingerprint=sample_fingerprint,
            target_fingerprint=None,
            result=high_conf,
        )
        entry2 = StructuralMemoryEntry(
            id="low",
            source_fingerprint=similar_fingerprint,
            target_fingerprint=None,
            result=low_conf,
        )
        transformer_default.store_memory(entry1)
        transformer_default.store_memory(entry2)
        results = transformer_default.search_memory(sample_fingerprint)
        assert results[0].result.confidence >= results[1].result.confidence

    def test_search_min_confidence_filter(self, transformer_default, sample_fingerprint):
        """search_memory with min_confidence should filter low-similarity entries."""
        # Use a fingerprint with zero overlap to sample_fingerprint
        no_overlap_fp = DomainFingerprint(
            domain="biology",
            entities=["cell", "organism", "ecosystem"],
            relations=[("cell", "part_of", "organism")],
            constraints=["homeostasis"],
        )
        low_conf = IsomorphismResult(
            source_domain="a",
            target_domain="b",
            source_state=None,
            target_state=None,
            confidence=0.1,
            isomorphism_type=IsomorphismType.FAILED,
        )
        entry = StructuralMemoryEntry(
            id="low",
            source_fingerprint=no_overlap_fp,
            target_fingerprint=None,
            result=low_conf,
        )
        transformer_default.store_memory(entry)
        results = transformer_default.search_memory(sample_fingerprint, min_confidence=0.5)
        assert len(results) == 0

    def test_search_empty_memory(self, transformer_default, sample_fingerprint):
        """Searching empty memory should return empty list."""
        results = transformer_default.search_memory(sample_fingerprint)
        assert results == []


# ═══════════════════════════════════════════════════════════════════
# Edge cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_fingerprint_none_entities(self, transformer_default):
        """fingerprint should not accept None for entities (type hint says list[str])."""
        with pytest.raises(TypeError):
            transformer_default.fingerprint(
                domain="test",
                entities=None,  # type: ignore[arg-type]
                relations=[],
                constraints=[],
            )

    def test_fingerprint_empty_strings(self, transformer_default):
        """fingerprint should handle empty strings in fields."""
        fp = transformer_default.fingerprint(
            domain="",
            entities=[""],
            relations=[("", "", "")],
            constraints=[""],
        )
        assert fp.domain == ""
        assert fp.entities == [""]
        assert fp.spectral_hash != ""

    def test_find_isomorphism_empty_entities(self, transformer_default):
        """find_isomorphism with empty entities should return FAILED."""
        empty_fp = DomainFingerprint(domain="empty", entities=[], relations=[], constraints=[])
        result = transformer_default.find_isomorphism(
            source=empty_fp,
            target_domain="empty",
            candidates=[empty_fp],
        )
        assert result.confidence == 0.0
        assert result.isomorphism_type == IsomorphismType.FAILED

    def test_structural_similarity_empty_both(self, transformer_default):
        """_structural_similarity with empty fingerprints returns zero score."""
        fp_a = DomainFingerprint(domain="a", entities=[], relations=[], constraints=[])
        fp_b = DomainFingerprint(domain="b", entities=[], relations=[], constraints=[])
        score, mapping = transformer_default._structural_similarity(fp_a, fp_b)
        assert score == 0.0
        assert mapping == {}

    def test_spectral_embedding_no_numpy(self, transformer_default, sample_fingerprint):
        """_spectral_embedding returns None when numpy is unavailable or entities < 2."""
        with patch("c4.transformer._HAS_NUMPY", False):
            emb = transformer_default._spectral_embedding(sample_fingerprint)
            assert emb is None

    def test_spectral_embedding_single_entity(self, transformer_default):
        """_spectral_embedding returns None for single-entity fingerprints."""
        fp = DomainFingerprint(domain="single", entities=["only_one"], relations=[], constraints=[])
        emb = transformer_default._spectral_embedding(fp)
        assert emb is None

    def test_spectral_similarity_none_embedding(self, transformer_default, sample_fingerprint):
        """_spectral_similarity returns 0.0 when either embedding is None."""
        fp = DomainFingerprint(domain="other", entities=["x"], relations=[], constraints=[])
        score = transformer_default._spectral_similarity(sample_fingerprint, fp)
        assert score == 0.0

    def test_store_memory_none_entry(self, transformer_default):
        """store_memory appends None to memory list without error (list.append allows None)."""
        transformer_default.store_memory(None)  # type: ignore[arg-type]
        assert transformer_default._structural_memory == [None]

    def test_search_memory_none_fingerprint(self, transformer_default):
        """search_memory with None fingerprint returns empty list when memory is empty."""
        results = transformer_default.search_memory(None)  # type: ignore[arg-type]
        assert results == []
        # After storing an entry, None fingerprint should raise AttributeError
        entry = StructuralMemoryEntry(
            id="e1",
            source_fingerprint=DomainFingerprint(domain="d", entities=["a"], relations=[], constraints=[]),
            target_fingerprint=None,
            result=IsomorphismResult(
                source_domain="a", target_domain="b", source_state=None, target_state=None,
                confidence=0.5, isomorphism_type=IsomorphismType.PARTIAL,
            ),
        )
        transformer_default.store_memory(entry)
        with pytest.raises(AttributeError):
            transformer_default.search_memory(None)  # type: ignore[arg-type]

    def test_fra_adapt_none_source(self, transformer_mocked, sample_isomorphism_result):
        """fra_adapt with None source should raise AttributeError."""
        with pytest.raises(AttributeError):
            transformer_mocked.fra_adapt(
                source=None,  # type: ignore[arg-type]
                analog=sample_isomorphism_result,
            )

    def test_fra_adapt_none_analog(self, transformer_mocked, sample_fingerprint):
        """fra_adapt with None analog should raise AttributeError."""
        with pytest.raises(AttributeError):
            transformer_mocked.fra_adapt(
                source=sample_fingerprint,
                analog=None,  # type: ignore[arg-type]
            )


# ═══════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════


class TestInternalHelpers:
    def test_infer_c4_path_with_states(self, transformer_mocked, sample_state, target_state):
        """_infer_c4_path should delegate to c4_space.shortest_path."""
        path = transformer_mocked._infer_c4_path(sample_state, target_state)
        transformer_mocked.c4_space.shortest_path.assert_called_once_with(
            sample_state, target_state
        )
        assert path == ["tau+", "lambda+"]

    def test_infer_c4_path_none_start(self, transformer_mocked):
        """_infer_c4_path returns [] when start is None."""
        path = transformer_mocked._infer_c4_path(None, C4State(T=1, S=1, A=1))
        assert path == []

    def test_infer_c4_path_none_end(self, transformer_mocked):
        """_infer_c4_path returns [] when end is None."""
        path = transformer_mocked._infer_c4_path(C4State(T=0, S=0, A=0), None)
        assert path == []

    def test_generate_adaptation_rules(self, transformer_mocked, sample_fingerprint, sample_isomorphism_result):
        """_generate_adaptation_rules should create mapping rules."""
        rules = transformer_mocked._generate_adaptation_rules(
            sample_fingerprint, sample_isomorphism_result
        )
        assert any("particle" in r and "market" in r for r in rules)

    def test_generate_adaptation_rules_no_states(self, transformer_default, sample_fingerprint):
        """_generate_adaptation_rules without c4_states should skip C4 transformation rule."""
        analog = IsomorphismResult(
            source_domain="a",
            target_domain="b",
            source_state=None,
            target_state=None,
            mapping={"x": "y"},
            confidence=0.5,
            isomorphism_type=IsomorphismType.PARTIAL,
        )
        rules = transformer_default._generate_adaptation_rules(sample_fingerprint, analog)
        assert all("C4 transformation" not in r for r in rules)
        assert any("x" in r and "y" in r for r in rules)

    def test_domain_fingerprint_compute_hash_deterministic(self):
        """compute_hash should be deterministic for identical fingerprints."""
        fp1 = DomainFingerprint(
            domain="d", entities=["a", "b"], relations=[("a", "r", "b")], constraints=["c"]
        )
        fp2 = DomainFingerprint(
            domain="d", entities=["a", "b"], relations=[("a", "r", "b")], constraints=["c"]
        )
        assert fp1.compute_hash() == fp2.compute_hash()

    def test_domain_fingerprint_compute_hash_order_invariant(self):
        """compute_hash should be invariant to entity/relation/constraint order."""
        fp1 = DomainFingerprint(
            domain="d",
            entities=["b", "a"],
            relations=[("a", "r", "b")],
            constraints=["c2", "c1"],
        )
        fp2 = DomainFingerprint(
            domain="d",
            entities=["a", "b"],
            relations=[("a", "r", "b")],
            constraints=["c1", "c2"],
        )
        assert fp1.compute_hash() == fp2.compute_hash()
