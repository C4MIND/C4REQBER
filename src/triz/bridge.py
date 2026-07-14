"""
C4REQBER: TRIZ-C4 Bridge
Provides C4↔TRIZ mapping for contradiction solving.
"""

from __future__ import annotations

import logging
from typing import Any

from src.triz.principles import PRINCIPLES
from src.triz.principles import Principle as TRIZPrinciple


logger = logging.getLogger(__name__)


class C4TrizBridge:
    """Bridge between C4 cognitive states and TRIZ principles."""

    def __init__(self) -> None:
        self.principles: dict[int, TRIZPrinciple] = PRINCIPLES
        self.using_config: bool = True  # Placeholder, can be extended

    def get_triz_for_c4_path(self, c4_path: list[str]) -> list[int]:
        """Get TRIZ principles for a C4 path.

        Args:
            c4_path: List of C4 operators.

        Returns:
            List of TRIZ principle numbers.
        """
        if not c4_path:
            return []
        # Heuristic: map operators to principle clusters
        op_map = {
            "T": [13, 35, 15],
            "T_INV": [2, 17, 34],
            "S": [1, 3, 5],
            "S_INV": [24, 28, 40],
            "A": [6, 24, 25],
            "A_INV": [12, 22, 31],
            "τ": [13, 35],
            "σ": [5, 7],
            "δ": [1, 2],
            "ρ": [19, 18],
            "ι": [34, 13],
            "λ": [1, 35],
            "κ": [3, 28],
            "φ": [24, 31],
            "ψ": [19, 40],
        }
        candidates: list[int] = []
        for op in c4_path:
            candidates.extend(op_map.get(op, []))
        # Deduplicate and return top 5
        ranked = list(dict.fromkeys(candidates))
        return ranked[:5]

    def get_c4_for_triz_principle(self, principle_id: int) -> list[str]:
        """Get C4 operators for a TRIZ principle.

        Args:
            principle_id: TRIZ principle number.

        Returns:
            List of C4 operator strings.
        """
        if principle_id not in self.principles:
            return []
        # Heuristic: map principles to operator hints (Latin + Greek unified)
        reverse: dict[int, list[str]] = {}
        latin = {
            1: ["S"], 2: ["T_INV"], 3: ["S"], 5: ["S"], 6: ["A"],
            12: ["A_INV"], 13: ["T"], 15: ["T"], 17: ["T_INV"],
            18: ["ρ"], 19: ["ρ"], 22: ["A_INV"], 24: ["A"],
            28: ["S_INV"], 31: ["A_INV"], 34: ["T_INV"],
            35: ["T"], 40: ["S_INV"],
        }
        greek = {
            1: ["σ"], 2: ["τ⁻"], 3: ["σ⁺"], 5: ["σ⁺"], 6: ["δ⁺"],
            10: ["τ⁺"], 13: ["τ⁺"], 14: ["τ⁻"], 15: ["τ⁺"], 17: ["τ⁻"],
            22: ["δ⁻"], 24: ["δ⁺"], 28: ["σ⁻"], 30: ["τ⁺"],
            31: ["δ⁻"], 32: ["σ⁺"], 34: ["τ⁻"], 35: ["τ⁺"], 40: ["σ⁻"],
        }
        for k, v in latin.items():
            reverse[k] = v
        for k, v in greek.items():
            reverse.setdefault(k, []).extend(v)
        return reverse.get(principle_id, [])

    def get_principle_info(self, principle_id: int) -> TRIZPrinciple | None:
        """Get information about a TRIZ principle.

        Args:
            principle_id: TRIZ principle number.

        Returns:
            TRIZPrinciple instance or None if not found.
        """
        return self.principles.get(principle_id)

    def get_all_principles(self) -> list[TRIZPrinciple]:
        """Return all TRIZ principles."""
        return list(self.principles.values())

    def recommend_for_contradiction(self, improving: str, worsening: str) -> dict[str, Any]:
        return recommend_for_contradiction(improving, worsening)

    def generate_c4_triz_path(self, problem: str, contradiction: tuple[str, str]) -> dict[str, Any]:
        return generate_c4_triz_path(problem, contradiction)


def get_c4_triz_mapping(
    c4_state: Any | None = None,
    improving_param: str | None = None,
    worsening_param: str | None = None,
) -> dict[str, Any]:
    """
    Map between C4 cognitive states and TRIZ parameters.

    Args:
        c4_state: Optional C4 state tuple (t, s, a)
        improving_param: TRIZ improving parameter
        worsening_param: TRIZ worsening parameter

    Returns:
        Dict with mapping information and recommendations
    """
    result: dict[str, Any] = {
        "c4_state": str(c4_state) if c4_state else None,
        "improving_param": improving_param,
        "worsening_param": worsening_param,
        "recommended_principles": [],
        "confidence": 0.5,
    }

    if improving_param and worsening_param:
        from src.triz.matrix import get_parameter_id, get_recommended_principles

        imp_id = get_parameter_id(improving_param)
        wors_id = get_parameter_id(worsening_param)
        if imp_id and wors_id:
            rec = get_recommended_principles(imp_id, wors_id)
            result["recommended_principles"] = rec[:5]
            result["confidence"] = 0.8 if result["recommended_principles"] else 0.4

    return result


def get_c4_triz_bridge_obj() -> C4TrizBridge:
    """Return a bridge instance."""
    return C4TrizBridge()


def recommend_for_contradiction(improving: str, worsening: str) -> dict[str, Any]:
    """Return TRIZ principles and mapped C4 operators for a contradiction."""
    from src.triz.matrix import get_parameter_id, get_recommended_principles

    imp_id = get_parameter_id(improving)
    wors_id = get_parameter_id(worsening)
    if not imp_id or not wors_id:
        return {"triz_principles": [], "c4_operators": [], "principle_details": []}

    principles = get_recommended_principles(imp_id, wors_id)
    bridge = C4TrizBridge()
    c4_ops: list[str] = []
    for pid in principles[:3]:
        c4_ops.extend(bridge.get_c4_for_triz_principle(pid))
    details = [bridge.get_principle_info(pid) for pid in principles]
    return {
        "triz_principles": principles,
        "c4_operators": c4_ops,
        "principle_details": details,
    }


def generate_c4_triz_path(problem: str, contradiction: tuple[str, str]) -> dict[str, Any]:
    """Generate a C4/TRIZ guided path for a problem statement."""
    improving, worsening = contradiction
    rec = recommend_for_contradiction(improving, worsening)
    return {
        "problem": problem,
        "contradiction": {"improving": improving, "worsening": worsening},
        "triz_principles": rec["triz_principles"],
        "c4_operators": rec["c4_operators"],
        "principle_details": rec["principle_details"],
    }


def map_c4_to_triz_parameters(c4_state: Any) -> list[str]:
    """Map C4 state to relevant TRIZ parameters."""
    from src.triz.matrix import PARAMETERS

    params = [{"id": pid, "name": name} for pid, name in PARAMETERS.items()]
    # Simple mapping: use axis to prioritize parameter groups
    t_val = getattr(c4_state, "t", None)
    if t_val is None:
        t_val = getattr(c4_state, "T", 0)
    assert t_val is not None
    s_val = getattr(c4_state, "s", None)
    if s_val is None:
        s_val = getattr(c4_state, "S", 0)
    assert s_val is not None
    a_val = getattr(c4_state, "a", None)
    if a_val is None:
        a_val = getattr(c4_state, "A", 0)
    assert a_val is not None
    seed = (t_val + s_val + a_val) % max(1, len(params))
    return [str(p.get("name", "")) for p in params[seed:seed + 5] if isinstance(p, dict)]


def map_triz_to_c4(improving: str, worsening: str) -> Any:
    """Map TRIZ contradiction to C4 state using parameter category semantics.

    TRIZ parameter categories:
      Physical (1-12)     → T axis (time: Past=0, Present=1, Future=2)
      Performance (13-24) → S axis (scale: Concrete=0, Abstract=1, Meta=2)
      Process (25-39)     → A axis (agency: Self=0, Other=1, System=2)
    """
    from src.c4.state import C4State
    from src.triz.matrix_core import get_parameter_id, get_recommended_principles

    imp_id = get_parameter_id(improving)
    wors_id = get_parameter_id(worsening)
    rec = get_recommended_principles(imp_id, wors_id) if imp_id and wors_id else []

    def _category(pid: int) -> int:
        if pid <= 12:
            return 0
        if pid <= 24:
            return 1
        return 2

    t = _category(imp_id or 13)  # Physical→Past/1, Perform→Present/2, Process→Future/0
    s = _category(wors_id or 13)
    avg_principles = sum(int(p) for p in rec) if rec else 0
    a = (avg_principles // len(rec)) % 3 if rec else 1
    return C4State(t=t % 3, s=s % 3, a=a % 3)
