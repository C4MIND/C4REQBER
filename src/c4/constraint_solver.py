# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


def _parse_dimension(dim_str: str) -> dict[str, int] | None:
    dim = {}
    i = 0
    s = dim_str.strip()
    while i < len(s):
        key = s[i]
        if not key.isalpha() or not key.isupper():
            return None
        i += 1
        exp_str = ""
        while i < len(s) and (s[i].isdigit() or s[i] in "+-⁻"):
            if s[i] == "⁻":
                exp_str += "-"
                i += 1
            elif s[i] in "¹²³⁴⁵⁶⁷⁸⁹⁰":
                sup_map = {"¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁰": "0"}
                exp_str += sup_map[s[i]]
                i += 1
            else:
                exp_str += s[i]
                i += 1
        dim[key] = int(exp_str) if exp_str else 1
    return dim


def _build_dimensional_matrix(
    parsed: list[dict[str, Any]], dimension_keys: list[str]
) -> tuple[Any, list[str]]:
    try:
        import numpy as np
    except ImportError:
        return None, []
    n_vars = len(parsed)
    n_dims = len(dimension_keys)
    mat = np.zeros((n_dims, n_vars))
    for j, p in enumerate(parsed):
        for i, dk in enumerate(dimension_keys):
            mat[i, j] = float(p["dims"].get(dk, 0))
    return mat, dimension_keys


class ConstraintSolver:
    """Find transformations that preserve specified invariants.

    Used for: Lorentz transformation (preserve c), gauge invariance,
    conformal mappings, Noether symmetry → conservation.
    """

    def __init__(self) -> None:
        self.dim_registry = DIMENSIONAL_REGISTRY

    def find_dimensionless_groups(
        self,
        variables: list[str],
    ) -> dict[str, Any]:
        """Find Buckingham π dimensionless groups from dimensional variables.

        Args:
            variables: list of "name:dimension" strings, e.g. ["v:LT⁻¹", "L:L", "t:T"]
        """
        parsed: list[dict[str, Any]] = []
        for v in variables:
            if ":" in v:
                name, dim_str = v.split(":", 1)
                dims = _parse_dimension(dim_str.strip())
                if dims is not None:
                    parsed.append({"name": name.strip(), "dims": dims})

        if not parsed:
            return {"error": "No valid dimensional variables", "groups": []}

        all_keys = sorted(set().union(*(p["dims"].keys() for p in parsed)))
        n_vars = len(parsed)
        n_dims = len(all_keys)

        if n_dims == 0:
            return {
                "variables": [p["name"] for p in parsed],
                "dimensions": [],
                "n_variables": n_vars,
                "n_dimensions": 0,
                "pi_groups": [p["name"] for p in parsed],
                "count": n_vars,
            }

        mat, _ = _build_dimensional_matrix(parsed, all_keys)

        if mat is None:
            logger.warning(
                "numpy not available — cannot compute π groups. Install numpy for Buckingham π-theorem."
            )
            return {
                "variables": [p["name"] for p in parsed],
                "dimensions": all_keys,
                "n_variables": n_vars,
                "n_dimensions": n_dims,
                "pi_groups": ["nyi: numpy required"],
                "count": 0,
                "error": "numpy_not_installed",
            }

        import numpy as np

        null_dim = n_vars - np.linalg.matrix_rank(mat)
        if null_dim <= 0:
            return {
                "variables": [p["name"] for p in parsed],
                "dimensions": all_keys,
                "n_variables": n_vars,
                "n_dimensions": n_dims,
                "pi_groups": [],
                "count": 0,
                "explanation": f"Rank of dimensional matrix = {n_vars - null_dim} ≥ {n_vars} variables → no dimensionless groups",
            }

        _, s, vt = np.linalg.svd(mat, full_matrices=True)
        tol = max(mat.shape) * np.finfo(mat.dtype).eps * max(s) if len(s) > 0 else 1e-10
        null_mask = s < tol
        null_vectors = vt[-null_dim:] if null_dim > 0 else np.zeros((0, n_vars))

        pi_groups: list[str] = []
        for row in null_vectors:
            coeffs = np.round(row / max(abs(row)) * 6).astype(int) if np.max(np.abs(row)) > 1e-10 else np.zeros_like(row)
            parts = []
            for j, coef in enumerate(coeffs):
                if coef != 0:
                    name = parsed[j]["name"]
                    formatted = f"{name}^{coef}" if abs(coef) != 1 else name
                    if coef == 1:
                        formatted = name
                    elif coef == -1:
                        formatted = f"{name}⁻¹"
                    elif coef < 0:
                        formatted = f"{name}^{coef}"
                    else:
                        formatted = f"{name}^{coef}"
                    parts.append(formatted)
            if parts:
                pi_groups.append("·".join(parts))

        return {
            "variables": [p["name"] for p in parsed],
            "dimensions": all_keys,
            "n_variables": n_vars,
            "n_dimensions": n_dims,
            "matrix_rank": int(np.linalg.matrix_rank(mat)),
            "pi_groups": pi_groups[:10],
            "count": len(pi_groups),
        }

    def find_invariant_transformations(
        self,
        invariant: str,
        domain: str = "",
    ) -> dict[str, Any]:
        """Find transformations that preserve a specified invariant.

        Args:
            invariant: e.g. "c", "E=mc²", "constant speed of light"
            domain: physics context
        """
        t = invariant.lower()

        # Lorentz: preserves c
        if "c" in t or "speed of light" in t or "light speed" in t:
            return {
                "invariant": invariant,
                "transformation": "Lorentz transformation",
                "group": "SO(3,1) — Lorentz group",
                "parameters": ["boost velocity v", "rotation angles θ, φ"],
                "preserves": ["speed of light c", "spacetime interval ds²", "Maxwell's equations"],
                "formula": "x' = γ(x - vt), t' = γ(t - vx/c²), γ = 1/√(1-v²/c²)",
            }

        # Galileo: preserves time
        if "time" in t or "absolute time" in t or "simultane" in t:
            return {
                "invariant": invariant,
                "transformation": "Galilean transformation",
                "group": "Galilean group",
                "parameters": ["relative velocity v"],
                "preserves": ["time intervals Δt", "spatial distances Δx", "mass m"],
                "formula": "x' = x - vt, t' = t",
            }

        # Conformal: preserves angles
        if "angle" in t or "conformal" in t:
            return {
                "invariant": invariant,
                "transformation": "Conformal transformation",
                "group": "SO(d,2) — conformal group",
                "parameters": ["translation a", "rotation R", "dilation λ", "special conformal b"],
                "preserves": ["angles", "causal structure", "null geodesics"],
                "formula": "x → (x + a|x|²)/(1 + 2a·x + |a|²|x|²)",
            }

        # Gauge: preserves Lagrangian
        if "gauge" in t or "phase" in t or "lagrangian" in t:
            return {
                "invariant": invariant,
                "transformation": "Gauge transformation",
                "group": "U(1) — gauge group",
                "parameters": ["phase α(x)"],
                "preserves": ["Lagrangian L", "equations of motion", "observables"],
                "formula": "ψ → e^{iα}ψ, A_μ → A_μ + ∂_μα",
            }

        # Scale invariance
        if "scale" in t or "self-similar" in t:
            return {
                "invariant": invariant,
                "transformation": "Scale transformation",
                "group": "Dilation group",
                "parameters": ["scale factor λ"],
                "preserves": ["dimensionless ratios", "angles", "power-law exponents"],
                "formula": "x → λx, t → λ^z t (with dynamical exponent z)",
            }

        return {
            "invariant": invariant,
            "transformation": f"Unknown — '{invariant}' not recognized in known transformation groups",
            "groups_checked": ["Lorentz SO(3,1)", "Galilean", "Conformal SO(d,2)", "Gauge U(1)", "Scale/Dilation"],
        }


DIMENSIONAL_REGISTRY: dict[str, str] = {
    "mass": "M", "length": "L", "time": "T", "temperature": "Θ",
    "current": "I", "amount": "N", "luminous": "J",
    "velocity": "LT⁻¹", "acceleration": "LT⁻²",
    "force": "MLT⁻²", "energy": "ML²T⁻²", "power": "ML²T⁻³",
    "pressure": "ML⁻¹T⁻²", "density": "ML⁻³",
    "frequency": "T⁻¹", "angular_velocity": "T⁻¹",
    "momentum": "MLT⁻¹", "impulse": "MLT⁻¹",
    "torque": "ML²T⁻²", "angular_momentum": "ML²T⁻¹",
    "viscosity": "ML⁻¹T⁻¹", "surface_tension": "MT⁻²",
    "electric_charge": "IT", "voltage": "ML²T⁻³I⁻¹",
    "resistance": "ML²T⁻³I⁻²", "capacitance": "M⁻¹L⁻²T⁴I²",
    "inductance": "ML²T⁻²I⁻²",
    "magnetic_flux": "ML²T⁻²I⁻¹", "magnetic_field": "MT⁻²I⁻¹",
}


__all__ = ["ConstraintSolver"]
