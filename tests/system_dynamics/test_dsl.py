"""
Comprehensive tests for System Dynamics Stock-Flow DSL.

Covers:
- models.py: Stock, Flow, Variable, Link, SFModel dataclasses
- dsl.py: DSL parsing, tokenization, round-trip dsl_to_string
- simulator.py: Euler and RK4 simulation
- visualizer.py: ASCII renderer, DOT renderer, loop detection
- dsl_archetypes.py: DSL archetype strings
"""
from __future__ import annotations

import numpy as np
import pytest

from src.system_dynamics.dsl import dsl_to_string, parse_dsl
from src.system_dynamics.dsl_archetypes import DSL_ARCHETYPES
from src.system_dynamics.models import Flow, Link, SFModel, Stock, Variable
from src.system_dynamics.simulator import simulate_euler, simulate_rk4
from src.system_dynamics.visualizer import detect_loops, render_ascii, render_dot


# ═══════════════════════════════════════════════════════════════════
# DSL Models
# ═══════════════════════════════════════════════════════════════════


class TestDSLStock:
    def test_default_init(self):
        s = Stock(name="population")
        assert s.name == "population"
        assert s.initial == 0.0
        assert s.unit == "units"

    def test_custom_init(self):
        s = Stock(name="tank", initial=100.0, unit="L")
        assert s.initial == 100.0
        assert s.unit == "L"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            Stock(name="")

    def test_whitespace_name_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            Stock(name="   ")


class TestDSLFlow:
    def test_default_init(self):
        f = Flow(name="inflow", source="tank", target="sewer", expression="0.1 * tank")
        assert f.name == "inflow"
        assert f.source == "tank"
        assert f.target == "sewer"
        assert f.expression == "0.1 * tank"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            Flow(name="", source="a", target="b", expression="0")

    def test_cloud_source(self):
        f = Flow(name="rain", source="Stock", target="reservoir", expression="5.0")
        assert f.source == "Stock"


class TestDSLVariable:
    def test_default_init(self):
        v = Variable(name="rate", expression="Population / 1000")
        assert v.name == "rate"
        assert v.expression == "Population / 1000"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            Variable(name="", expression="x")


class TestDSLLink:
    def test_default_init(self):
        l = Link(source="A", target="B", polarity="+")
        assert l.source == "A"
        assert l.target == "B"
        assert l.polarity == "+"

    def test_negative_polarity(self):
        l = Link(source="A", target="B", polarity="-")
        assert l.polarity == "-"

    def test_invalid_polarity_raises(self):
        with pytest.raises(ValueError, match="Polarity"):
            Link(source="A", target="B", polarity="x")


class TestSFModel:
    def test_default_init(self):
        m = SFModel(name="test")
        assert m.name == "test"
        assert m.stocks == []
        assert m.flows == []
        assert m.start_time == 0.0
        assert m.end_time == 10.0
        assert m.dt == 0.1

    def test_get_stock(self):
        m = SFModel(name="test")
        m.stocks.append(Stock(name="pop", initial=100.0))
        assert m.get_stock("pop") is not None
        assert m.get_stock("missing") is None

    def test_get_variable(self):
        m = SFModel(name="test")
        m.variables.append(Variable(name="rate", expression="0.1"))
        assert m.get_variable("rate") is not None
        assert m.get_variable("missing") is None

    def test_validate_valid(self):
        m = SFModel(name="test")
        m.stocks.append(Stock(name="pop", initial=100.0))
        m.flows.append(Flow(name="grow", source="Stock", target="pop", expression="0.1"))
        assert m.validate() == []

    def test_validate_missing_stock(self):
        m = SFModel(name="test")
        m.flows.append(Flow(name="grow", source="unknown", target="unknown2", expression="0.1"))
        errors = m.validate()
        assert len(errors) == 2
        assert "unknown" in errors[0]


# ═══════════════════════════════════════════════════════════════════
# DSL Parser
# ═══════════════════════════════════════════════════════════════════


class TestDSLParser:
    def test_parse_empty(self):
        m = parse_dsl("")
        assert m.name == "parsed"
        assert len(m.stocks) == 0

    def test_parse_single_stock(self):
        m = parse_dsl("STOCK Pop 100.0 people")
        assert len(m.stocks) == 1
        assert m.stocks[0].name == "Pop"
        assert m.stocks[0].initial == 100.0
        assert m.stocks[0].unit == "people"

    def test_parse_stock_defaults(self):
        m = parse_dsl("STOCK X")
        assert m.stocks[0].initial == 0.0
        assert m.stocks[0].unit == "units"

    def test_parse_flow(self):
        m = parse_dsl("""
STOCK A 10
STOCK B 0
FLOW F A B "0.1 * A"
""")
        assert len(m.flows) == 1
        assert m.flows[0].name == "F"
        assert m.flows[0].source == "A"
        assert m.flows[0].target == "B"
        assert m.flows[0].expression == "0.1 * A"

    def test_parse_param(self):
        m = parse_dsl("PARAM rate 0.1")
        assert len(m.variables) == 1
        assert m.variables[0].name == "rate"
        assert m.variables[0].expression == "0.1"

    def test_parse_link(self):
        m = parse_dsl("""
STOCK A 10
STOCK B 0
LINK A B +
""")
        assert len(m.links) == 1
        assert m.links[0].source == "A"
        assert m.links[0].target == "B"
        assert m.links[0].polarity == "+"

    def test_parse_link_negative(self):
        m = parse_dsl("STOCK A 10\nSTOCK B 0\nLINK A B -")
        assert m.links[0].polarity == "-"

    def test_parse_time(self):
        m = parse_dsl("TIME 5 25")
        assert m.start_time == 5.0
        assert m.end_time == 25.0

    def test_parse_comment(self):
        m = parse_dsl("# This is a comment\nSTOCK X 10\n# Another comment")
        assert len(m.stocks) == 1
        assert m.stocks[0].name == "X"

    def test_parse_full_model(self):
        dsl = """
STOCK Population 100 people
STOCK Food 500 tons
FLOW Birth Stock Population "0.05 * Population"
FLOW Death Population Stock "0.02 * Population"
FLOW Harvest Food Stock "0.1 * Population"
PARAM growth_rate 0.05
LINK Population Food +
TIME 0 100
"""
        m = parse_dsl(dsl)
        assert len(m.stocks) == 2
        assert len(m.flows) == 3
        assert len(m.variables) == 1
        assert len(m.links) == 1
        assert m.start_time == 0.0
        assert m.end_time == 100.0

    def test_round_trip(self):
        dsl = """
STOCK A 10 u
STOCK B 0 u
FLOW F A B "0.1 * A"
PARAM k 0.5
TIME 0 20
"""
        m1 = parse_dsl(dsl)
        regenerated = dsl_to_string(m1)
        m2 = parse_dsl(regenerated)
        assert len(m2.stocks) == 2
        assert len(m2.flows) == 1
        assert len(m2.variables) == 1

    def test_parse_invalid_stock_initial(self):
        with pytest.raises(ValueError, match="invalid initial"):
            parse_dsl("STOCK X abc")

    def test_parse_invalid_time(self):
        with pytest.raises(ValueError, match="invalid time"):
            parse_dsl("TIME abc def")


# ═══════════════════════════════════════════════════════════════════
# Simulator
# ═══════════════════════════════════════════════════════════════════


class TestSimulateEuler:
    def test_constant_model(self):
        dsl = """
STOCK X 10
FLOW Zero Stock X "0"
TIME 0 10
"""
        model = parse_dsl(dsl)
        t, y_dict = simulate_euler(model, n_steps=50)
        assert len(t) == 51
        assert y_dict["X"][0] == 10.0
        assert y_dict["X"][-1] == 10.0

    def test_linear_growth(self):
        dsl = """
STOCK X 0
FLOW Grow Stock X "2"
TIME 0 5
"""
        model = parse_dsl(dsl)
        t, y_dict = simulate_euler(model, n_steps=100)
        expected = 10.0  # 2 * 5
        assert y_dict["X"][-1] == pytest.approx(expected, abs=0.2)

    def test_decay(self):
        dsl = """
STOCK X 100
FLOW Decay X Stock "0.1 * X"
TIME 0 10
"""
        model = parse_dsl(dsl)
        t, y_dict = simulate_euler(model, n_steps=200)
        assert y_dict["X"][-1] < y_dict["X"][0]

    def test_two_stocks_transfer(self):
        dsl = """
STOCK A 100
STOCK B 0
FLOW Transfer A B "0.1 * A"
TIME 0 5
"""
        model = parse_dsl(dsl)
        t, y_dict = simulate_euler(model, n_steps=100)
        total = np.array(y_dict["A"]) + np.array(y_dict["B"])
        np.testing.assert_allclose(total, np.full_like(total, 100.0), rtol=1e-2)

    def test_with_param(self):
        dsl = """
STOCK X 0
PARAM k 3.0
FLOW Grow Stock X "k"
TIME 0 5
"""
        model = parse_dsl(dsl)
        t, y_dict = simulate_euler(model, n_steps=100)
        assert y_dict["X"][-1] == pytest.approx(15.0, abs=0.2)


class TestSimulateRK4:
    def test_rk4_constant(self):
        dsl = """
STOCK X 10
FLOW Zero Stock X "0"
TIME 0 10
"""
        model = parse_dsl(dsl)
        t, y_dict = simulate_rk4(model, n_steps=50)
        assert y_dict["X"][0] == 10.0
        assert y_dict["X"][-1] == 10.0

    def test_rk4_exponential(self):
        dsl = """
STOCK Y 1
FLOW Grow Stock Y "Y"
TIME 0 1
"""
        model = parse_dsl(dsl)
        t, y_dict = simulate_rk4(model, n_steps=200)
        assert y_dict["Y"][-1] == pytest.approx(np.exp(1.0), rel=1e-4)


# ═══════════════════════════════════════════════════════════════════
# Visualizer
# ═══════════════════════════════════════════════════════════════════


class TestVisualizer:
    def test_render_ascii(self):
        dsl = """
STOCK A 10 u
STOCK B 5 u
FLOW Transfer A B "0.1 * A"
LINK A B +
TIME 0 20
"""
        model = parse_dsl(dsl)
        result = render_ascii(model)
        assert "CLD:" in result
        assert "[A]" in result
        assert "[B]" in result
        assert "Transfer" in result
        assert "T =" in result

    def test_render_dot(self):
        dsl = """
STOCK A 10 u
STOCK B 0 u
FLOW F A B "0.5 * A"
LINK A B +
TIME 0 10
"""
        model = parse_dsl(dsl)
        dot = render_dot(model)
        assert "digraph" in dot
        assert '"A"' in dot
        assert '"B"' in dot
        assert 'label="S"' in dot or 'label=" S"' in dot
        assert 'style=dashed' in dot

    def test_render_dot_horizontal(self):
        dsl = "STOCK A 10\nTIME 0 10"
        model = parse_dsl(dsl)
        dot = render_dot(model, horizontal=True)
        assert 'rankdir=LR' in dot

    def test_detect_loops_reinforcing(self):
        dsl = """
STOCK A 10
STOCK B 10
LINK A B +
LINK B A +
TIME 0 10
"""
        model = parse_dsl(dsl)
        loops = detect_loops(model)
        assert len(loops) >= 1
        _, is_balancing = loops[0]
        assert not is_balancing

    def test_detect_loops_balancing(self):
        dsl = """
STOCK A 10
STOCK B 10
LINK A B +
LINK B A -
TIME 0 10
"""
        model = parse_dsl(dsl)
        loops = detect_loops(model)
        assert len(loops) >= 1
        _, is_balancing = loops[0]
        assert is_balancing

    def test_detect_loops_empty(self):
        dsl = "STOCK A 10\nTIME 0 10"
        model = parse_dsl(dsl)
        loops = detect_loops(model)
        assert loops == []


# ═══════════════════════════════════════════════════════════════════
# DSL Archetypes
# ═══════════════════════════════════════════════════════════════════


class TestDSLArchetypes:
    def test_all_defined(self):
        assert len(DSL_ARCHETYPES) == 5
        for name in ["limits_to_growth", "shifting_the_burden",
                     "tragedy_of_commons", "escalation", "fixes_that_fail"]:
            assert name in DSL_ARCHETYPES

    def test_parse_all_archetypes(self):
        for name, dsl in DSL_ARCHETYPES.items():
            model = parse_dsl(dsl)
            assert len(model.stocks) > 0, f"Archetype '{name}' has no stocks"
            assert len(model.flows) > 0, f"Archetype '{name}' has no flows"

    def test_simulate_limits_to_growth(self):
        dsl = DSL_ARCHETYPES["limits_to_growth"]
        model = parse_dsl(dsl)
        t, y_dict = simulate_euler(model, n_steps=200)
        assert y_dict["Population"][0] == 100.0
        pop = np.array(y_dict["Population"])
        assert pop[-1] > pop[0]

    def test_simulate_shifting_the_burden(self):
        dsl = DSL_ARCHETYPES["shifting_the_burden"]
        model = parse_dsl(dsl)
        t, y_dict = simulate_euler(model, n_steps=200)
        symptoms = np.array(y_dict["ProblemSymptoms"])
        assert symptoms[-1] < symptoms[0]

    def test_simulate_tragedy_of_commons(self):
        dsl = DSL_ARCHETYPES["tragedy_of_commons"]
        model = parse_dsl(dsl)
        t, y_dict = simulate_euler(model, n_steps=200)
        resource = np.array(y_dict["Resource"])
        assert resource[-1] < resource[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
