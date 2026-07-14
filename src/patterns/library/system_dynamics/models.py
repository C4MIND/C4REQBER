"""
Model building for System Dynamics simulation
"""

import logging
from collections.abc import Callable
from typing import Any

import numpy as np

from src.utils.safe_eval import SafeExpressionEvaluator

from .types import Flow, Stock


def build_logistic_model(stocks: dict[str, Stock], params: dict[str, Any]) -> list[Flow]:
    """Build logistic growth model"""
    return [
        Flow(
            name="growth",
            source=None,
            sink="population",
            rate_expression=f"{params.get('growth_rate', 0.1)} * population * (1 - population / {params.get('carrying_capacity', 1000)})",
        ),
        Flow(
            name="death",
            source="population",
            sink=None,
            rate_expression=f"{params.get('death_rate', 0.05)} * population",
        ),
    ]

def build_predator_prey_model(stocks: dict[str, Stock], params: dict[str, Any]) -> list[Flow]:
    """Build Lotka-Volterra predator-prey model"""
    flows = [
        Flow(
            name="prey_growth",
            source=None,
            sink="prey",
            rate_expression=f"{params.get('prey_growth', 1.0)} * prey",
        ),
        Flow(
            name="predation",
            source="prey",
            sink=None,
            rate_expression=f"{params.get('predation_rate', 0.1)} * prey * predators",
        ),
        Flow(
            name="predator_growth",
            source=None,
            sink="predators",
            rate_expression=f"{params.get('conversion_efficiency', 0.075)} * {params.get('predation_rate', 0.1)} * prey * predators",
        ),
        Flow(
            name="predator_death",
            source="predators",
            sink=None,
            rate_expression=f"{params.get('predator_death', 0.5)} * predators",
        ),
    ]

    # Add stocks if not present
    if "prey" not in stocks:
        stocks["prey"] = Stock(name="prey", initial_value=params.get("prey_initial", 100.0))
    if "predators" not in stocks:
        stocks["predators"] = Stock(name="predators", initial_value=params.get("predator_initial", 10.0))

    return flows

def build_epidemic_model(stocks: dict[str, Stock], params: dict[str, Any]) -> list[Flow]:
    """Build SIR epidemic model"""
    # Ensure SIR stocks exist
    if "susceptible" not in stocks:
        stocks["susceptible"] = Stock(name="susceptible", initial_value=params.get("S0", 990.0))
    if "infected" not in stocks:
        stocks["infected"] = Stock(name="infected", initial_value=params.get("I0", 10.0))
    if "recovered" not in stocks:
        stocks["recovered"] = Stock(name="recovered", initial_value=params.get("R0", 0.0))

    total = sum(s.initial_value for s in stocks.values())

    return [
        Flow(
            name="infection",
            source="susceptible",
            sink="infected",
            rate_expression=f"{params.get('beta', 0.3)} * susceptible * infected / {total}",
        ),
        Flow(
            name="recovery",
            source="infected",
            sink="recovered",
            rate_expression=f"{params.get('gamma', 0.1)} * infected",
        ),
    ]

def build_custom_model(stocks: dict[str, Stock], params: dict[str, Any]) -> list[Flow]:
    """Build custom model from explicit flow definitions"""
    flows = []
    flow_defs = params.get("flows", [])
    for flow_def in flow_defs:
        flows.append(Flow(
            name=flow_def["name"],
            source=flow_def.get("source"),
            sink=flow_def.get("sink"),
            rate_expression=flow_def["expression"],
        ))
    return flows

def build_generic_model(stocks: dict[str, Stock], params: dict[str, Any]) -> list[Flow]:
    """Build generic two-stock model with feedback"""
    if len(stocks) >= 2:
        stock_names = list(stocks.keys())
        return [
            Flow(
                name="flow_1",
                source=None,
                sink=stock_names[0],
                rate_expression=f"{params.get('inflow_rate', 1.0)} - 0.01 * {stock_names[0]}",
            ),
            Flow(
                name="flow_2",
                source=stock_names[0],
                sink=stock_names[1],
                rate_expression=f"{params.get('transfer_rate', 0.1)} * {stock_names[0]}",
            ),
            Flow(
                name="outflow",
                source=stock_names[1],
                sink=None,
                rate_expression=f"{params.get('outflow_rate', 0.05)} * {stock_names[1]}",
            ),
        ]
    return []

def create_ode_function(stocks: dict[str, Stock], flows: list[Flow]) -> Callable[..., Any]:
    """Create ODE function from stocks and flows"""
    stock_names = list(stocks.keys())

    def ode_func(t: float, y: np.ndarray) -> np.ndarray:
        # Create state dict[str, Any]
        """Ode func."""
        state = {name: y[i] for i, name in enumerate(stock_names)}

        # Calculate flows
        flow_values = {}
        for flow in flows:
            try:
                local_vars = {**state, "t": t, "np": np}
                evaluator = SafeExpressionEvaluator(local_vars)
                flow_values[flow.name] = evaluator.evaluate(flow.rate_expression)
            except (ValueError, SyntaxError, ZeroDivisionError) as e:
                logger = logging.getLogger(__name__)
                logger.debug("Failed to evaluate flow expression '%s': %s", flow.rate_expression, e)
                flow_values[flow.name] = 0.0

        # Calculate derivatives (net flow into each stock)
        dydt = np.zeros(len(stock_names))
        for i, name in enumerate(stock_names):
            for flow in flows:
                if flow.sink == name:
                    dydt[i] += flow_values[flow.name]
                if flow.source == name:
                    dydt[i] -= flow_values[flow.name]

        return dydt

    return ode_func
