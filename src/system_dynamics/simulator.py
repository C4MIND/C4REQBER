"""
System Dynamics simulation engine.

Runs SFModel instances using fixed-step Euler integration with
expression evaluation. Uses the existing stock_flow.py RK4 integrator
when compiled specs are available.
"""
from __future__ import annotations

import logging
import math
from collections.abc import Callable
from typing import Any

import numpy as np
from numpy.typing import NDArray

from src.utils.safe_eval import SafeExpressionEvaluator

from .models import SFModel


def _build_eval_context(
    model: SFModel,
    stock_values: dict[str, float],
    t: float,
) -> dict[str, float]:
    ctx: dict[str, float] = {"t": t}
    ctx.update(stock_values)
    for var in model.variables:
        ctx[var.name] = _safe_eval_expression(var.expression, ctx)
    return ctx

def _safe_eval_expression(expression: str, ctx: dict[str, float]) -> float:
    allowed: dict[str, Any] = {}
    allowed.update({"sin": math.sin, "cos": math.cos, "tan": math.tan,
                     "exp": math.exp, "log": math.log, "sqrt": math.sqrt,
                     "abs": abs, "pi": math.pi, "e": math.e,
                     "max": max, "min": min, "pow": pow})
    allowed.update(ctx)
    try:
        evaluator = SafeExpressionEvaluator(allowed)
        result = evaluator.evaluate(expression)
        return float(result)
    except (ValueError, TypeError, SyntaxError) as e:
        logger = logging.getLogger(__name__)
        logger.debug("Failed to evaluate expression '%s': %s", expression, e)
        return 0.0

def simulate_euler(
    model: SFModel,
    n_steps: int = 100,
) -> tuple[NDArray[np.float64], dict[str, NDArray[np.float64]]]:
    """Simulate euler."""
    dt = (model.end_time - model.start_time) / n_steps
    t_arr = np.linspace(model.start_time, model.end_time, n_steps + 1)

    state: dict[str, list[float]] = {}
    for s in model.stocks:
        state[s.name] = [s.initial]

    for i in range(n_steps):
        t = t_arr[i]
        current = {name: vals[-1] for name, vals in state.items()}
        ctx = _build_eval_context(model, current, t)

        flows_dict: dict[str, tuple[str, str, float]] = {}
        for fl in model.flows:
            rate = _safe_eval_expression(fl.expression, ctx)
            flows_dict[fl.name] = (fl.source, fl.target, rate)

        deltas: dict[str, float] = {s.name: 0.0 for s in model.stocks}
        for _, (source, target, rate) in flows_dict.items():
            if source in deltas:
                deltas[source] -= rate * dt
            if target in deltas:
                deltas[target] += rate * dt

        for s in model.stocks:
            state[s.name].append(current[s.name] + deltas[s.name])

    result: dict[str, NDArray[np.float64]] = {}
    for name, vals in state.items():
        result[name] = np.array(vals, dtype=np.float64)

    return t_arr, result

def simulate_rk4(
    model: SFModel,
    n_steps: int = 200,
) -> tuple[NDArray[np.float64], dict[str, NDArray[np.float64]]]:
    try:
        from .stock_flow import CompiledSystem, SystemSpec, rk4_integrate
        spec = model_to_system_spec(model)
        compiled = CompiledSystem(spec)
        t, y = rk4_integrate(compiled, t_span=(model.start_time, model.end_time), n_steps=n_steps)
        result: dict[str, NDArray[np.float64]] = {}
        for i, s in enumerate(spec._stock_order):
            result[s] = y[:, i]
        return t, result
    except (ImportError, AttributeError, TypeError):
        return simulate_euler(model, n_steps=n_steps)

def model_to_system_spec(model: SFModel) -> Any:
    """Model to system spec."""
    from .stock_flow import SystemSpec

    spec = SystemSpec(name=model.name)

    for s in model.stocks:
        spec.add_stock(s.name, initial=s.initial, unit=s.unit)

    for var in model.variables:
        spec.add_auxiliary(
            var.name,
            _make_aux_fn(var.expression, model),
        )

    for fl in model.flows:
        spec.add_flow(
            fl.name,
            _make_flow_fn(fl.expression, model),
            source=fl.source if fl.source != "Stock" else None,
            sink=fl.target if fl.target != "Stock" else None,
        )

    return spec

def _make_aux_fn(expression: str, model: SFModel) -> Callable[..., float]:
    param_names = [var.name for var in model.variables]
    stock_names = [s.name for s in model.stocks]

    def aux_fn(**kwargs: float) -> float:
        """Aux fn."""
        ctx: dict[str, float] = {}
        ctx.update(kwargs)
        for p in param_names:
            if p in ctx:
                var = model.get_variable(p)
                val = _safe_eval_expression(var.expression, ctx) if var else ctx[p]
                ctx[p] = val
        return _safe_eval_expression(expression, ctx)

    import inspect
    from inspect import Parameter
    params = [Parameter(name=n, kind=Parameter.KEYWORD_ONLY) for n in stock_names]
    aux_fn.__signature__ = inspect.Signature(params)  # type: ignore[attr-defined]
    return aux_fn

def _make_flow_fn(expression: str, model: SFModel) -> Callable[..., float]:
    stock_names = [s.name for s in model.stocks]
    var_names = [v.name for v in model.variables]

    def flow_fn(**kwargs: float) -> float:
        """Flow fn."""
        ctx: dict[str, float] = {}
        ctx.update(kwargs)
        for vn in var_names:
            v = model.get_variable(vn)
            if v:
                ctx[vn] = _safe_eval_expression(v.expression, ctx)
        return _safe_eval_expression(expression, ctx)

    import inspect
    from inspect import Parameter
    params = [Parameter(name=n, kind=Parameter.KEYWORD_ONLY) for n in stock_names]
    flow_fn.__signature__ = inspect.Signature(params)  # type: ignore[attr-defined]
    return flow_fn

__all__ = [
    "simulate_euler",
    "simulate_rk4",
    "model_to_system_spec",
]
