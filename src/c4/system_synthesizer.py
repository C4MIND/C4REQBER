# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
from typing import Any

from src.c4.cognitive_router import CognitiveRouter
from src.c4.extended_engines import CognitiveStateClassifier


logger = logging.getLogger(__name__)

# Patterns that indicate SYSTEMIC (interconnected) problems, not independent
SYSTEMIC_INDICATORS = [
    "causes", "leads to", "results in", "drives", "which causes",
    "which leads", "which drives", "which reduces", "which increases",
    "creates a", "creating a", "forming a", "producing a",
    "because", "therefore", "consequently", "as a result",
    "feedback", "cascade", "chain reaction", "domino", "knock-on",
    "interconnected", "interdependent", "system of", "network of",
    "due to", "owing to", "in turn", "by extension",
]


class SystemSynthesizer:
    """Detect systemic problems and merge their C4 paths."""

    def __init__(self) -> None:
        self.router = CognitiveRouter()
        self.classifier = CognitiveStateClassifier()

    def is_systemic(self, prompt: str) -> bool:
        """Check if prompt describes systemic (interconnected) problems."""
        t = prompt.lower()
        return any(ind in t for ind in SYSTEMIC_INDICATORS)

    def decompose_and_merge(self, prompt: str) -> dict[str, Any]:
        """Full pipeline: decompose → detect systemic → route each → merge.

        Returns:
            systemic: True if problems are interconnected
            sub_paths: list of individual C4 paths
            intersections: C4 states where paths converge
            merged_path: unified cognitive journey
            synthesis_points: where to inject synthesis engines
        """
        # 1. Split into sub-problems
        sub_problems = self._split_systemic(prompt)
        if len(sub_problems) <= 1:
            route = self.router.route(prompt)
            return {
                "systemic": False, "sub_paths": [route],
                "intersections": [], "merged_path": route["states"],
                "explanation": "Single problem — no merging needed.",
            }

        # 2. Route each
        paths = []
        for i, sub_text in enumerate(sub_problems):
            route = self.router.route(sub_text)
            paths.append({
                "index": i + 1,
                "text": sub_text[:200],
                "c4_path": route["states"],
                "scientist": route["scientist_pattern"],
                "steps": route["path_length"],
            })

        # 3. Find C4 state intersections
        intersections = self._find_intersections(paths)

        # 4. Build merged cognitive journey
        merged = self._merge_paths(paths, intersections)

        # 5. Detect synthesis points (where to apply merge engines)
        synthesis = self._identify_synthesis_points(merged, intersections)

        return {
            "systemic": True,
            "sub_paths": paths,
            "intersections": intersections,
            "merged_path": merged,
            "synthesis_points": synthesis,
            "total_c4_states": len(merged),
            "engines_engaged": list(set(s["engine"] for s in merged)),
            "explanation": self._explain(paths, intersections),
        }

    def _split_systemic(self, prompt: str) -> list[str]:
        """Split systemic prompt into causal-chain sub-problems."""
        t = prompt.lower()

        # Split by causal connectors into chain
        connectors = ["causes", "caused by", "leads to", "results in", "drives", "driven by",
                      "which causes", "which leads", "which drives", "which reduces", "which increases",
                      "creates a", "creating a", "producing a", "because", "due to", "owing to"]
        parts = [t]
        for conn in connectors:
            new_parts = []
            for part in parts:
                if conn in part:
                    before, _, after = part.partition(conn)
                    if before.strip() and after.strip():
                        new_parts.append(before.strip())
                        new_parts.append(after.strip())
                    else:
                        new_parts.append(part)
                else:
                    new_parts.append(part)
            parts = new_parts
            if len(parts) >= 2:
                break

        # Clean: remove leading ", which"
        parts = [p.strip().lstrip(", ") for p in parts if len(p.strip()) > 5]

        # Fallback: "and" splitting
        if len(parts) <= 1 and " and " in prompt:
            parts = [p.strip() for p in prompt.split(" and ") if len(p.strip()) > 5]

        return parts if len(parts) >= 2 else [prompt]

    def _find_intersections(self, paths: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Find C4 states where multiple paths converge."""
        if len(paths) < 2:
            return []

        # Collect all C4 states
        state_to_paths: dict[str, list[int]] = {}
        for p in paths:
            for state in p["c4_path"]:
                c4 = state["c4_state"]
                if c4 not in state_to_paths:
                    state_to_paths[c4] = []
                state_to_paths[c4].append(p["index"])

        # States visited by ≥2 paths
        intersections = []
        for c4_state, path_indices in state_to_paths.items():
            if len(path_indices) >= 2:
                # Find the engine at this state in each path
                engines = []
                for pid in path_indices:
                    path = paths[pid - 1]
                    for s in path["c4_path"]:
                        if s["c4_state"] == c4_state:
                            engines.append(s["engine"])
                            break
                intersections.append({
                    "c4_state": c4_state,
                    "paths": path_indices,
                    "engines": engines,
                    "synthesis_type": "convergence",
                })

        # Sort by number of converging paths (most important first)
        intersections.sort(key=lambda x: -len(x["paths"]))
        return intersections

    def _merge_paths(self, paths: list[dict[str, Any]], intersections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Merge multiple C4 paths into one unified cognitive journey.

        Strategy: topological merge — each path's states in order,
        with intersection states marked as synthesis points.
        """
        if len(paths) <= 1:
            return paths[0]["c4_path"] if paths else []

        merged: list[dict[str, Any]] = []
        seen_states: set[str] = set()

        for p in paths:
            for state in p["c4_path"]:
                c4 = state["c4_state"]
                is_intersection = any(i["c4_state"] == c4 for i in intersections)

                if is_intersection:
                    # Mark as synthesis point
                    merged_state = dict(state)
                    merged_state["synthesis"] = True
                    merged_state["description"] = f"SYNTHESIS: {state['description']} — paths converge here"
                    if c4 not in seen_states:
                        merged.append(merged_state)
                        seen_states.add(c4)
                else:
                    if c4 not in seen_states:
                        merged.append(state)
                        seen_states.add(c4)

        return merged

    def _identify_synthesis_points(
        self, merged: list[dict[str, Any]], intersections: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Identify where to inject synthesis engines (ConstraintSolver, RecursiveValidation)."""
        synthesis = []
        for i, state in enumerate(merged):
            if state.get("synthesis"):
                synthesis.append({
                    "step": i + 1,
                    "c4_state": state["c4_state"],
                    "engine": "ConstraintSolver",
                    "action": "Merge converging paths — find unifying invariant",
                    "followed_by": state.get("engine", "MultiStepChain"),
                })
        # Final synthesis point
        if merged and not synthesis:
            synthesis.append({
                "step": len(merged) + 1,
                "c4_state": merged[-1]["c4_state"] if merged else "META/PRESENT/SELF",
                "engine": "RecursiveValidation",
                "action": "Validate merged theory against all sub-problem constraints",
            })
        return synthesis

    def _explain(self, paths: list[dict[str, Any]], intersections: list[dict[str, Any]]) -> str:
        n = len(paths)
        scientists = ", ".join(p["scientist"] for p in paths[:3])
        inter = len(intersections)

        if inter > 0:
            states = ", ".join(i["c4_state"] for i in intersections[:3])
            return (
                f"Systemic problem with {n} interconnected sub-problems. "
                f"Individual routes: {scientists}. "
                f"Paths converge at {inter} C4 state(s): {states}. "
                "Merged into unified cognitive journey with synthesis at intersections."
            )
        return (
            f"Systemic problem with {n} interconnected sub-problems. "
            f"Individual routes: {scientists}. "
            f"No direct C4 intersections — merged via sequential ordering."
        )


__all__ = ["SystemSynthesizer", "SYSTEMIC_INDICATORS"]
