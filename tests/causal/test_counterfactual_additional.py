"""Additional tests for counterfactual reasoning to improve coverage."""
from __future__ import annotations

import numpy as np
import pytest

from causal.counterfactual import (
    CounterfactualEngine,
    CounterfactualQuery,
    CounterfactualResult,
)
from causal.scm import Intervention, StructuralCausalModel


class TestCounterfactualQueryAndResult:
    """Tests for dataclasses."""

    def test_query_creation(self):
        query = CounterfactualQuery(
            evidence={"X": 1.0},
            intervention=Intervention("X", 2.0),
            target="Y",
        )
        assert query.evidence == {"X": 1.0}
        assert query.intervention.target == "X"
        assert query.intervention.value == 2.0
        assert query.target == "Y"

    def test_result_creation(self):
        query = CounterfactualQuery(
            evidence={"X": 1.0},
            intervention=Intervention("X", 2.0),
            target="Y",
        )
        result = CounterfactualResult(
            query=query,
            factual_value=1.0,
            counterfactual_value=2.0,
            effect=1.0,
            exogenous_values={"U": 0.5},
        )
        assert result.factual_value == 1.0
        assert result.counterfactual_value == 2.0
        assert result.effect == 1.0
        assert result.exogenous_values == {"U": 0.5}


class TestInferExogenousExtended:
    """Extended tests for exogenous inference."""

    def test_infer_exogenous_no_evidence(self):
        scm = StructuralCausalModel()
        engine = CounterfactualEngine(scm)
        u = engine._infer_exogenous({})
        assert u == {}

    def test_infer_exogenous_exogenous_node(self):
        scm = StructuralCausalModel()
        scm.add_node("U", is_exogenous=True, noise=lambda: 0.0)

        engine = CounterfactualEngine(scm)
        u = engine._infer_exogenous({"U": 5.0})
        assert u["U"] == 5.0

    def test_infer_exogenous_with_mechanism_single_parent(self):
        scm = StructuralCausalModel()
        scm.add_node("U", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("X", parents=["U"], mechanism=lambda u, n: u + n)

        engine = CounterfactualEngine(scm)
        u = engine._infer_exogenous({"X": 5.0, "U": 3.0})
        assert "noise_X" in u
        # X = U + noise_X = 3 + noise_X = 5, so noise_X = 2
        assert abs(u["noise_X"] - 2.0) < 0.01

    def test_infer_exogenous_no_mechanism(self):
        scm = StructuralCausalModel()
        scm.add_node("U", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("X", parents=["U"])

        engine = CounterfactualEngine(scm)
        u = engine._infer_exogenous({"X": 5.0, "U": 3.0})
        assert "noise_X" in u
        # X = sum(parents) + noise = 3 + noise = 5, so noise = 2
        assert abs(u["noise_X"] - 2.0) < 0.01

    def test_infer_exogenous_missing_evidence_node(self):
        scm = StructuralCausalModel()
        scm.add_node("U", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("X", parents=["U"], mechanism=lambda u, n: u + n)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, n: 2 * x + n)

        engine = CounterfactualEngine(scm)
        # Only evidence for U, not X or Y
        u = engine._infer_exogenous({"U": 1.0})
        assert "U" in u
        assert "noise_X" in u
        assert "noise_Y" in u

    def test_infer_exogenous_with_noise_distribution(self):
        scm = StructuralCausalModel()
        scm.add_node("U", is_exogenous=True, noise=lambda: 0.5)

        engine = CounterfactualEngine(scm)
        u = engine._infer_exogenous({})
        # Should sample from noise distribution
        assert "U" in u


class TestSolveForNoiseExtended:
    """Extended tests for noise solving."""

    def test_solve_for_noise_constant_mechanism(self):
        scm = StructuralCausalModel()
        engine = CounterfactualEngine(scm)

        mechanism = lambda a, u: 5.0  # constant
        u = engine._solve_for_noise(mechanism, [2.0], 5.0, 1e-6, 100)
        # Any u should work since mechanism ignores it
        assert abs(mechanism(2.0, u) - 5.0) < 1e-5

    def test_solve_for_noise_noisy_convergence(self):
        scm = StructuralCausalModel()
        engine = CounterfactualEngine(scm)

        mechanism = lambda a, b, u: a * b + u * 0.001
        u = engine._solve_for_noise(mechanism, [2.0, 3.0], 6.0, 1e-3, 100)
        # Should be close to 0 since a*b = 6
        assert abs(u) < 10.0

    def test_solve_for_noise_at_boundary(self):
        scm = StructuralCausalModel()
        engine = CounterfactualEngine(scm)

        mechanism = lambda a, u: a + u
        u = engine._solve_for_noise(mechanism, [5.0], 105.0, 1e-6, 100)
        # u should be ~100
        assert abs(u - 100.0) < 1.0

    def test_solve_for_noise_negative_boundary(self):
        scm = StructuralCausalModel()
        engine = CounterfactualEngine(scm)

        mechanism = lambda a, u: a + u
        u = engine._solve_for_noise(mechanism, [5.0], -95.0, 1e-6, 100)
        # u should be ~-100
        assert abs(u - (-100.0)) < 1.0

    def test_solve_for_noise_large_range(self):
        scm = StructuralCausalModel()
        engine = CounterfactualEngine(scm)

        mechanism = lambda a, u: a + u
        u = engine._solve_for_noise(mechanism, [0.0], 500.0, 1e-6, 100)
        assert abs(u - 500.0) < 1.0


class TestQueryExtended:
    """Extended tests for counterfactual queries."""

    def test_query_with_exogenous_evidence(self):
        scm = StructuralCausalModel()
        scm.add_node("U", is_exogenous=True, noise=lambda: 1.0)
        scm.add_node("X", parents=["U"], mechanism=lambda u, n: u + n)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, n: 2 * x + n)

        engine = CounterfactualEngine(scm)
        query = CounterfactualQuery(
            evidence={"U": 1.0, "X": 1.0, "Y": 2.0},
            intervention=Intervention("X", 3.0),
            target="Y",
        )
        result = engine.query(query)
        assert result.counterfactual_value == 6.0  # 2 * 3 = 6

    def test_query_with_collider_intervention(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 1.0)
        scm.add_node("Y", is_exogenous=True, noise=lambda: 2.0)
        scm.add_node("Z", parents=["X", "Y"], mechanism=lambda x, y, n: x + y + n)
        scm.add_node("W", parents=["Z"], mechanism=lambda z, n: z * 2 + n)

        engine = CounterfactualEngine(scm)
        result = engine.what_if(
            evidence={"X": 1.0, "Y": 2.0, "Z": 3.0, "W": 6.0},
            intervention_target="X",
            intervention_value=5.0,
            target_variable="W",
        )
        assert result.counterfactual_value == 14.0  # (5 + 2) * 2 = 14

    def test_query_effect_computation(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, u: 3 * x + u)

        engine = CounterfactualEngine(scm)
        query = CounterfactualQuery(
            evidence={"X": 1.0, "Y": 3.0},
            intervention=Intervention("X", 4.0),
            target="Y",
        )
        result = engine.query(query)
        assert result.factual_value == 3.0
        assert result.counterfactual_value == 12.0
        assert result.effect == 9.0

    def test_query_preserves_evidence(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, u: x + u)

        engine = CounterfactualEngine(scm)
        query = CounterfactualQuery(
            evidence={"X": 2.0},
            intervention=Intervention("X", 5.0),
            target="Y",
        )
        result = engine.query(query)
        assert result.query == query


class TestWhatIfExtended:
    """Extended tests for what_if convenience method."""

    def test_what_if_chain_structure(self):
        scm = StructuralCausalModel()
        scm.add_node("A", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("B", parents=["A"], mechanism=lambda a, u: a + u)
        scm.add_node("C", parents=["B"], mechanism=lambda b, u: b + u)
        scm.add_node("D", parents=["C"], mechanism=lambda c, u: c + u)

        engine = CounterfactualEngine(scm)
        result = engine.what_if(
            evidence={"A": 1.0, "B": 1.0, "C": 1.0, "D": 1.0},
            intervention_target="A",
            intervention_value=3.0,
            target_variable="D",
        )
        assert result.counterfactual_value == 3.0

    def test_what_if_multiple_parents(self):
        scm = StructuralCausalModel()
        scm.add_node("A", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("B", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("C", parents=["A", "B"], mechanism=lambda a, b, u: a + b + u)

        engine = CounterfactualEngine(scm)
        result = engine.what_if(
            evidence={"A": 1.0, "B": 2.0, "C": 3.0},
            intervention_target="A",
            intervention_value=5.0,
            target_variable="C",
        )
        assert result.counterfactual_value == 7.0  # 5 + 2 = 7


class TestCompareInterventionsExtended:
    """Extended tests for compare_interventions."""

    def test_compare_multiple_interventions(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, u: x + u)

        engine = CounterfactualEngine(scm)
        results = engine.compare_interventions(
            evidence={"X": 1.0, "Y": 1.0},
            target="Y",
            interventions=[("X", 2.0), ("X", 3.0), ("X", 4.0)],
        )
        assert len(results) == 3
        assert results[0].counterfactual_value == 2.0
        assert results[1].counterfactual_value == 3.0
        assert results[2].counterfactual_value == 4.0

    def test_compare_interventions_empty(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, u: x + u)

        engine = CounterfactualEngine(scm)
        results = engine.compare_interventions(
            evidence={"X": 1.0},
            target="Y",
            interventions=[],
        )
        assert len(results) == 0

    def test_compare_different_targets(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, u: x + u)
        scm.add_node("Z", parents=["X"], mechanism=lambda x, u: 2 * x + u)

        engine = CounterfactualEngine(scm)
        y_results = engine.compare_interventions(
            evidence={"X": 1.0},
            target="Y",
            interventions=[("X", 2.0)],
        )
        z_results = engine.compare_interventions(
            evidence={"X": 1.0},
            target="Z",
            interventions=[("X", 2.0)],
        )
        assert y_results[0].counterfactual_value == 2.0
        assert z_results[0].counterfactual_value == 4.0


class TestNaturalEffectsExtended:
    """Extended tests for natural effects decomposition."""

    def test_natural_effects_with_levels(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, u: 2 * x + u)

        engine = CounterfactualEngine(scm)
        effects = engine.natural_effects_decomposition(
            treatment="X",
            outcome="Y",
            evidence={"X": 0.0},
            treatment_levels=(0.0, 1.0),
        )
        assert effects["total_effect"] == 2.0
        assert effects["y_control"] == 0.0
        assert effects["y_treatment"] == 2.0

    def test_natural_effects_negative_effect(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, u: -1 * x + u)

        engine = CounterfactualEngine(scm)
        effects = engine.natural_effects_decomposition(
            treatment="X",
            outcome="Y",
            evidence={"X": 0.0},
            treatment_levels=(0.0, 1.0),
        )
        assert effects["total_effect"] == -1.0
        assert effects["y_treatment"] == -1.0

    def test_natural_effects_nonzero_control(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, u: x + 5 + u)

        engine = CounterfactualEngine(scm)
        effects = engine.natural_effects_decomposition(
            treatment="X",
            outcome="Y",
            evidence={"X": 1.0},
            treatment_levels=(1.0, 3.0),
        )
        assert effects["total_effect"] == 2.0
        assert effects["y_control"] == 6.0  # Under do(X=1), Y = 1 + 5 = 6
        # Actually with evidence, factual is from evidence


class TestCounterfactualErrorHandling:
    """Tests for error handling in counterfactual engine."""

    def test_solve_for_noise_exception_in_mechanism(self):
        scm = StructuralCausalModel()
        engine = CounterfactualEngine(scm)

        def bad_mechanism(a, u):
            if u > 50:
                raise ValueError("overflow")
            return a + u

        u = engine._solve_for_noise(bad_mechanism, [1.0], 10.0, 1e-6, 100)
        # Should handle exception gracefully
        assert isinstance(u, float)

    def test_query_with_missing_target(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 0.0)

        engine = CounterfactualEngine(scm)
        query = CounterfactualQuery(
            evidence={"X": 1.0},
            intervention=Intervention("X", 2.0),
            target="Y",  # Y doesn't exist
        )
        result = engine.query(query)
        # Should return 0.0 for missing target
        assert result.counterfactual_value == 0.0
