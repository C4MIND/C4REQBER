"""
Stock-Flow DSL for System Dynamics.

Provides a domain-specific language for defining system dynamics models
(stocks, flows, auxiliaries) and compiling them to ODE systems solvable
via RK4 and adaptive integration.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Callable

import numpy as np
from numpy.typing import NDArray


# ---------------------------------------------------------------------------
# Domain classes
# ---------------------------------------------------------------------------


@dataclass
class Stock:
    """A stock (state variable) that accumulates over time."""

    name: str
    initial: float = 0.0
    unit: str = ""
    min_value: float | None = None
    max_value: float | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Stock name must be non-empty")


@dataclass
class Flow:
    """A flow that changes the level of a stock."""

    name: str
    rate_fn: Callable[..., float]
    source: str | None = None  # stock name or None (cloud)
    sink: str | None = None    # stock name or None (cloud)
    unit: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Flow name must be non-empty")
        if self.source is None and self.sink is None:
            raise ValueError("Flow must connect at least one stock")


@dataclass
class Auxiliary:
    """An auxiliary variable (converter / intermediate)."""

    name: str
    value_fn: Callable[..., float]
    unit: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Auxiliary name must be non-empty")


# ---------------------------------------------------------------------------
# DSL container
# ---------------------------------------------------------------------------


class SystemSpec:
    """Container for a stock-and-flow model specification."""

    def __init__(self, name: str = "model") -> None:
        self.name = name
        self.stocks: dict[str, Stock] = {}
        self.flows: dict[str, Flow] = {}
        self.auxiliaries: dict[str, Auxiliary] = {}
        self._stock_order: list[str] = []

    # -- DSL builder methods ------------------------------------------------

    def add_stock(
        self,
        name: str,
        initial: float = 0.0,
        unit: str = "",
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> SystemSpec:
        """Add stock."""
        if name in self.stocks:
            raise ValueError(f"Stock '{name}' already defined")
        s = Stock(name, initial, unit, min_value, max_value)
        self.stocks[name] = s
        self._stock_order.append(name)
        return self

    def add_flow(
        self,
        name: str,
        rate_fn: Callable[..., float],
        source: str | None = None,
        sink: str | None = None,
        unit: str = "",
    ) -> SystemSpec:
        """Add flow."""
        if name in self.flows:
            raise ValueError(f"Flow '{name}' already defined")
        if source is not None and source not in self.stocks:
            raise ValueError(f"Source stock '{source}' not found")
        if sink is not None and sink not in self.stocks:
            raise ValueError(f"Sink stock '{sink}' not found")
        self.flows[name] = Flow(name, rate_fn, source, sink, unit)
        return self

    def add_auxiliary(
        self, name: str, value_fn: Callable[..., float], unit: str = ""
    ) -> SystemSpec:
        """Add auxiliary."""
        if name in self.auxiliaries:
            raise ValueError(f"Auxiliary '{name}' already defined")
        self.auxiliaries[name] = Auxiliary(name, value_fn, unit)
        return self

    # -- helpers ------------------------------------------------------------

    def initial_state(self) -> NDArray[np.float64]:
        return np.array(
            [self.stocks[s].initial for s in self._stock_order],
            dtype=np.float64,
        )

    def state_dict(self, y: NDArray[np.float64]) -> dict[str, float]:
        return {name: float(y[i]) for i, name in enumerate(self._stock_order)}


# ---------------------------------------------------------------------------
# Compilation to ODE system
# ---------------------------------------------------------------------------


class CompiledSystem:
    """Compiled ODE system from a SystemSpec."""

    def __init__(self, spec: SystemSpec) -> None:
        self.spec = spec
        self._order = spec._stock_order[:]
        self._flow_indices: dict[str, tuple[int | None, int | None]] = {}
        for fl in spec.flows.values():
            src_idx = self._order.index(fl.source) if fl.source is not None else None
            dst_idx = self._order.index(fl.sink) if fl.sink is not None else None
            self._flow_indices[fl.name] = (src_idx, dst_idx)

    def _build_context(
        self, t: float, y: NDArray[np.float64]
    ) -> dict[str, float]:
        ctx: dict[str, float] = {"t": float(t)}
        ctx.update(self.spec.state_dict(y))
        # evaluate auxiliaries (single-pass; no dependency ordering)
        for aux in self.spec.auxiliaries.values():
            ctx[aux.name] = _safe_call(aux.value_fn, ctx)
        return ctx

    def derivs(
        self, t: float, y: NDArray[np.float64]
    ) -> NDArray[np.float64]:
        """Derivs."""
        ctx = self._build_context(t, y)
        dydt = np.zeros(len(self._order), dtype=np.float64)
        for fl in self.spec.flows.values():
            rate = _safe_call(fl.rate_fn, ctx)
            src_idx, dst_idx = self._flow_indices[fl.name]
            if src_idx is not None:
                dydt[src_idx] -= rate
            if dst_idx is not None:
                dydt[dst_idx] += rate
        # enforce hard bounds
        for i, name in enumerate(self._order):
            stock = self.spec.stocks[name]
            if stock.min_value is not None and y[i] <= stock.min_value and dydt[i] < 0:
                dydt[i] = 0.0
            if stock.max_value is not None and y[i] >= stock.max_value and dydt[i] > 0:
                dydt[i] = 0.0
        return dydt


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


def rk4_step(
    f: Callable[[float, NDArray[np.float64]], NDArray[np.float64]],
    t: float,
    y: NDArray[np.float64],
    h: float,
) -> NDArray[np.float64]:
    """Single RK4 step."""
    k1 = f(t, y)
    k2 = f(t + h * 0.5, y + h * 0.5 * k1)
    k3 = f(t + h * 0.5, y + h * 0.5 * k2)
    k4 = f(t + h, y + h * k3)
    return y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)  # type: ignore[no-any-return]


def rk4_integrate(
    compiled: CompiledSystem,
    t_span: tuple[float, float],
    n_steps: int = 100,
    y0: NDArray[np.float64] | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Fixed-step RK4 integration.

    Returns
    -------
    t : NDArray, shape (n_steps+1,)
    y : NDArray, shape (n_steps+1, n_stocks)
    """
    t0, tf = t_span
    if n_steps <= 0:
        y0 = y0 if y0 is not None else compiled.spec.initial_state()
        return np.array([t0]), y0.reshape(1, -1)
    h = (tf - t0) / n_steps
    y0 = y0 if y0 is not None else compiled.spec.initial_state()
    t_vals = np.linspace(t0, tf, n_steps + 1)
    y_vals = np.zeros((n_steps + 1, len(y0)), dtype=np.float64)
    y_vals[0] = y0
    for i in range(n_steps):
        y_vals[i + 1] = rk4_step(compiled.derivs, t_vals[i], y_vals[i], h)
    return t_vals, y_vals


def adaptive_rk45_step(
    f: Callable[[float, NDArray[np.float64]], NDArray[np.float64]],
    t: float,
    y: NDArray[np.float64],
    h: float,
    atol: float = 1e-6,
    rtol: float = 1e-3,
) -> tuple[NDArray[np.float64], float, float]:
    """Single adaptive RK4(5) step (Dormand-Prince coefficients simplified).

    Returns (y_next, h_new, error_estimate).
    """
    # Dormand-Prince Butcher tableau (simplified)
    a2, a3, a4, a5, a6 = 1 / 5, 3 / 10, 4 / 5, 8 / 9, 1.0
    b21 = 1 / 5
    b31, b32 = 3 / 40, 9 / 40
    b41, b42, b43 = 44 / 45, -56 / 15, 32 / 9
    b51, b52, b53, b54 = 19372 / 6561, -25360 / 2187, 64448 / 6561, -212 / 729
    b61, b62, b63, b64, b65 = 9017 / 3168, -355 / 33, 46732 / 5247, 49 / 176, -5103 / 18656
    c1, c3, c4, c5, c6 = 35 / 384, 500 / 1113, 125 / 192, -2187 / 6784, 11 / 84
    # 5th-order weights (for error estimation)
    e1, e3, e4, e5, e6, e7 = (
        71 / 57600,
        -71 / 16695,
        71 / 1920,
        -17253 / 339200,
        22 / 525,
        -1 / 40,
    )

    k1 = f(t, y)
    k2 = f(t + a2 * h, y + h * (b21 * k1))
    k3 = f(t + a3 * h, y + h * (b31 * k1 + b32 * k2))
    k4 = f(t + a4 * h, y + h * (b41 * k1 + b42 * k2 + b43 * k3))
    k5 = f(t + a5 * h, y + h * (b51 * k1 + b52 * k2 + b53 * k3 + b54 * k4))
    k6 = f(t + a6 * h, y + h * (b61 * k1 + b62 * k2 + b63 * k3 + b64 * k4 + b65 * k5))
    y4 = y + h * (c1 * k1 + c3 * k3 + c4 * k4 + c5 * k5 + c6 * k6)
    k7 = f(t + h, y4)
    error = h * np.abs(
        e1 * k1 + e3 * k3 + e4 * k4 + e5 * k5 + e6 * k6 + e7 * k7
    )
    scale = atol + rtol * np.maximum(np.abs(y), np.abs(y4))
    err_norm = np.sqrt(np.mean((error / scale) ** 2))
    if err_norm == 0.0:
        h_new = h * 2.0
    else:
        h_new = h * min(2.0, max(0.5, 0.9 * err_norm ** -0.2))
    return y4, h_new, float(err_norm)


def adaptive_integrate(
    compiled: CompiledSystem,
    t_span: tuple[float, float],
    y0: NDArray[np.float64] | None = None,
    h0: float = 0.01,
    atol: float = 1e-6,
    rtol: float = 1e-3,
    max_steps: int = 10000,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Adaptive RK45 integration with dense output points."""
    t0, tf = t_span
    if tf < t0:
        # Reverse integration not supported; return initial state at t0
        y = y0 if y0 is not None else compiled.spec.initial_state()
        return np.array([t0]), y.reshape(1, -1)
    y = y0 if y0 is not None else compiled.spec.initial_state()
    h = h0
    t_list: list[float] = [t0]
    y_list: list[NDArray[np.float64]] = [y.copy()]
    t = t0
    for _ in range(max_steps):
        if t >= tf:
            break
        if t + h > tf:
            h = tf - t
        y_next, h_new, err = adaptive_rk45_step(
            compiled.derivs, t, y, h, atol, rtol
        )
        if err > 1.0:
            h = h_new
            continue
        t += h
        y = y_next
        t_list.append(t)
        y_list.append(y.copy())
        h = min(h_new, tf - t) if t < tf else h_new
    return np.array(t_list), np.stack(y_list)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _safe_call(fn: Callable[..., float], ctx: dict[str, float]) -> float:
    """Call *fn* passing only the kwargs it accepts from *ctx*."""
    sig = inspect.signature(fn)
    kwargs = {p: ctx[p] for p in sig.parameters if p in ctx}
    missing = [p for p in sig.parameters if p not in ctx]
    if missing:
        raise KeyError(f"Missing required arguments: {missing}")
    return float(fn(**kwargs))


# ---------------------------------------------------------------------------
# __init__ exports
# ---------------------------------------------------------------------------

__all__ = [
    "Stock",
    "Flow",
    "Auxiliary",
    "SystemSpec",
    "CompiledSystem",
    "rk4_step",
    "rk4_integrate",
    "adaptive_rk45_step",
    "adaptive_integrate",
]
