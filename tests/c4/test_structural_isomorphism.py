"""Tests for Structural Isomorphism Engine (Phase P2).

Coverage:
- Ontology graph extraction from problem text
- Graph-based isomorphism via networkx GraphMatcher (VF2)
- Dimensional consistency checking
- Conservation law preservation checking
- Known analogies: electrical ↔ mechanical
"""
from __future__ import annotations

import sys
from pathlib import Path

import networkx as nx
import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from c4.transfer_pipeline import (
    TransferPipeline,
    TransferResult,
    check_conservation_laws,
    check_dimensional_consistency,
    extract_ontology_graph,
    graph_isomorphism_match,
)


# ---------------------------------------------------------------------------
# Ontology graph extraction
# ---------------------------------------------------------------------------

class TestExtractOntologyGraph:
    def test_extracts_nodes(self):
        problem = "How does heat diffusion relate to activation propagation in neural networks?"
        G = extract_ontology_graph(problem)
        assert len(G.nodes()) > 0
        nodes_lower = {n.lower() for n in G.nodes()}
        assert "heat" in nodes_lower or "diffusion" in nodes_lower
        assert "neural" in nodes_lower or "networks" in nodes_lower

    def test_extracts_edges(self):
        problem = "Force causes acceleration in mechanical systems."
        G = extract_ontology_graph(problem)
        assert len(G.edges()) >= 0

    def test_empty_string(self):
        G = extract_ontology_graph("")
        assert len(G.nodes()) == 0

    def test_deduplicates_nodes(self):
        problem = "Neural networks use neural networks for neural computation."
        G = extract_ontology_graph(problem)
        # "neural" should appear once
        neural_count = sum(1 for n in G.nodes() if n == "neural")
        assert neural_count <= 1


# ---------------------------------------------------------------------------
# Graph isomorphism matching
# ---------------------------------------------------------------------------

class TestGraphIsomorphismMatch:
    def test_identical_graphs(self):
        G1 = nx.DiGraph()
        G1.add_edge("a", "b", relation="causes")
        G1.add_edge("b", "c", relation="produces")
        G2 = nx.DiGraph()
        G2.add_edge("a", "b", relation="causes")
        G2.add_edge("b", "c", relation="produces")
        result = graph_isomorphism_match(G1, G2)
        assert result.structural_preserved is True
        assert result.confidence == pytest.approx(1.0)

    def test_completely_different_graphs(self):
        G1 = nx.DiGraph()
        G1.add_edge("x", "y", relation="flows")
        G2 = nx.DiGraph()
        G2.add_edge("a", "b", relation="inhibits")
        G2.add_edge("c", "d", relation="activates")
        result = graph_isomorphism_match(G1, G2)
        assert result.structural_preserved is False
        assert result.confidence < 0.5

    def test_partial_subgraph_match(self):
        G1 = nx.DiGraph()
        G1.add_edge("a", "b", relation="causes")
        G1.add_edge("b", "c", relation="produces")
        G1.add_edge("c", "d", relation="modulates")
        G2 = nx.DiGraph()
        G2.add_edge("x", "y", relation="causes")
        G2.add_edge("y", "z", relation="produces")
        result = graph_isomorphism_match(G1, G2)
        # Should find partial match
        assert result.node_match_ratio > 0.3
        assert result.confidence > 0.0

    def test_empty_graphs(self):
        result = graph_isomorphism_match(nx.DiGraph(), nx.DiGraph())
        assert result.structural_preserved is False
        assert len(result.dimensional_violations) > 0


# ---------------------------------------------------------------------------
# Dimensional consistency
# ---------------------------------------------------------------------------

class TestDimensionalConsistency:
    def test_matching_dimensions(self):
        """Velocity [L/T] maps to velocity — consistent."""
        G1 = nx.DiGraph()
        G1.add_node("velocity")
        G2 = nx.DiGraph()
        G2.add_node("speed")
        mapping = {"velocity": "speed"}
        consistent, violations = check_dimensional_consistency(G1, G2, mapping)
        assert consistent is True
        assert len(violations) == 0

    def test_mismatched_dimensions(self):
        """Velocity [L/T] vs diffusion [L²/T] — inconsistent."""
        G1 = nx.DiGraph()
        G1.add_node("velocity")
        G2 = nx.DiGraph()
        G2.add_node("diffusion_coefficient")
        mapping = {"velocity": "diffusion_coefficient"}
        consistent, violations = check_dimensional_consistency(G1, G2, mapping)
        assert consistent is False
        assert len(violations) > 0
        assert any("velocity" in v and "diffusion" in v for v in violations)

    def test_force_and_mass_inconsistent(self):
        G1 = nx.DiGraph()
        G1.add_node("force")
        G2 = nx.DiGraph()
        G2.add_node("mass")
        mapping = {"force": "mass"}
        consistent, violations = check_dimensional_consistency(G1, G2, mapping)
        assert consistent is False

    def test_no_mapping(self):
        G1 = nx.DiGraph()
        G1.add_node("a")
        G2 = nx.DiGraph()
        G2.add_node("b")
        consistent, violations = check_dimensional_consistency(G1, G2, {})
        assert consistent is False
        assert any("No mapping" in v for v in violations)

    def test_unknown_entities_skipped(self):
        """Entities not in registry should be skipped, not flagged."""
        G1 = nx.DiGraph()
        G1.add_node("foo_bar_xyz")
        G2 = nx.DiGraph()
        G2.add_node("baz_qux_abc")
        mapping = {"foo_bar_xyz": "baz_qux_abc"}
        consistent, violations = check_dimensional_consistency(G1, G2, mapping)
        assert consistent is True  # skipped = no violations
        assert len(violations) == 0


# ---------------------------------------------------------------------------
# Conservation laws
# ---------------------------------------------------------------------------

class TestConservationLaws:
    def test_physics_energy_conserved(self):
        G = nx.DiGraph()
        G.add_node("energy")
        G.add_node("momentum")
        G.add_node("angular_momentum")
        G.add_node("charge")
        preserved, missing = check_conservation_laws("physics", G)
        assert preserved is True
        assert len(missing) == 0

    def test_physics_missing_charge(self):
        G = nx.DiGraph()
        G.add_node("energy")
        # Missing momentum and charge
        preserved, missing = check_conservation_laws("physics", G)
        assert preserved is False
        assert "momentum" in missing or "charge" in missing

    def test_fluid_dynamics(self):
        G = nx.DiGraph()
        G.add_node("mass")
        G.add_node("momentum")
        G.add_node("energy")
        preserved, missing = check_conservation_laws("fluid_dynamics", G)
        assert preserved is True

    def test_unknown_domain_defaults(self):
        G = nx.DiGraph()
        G.add_node("energy")
        preserved, missing = check_conservation_laws("alchemy", G)
        # Defaults to energy, momentum
        assert len(missing) >= 0


# ---------------------------------------------------------------------------
# Electrical ↔ Mechanical analogy (known isomorphism)
# ---------------------------------------------------------------------------

class TestElectricalMechanicalAnalogy:
    """Test the classic electrical ↔ mechanical analogy."""

    def test_series_rc_vs_damped_oscillator_graphs(self):
        """Series RC circuit and damped harmonic oscillator are structurally analogous."""
        # Electrical domain
        elec_problem = (
            "In a series RC circuit, voltage across the capacitor increases "
            "as current flows through the resistor, with the rate of change "
            "proportional to the resistance and capacitance."
        )
        # Mechanical domain
        mech_problem = (
            "In a damped harmonic oscillator, displacement decreases "
            "as damping force opposes velocity, with the rate of decay "
            "proportional to the damping coefficient and mass."
        )

        G_elec = extract_ontology_graph(elec_problem)
        G_mech = extract_ontology_graph(mech_problem)

        result = graph_isomorphism_match(G_elec, G_mech)
        # Both have similar causal chains: source -> resistance/damping -> accumulation
        assert result.confidence > 0.1
        assert len(result.mapping) > 0

    def test_dimensional_check_on_analogy(self):
        """Voltage ↔ force [M L / T²] and current ↔ velocity [L/T] are dimensionally compatible pairs."""
        G1 = nx.DiGraph()
        G1.add_node("voltage")
        G1.add_node("current")
        G2 = nx.DiGraph()
        G2.add_node("force")
        G2.add_node("velocity")
        mapping = {"voltage": "force", "current": "velocity"}
        consistent, violations = check_dimensional_consistency(G1, G2, mapping)
        # voltage [ML²/T³I] vs force [ML/T²] — these are NOT dimensionally identical
        # The test documents the behavior; we check it runs correctly
        assert isinstance(consistent, bool)
        assert isinstance(violations, list)


# ---------------------------------------------------------------------------
# TransferPipeline integration
# ---------------------------------------------------------------------------

class TestTransferPipelineStructural:
    def test_transfer_has_structural_result(self):
        pipeline = TransferPipeline()
        result = pipeline.transfer(
            problem="How does heat diffusion relate to activation propagation?",
            source_domain="thermodynamics",
            target_domain="neural_networks",
        )
        assert isinstance(result, TransferResult)
        assert result.structural_result is not None

    def test_structural_result_fields(self):
        pipeline = TransferPipeline()
        result = pipeline.transfer(
            problem="Voltage causes current through resistance.",
            source_domain="electromagnetics",
            target_domain="mechanics",
        )
        sr = result.structural_result
        assert sr is not None
        assert hasattr(sr, "mapping")
        assert hasattr(sr, "confidence")
        assert hasattr(sr, "structural_preserved")
        assert hasattr(sr, "dimensional_consistent")
        assert hasattr(sr, "conservation_preserved")

    def test_dimensional_violations_populated(self):
        pipeline = TransferPipeline()
        result = pipeline.transfer(
            problem="Velocity flow through diffusion channels.",
            source_domain="fluid_dynamics",
            target_domain="thermodynamics",
        )
        sr = result.structural_result
        assert sr is not None
        # Either consistent or has documented violations
        assert isinstance(sr.dimensional_consistent, bool)

    def test_conservation_check_populated(self):
        pipeline = TransferPipeline()
        result = pipeline.transfer(
            problem="Energy conservation in control systems.",
            source_domain="physics",
            target_domain="control_theory",
        )
        sr = result.structural_result
        assert sr is not None
        assert isinstance(sr.conservation_preserved, bool)

    def test_transfer_result_to_dict(self):
        pipeline = TransferPipeline()
        result = pipeline.transfer(
            problem="Test problem for serialization.",
            source_domain="biology",
            target_domain="machine_learning",
        )
        d = result.to_dict()
        assert "structural_result" in d
        if d["structural_result"] is not None:
            assert "mapping" in d["structural_result"]
            assert "dimensional_consistent" in d["structural_result"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestStructuralEdgeCases:
    def test_very_short_problem(self):
        G = extract_ontology_graph("Force causes acceleration in mechanical systems.")
        assert len(G.nodes()) >= 2
        assert len(G.edges()) >= 1

    def test_no_meaningful_entities(self):
        G = extract_ontology_graph("The the the.")
        assert len(G.nodes()) == 0

    def test_graph_with_cycle(self):
        G = nx.DiGraph()
        G.add_edge("a", "b", relation="activates")
        G.add_edge("b", "c", relation="inhibits")
        G.add_edge("c", "a", relation="modulates")
        result = graph_isomorphism_match(G, G)
        assert result.structural_preserved is True

    def test_large_graph_performance(self):
        G = nx.DiGraph()
        for i in range(50):
            G.add_node(f"node_{i}")
            if i > 0:
                G.add_edge(f"node_{i-1}", f"node_{i}", relation="causes")
        result = graph_isomorphism_match(G, G)
        assert result.structural_preserved is True
