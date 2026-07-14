"""Tests for TURBO-CDI L1 Causal Engine — Counterfactual reasoning."""
from __future__ import annotations

import numpy as np
import pytest

from src.causal.counterfactual import CounterfactualEngine, CounterfactualQuery
from src.causal.scm import Intervention, StructuralCausalModel


class TestCounterfactualEngine:
    def test_engine_creation(self) -> None:
        scm = StructuralCausalModel()
        engine = CounterfactualEngine(scm)
        assert engine.scm is scm

    def test_infer_exogenous_empty(self) -> None:
        scm = StructuralCausalModel()
        engine = CounterfactualEngine(scm)
        u = engine._infer_exogenous({})
        assert u == {}

    def test_infer_exogenous_simple(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("U", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("X", parents=["U"], mechanism=lambda u, n: u + n)

        engine = CounterfactualEngine(scm)
        u = engine._infer_exogenous({"X": 5.0})
        assert "noise_X" in u

    def test_query_simple(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("U", is_exogenous=True, noise=lambda: 2.0)
        scm.add_node("X", parents=["U"], mechanism=lambda u, n: u + n)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, n: 3 * x + n)

        engine = CounterfactualEngine(scm)
        query = CounterfactualQuery(
            evidence={"X": 2.0},
            intervention=Intervention("X", 5.0),
            target="Y",
        )
        result = engine.query(query)
        assert result.counterfactual_value == 15.0

    def test_what_if(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, u: 2 * x + u)

        engine = CounterfactualEngine(scm)
        result = engine.what_if(
            evidence={"X": 1.0},
            intervention_target="X",
            intervention_value=3.0,
            target_variable="Y",
        )
        assert result.counterfactual_value == 6.0
        assert result.effect == 5.0

    def test_compare_interventions(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, u: 2 * x + u)

        engine = CounterfactualEngine(scm)
        results = engine.compare_interventions(
            evidence={"X": 1.0},
            target="Y",
            interventions=[("X", 2.0), ("X", 3.0)],
        )
        assert len(results) == 2
        assert results[0].counterfactual_value == 4.0
        assert results[1].counterfactual_value == 6.0

    def test_natural_effects_decomposition(self) -> None:
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
        assert "total_effect" in effects
        assert "y_control" in effects
        assert "y_treatment" in effects
        assert abs(effects["total_effect"] - 2.0) < 0.01

    def test_counterfactual_result_fields(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 0.0)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, u: x + u)

        engine = CounterfactualEngine(scm)
        query = CounterfactualQuery(
            evidence={"X": 1.0},
            intervention=Intervention("X", 2.0),
            target="Y",
        )
        result = engine.query(query)
        assert hasattr(result, "query")
        assert hasattr(result, "factual_value")
        assert hasattr(result, "counterfactual_value")
        assert hasattr(result, "effect")
        assert hasattr(result, "exogenous_values")
        assert result.effect == result.counterfactual_value - result.factual_value

    def test_solve_for_noise(self) -> None:
        scm = StructuralCausalModel()
        engine = CounterfactualEngine(scm)

        mechanism = lambda a, b, u: a + b + u
        u = engine._solve_for_noise(mechanism, [2.0, 3.0], 10.0, 1e-6, 1000)
        assert abs(u - 5.0) < 0.01

    def test_solve_for_noise_linear(self) -> None:
        scm = StructuralCausalModel()
        engine = CounterfactualEngine(scm)

        mechanism = lambda x, u: 2 * x + 3 * u
        u = engine._solve_for_noise(mechanism, [1.0], 11.0, 1e-6, 1000)
        assert abs(3 * u + 2 - 11) < 0.1

    def test_query_with_collider(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True, noise=lambda: 1.0)
        scm.add_node("Y", is_exogenous=True, noise=lambda: 2.0)
        scm.add_node("Z", parents=["X", "Y"], mechanism=lambda x, y, u: x + y + u)

        engine = CounterfactualEngine(scm)
        query = CounterfactualQuery(
            evidence={"X": 1.0, "Y": 2.0, "Z": 3.0},
            intervention=Intervention("X", 5.0),
            target="Z",
        )
        result = engine.query(query)
        assert result.counterfactual_value == 7.0

    def test_evidence_propagation(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("A", is_exogenous=True, noise=lambda: 1.0)
        scm.add_node("B", parents=["A"], mechanism=lambda a, u: a + u)
        scm.add_node("C", parents=["B"], mechanism=lambda b, u: 2 * b + u)

        engine = CounterfactualEngine(scm)
        result = engine.what_if(
            evidence={"A": 1.0, "B": 1.0, "C": 2.0},
            intervention_target="A",
            intervention_value=3.0,
            target_variable="C",
        )
        assert result.counterfactual_value == 6.0
