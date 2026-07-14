"""Bridge: Maps QZRF strategies -> Fractal27 paradigms -> UTA operations.

Example:
    QZRF "Branching" -> Fractal27 "delta∘iota" (perspective differentiation)
                      -> UTA ["Separate", "Scan", "Focus"]
"""
from __future__ import annotations

from typing import Any

from src.operators.uta import UTALibrary, UTAOperator


# Mapping tables
QZRF_TO_FRACTAL27: dict[str, list[str]] = {
    "QZ-01": ["delta", "iota", "tau_plus"],      # Branching -> separate + invert + forward
    "QZ-02": ["rho", "shift"],                    # Annealing -> pattern + shift
    "QZ-03": ["sigma", "lambda_plus"],            # Synthesis -> connect + compress
    "QZ-04": ["delta", "kappa_minus"],            # Pruning -> separate + attenuate
    "QZ-05": ["tau_plus", "phi"],                 # Propagation -> forward + adapt
    "QZ-06": ["mu", "kappa_plus"],                # Meta-optimization -> reflect + amplify
    "QZ-07": ["lambda_minus", "tau_minus"],       # Crystallization -> expand + backward
    "QZ-08": ["rho", "tau_plus", "sigma"],        # Pattern completion -> pattern + forward + connect
    "QZ-09": ["iota", "phi", "shift"],            # Perspective inversion -> invert + adapt + shift
    "QZ-10": ["kappa_plus", "kappa_minus", "mu"], # Agency balance -> amplify + attenuate + reflect
    "QZ-11": ["lambda_plus", "lambda_minus"],     # Compression cycle -> compress + expand
    "QZ-12": ["sigma", "delta", "mu"],            # Structural analysis -> connect + separate + reflect
    "QZ-13": ["tau_plus", "tau_minus", "cycle"],  # Oscillation -> forward + backward + cycle
    "QZ-14": ["phi", "mu", "kappa_plus"],         # Emergence -> adapt + reflect + amplify
}

FRACTAL27_TO_UTA: dict[str, list[str]] = {
    "tau+": ["scan", "track"],
    "tau-": ["detect", "focus"],
    "sigma": ["connect", "layer"],
    "delta": ["separate", "parse"],
    "rho": ["detect", "focus"],
    "iota": ["shift", "parse"],  # shift perspective, then decompose
    "lambda+": ["compress", "filter"],  # compress to essence
    "lambda-": ["expand", "crystallize"],  # expand to concrete
    "kappa+": ["amplify", "channel"],  # expand agency
    "kappa-": ["attenuate", "block"],  # contract agency
    "mu": ["track", "tune"],  # meta-reflection
    "phi": ["tune", "shift"],  # context adaptation
    "shift": ["shift", "focus"],
    "cycle": ["cycle", "pulse"],
}


def resolve_qzrf_to_utas(qzrf_id: str) -> list[str]:
    """Resolve a QZRF strategy ID to a list of UTA operator names."""
    fractal_keys = QZRF_TO_FRACTAL27.get(qzrf_id, [])
    uta_names: list[str] = []
    for key in fractal_keys:
        uta_names.extend(FRACTAL27_TO_UTA.get(key, []))
    return uta_names


def resolve_qzrf_to_operators(qzrf_id: str, library: UTALibrary | None = None) -> list[UTAOperator]:
    """Resolve a QZRF strategy ID to actual UTAOperator objects."""
    lib = library or UTALibrary()
    names = resolve_qzrf_to_utas(qzrf_id)
    operators: list[UTAOperator] = []
    seen: set[str] = set()
    for name in names:
        op = lib.get(name)
        if op and op.name not in seen:
            operators.append(op)
            seen.add(op.name)
    return operators


def apply_qzrf(qzrf_id: str, context: dict[str, Any], library: UTALibrary | None = None) -> dict[str, Any]:
    """Apply the UTA sequence corresponding to a QZRF strategy to a context."""
    lib = library or UTALibrary()
    names = resolve_qzrf_to_utas(qzrf_id)
    return lib.apply_sequence(names, context)


def get_uta_by_fractal(fractal_key: str, library: UTALibrary | None = None) -> list[UTAOperator]:
    """Get UTA operators mapped from a Fractal27 paradigm key."""
    lib = library or UTALibrary()
    names = FRACTAL27_TO_UTA.get(fractal_key, [])
    return [op for name in names if (op := lib.get(name)) is not None]
