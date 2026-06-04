"""
Comprehensive tests for src/system_dynamics/stock_flow.py

Covers:
- Stock dataclass (init, defaults, validation)
- Flow dataclass (init, defaults, validation)
- Auxiliary dataclass (init, defaults, validation)
- SystemSpec (DSL builder, validation, helpers)
- CompiledSystem (context building, derivatives, bounds)
- rk4_step (single step accuracy)
- rk4_integrate (fixed-step integration)
- adaptive_rk45_step (step size adaptation)
- adaptive_integrate (adaptive integration)
- _safe_call (kwargs filtering)
- Edge cases: empty names, duplicate names, missing stocks, min/max bounds,
  zero-step integration, single stock, cloud-to-cloud flow rejection
"""
from __future__ import annotations

import numpy as np
import pytest

from src.system_dynamics.stock_flow import (
    Auxiliary,
    CompiledSystem,
    Flow,
    Stock,
    SystemSpec,
    _safe_call,
    adaptive_integrate,
    adaptive_rk45_step,
    rk4_integrate,
    rk4_step,
)


# ═══════════════════════════════════════════════════════════════════
# Stock
# ═══════════════════════════════════════════════════════════════════


class TestStock:
    def test_default_init(self):
        s = Stock(name="population")
        assert s.name == "population"
        assert s.initial == 0.0
        assert s.unit == ""
        assert s.min_value is None
        assert s.max_value is None

    def test_custom_init(self):
        s = Stock(name="tank", initial=100.0, unit="L", min_value=0.0, max_value=500.0)
        assert s.initial == 100.0
        assert s.unit == "L"
        assert s.min_value == 0.0
        assert s.max_value == 500.0

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            Stock(name="")

    def test_whitespace_name_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            Stock(name="   ")


# ═══════════════════════════════════════════════════════════════════
# Flow
# ═══════════════════════════════════════════════════════════════════


class TestFlow:
    def test_default_init(self):
        f = Flow(name="inflow", rate_fn=lambda t, x: 1.0, source="tank")
        assert f.name == "inflow"
        assert f.source == "tank"
        assert f.sink is None
        assert f.unit == ""

    def test_custom_init(self):
        f = Flow(
            name="drain",
            rate_fn=lambda t, x: 0.5,
            source="tank",
            sink="sewer",
            unit="L/min",
        )
        assert f.source == "tank"
        assert f.sink == "sewer"
        assert f.unit == "L/min"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            Flow(name="", rate_fn=lambda: 0.0)

    def test_both_none_raises(self):
        with pytest.raises(ValueError, match="at least one stock"):
            Flow(name="cloud", rate_fn=lambda: 0.0, source=None, sink=None)

    def test_source_only_ok(self):
        f = Flow(name="outflow", rate_fn=lambda: 0.0, source="tank", sink=None)
        assert f.source == "tank"
        assert f.sink is None

    def test_sink_only_ok(self):
        f = Flow(name="inflow", rate_fn=lambda: 0.0, source=None, sink="tank")
        assert f.source is None
        assert f.sink == "tank"


# ═══════════════════════════════════════════════════════════════════
# Auxiliary
# ═══════════════════════════════════════════════════════════════════


class TestAuxiliary:
    def test_default_init(self):
        a = Auxiliary(name="pressure", value_fn=lambda t: 1.0)
        assert a.name == "pressure"
        assert a.unit == ""

    def test_custom_init(self):
        a = Auxiliary(name="temp", value_fn=lambda t: 300.0, unit="K")
        assert a.unit == "K"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            Auxiliary(name="", value_fn=lambda: 0.0)


# ═══════════════════════════════════════════════════════════════════
# SystemSpec — DSL builder
# ═══════════════════════════════════════════════════════════════════


class TestSystemSpec:
    def test_default_init(self):
        spec = SystemSpec()
        assert spec.name == "model"
        assert spec.stocks == {}
        assert spec.flows == {}
        assert spec.auxiliaries == {}

    def test_custom_name(self):
        spec = SystemSpec(name="predator_prey")
        assert spec.name == "predator_prey"

    # -- add_stock -------------------------------------------------

    def test_add_stock(self):
        spec = SystemSpec()
        result = spec.add_stock("x", initial=10.0, unit="units")
        assert result is spec  # fluent API
        assert "x" in spec.stocks
        assert spec.stocks["x"].initial == 10.0
        assert spec._stock_order == ["x"]

    def test_add_stock_duplicate_raises(self):
        spec = SystemSpec().add_stock("x")
        with pytest.raises(ValueError, match="already defined"):
            spec.add_stock("x")

    def test_add_stock_multiple(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=1.0)
        spec.add_stock("b", initial=2.0)
        assert spec._stock_order == ["a", "b"]

    # -- add_flow --------------------------------------------------

    def test_add_flow(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=1.0)
        spec.add_stock("b", initial=2.0)
        result = spec.add_flow("f", lambda a, b: 0.1, source="a", sink="b")
        assert result is spec
        assert "f" in spec.flows
        assert spec.flows["f"].source == "a"
        assert spec.flows["f"].sink == "b"

    def test_add_flow_duplicate_raises(self):
        spec = SystemSpec().add_stock("a").add_flow("f", lambda a: 0.0, sink="a")
        with pytest.raises(ValueError, match="already defined"):
            spec.add_flow("f", lambda a: 0.0, sink="a")

    def test_add_flow_missing_source_raises(self):
        spec = SystemSpec().add_stock("a")
        with pytest.raises(ValueError, match="Source stock"):
            spec.add_flow("f", lambda: 0.0, source="missing", sink="a")

    def test_add_flow_missing_sink_raises(self):
        spec = SystemSpec().add_stock("a")
        with pytest.raises(ValueError, match="Sink stock"):
            spec.add_flow("f", lambda: 0.0, source="a", sink="missing")

    def test_add_flow_cloud_source(self):
        spec = SystemSpec().add_stock("a")
        spec.add_flow("in", lambda: 1.0, source=None, sink="a")
        assert spec.flows["in"].source is None

    def test_add_flow_cloud_sink(self):
        spec = SystemSpec().add_stock("a")
        spec.add_flow("out", lambda a: 0.1, source="a", sink=None)
        assert spec.flows["out"].sink is None

    # -- add_auxiliary ---------------------------------------------

    def test_add_auxiliary(self):
        spec = SystemSpec()
        result = spec.add_auxiliary("aux", lambda t: t * 2)
        assert result is spec
        assert "aux" in spec.auxiliaries

    def test_add_auxiliary_duplicate_raises(self):
        spec = SystemSpec().add_auxiliary("aux", lambda: 0.0)
        with pytest.raises(ValueError, match="already defined"):
            spec.add_auxiliary("aux", lambda: 0.0)

    # -- helpers ---------------------------------------------------

    def test_initial_state(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=1.0)
        spec.add_stock("b", initial=2.5)
        y0 = spec.initial_state()
        assert isinstance(y0, np.ndarray)
        assert y0.dtype == np.float64
        np.testing.assert_array_equal(y0, np.array([1.0, 2.5]))

    def test_initial_state_empty(self):
        spec = SystemSpec()
        y0 = spec.initial_state()
        assert y0.shape == (0,)

    def test_state_dict(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=0.0)
        spec.add_stock("b", initial=0.0)
        d = spec.state_dict(np.array([3.0, 4.0]))
        assert d == {"a": 3.0, "b": 4.0}

    def test_state_dict_empty(self):
        spec = SystemSpec()
        assert spec.state_dict(np.array([])) == {}


# ═══════════════════════════════════════════════════════════════════
# CompiledSystem
# ═══════════════════════════════════════════════════════════════════


class TestCompiledSystem:
    def test_init(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=1.0)
        spec.add_flow("f", lambda a: 0.1, source="a", sink=None)
        cs = CompiledSystem(spec)
        assert cs.spec is spec
        assert cs._order == ["a"]
        assert cs._flow_indices == {"f": (0, None)}

    def test_build_context(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=1.0)
        spec.add_auxiliary("double", lambda a: a * 2)
        cs = CompiledSystem(spec)
        ctx = cs._build_context(t=5.0, y=np.array([3.0]))
        assert ctx["t"] == 5.0
        assert ctx["a"] == 3.0
        assert ctx["double"] == 6.0

    def test_build_context_no_aux(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=1.0)
        cs = CompiledSystem(spec)
        ctx = cs._build_context(t=0.0, y=np.array([2.0]))
        assert ctx == {"t": 0.0, "a": 2.0}

    def test_derivs_simple_decay(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=10.0)
        spec.add_flow("decay", lambda a: 0.5 * a, source="a", sink=None)
        cs = CompiledSystem(spec)
        dydt = cs.derivs(t=0.0, y=np.array([10.0]))
        np.testing.assert_allclose(dydt, np.array([-5.0]))

    def test_derivs_inflow_only(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=0.0)
        spec.add_flow("in", lambda: 2.0, source=None, sink="a")
        cs = CompiledSystem(spec)
        dydt = cs.derivs(t=0.0, y=np.array([0.0]))
        np.testing.assert_allclose(dydt, np.array([2.0]))

    def test_derivs_two_stocks(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=10.0)
        spec.add_stock("b", initial=0.0)
        spec.add_flow("transfer", lambda a: 0.1 * a, source="a", sink="b")
        cs = CompiledSystem(spec)
        dydt = cs.derivs(t=0.0, y=np.array([10.0, 0.0]))
        np.testing.assert_allclose(dydt, np.array([-1.0, 1.0]))

    def test_derivs_with_auxiliary(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=10.0)
        spec.add_auxiliary("rate", lambda a: 0.2 * a)
        spec.add_flow("out", lambda rate: rate, source="a", sink=None)
        cs = CompiledSystem(spec)
        dydt = cs.derivs(t=0.0, y=np.array([10.0]))
        np.testing.assert_allclose(dydt, np.array([-2.0]))

    # -- bounds ----------------------------------------------------

    def test_min_value_blocks_decrease(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=0.0, min_value=0.0)
        spec.add_flow("drain", lambda: 1.0, source="a", sink=None)
        cs = CompiledSystem(spec)
        dydt = cs.derivs(t=0.0, y=np.array([0.0]))
        np.testing.assert_allclose(dydt, np.array([0.0]))

    def test_min_value_allows_increase(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=0.0, min_value=0.0)
        spec.add_flow("fill", lambda: 1.0, source=None, sink="a")
        cs = CompiledSystem(spec)
        dydt = cs.derivs(t=0.0, y=np.array([0.0]))
        np.testing.assert_allclose(dydt, np.array([1.0]))

    def test_max_value_blocks_increase(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=100.0, max_value=100.0)
        spec.add_flow("fill", lambda: 1.0, source=None, sink="a")
        cs = CompiledSystem(spec)
        dydt = cs.derivs(t=0.0, y=np.array([100.0]))
        np.testing.assert_allclose(dydt, np.array([0.0]))

    def test_max_value_allows_decrease(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=100.0, max_value=100.0)
        spec.add_flow("drain", lambda: 1.0, source="a", sink=None)
        cs = CompiledSystem(spec)
        dydt = cs.derivs(t=0.0, y=np.array([100.0]))
        np.testing.assert_allclose(dydt, np.array([-1.0]))

    def test_bounds_exactly_at_boundary(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=5.0, min_value=5.0, max_value=5.0)
        spec.add_flow("in", lambda: 1.0, source=None, sink="a")
        spec.add_flow("out", lambda: 1.0, source="a", sink=None)
        cs = CompiledSystem(spec)
        dydt = cs.derivs(t=0.0, y=np.array([5.0]))
        np.testing.assert_allclose(dydt, np.array([0.0]))

    def test_bounds_below_min(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=5.0, min_value=10.0)
        spec.add_flow("drain", lambda: 1.0, source="a", sink=None)
        cs = CompiledSystem(spec)
        dydt = cs.derivs(t=0.0, y=np.array([5.0]))
        np.testing.assert_allclose(dydt, np.array([0.0]))

    def test_bounds_above_max(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=15.0, max_value=10.0)
        spec.add_flow("fill", lambda: 1.0, source=None, sink="a")
        cs = CompiledSystem(spec)
        dydt = cs.derivs(t=0.0, y=np.array([15.0]))
        np.testing.assert_allclose(dydt, np.array([0.0]))


# ═══════════════════════════════════════════════════════════════════
# RK4 step
# ═══════════════════════════════════════════════════════════════════


class TestRK4Step:
    def test_constant_zero(self):
        f = lambda t, y: np.zeros_like(y)
        y0 = np.array([1.0, 2.0])
        y1 = rk4_step(f, t=0.0, y=y0, h=0.1)
        np.testing.assert_allclose(y1, y0)

    def test_linear_growth(self):
        f = lambda t, y: np.ones_like(y)
        y0 = np.array([0.0])
        y1 = rk4_step(f, t=0.0, y=y0, h=1.0)
        np.testing.assert_allclose(y1, np.array([1.0]), rtol=1e-10)

    def test_exponential_approx(self):
        f = lambda t, y: y
        y0 = np.array([1.0])
        y1 = rk4_step(f, t=0.0, y=y0, h=0.1)
        expected = np.exp(0.1)
        assert y1[0] == pytest.approx(expected, rel=1e-4)

    def test_multidimensional(self):
        f = lambda t, y: np.array([y[1], -y[0]])
        y0 = np.array([1.0, 0.0])
        y1 = rk4_step(f, t=0.0, y=y0, h=0.01)
        assert y1.shape == (2,)

    def test_small_step(self):
        f = lambda t, y: y
        y0 = np.array([1.0])
        y1 = rk4_step(f, t=0.0, y=y0, h=1e-6)
        assert y1[0] == pytest.approx(1.000001, rel=1e-8)


# ═══════════════════════════════════════════════════════════════════
# RK4 integrate
# ═══════════════════════════════════════════════════════════════════


class TestRK4Integrate:
    def test_exponential_growth(self):
        spec = SystemSpec()
        spec.add_stock("x", initial=1.0)
        spec.add_flow("growth", lambda x: x, source=None, sink="x")
        compiled = CompiledSystem(spec)
        t, y = rk4_integrate(compiled, t_span=(0.0, 1.0), n_steps=1000)
        assert t[0] == 0.0
        assert t[-1] == 1.0
        assert len(t) == 1001
        assert y[-1, 0] == pytest.approx(np.exp(1.0), rel=1e-6)

    def test_custom_y0(self):
        spec = SystemSpec()
        spec.add_stock("x", initial=1.0)
        spec.add_flow("growth", lambda x: 0.0, source=None, sink="x")
        compiled = CompiledSystem(spec)
        t, y = rk4_integrate(compiled, t_span=(0.0, 1.0), y0=np.array([5.0]), n_steps=10)
        assert y[0, 0] == 5.0
        np.testing.assert_allclose(y[-1], np.array([5.0]))

    def test_default_y0(self):
        spec = SystemSpec()
        spec.add_stock("x", initial=3.0)
        spec.add_flow("growth", lambda x: 0.0, source=None, sink="x")
        compiled = CompiledSystem(spec)
        t, y = rk4_integrate(compiled, t_span=(0.0, 1.0), n_steps=10)
        assert y[0, 0] == 3.0

    def test_zero_steps(self):
        spec = SystemSpec()
        spec.add_stock("x", initial=1.0)
        spec.add_flow("growth", lambda x: 0.0, source=None, sink="x")
        compiled = CompiledSystem(spec)
        t, y = rk4_integrate(compiled, t_span=(0.0, 0.0), n_steps=0)
        assert len(t) == 1
        assert t[0] == 0.0
        assert y[0, 0] == 1.0

    def test_negative_t_span(self):
        spec = SystemSpec()
        spec.add_stock("x", initial=1.0)
        spec.add_flow("decay", lambda x: x, source="x", sink=None)
        compiled = CompiledSystem(spec)
        # Negative t_span is not supported; expect graceful handling
        t, y = rk4_integrate(compiled, t_span=(1.0, 0.0), n_steps=100)
        assert t[0] == 1.0
        # With n_steps > 0, it integrates forward from 1.0 to 0.0 with negative step
        # This is edge-case behavior; just verify it returns arrays
        assert len(t) == 101
        assert y.shape == (101, 1)

    def test_multidimensional(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=1.0)
        spec.add_stock("b", initial=0.0)
        spec.add_flow("transfer", lambda a: a, source="a", sink="b")
        compiled = CompiledSystem(spec)
        t, y = rk4_integrate(compiled, t_span=(0.0, 1.0), n_steps=100)
        assert y.shape == (101, 2)
        assert y[-1, 0] + y[-1, 1] == pytest.approx(1.0, rel=1e-6)


# ═══════════════════════════════════════════════════════════════════
# Adaptive RK45 step
# ═══════════════════════════════════════════════════════════════════


class TestAdaptiveRK45Step:
    def test_constant_zero(self):
        f = lambda t, y: np.zeros_like(y)
        y0 = np.array([1.0])
        y_next, h_new, err = adaptive_rk45_step(f, t=0.0, y=y0, h=0.1)
        np.testing.assert_allclose(y_next, y0)
        assert err == 0.0
        assert h_new == 0.2

    def test_linear_growth(self):
        f = lambda t, y: np.ones_like(y)
        y0 = np.array([0.0])
        y_next, h_new, err = adaptive_rk45_step(f, t=0.0, y=y0, h=1.0)
        np.testing.assert_allclose(y_next, np.array([1.0]), rtol=1e-10)
        assert err < 1e-10

    def test_exponential_small_step(self):
        f = lambda t, y: y
        y0 = np.array([1.0])
        y_next, h_new, err = adaptive_rk45_step(f, t=0.0, y=y0, h=0.01)
        expected = np.exp(0.01)
        assert y_next[0] == pytest.approx(expected, rel=1e-6)
        assert err < 1.0
        assert h_new > 0.0

    def test_error_estimate_positive(self):
        f = lambda t, y: y
        y0 = np.array([1.0])
        y_next, h_new, err = adaptive_rk45_step(f, t=0.0, y=y0, h=1.0)
        assert err > 0.0
        assert 0.5 <= h_new <= 2.0

    def test_multidimensional(self):
        f = lambda t, y: np.array([y[1], -y[0]])
        y0 = np.array([1.0, 0.0])
        y_next, h_new, err = adaptive_rk45_step(f, t=0.0, y=y0, h=0.1)
        assert y_next.shape == (2,)
        assert h_new > 0.0

    def test_atol_rtol_effect(self):
        f = lambda t, y: y
        y0 = np.array([1.0])
        _, _, err_loose = adaptive_rk45_step(f, t=0.0, y=y0, h=0.5, atol=1e-2, rtol=1e-2)
        _, _, err_strict = adaptive_rk45_step(f, t=0.0, y=y0, h=0.5, atol=1e-10, rtol=1e-10)
        assert err_loose < err_strict


# ═══════════════════════════════════════════════════════════════════
# Adaptive integrate
# ═══════════════════════════════════════════════════════════════════


class TestAdaptiveIntegrate:
    def test_exponential_growth(self):
        spec = SystemSpec()
        spec.add_stock("x", initial=1.0)
        spec.add_flow("growth", lambda x: x, source=None, sink="x")
        compiled = CompiledSystem(spec)
        t, y = adaptive_integrate(compiled, t_span=(0.0, 1.0), h0=0.01)
        assert t[0] == 0.0
        assert t[-1] == pytest.approx(1.0, abs=1e-6)
        assert y[-1, 0] == pytest.approx(np.exp(1.0), rel=1e-4)

    def test_custom_y0(self):
        spec = SystemSpec()
        spec.add_stock("x", initial=1.0)
        spec.add_flow("growth", lambda x: 0.0, source=None, sink="x")
        compiled = CompiledSystem(spec)
        t, y = adaptive_integrate(compiled, t_span=(0.0, 1.0), y0=np.array([5.0]), h0=0.1)
        assert y[0, 0] == 5.0
        np.testing.assert_allclose(y[-1], np.array([5.0]), atol=1e-10)

    def test_default_y0(self):
        spec = SystemSpec()
        spec.add_stock("x", initial=3.0)
        spec.add_flow("growth", lambda x: 0.0, source=None, sink="x")
        compiled = CompiledSystem(spec)
        t, y = adaptive_integrate(compiled, t_span=(0.0, 1.0), h0=0.1)
        assert y[0, 0] == 3.0

    def test_zero_span(self):
        spec = SystemSpec()
        spec.add_stock("x", initial=1.0)
        spec.add_flow("growth", lambda x: 0.0, source=None, sink="x")
        compiled = CompiledSystem(spec)
        t, y = adaptive_integrate(compiled, t_span=(0.0, 0.0), h0=0.1)
        assert len(t) == 1
        assert t[0] == 0.0

    def test_negative_span(self):
        spec = SystemSpec()
        spec.add_stock("x", initial=1.0)
        spec.add_flow("decay", lambda x: x, source="x", sink=None)
        compiled = CompiledSystem(spec)
        # Negative t_span is not supported; expect graceful handling (return initial state)
        t, y = adaptive_integrate(compiled, t_span=(1.0, 0.0), h0=0.01)
        assert t[0] == 1.0
        assert len(t) == 1
        assert y[0, 0] == 1.0

    def test_max_steps_limit(self):
        spec = SystemSpec()
        spec.add_stock("x", initial=1.0)
        spec.add_flow("growth", lambda x: x, source=None, sink="x")
        compiled = CompiledSystem(spec)
        t, y = adaptive_integrate(compiled, t_span=(0.0, 10.0), h0=0.001, max_steps=50)
        assert len(t) <= 52  # initial + at most max_steps accepted + some rejected

    def test_multidimensional(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=1.0)
        spec.add_stock("b", initial=0.0)
        spec.add_flow("transfer", lambda a: a, source="a", sink="b")
        compiled = CompiledSystem(spec)
        t, y = adaptive_integrate(compiled, t_span=(0.0, 1.0), h0=0.01)
        assert y[-1, 0] + y[-1, 1] == pytest.approx(1.0, rel=1e-4)

    def test_with_bounds(self):
        spec = SystemSpec()
        spec.add_stock("x", initial=0.0, min_value=0.0)
        spec.add_flow("drain", lambda: 1.0, source="x", sink=None)
        compiled = CompiledSystem(spec)
        t, y = adaptive_integrate(compiled, t_span=(0.0, 1.0), h0=0.01)
        assert np.all(y[:, 0] >= -1e-12)  # allow tiny numerical under


# ═══════════════════════════════════════════════════════════════════
# _safe_call
# ═══════════════════════════════════════════════════════════════════


class TestSafeCall:
    def test_passes_matching_kwargs(self):
        def fn(a, b):
            return a + b

        assert _safe_call(fn, {"a": 1, "b": 2, "c": 3}) == 3.0

    def test_ignores_extra_kwargs(self):
        def fn(x):
            return x * 2

        assert _safe_call(fn, {"x": 5, "y": 10}) == 10.0

    def test_no_kwargs(self):
        def fn():
            return 42.0

        assert _safe_call(fn, {"a": 1}) == 42.0

    def test_missing_kwargs_raises(self):
        def fn(a, b):
            return a + b

        with pytest.raises(KeyError):
            _safe_call(fn, {"a": 1})

    def test_returns_float(self):
        def fn(x):
            return x

        result = _safe_call(fn, {"x": 5})
        assert isinstance(result, float)
        assert result == 5.0

    def test_with_t_kwarg(self):
        def fn(t):
            return t * 2

        assert _safe_call(fn, {"t": 3.0}) == 6.0


# ═══════════════════════════════════════════════════════════════════
# Integration / end-to-end
# ═══════════════════════════════════════════════════════════════════


class TestEndToEnd:
    def test_predator_prey_rk4(self):
        spec = SystemSpec(name="lotka_volterra")
        spec.add_stock("prey", initial=10.0)
        spec.add_stock("predator", initial=5.0)
        spec.add_flow(
            "prey_growth",
            lambda prey: 1.1 * prey,
            source=None,
            sink="prey",
        )
        spec.add_flow(
            "predation",
            lambda prey, predator: 0.4 * prey * predator,
            source="prey",
            sink="predator",
        )
        spec.add_flow(
            "predator_death",
            lambda predator: 0.4 * predator,
            source="predator",
            sink=None,
        )
        compiled = CompiledSystem(spec)
        t, y = rk4_integrate(compiled, t_span=(0.0, 10.0), n_steps=2000)
        assert y.shape == (2001, 2)
        total = y[:, 0] + y[:, 1]
        assert np.std(total) > 0.0  # dynamics are non-trivial

    def test_predator_prey_adaptive(self):
        spec = SystemSpec(name="lotka_volterra")
        spec.add_stock("prey", initial=10.0)
        spec.add_stock("predator", initial=5.0)
        spec.add_flow(
            "prey_growth",
            lambda prey: 1.1 * prey,
            source=None,
            sink="prey",
        )
        spec.add_flow(
            "predation",
            lambda prey, predator: 0.4 * prey * predator,
            source="prey",
            sink="predator",
        )
        spec.add_flow(
            "predator_death",
            lambda predator: 0.4 * predator,
            source="predator",
            sink=None,
        )
        compiled = CompiledSystem(spec)
        t, y = adaptive_integrate(compiled, t_span=(0.0, 10.0), h0=0.01)
        assert y.shape[1] == 2

    def test_conservation_rk4(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=10.0)
        spec.add_stock("b", initial=0.0)
        spec.add_flow("transfer", lambda a: 0.5 * a, source="a", sink="b")
        compiled = CompiledSystem(spec)
        t, y = rk4_integrate(compiled, t_span=(0.0, 5.0), n_steps=500)
        total = y[:, 0] + y[:, 1]
        np.testing.assert_allclose(total, np.full_like(total, 10.0), rtol=1e-6)

    def test_conservation_adaptive(self):
        spec = SystemSpec()
        spec.add_stock("a", initial=10.0)
        spec.add_stock("b", initial=0.0)
        spec.add_flow("transfer", lambda a: 0.5 * a, source="a", sink="b")
        compiled = CompiledSystem(spec)
        t, y = adaptive_integrate(compiled, t_span=(0.0, 5.0), h0=0.01)
        total = y[:, 0] + y[:, 1]
        np.testing.assert_allclose(total, np.full_like(total, 10.0), rtol=1e-4)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
