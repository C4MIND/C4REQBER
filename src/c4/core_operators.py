"""
C4 Core Operators — The 6 period-3 generators.

These are the formally proven operators from the Agda verification:
    formal-proofs/c4-comp-v5.agda

Operators:
    tau+   (T̂)   — cyclic shift +1 along Time axis
    tau-   (T̂⁻¹) — cyclic shift -1 along Time axis
    lambda+ (Ŝ)  — cyclic shift +1 along Scale axis
    lambda- (Ŝ⁻¹)— cyclic shift -1 along Scale axis
    kappa+  (Â)  — cyclic shift +1 along Agency axis
    kappa-  (Â⁻¹)— cyclic shift -1 along Agency axis

Properties (verified in Agda):
    - Period 3: tau³ = lambda³ = kappa³ = id
    - Commutative: [T̂, Ŝ] = [T̂, Â] = [Ŝ, Â] = 0
    - Independence: each operator affects only its own axis

Label: FORMALLY PROVEN IN AGDA
"""
from __future__ import annotations

from typing import Callable

from .types import C4State


# Core operator functions
CORE_OPERATORS: dict[str, Callable[[C4State], C4State]] = {
    "tau+": lambda s: s.shift_time(1),
    "tau-": lambda s: s.shift_time(-1),
    "lambda+": lambda s: s.shift_scale(1),
    "lambda-": lambda s: s.shift_scale(-1),
    "kappa+": lambda s: s.shift_agency(1),
    "kappa-": lambda s: s.shift_agency(-1),
}


def apply_core_operator(name: str, state: C4State) -> C4State:
    """Apply a named core operator to a state."""
    if name not in CORE_OPERATORS:
        raise ValueError(f"Unknown core operator: {name}")
    return CORE_OPERATORS[name](state)


def verify_period_3(state: C4State) -> dict[str, bool]:
    """Verify tau³ = lambda³ = kappa³ = id for a given state."""
    results = {}
    for name, op in CORE_OPERATORS.items():
        if name.endswith("+"):
            # Apply forward operator 3 times
            s = state
            for _ in range(3):
                s = op(s)
            results[name] = s == state
    return results
