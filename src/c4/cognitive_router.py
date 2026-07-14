# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
from typing import Any

from src.c4.scientist_paths import ALL_SCIENTIST_PATHS, PROBLEM_TO_SCIENTIST


logger = logging.getLogger(__name__)


class CognitiveRouter:
    """Route problems through C4 Z₃³ space. 18 discovery patterns available.

    Each pattern maps to a specific scientist's cognitive journey.
    The Router selects the best match based on problem type and
    provides explainability: WHY this path was chosen.
    """

    # Copernican meta-principle: all 18 paths are valid discovery routes.
    # The router selects based on problem fingerprint, not hardcoded priorities.
    SCIENTIST_PATHS = ALL_SCIENTIST_PATHS

    def __init__(self) -> None:
        pass

    def fingerprint_problem(self, problem_text: str) -> dict[str, Any]:
        """Classify problem into C4 state + match to scientist pattern."""
        t = problem_text.lower()

        # Time axis
        time_state = "PRESENT"
        if any(kw in t for kw in ("future", "predict", "will", "forecast", "next", "project")):
            time_state = "FUTURE"
        elif any(kw in t for kw in ("past", "historical", "previous", "was", "had", "occurred")):
            time_state = "PAST"

        # Scale axis
        scale_state = "CONCRETE"
        if any(kw in t for kw in ("meta", "theory of", "philosophy of", "methodology", "epistemology")):
            scale_state = "META"
        elif any(kw in t for kw in ("abstract", "principle", "general", "universal", "mathematical", "formalism")):
            scale_state = "ABSTRACT"

        # Agency axis
        agency_state = "SELF"
        if any(kw in t for kw in ("system", "ecosystem", "network", "collective", "emergent")):
            agency_state = "SYSTEM"
        elif any(kw in t for kw in ("other", "competitor", "external", "social", "collaborative", "multi-agent")):
            agency_state = "OTHER"

        # Match to scientist path
        scientist_key = "darwin"  # default
        for keyword, sci_key in PROBLEM_TO_SCIENTIST.items():
            # Exact phrase match OR single-word substring (for variant word forms)
            if keyword in t:
                scientist_key = sci_key
            elif " " not in keyword and len(keyword) > 6:
                # Single long word → check if it's a substring of any word in text
                for word in t.split():
                    if (keyword in word) or (word in keyword and len(word) > 3):
                        scientist_key = sci_key
                        break
        # No break: last matching keyword wins (more specific keywords come later)

        pattern = self.SCIENTIST_PATHS.get(scientist_key, self.SCIENTIST_PATHS["darwin"])

        return {
            "c4_state": f"{scale_state}/{time_state}/{agency_state}",
            "time": time_state, "scale": scale_state, "agency": agency_state,
            "scientist_key": scientist_key,
            "scientist_name": pattern["scientist"],
            "era": pattern["era"],
            "discovery": pattern["discovery"],
            "method": pattern["method"],
            "path_data": pattern,
        }

    def route(self, problem_text: str) -> dict[str, Any]:
        """Find optimal C4 path. Returns path + scientist + explanation."""
        fp = self.fingerprint_problem(problem_text)
        pattern = fp["path_data"]
        path = pattern["path"]

        if len(path) > 6:
            logger.warning(
                "CognitiveRouter: path truncated from %d to 6 (Theorem 11 bound)",
                len(path),
            )
            path = path[:6]

        states = []
        for scale, time, agency, engine, description in path:
            states.append({
                "c4_state": f"{scale}/{time}/{agency}",
                "scale": scale, "time": time, "agency": agency,
                "engine": engine, "description": description,
            })

        return {
            "problem": problem_text[:200],
            "fingerprint": fp,
            "scientist_pattern": f"{pattern['scientist']} ({pattern['era']})",
            "discovery_example": pattern["discovery"],
            "method_summary": pattern["method"],
            "path_length": len(path),
            "theorem_11_bound": 6,
            "within_bound": len(path) <= 6,
            "states": states,
            "engines_engaged": [s["engine"] for s in states],
            "explanation": self._generate_explanation(fp, pattern, len(path)),
        }

    def find_alternatives(self, problem_text: str) -> list[dict[str, Any]]:
        """All alternative scientist paths for explainability."""
        fp = self.fingerprint_problem(problem_text)
        alternatives = []
        for key, pat in self.SCIENTIST_PATHS.items():
            if key == fp["scientist_key"]:
                continue
            alternatives.append({
                "scientist": pat["scientist"],
                "era": pat["era"],
                "discovery": pat["discovery"],
                "path_length": len(pat["path"]),
                "method": pat["method"][:80],
            })
        return sorted(alternatives, key=lambda a: a["path_length"])

    def list_all_paths(self) -> list[dict[str, Any]]:
        """Return all 18 scientist paths for documentation."""
        return [
            {
                "key": key,
                "scientist": pat["scientist"],
                "era": pat["era"],
                "discovery": pat["discovery"],
                "steps": len(pat["path"]),
                "start_state": f"{pat['path'][0][0]}/{pat['path'][0][1]}/{pat['path'][0][2]}",
                "end_state": f"{pat['path'][-1][0]}/{pat['path'][-1][1]}/{pat['path'][-1][2]}",
            }
            for key, pat in self.SCIENTIST_PATHS.items()
        ]

    def _generate_explanation(self, fp: dict[str, Any], pattern: dict[str, Any], steps: int) -> str:
        """Generate human-readable explanation of WHY this path was chosen."""
        scientist = pattern["scientist"]
        state = fp["c4_state"]
        return (
            f"Problem classified as '{fp['scientist_key']}' type (C4 state: {state}). "
            f"Selected {scientist}'s cognitive path ({steps} steps): {pattern['method']}. "
            f"The path starts at {state} and navigates through Z₃³ space "
            f"using engines assigned to each cognitive state. "
            f"All paths respect Theorem 11 (≤6 steps between any two states)."
        )


__all__ = ["CognitiveRouter"]
