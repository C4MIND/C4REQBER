"""Runtime budgets and evidence thresholds for discovery pipelines."""

from __future__ import annotations

import os


def _positive_number(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def simulation_timeout_seconds() -> float:
    """Maximum wall time for the simulation phase."""
    return _positive_number("C4_SIMULATION_TIMEOUT_SECONDS", 60.0)


def minimum_discovery_papers() -> int:
    """Minimum evidence floor before a discovery may be claimed."""
    return max(1, int(_positive_number("C4_MIN_DISCOVERY_PAPERS", 5.0)))


def minimum_paradigm_shift_papers() -> int:
    """Higher evidence floor used for paradigm-shift claims."""
    return max(
        minimum_discovery_papers(),
        int(_positive_number("C4_MIN_PARADIGM_SHIFT_PAPERS", 20.0)),
    )
