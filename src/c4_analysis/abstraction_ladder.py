# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)

# QZRF operators mapped to abstraction rungs
ABSTRACTION_RUNGS = [
    ("CONCRETE", 0, "No abstraction — raw observation"),
    ("PATTERN", 1, "Identify recurring structure across instances (Generalize)"),
    ("PRINCIPLE", 2, "Extract underlying principle (FirstPrinciples)"),
    ("LAW", 3, "Formalize as law/equation (Specify)"),
    ("THEORY", 4, "Embed in broader theory (Systemic, Recursive)"),
    ("PARADIGM", 5, "Recognize paradigm-level shift (MetaReflect)"),
]


class AbstractionLadder:
    """Climb from concrete observation to meta-level insight using C4+QZRF.

    Usage:
        ladder = AbstractionLadder()
        result = ladder.climb("Michelson-Morley found no aether drift")
        # → pattern=constant_speed, principle=relativity, meta=spacetime
    """

    def __init__(self) -> None:
        self.patterns = PATTERN_DB

    def climb(
        self,
        observation: str,
        max_rungs: int = 6,
        theory_if_known: str = "",
    ) -> dict[str, Any]:
        """Iteratively abstract from observation to meta-principle."""
        rungs_visited: list[dict[str, Any]] = []
        current = observation
        current_level = 0  # CONCRETE

        while current_level < min(max_rungs, len(ABSTRACTION_RUNGS) - 1):
            rung = self._abstract_step(current, current_level, theory_if_known)
            rungs_visited.append(rung)

            if rung.get("terminial", False) or not rung.get("next_level"):
                break

            current = rung.get("result", current)
            current_level = rung.get("next_level", current_level + 1)

        return {
            "observation": observation,
            "rungs": rungs_visited,
            "rungs_climbed": len(rungs_visited),
            "final_level": ABSTRACTION_RUNGS[min(current_level, 5)][0] if rungs_visited else "CONCRETE",
            "final_insight": rungs_visited[-1].get("result", observation) if rungs_visited else observation,
            "c4_scale_path": [ABSTRACTION_RUNGS[min(r.get("level", 0), 5)][0] for r in rungs_visited],
        }

    def _abstract_step(self, text: str, level: int, theory: str) -> dict[str, Any]:
        """One rung of the abstraction ladder."""
        rung_name = ABSTRACTION_RUNGS[min(level + 1, 5)][0]
        operator = self._select_operator(level)

        # Try pattern DB first for known domain abstractions
        for kw, result in self.patterns.items():
            if kw in text.lower():
                return {
                    "level": level,
                    "next_level": level + 1,
                    "rung": rung_name,
                    "operator": operator,
                    "input": text[:200],
                    "result": result,
                    "mechanism": "pattern_db_match",
                    "terminial": level >= 4,
                }

        # LLM-driven abstraction (via system prompt)
        result = self._llm_abstract(text, operator, rung_name, theory)
        return {
            "level": level,
            "next_level": level + 1,
            "rung": rung_name,
            "operator": operator,
            "input": text[:200],
            "result": result,
            "mechanism": "llm_driven",
            "terminial": level >= 4,
        }

    def _select_operator(self, level: int) -> str:
        ops = ["Generalize", "FirstPrinciples", "Specify", "Systemic", "MetaReflect", "MetaReflect"]
        return ops[min(level, 5)]

    def _llm_abstract(self, text: str, operator: str, rung: str, theory: str) -> str:
        """Use LLM to perform abstraction step. Graceful fallback if unavailable."""
        try:
            from src.plugins._llm_base import _llm_reason
            system = "You are an abstraction engine that climbs from concrete observations to meta-level principles. Be concise."
            prompt = f"Apply the cognitive operator '{operator}' to reach abstraction rung '{rung}'.\n\nINPUT: {text[:1000]}\n{'THEORY CONTEXT: ' + theory[:500] if theory else ''}\n\nOutput 1-3 sentences — the next level of abstraction."
            result = _llm_reason(prompt, system=system, max_tokens=300, temperature=0.4)
            if result:
                return result.strip()
        except Exception:
            logger.debug("LLM abstraction unavailable, using heuristic")
        return self._heuristic_abstract(text, level=0)

    def _heuristic_abstract(self, text: str, level: int) -> str:
        """Fallback: pattern-based abstraction."""
        t = text.lower()
        if "zero" in t or "null" in t or "none" in t:
            return "The null result indicates an invariant — a conserved property independent of measurement conditions."
        if "constant" in t or "same" in t or "identical" in t:
            return "Invariance across conditions suggests a fundamental conservation law or symmetry principle."
        if "contradict" in t or "inconsistent" in t or "incompatible" in t:
            return "The contradiction implies the current theoretical framework has an unresolved tension that requires a unifying meta-principle."
        if "predict" in t or "explain" in t or "derive" in t:
            return "The predictive pattern suggests an underlying generative mechanism operating at a more abstract level."
        return "Generalization: the specific observation instantiates a broader principle operating across multiple domains."


# Known abstraction patterns (domain-specific)
PATTERN_DB: dict[str, str] = {
    # Physics: zero aether drift → speed of light is absolute
    "null result": "Null result across all orientations implies the measured quantity is an absolute invariant — independent of reference frame.",
    "no aether": "Absence of aether drift suggests the propagation speed of light is frame-independent — contradicting Galilean relativity.",
    "michelson-morley": "Michelson-Morley null result → light speed is constant in all inertial frames → principle of relativity must be generalized.",
    "michelson": "Michelson-Morley null result → light speed is constant in all inertial frames → principle of relativity must be generalized.",
    "morley": "Michelson-Morley null result → light speed is constant in all inertial frames → principle of relativity must be generalized.",
    # Physics: constancy of c → time dilation
    "speed of light": "Constant speed of light across frames implies time and space are not absolute — they transform to preserve c.",
    "light speed": "Constancy of c → requires Lorentz transformations → space and time are unified as spacetime.",
    "constancy": "Constancy of physical law across observers implies symmetry principles that constrain possible theories.",
    # Physics: perihelion precession → curved spacetime
    "precession": "Anomalous precession cannot be explained within current framework — suggests incomplete understanding of underlying geometry.",
    "perihelion": "Mercury's anomalous perihelion precession → Newtonian gravity is an approximation → spacetime geometry is dynamic.",
    # Biology: conserved sequences → common ancestor
    "conserved sequence": "Sequence conservation across species suggests functional constraint → common evolutionary origin or convergent functional adaptation.",
    "homologous": "Homology across species implies descent from common ancestor → tree-like evolutionary structure.",
    # Generic patterns
    "anomaly": "Anomaly in current framework → signals boundary of theory's applicability → opportunity for generalization.",
    "invariant": "Invariant across transformations → conserved quantity → symmetry → fundamental principle.",
    "symmetry": "Symmetry in observations → Noether-type theorem → conserved quantity → deeper structural principle.",
}


__all__ = ["AbstractionLadder", "ABSTRACTION_RUNGS"]
