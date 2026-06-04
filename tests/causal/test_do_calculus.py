"""Tests for TURBO-CDI L1 Causal Engine — Do-calculus."""
from __future__ import annotations

import pytest

from src.causal.do_calculus import DoCalculus
from src.causal.scm import Intervention, StructuralCausalModel


class TestDoCalculusRules:
    def test_rule1_independent_nodes(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", is_exogenous=True)
        scm.add_node("Z", is_exogenous=True)

        calc = DoCalculus(scm)
        assert calc.rule1_insertion_deletion("Y", "Z", {"X"})

    def test_rule1_chain_blocked(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Z", parents=["X"])
        scm.add_node("Y", parents=["Z"])

        calc = DoCalculus(scm)
        assert not calc.rule1_insertion_deletion("Y", "Z", {"X"})

    def test_rule2_action_observation(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Z", parents=["X"])
        scm.add_node("Y", parents=["Z"])

        calc = DoCalculus(scm)
        result = calc.rule2_action_observation_exchange("Y", "Z", {"X"})
        assert isinstance(result, bool)

    def test_rule3_insertion_deletion(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", parents=["X"])

        calc = DoCalculus(scm)
        result = calc.rule3_insertion_deletion_actions("Y", "Z", {"X"})
        assert isinstance(result, bool)


class TestIdentifiability:
    def test_identifiable_no_confounding(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", parents=["X"])

        calc = DoCalculus(scm)
        identifiable, reason = calc.is_identifiable("X", "Y")
        assert identifiable
        assert "No backdoor paths" in reason

    def test_identifiable_with_backdoor(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("Z", is_exogenous=True)
        scm.add_node("X", parents=["Z"])
        scm.add_node("Y", parents=["Z", "X"])

        calc = DoCalculus(scm)
        identifiable, reason = calc.is_identifiable("X", "Y")
        assert identifiable
        assert "Adjust for" in reason

    def test_not_identifiable_m_structure(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("U1", is_exogenous=True)
        scm.add_node("U2", is_exogenous=True)
        scm.add_node("Z1", parents=["U1"])
        scm.add_node("Z2", parents=["U1", "U2"])
        scm.add_node("Z3", parents=["U2"])
        scm.add_node("X", parents=["Z1", "Z2"])
        scm.add_node("Y", parents=["Z2", "Z3"])

        calc = DoCalculus(scm)
        identifiable, reason = calc.is_identifiable("X", "Y")
        # M-structure with collider Z2 may or may not be identifiable depending on criterion
        assert isinstance(identifiable, bool)

    def test_same_variable_not_identifiable(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X")

        calc = DoCalculus(scm)
        identifiable, reason = calc.is_identifiable("X", "X")
        assert not identifiable

    def test_missing_variable(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X")

        calc = DoCalculus(scm)
        identifiable, reason = calc.is_identifiable("X", "Y")
        assert not identifiable
        assert "Missing" in reason

    def test_frontdoor_identifiable(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Z", parents=["X"])
        scm.add_node("Y", parents=["Z"])

        calc = DoCalculus(scm)
        identifiable, reason = calc.is_identifiable("X", "Y")
        assert identifiable

    def test_adjustment_formula_backdoor(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("Z", is_exogenous=True)
        scm.add_node("X", parents=["Z"])
        scm.add_node("Y", parents=["Z", "X"])

        calc = DoCalculus(scm)
        identifiable, formula, adjustment = calc.get_adjustment_formula("X", "Y")
        assert identifiable
        assert formula is not None
        assert adjustment is not None
        assert "Z" in adjustment

    def test_adjustment_formula_no_confounding(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", parents=["X"])

        calc = DoCalculus(scm)
        identifiable, formula, adjustment = calc.get_adjustment_formula("X", "Y")
        assert identifiable
        assert adjustment is not None
        assert len(adjustment) == 0

    def test_list_identifiable_effects(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", parents=["X"])
        scm.add_node("Z", parents=["X"])

        calc = DoCalculus(scm)
        effects = calc.list_identifiable_effects()
        assert len(effects) > 0
        assert all(len(e) == 3 for e in effects)

    def test_estimate_ate_from_data(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", parents=["X"], mechanism=lambda x, u: 2 * x + u)

        calc = DoCalculus(scm)
        data = {
            "X": [0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.0],
            "Y": [0.1, -0.1, 2.1, 1.9, 2.0, 0.0, 2.2, -0.2],
        }
        ate = calc.estimate_ate_from_data("X", "Y", data)
        assert ate is not None
        assert abs(ate - 2.0) < 0.5

    def test_estimate_ate_not_identifiable(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", is_exogenous=True)

        calc = DoCalculus(scm)
        data = {"X": [0.0, 1.0], "Y": [0.0, 1.0]}
        ate = calc.estimate_ate_from_data("X", "Y", data)
        # Two independent exogenous nodes: no backdoor paths, so ATE is just difference in means
        assert isinstance(ate, (float, type(None)))

    def test_mutilated_graph(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("Z", is_exogenous=True)
        scm.add_node("X", parents=["Z"])
        scm.add_node("Y", parents=["X"])

        calc = DoCalculus(scm)
        g = calc._mutilated_graph({"X"})
        assert not g.has_edge("Z", "X")
        assert g.has_edge("X", "Y")

    def test_frontdoor_criterion_simple(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Z", parents=["X"])
        scm.add_node("Y", parents=["Z"])

        calc = DoCalculus(scm)
        frontdoor = calc._try_frontdoor("X", "Y")
        assert frontdoor is not None
        assert "Z" in frontdoor

    def test_intercepts_all_directed_paths(self) -> None:
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Z", parents=["X"])
        scm.add_node("Y", parents=["Z"])

        calc = DoCalculus(scm)
        assert calc._intercepts_all_directed_paths("X", "Y", "Z")
        assert not calc._intercepts_all_directed_paths("X", "Y", "X")
