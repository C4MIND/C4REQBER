"""
ODE solver and simulation runner for System Dynamics
"""

from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

from .models import create_ode_function
from .types import Flow, Stock, SystemDynamicsConfig


async def run_simulation(
    config: SystemDynamicsConfig,
    stocks: dict[str, Stock],
    flows: list[Flow],
    events_detected: list[dict[str, Any]],
) -> Any:
    """Run the ODE simulation"""
    ode_func = create_ode_function(stocks, flows)

    # Initial conditions
    y0 = np.array([s.initial_value for s in stocks.values()])
    stock_names = list(stocks.keys())

    # Time span
    t_span = (config.t_start, config.t_end)
    t_eval = np.arange(config.t_start, config.t_end + config.dt, config.dt)

    # Event detection
    events = []
    if config.detect_events and config.threshold_crossings:
        for threshold in config.threshold_crossings:
            def make_event(th: Any) -> Any:
                """Make event."""
                def event(t: Any, y: Any) -> Any:
                    return np.max(y) - th
                event.terminal = False  # type: ignore[attr-defined]
                event.direction = 0  # type: ignore[attr-defined]
                return event
            events.append(make_event(threshold))

    # Run solver
    solution = solve_ivp(
        ode_func,
        t_span,
        y0,
        method=config.solver,
        t_eval=t_eval,
        dense_output=True,
        events=events if events else None,
        max_step=config.dt * 10,
    )

    # Record events
    events_detected.clear()
    if hasattr(solution, 'events') and solution.events is not None:
        for i, event_times in enumerate(solution.events):
            if event_times is not None:
                for t in event_times:
                    events_detected.append({
                        "time": float(t),
                        "type": "threshold_crossing",
                        "threshold_index": i,
                    })

    return solution, stock_names
