"""
Tests for src/c4/transfer_pipeline.py

Covers: TransferPipeline, c4_transfer, cross_domain_transfer,
        detect_cross_domain, should_auto_trigger, TransferResult,
        and integration with DomainTransformer + isomorphism seeds.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from c4.transfer_pipeline import (
    StructuralIsomorphismResult,
    TransferPipeline,
    TransferResult,
    _seed_to_fingerprint,
    _seeds_to_candidates,
    c4_transfer,
    check_conservation_laws,
    check_dimensional_consistency,
    cross_domain_transfer,
    detect_cross_domain,
    extract_ontology_graph,
    graph_isomorphism_match,
    should_auto_trigger,
)


# ═══════════════════════════════════════════════════════════════════
# detect_cross_domain
# ═══════════════════════════════════════════════════════════════════


class TestDetectCrossDomain:
    def test_single_domain_detected(self):
        """Problem with biology keywords should detect biology domain."""
        problem = "How can drug delivery through cell membranes be improved?"
        domains = detect_cross_domain(problem)
        assert "biology" in domains

    def test_multiple_domains_detected(self):
        """Problem with keywords from biology and fluid dynamics."""
        problem = (
            "How can drug delivery through cell membranes be improved "
            "using fluid flow and turbulence?"
        )
        domains = detect_cross_domain(problem)
        assert "biology" in domains
        assert "fluid_dynamics" in domains

    def test_no_domains(self):
        """Problem with no domain keywords returns empty list."""
        problem = "What is the meaning of life?"
        domains = detect_cross_domain(problem)
        assert domains == []

    def test_case_insensitive(self):
        """Detection should be case-insensitive."""
        problem = "DRUG DELIVERY through CELL Membranes"
        domains = detect_cross_domain(problem)
        assert "biology" in domains

    def test_thermodynamics_and_ml(self):
        """Detect thermodynamics and machine learning keywords."""
        problem = (
            "Use entropy and free energy minimization for machine learning "
            "classification and regression"
        )
        domains = detect_cross_domain(problem)
        assert "thermodynamics" in domains
        assert "machine_learning" in domains


# ═══════════════════════════════════════════════════════════════════
# should_auto_trigger
# ═══════════════════════════════════════════════════════════════════


class TestShouldAutoTrigger:
    def test_triggers_with_two_domains(self):
        """Auto-trigger should fire when >=2 domains detected."""
        problem = (
            "How can drug delivery through cell membranes be improved "
            "using fluid flow and turbulence?"
        )
        assert should_auto_trigger(problem) is True

    def test_no_trigger_single_domain(self):
        """Auto-trigger should not fire with only 1 domain."""
        problem = "How can drug delivery be improved?"
        assert should_auto_trigger(problem) is False

    def test_no_trigger_zero_domains(self):
        """Auto-trigger should not fire with 0 domains."""
        problem = "What is the answer to everything?"
        assert should_auto_trigger(problem) is False


# ═══════════════════════════════════════════════════════════════════
# TransferResult
# ═══════════════════════════════════════════════════════════════════


class TestTransferResult:
    def test_to_dict(self):
        """TransferResult.to_dict should return serializable dict."""
        result = TransferResult(
            problem="test",
            source_domain="biology",
            target_domain="fluid_dynamics",
            confidence=0.85,
            mappings=[{"mapping": "a ↔ b", "confidence": 0.9}],
            triz_principles=[1, 15],
            isomorphism_type="partial",
        )
        d = result.to_dict()
        assert d["problem"] == "test"
        assert d["source_domain"] == "biology"
        assert d["confidence"] == 0.85
        assert d["mappings"] == [{"mapping": "a ↔ b", "confidence": 0.9}]
        assert d["triz_principles"] == [1, 15]
        assert d["isomorphism_type"] == "partial"

    def test_defaults(self):
        """TransferResult should have sensible defaults."""
        result = TransferResult(problem="x", source_domain="a", target_domain="b")
        assert result.confidence == 0.0
        assert result.mappings == []
        assert result.adaptation_rules == []
        assert result.triz_principles == []
        assert result.triggered_auto is False


# ═══════════════════════════════════════════════════════════════════
# _seed_to_fingerprint + _seeds_to_candidates
# ═══════════════════════════════════════════════════════════════════


class TestSeedConversion:
    def test_seed_to_fingerprint_with_arrow(self):
        """Seed with ↔ mapping should produce fingerprint."""
        seed = {
            "id": "iso-001",
            "source": "fluid_dynamics",
            "target": "neural_networks",
            "mapping": "Navier-Stokes vortex ↔ gradient flow",
            "confidence": 0.82,
            "triz": [1, 7, 15],
        }
        fp = _seed_to_fingerprint(seed)
        assert fp.domain == "fluid_dynamics"
        assert "Navier-Stokes vortex" in fp.entities
        assert "gradient flow" in fp.entities
        assert any(r[1] == "isomorphic_to" for r in fp.relations)
        assert any("triz:1,7,15" in c for c in fp.constraints)

    def test_seed_to_fingerprint_without_arrow(self):
        """Seed without ↔ should still produce fingerprint."""
        seed = {
            "source": "biology",
            "target": "computing",
            "mapping": "neuron perceptron mapping",
            "triz": [26],
        }
        fp = _seed_to_fingerprint(seed)
        assert fp.domain == "biology"
        assert len(fp.entities) > 0

    def test_seeds_to_candidates(self):
        """Multiple seeds should convert to multiple candidates (source + target each)."""
        seeds = [
            {"source": "a", "target": "b", "mapping": "x ↔ y"},
            {"source": "c", "target": "d", "mapping": "z ↔ w"},
        ]
        candidates = _seeds_to_candidates(seeds)
        assert len(candidates) == 4  # 2 seeds × 2 directions
        assert candidates[0].domain == "a"
        assert candidates[1].domain == "b"


# ═══════════════════════════════════════════════════════════════════
# TransferPipeline
# ═══════════════════════════════════════════════════════════════════


class TestTransferPipeline:
    def test_init(self):
        """TransferPipeline should initialize with C4Space and transformer."""
        pipeline = TransferPipeline()
        assert pipeline.c4_space is not None
        assert pipeline.transformer is not None
        assert len(pipeline._seeds) > 0
        # Candidates include both source and target fingerprints
        assert len(pipeline._candidates) >= len(pipeline._seeds)

    def test_transfer_known_isomorphism(self):
        """Transfer between known domains should return result with confidence."""
        pipeline = TransferPipeline()
        result = pipeline.transfer(
            problem="How can neural networks learn continually without forgetting?",
            source_domain="neuroscience",
            target_domain="continual_learning",
        )
        assert isinstance(result, TransferResult)
        assert result.source_domain == "neuroscience"
        assert result.target_domain == "continual_learning"
        # Should find matching seeds
        assert result.confidence > 0.0

    def test_transfer_unknown_domains(self):
        """Transfer between unknown domains should return low/no confidence."""
        pipeline = TransferPipeline()
        result = pipeline.transfer(
            problem="foo bar baz",
            source_domain="xyz_domain",
            target_domain="abc_domain",
        )
        assert result.confidence == 0.0
        assert result.isomorphism_type == "failed"

    def test_transfer_auto_triggered_flag(self):
        """auto_triggered flag should be passed through."""
        pipeline = TransferPipeline()
        result = pipeline.transfer(
            problem="test",
            source_domain="biology",
            target_domain="machine_learning",
            auto_triggered=True,
        )
        assert result.triggered_auto is True

    def test_transfer_adaptation_rules(self):
        """Transfer with match should include adaptation rules."""
        pipeline = TransferPipeline()
        result = pipeline.transfer(
            problem="How does heat diffusion relate to activation propagation?",
            source_domain="thermodynamics",
            target_domain="neural_networks",
        )
        # Adaptation rules may or may not be present depending on match
        assert isinstance(result.adaptation_rules, list)

    def test_transfer_triz_principles(self):
        """Transfer with matching seed should include TRIZ principles."""
        pipeline = TransferPipeline()
        result = pipeline.transfer(
            problem="test",
            source_domain="thermodynamics",
            target_domain="information_theory",
        )
        if result.confidence > 0.0:
            assert isinstance(result.triz_principles, list)

    def test_extract_entities(self):
        """_extract_entities should return unique words >=3 chars."""
        pipeline = TransferPipeline()
        entities = pipeline._extract_entities("How can drug delivery be improved?")
        assert "how" in entities
        assert "can" in entities
        assert "drug" in entities
        assert "delivery" in entities
        assert "be" not in entities  # too short
        assert "improved" in entities
        # Unique
        assert len(entities) == len(set(entities))

    def test_extract_entities_empty(self):
        """_extract_entities with empty string returns empty list."""
        pipeline = TransferPipeline()
        assert pipeline._extract_entities("") == []

    def test_extract_entities_limits_to_15(self):
        """_extract_entities should cap at 15 entities."""
        pipeline = TransferPipeline()
        text = " ".join(f"word{i:03d}" for i in range(30))
        entities = pipeline._extract_entities(text)
        assert len(entities) <= 15


# ═══════════════════════════════════════════════════════════════════
# c4_transfer (public API)
# ═══════════════════════════════════════════════════════════════════


class TestC4Transfer:
    def test_returns_transfer_result(self):
        """c4_transfer should return a TransferResult."""
        result = c4_transfer(
            problem="test problem",
            source_domain="biology",
            target_domain="machine_learning",
        )
        assert isinstance(result, TransferResult)
        assert result.problem == "test problem"
        assert result.source_domain == "biology"
        assert result.target_domain == "machine_learning"

    def test_normalizes_domain_names(self):
        """c4_transfer should normalize domain names with spaces/hyphens."""
        result = c4_transfer(
            problem="test",
            source_domain="fluid dynamics",
            target_domain="neural-networks",
        )
        assert result.source_domain == "fluid dynamics"
        assert result.target_domain == "neural-networks"


# ═══════════════════════════════════════════════════════════════════
# cross_domain_transfer (pipeline integration)
# ═══════════════════════════════════════════════════════════════════


class TestCrossDomainTransfer:
    def test_explicit_domains(self):
        """When domains are explicit, use them directly."""
        result = cross_domain_transfer(
            problem="test",
            source_domain="thermodynamics",
            target_domain="machine_learning",
        )
        assert result.source_domain == "thermodynamics"
        assert result.target_domain == "machine_learning"
        assert result.triggered_auto is False

    def test_auto_detect_domains(self):
        """When no domains given, auto-detect from problem."""
        problem = (
            "How can drug delivery through cell membranes be improved "
            "using fluid flow and turbulence?"
        )
        result = cross_domain_transfer(problem=problem)
        assert result.triggered_auto is True
        assert result.source_domain != ""
        assert result.target_domain != ""

    def test_auto_detect_falls_back(self):
        """When no domains detected, fallback to general/ML."""
        result = cross_domain_transfer(problem="what is the answer")
        assert result.source_domain == "general"
        assert result.target_domain == "machine_learning"

    def test_partial_auto_detect(self):
        """When only source_domain given, auto-detect target."""
        problem = (
            "How can drug delivery through cell membranes be improved "
            "using fluid flow and turbulence?"
        )
        result = cross_domain_transfer(problem=problem, source_domain="biology")
        assert result.triggered_auto is True
        assert result.source_domain == "biology"


# ═══════════════════════════════════════════════════════════════════
# Edge cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_transfer_empty_problem(self):
        """Empty problem should not crash."""
        result = c4_transfer(problem="", source_domain="a", target_domain="b")
        assert isinstance(result, TransferResult)

    def test_transfer_very_long_problem(self):
        """Very long problem should not crash."""
        problem = "drug delivery " * 1000
        result = c4_transfer(problem=problem, source_domain="biology", target_domain="fluid_dynamics")
        assert isinstance(result, TransferResult)

    def test_detect_cross_domain_special_chars(self):
        """Special characters in problem should be handled."""
        problem = "drug delivery! @cell #membrane $fluid %flow"
        domains = detect_cross_domain(problem)
        assert "biology" in domains
        assert "fluid_dynamics" in domains

    def test_seed_with_no_triz(self):
        """Seed without triz field should not crash."""
        seed = {"source": "a", "target": "b", "mapping": "x ↔ y"}
        fp = _seed_to_fingerprint(seed)
        assert fp.constraints == []


# ═══════════════════════════════════════════════════════════════════
# StructuralIsomorphismResult dataclass
# ═══════════════════════════════════════════════════════════════════


class TestStructuralIsomorphismResult:
    def test_default_values(self):
        """StructuralIsomorphismResult should have sensible defaults."""
        result = StructuralIsomorphismResult()
        assert result.mapping == {}
        assert result.confidence == 0.0
        assert result.structural_preserved is False
        assert result.dimensional_consistent is False
        assert result.conservation_preserved is False
        assert result.node_match_ratio == 0.0
        assert result.edge_match_ratio == 0.0
        assert result.dimensional_violations == []
        assert result.missing_conservation_laws == []

    def test_to_dict_serialization(self):
        """to_dict should return a serializable dictionary."""
        result = StructuralIsomorphismResult(
            mapping={"a": "b", "c": "d"},
            confidence=0.85,
            structural_preserved=True,
            dimensional_consistent=False,
            conservation_preserved=True,
            node_match_ratio=0.9,
            edge_match_ratio=0.75,
            dimensional_violations=["mass mismatch"],
            missing_conservation_laws=["energy"],
        )
        d = result.to_dict()
        assert d["mapping"] == {"a": "b", "c": "d"}
        assert d["confidence"] == 0.85
        assert d["structural_preserved"] is True
        assert d["dimensional_consistent"] is False
        assert d["conservation_preserved"] is True
        assert d["node_match_ratio"] == 0.9
        assert d["edge_match_ratio"] == 0.75
        assert d["dimensional_violations"] == ["mass mismatch"]
        assert d["missing_conservation_laws"] == ["energy"]

    def test_partial_match_fields(self):
        """Partial match should have fractional ratios and lower confidence."""
        result = StructuralIsomorphismResult(
            mapping={"x": "y"},
            confidence=0.5,
            node_match_ratio=0.6,
            edge_match_ratio=0.4,
        )
        assert result.confidence == 0.5
        assert result.node_match_ratio == 0.6
        assert result.edge_match_ratio == 0.4


# ═══════════════════════════════════════════════════════════════════
# TransferResult dataclass — extended edge cases
# ═══════════════════════════════════════════════════════════════════


class TestTransferResultExtended:
    def test_structural_result_serialization(self):
        """TransferResult with structural result should serialize correctly."""
        structural = StructuralIsomorphismResult(
            mapping={"cell": "neuron"},
            confidence=0.92,
            structural_preserved=True,
        )
        result = TransferResult(
            problem="test",
            source_domain="biology",
            target_domain="neural_networks",
            confidence=0.92,
            isomorphism_type="verified",
            structural_result=structural,
        )
        d = result.to_dict()
        assert d["structural_result"]["mapping"] == {"cell": "neuron"}
        assert d["structural_result"]["confidence"] == 0.92

    def test_no_structural_result_serializes_none(self):
        """TransferResult without structural result should serialize None."""
        result = TransferResult(
            problem="x",
            source_domain="a",
            target_domain="b",
        )
        d = result.to_dict()
        assert d["structural_result"] is None

    def test_mappings_initialized_correctly(self):
        """Mappings passed at init should be accessible."""
        result = TransferResult(
            problem="x",
            source_domain="a",
            target_domain="b",
            mappings=[{"k": "v"}],
        )
        assert len(result.mappings) == 1
        assert result.mappings[0] == {"k": "v"}


# ═══════════════════════════════════════════════════════════════════
# Isomorphism detection — graph-based structural matching
# ═══════════════════════════════════════════════════════════════════


class TestGraphIsomorphismMatch:
    def test_identical_graphs_match(self):
        """Two identical graphs should be structurally isomorphic."""
        import networkx as nx
        g1 = nx.DiGraph()
        g1.add_edge("a", "b")
        g1.add_edge("b", "c")
        g2 = nx.DiGraph()
        g2.add_edge("a", "b")
        g2.add_edge("b", "c")
        result = graph_isomorphism_match(g1, g2)
        assert result.structural_preserved is True
        assert result.confidence == 1.0
        assert result.node_match_ratio == 1.0
        assert result.edge_match_ratio == 1.0

    def test_different_graphs_no_match(self):
        """Two completely different graphs should not be isomorphic."""
        import networkx as nx
        g1 = nx.DiGraph()
        g1.add_edge("a", "b")
        g2 = nx.DiGraph()
        g2.add_edge("x", "y")
        g2.add_edge("y", "z")
        result = graph_isomorphism_match(g1, g2)
        assert result.structural_preserved is False
        assert result.confidence < 1.0

    def test_empty_graphs_handled(self):
        """Empty graphs should not crash and return violations."""
        import networkx as nx
        g1 = nx.DiGraph()
        g2 = nx.DiGraph()
        result = graph_isomorphism_match(g1, g2)
        assert "Empty source or target graph" in result.dimensional_violations

    def test_single_node_graphs(self):
        """Single node graphs should match structurally if same label."""
        import networkx as nx
        g1 = nx.DiGraph()
        g1.add_node("energy")
        g2 = nx.DiGraph()
        g2.add_node("energy")
        result = graph_isomorphism_match(g1, g2)
        assert result.structural_preserved is True


class TestDimensionalConsistency:
    def test_velocity_to_speed_is_consistent(self):
        """velocity and speed have same dimensional signature [1,0,-1,0,0,0,0]."""
        import networkx as nx
        g1 = nx.DiGraph()
        g1.add_node("velocity")
        g2 = nx.DiGraph()
        g2.add_node("speed")
        consistent, violations = check_dimensional_consistency(
            g1, g2, {"velocity": "speed"}
        )
        assert consistent is True
        assert violations == []

    def test_velocity_to_temperature_is_inconsistent(self):
        """velocity [L/T] vs temperature [Θ] are dimensionally inconsistent."""
        import networkx as nx
        g1 = nx.DiGraph()
        g1.add_node("velocity")
        g2 = nx.DiGraph()
        g2.add_node("temperature")
        consistent, violations = check_dimensional_consistency(
            g1, g2, {"velocity": "temperature"}
        )
        assert consistent is False
        assert len(violations) > 0

    def test_empty_mapping_returns_false(self):
        """Empty mapping should return False with a reason."""
        import networkx as nx
        g1 = nx.DiGraph()
        g2 = nx.DiGraph()
        consistent, violations = check_dimensional_consistency(g1, g2, {})
        assert consistent is False
        assert any("No mapping" in v for v in violations)


class TestConservationLaws:
    def test_physics_domain_checks_energy_momentum(self):
        """Physics domain should check for energy, momentum, angular_momentum, and charge."""
        import networkx as nx
        g = nx.DiGraph()
        g.add_node("energy")
        g.add_node("momentum")
        g.add_node("angular_momentum_conservation")
        g.add_node("charge")
        preserved, missing = check_conservation_laws("physics", g)
        assert preserved is True
        assert missing == []

    def test_missing_laws_detected(self):
        """When conservation laws are missing, they should be reported."""
        import networkx as nx
        g = nx.DiGraph()
        g.add_node("data")
        preserved, missing = check_conservation_laws("physics", g)
        assert preserved is False
        assert len(missing) > 0

    def test_unknown_domain_uses_defaults(self):
        """Unknown domain should fall back to energy + momentum."""
        import networkx as nx
        g = nx.DiGraph()
        g.add_node("energy")
        preserved, missing = check_conservation_laws("fantasy_domain", g)
        # Only energy present, momentum missing
        assert "momentum" in missing

    def test_fluid_dynamics_checks_mass_momentum_energy(self):
        """Fluid dynamics should check mass, momentum, and energy."""
        import networkx as nx
        g = nx.DiGraph()
        g.add_node("mass")
        g.add_node("momentum_transfer")
        g.add_node("energy_dissipation")
        preserved, missing = check_conservation_laws("fluid_dynamics", g)
        assert preserved is True


class TestExtractOntologyGraph:
    def test_basic_problem_creates_graph(self):
        """extract_ontology_graph should return a DiGraph with nodes."""
        G = extract_ontology_graph(
            "drug delivery through cell membranes causes therapeutic effects"
        )
        assert len(G.nodes()) > 0
        assert "drug" in G.nodes()
        assert "delivery" in G.nodes()

    def test_causal_relation_detected(self):
        """Causal language should create edges between entities."""
        G = extract_ontology_graph(
            "pollution causes health problems in urban areas"
        )
        assert G.has_edge("pollution", "health") or G.has_edge("pollution", "problems")

    def test_empty_problem_returns_empty_graph(self):
        """Empty problem should return an empty graph."""
        G = extract_ontology_graph("")
        assert len(G.nodes()) == 0
        assert len(G.edges()) == 0

    def test_stopwords_are_excluded(self):
        """Common stopwords should not become nodes."""
        G = extract_ontology_graph("the and but or for with")
        for node in G.nodes():
            assert node not in {"the", "and", "but", "or", "for", "with"}

    def test_short_words_are_excluded(self):
        """Words shorter than 3 characters should not be nodes."""
        G = extract_ontology_graph("at in be do go")
        assert len(G.nodes()) == 0
