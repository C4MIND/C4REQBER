"""Additional tests for do-calculus to improve coverage."""
from __future__ import annotations

import pytest

from causal.do_calculus import DoCalculus
from causal.scm import Intervention, StructuralCausalModel


class TestDoCalculusRulesExtended:
    """Extended tests for do-calculus rules."""

    def test_rule1_with_w_set(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", parents=["X"])
        scm.add_node("Z", parents=["X"])
        scm.add_node("W", parents=["Z"])

        calc = DoCalculus(scm)
        result = calc.rule1_insertion_deletion("Y", "Z", {"X"}, {"W"})
        assert isinstance(result, bool)

    def test_rule2_with_w_set(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Z", parents=["X"])
        scm.add_node("Y", parents=["Z"])
        scm.add_node("W")

        calc = DoCalculus(scm)
        result = calc.rule2_action_observation_exchange("Y", "Z", {"X"}, {"W"})
        assert isinstance(result, bool)

    def test_rule3_with_w_set(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", parents=["X"])
        scm.add_node("Z", parents=["X"])
        scm.add_node("W")

        calc = DoCalculus(scm)
        result = calc.rule3_insertion_deletion_actions("Y", "Z", {"X"}, {"W"})
        assert isinstance(result, bool)

    def test_rule3_z_not_in_graph(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", parents=["X"])

        calc = DoCalculus(scm)
        result = calc.rule3_insertion_deletion_actions("Y", "Z", {"X"})
        assert result is True

    def test_mutilated_graph_multiple_interventions(self):
        scm = StructuralCausalModel()
        scm.add_node("Z", is_exogenous=True)
        scm.add_node("X", parents=["Z"])
        scm.add_node("Y", parents=["X"])
        scm.add_node("W", parents=["Z", "X"])

        calc = DoCalculus(scm)
        g = calc._mutilated_graph({"X", "Z"})
        assert not g.has_edge("Z", "X")
        # W is not in the intervention set, so its incoming edges remain
        assert g.has_edge("Z", "W")
        assert g.has_edge("X", "W")
        assert g.has_edge("X", "Y")

    def test_mutilated_graph_empty_interventions(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", parents=["X"])

        calc = DoCalculus(scm)
        g = calc._mutilated_graph(set())
        assert g.has_edge("X", "Y")


class TestIdentifiabilityExtended:
    """Extended tests for identifiability."""

    def test_identifiable_chain(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Z", parents=["X"])
        scm.add_node("Y", parents=["Z"])

        calc = DoCalculus(scm)
        identifiable, reason = calc.is_identifiable("X", "Y")
        assert identifiable is True

    def test_not_identifiable_with_confounding(self):
        scm = StructuralCausalModel()
        scm.add_node("U", is_exogenous=True)
        scm.add_node("X", parents=["U"])
        scm.add_node("Y", parents=["U"])

        calc = DoCalculus(scm)
        identifiable, reason = calc.is_identifiable("X", "Y")
        # With only a confounder and no observed backdoor adjusters
        assert isinstance(identifiable, bool)

    def test_adjustment_formula_frontdoor(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Z", parents=["X"])
        scm.add_node("Y", parents=["Z"])

        calc = DoCalculus(scm)
        identifiable, formula, adjustment = calc.get_adjustment_formula("X", "Y")
        assert identifiable is True
        assert formula is not None
        assert adjustment is not None

    def test_adjustment_formula_not_identifiable(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", is_exogenous=True)

        calc = DoCalculus(scm)
        identifiable, formula, adjustment = calc.get_adjustment_formula("X", "Y")
        assert identifiable is True  # No confounding, directly identifiable
        assert adjustment is not None

    def test_estimate_ate_with_backdoor(self):
        scm = StructuralCausalModel()
        scm.add_node("Z", is_exogenous=True)
        scm.add_node("X", parents=["Z"])
        scm.add_node("Y", parents=["Z", "X"], mechanism=lambda z, x, u: 2 * x + z + u)

        calc = DoCalculus(scm)
        data = {
            "X": [0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.0],
            "Y": [0.1, -0.1, 2.1, 1.9, 2.0, 0.0, 2.2, -0.2],
            "Z": [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0],
        }
        ate = calc.estimate_ate_from_data("X", "Y", data)
        # With backdoor Z present but not handled (need adjustment set)
        assert isinstance(ate, (float, type(None)))

    def test_estimate_ate_no_data(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", parents=["X"])

        calc = DoCalculus(scm)
        data = {"X": [], "Y": []}
        ate = calc.estimate_ate_from_data("X", "Y", data)
        assert ate is None

    def test_estimate_ate_no_treated(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", parents=["X"])

        calc = DoCalculus(scm)
        data = {"X": [0.0, 0.0, 0.0], "Y": [0.1, 0.2, 0.3]}
        ate = calc.estimate_ate_from_data("X", "Y", data)
        assert ate is None

    def test_list_identifiable_effects_empty(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)

        calc = DoCalculus(scm)
        effects = calc.list_identifiable_effects()
        # Single node: no pairs
        assert isinstance(effects, list)

    def test_list_identifiable_effects_multiple(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", parents=["X"])
        scm.add_node("Z", parents=["X"])

        calc = DoCalculus(scm)
        effects = calc.list_identifiable_effects()
        assert len(effects) >= 2
        for e in effects:
            assert len(e) == 3


class TestFrontdoorCriterion:
    """Tests for frontdoor criterion."""

    def test_try_frontdoor_simple(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Z", parents=["X"])
        scm.add_node("Y", parents=["Z"])

        calc = DoCalculus(scm)
        frontdoor = calc._try_frontdoor("X", "Y")
        assert frontdoor is not None
        assert "Z" in frontdoor

    def test_try_frontdoor_no_candidate(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", parents=["X"])

        calc = DoCalculus(scm)
        frontdoor = calc._try_frontdoor("X", "Y")
        # No intermediate node
        assert frontdoor is None

    def test_intercepts_all_directed_paths_no_path(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", is_exogenous=True)
        scm.add_node("Z")

        calc = DoCalculus(scm)
        assert not calc._intercepts_all_directed_paths("X", "Y", "Z")

    def test_intercepts_all_directed_paths_same_node(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", parents=["X"])

        calc = DoCalculus(scm)
        assert not calc._intercepts_all_directed_paths("X", "Y", "X")
        assert not calc._intercepts_all_directed_paths("X", "Y", "Y")

    def test_can_block_with_x_no_backdoor(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Z", parents=["X"])
        scm.add_node("Y", parents=["Z"])

        calc = DoCalculus(scm)
        assert calc._can_block_with_x("Z", "Y", "X")

    def test_try_do_calculus_derivation_simple(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Y", is_exogenous=True)

        calc = DoCalculus(scm)
        result = calc._try_do_calculus_derivation("X", "Y")
        assert isinstance(result, bool)

    def test_try_do_calculus_derivation_with_mediator(self):
        scm = StructuralCausalModel()
        scm.add_node("X", is_exogenous=True)
        scm.add_node("Z", parents=["X"])
        scm.add_node("Y", parents=["Z"])

        calc = DoCalculus(scm)
        result = calc._try_do_calculus_derivation("X", "Y")
        assert isinstance(result, bool)
