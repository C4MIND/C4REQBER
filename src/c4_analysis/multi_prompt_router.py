# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
from typing import Any

from src.c4.cognitive_router import CognitiveRouter
from src.c4_analysis.extended_engines import CognitiveStateClassifier


logger = logging.getLogger(__name__)


class MultiPromptRouter:
    """Decompose real user prompts into sub-problems and route each."""

    SEPARATORS = [" and ", " & ", " also ", "; ", ". ", " furthermore ", " moreover ", " plus "]
    VAGUE_INDICATORS = ["explore", "discover", "investigate", "research", "study", "understand", "learn about"]
    GOAL_INDICATORS = ["i want to", "i need to", "help me", "can you", "how to", "how do i"]

    def __init__(self) -> None:
        self.router = CognitiveRouter()
        self.classifier = CognitiveStateClassifier()

    def route(self, prompt: str, cost_tier: str = "budget") -> dict[str, Any]:
        """Route a real user prompt through multi-problem decomposition.

        Returns:
            sub_problems: list of (text, C4_coords, scientist_path)
            merged: single unified C4 state for the whole prompt
            explanation: why this decomposition was chosen
            clarification_needed: True if prompt is too vague
        """
        prompt_lower = prompt.lower()

        # 1. Detect prompt type
        is_vague = self._is_vague(prompt_lower)
        is_goal = self._is_goal(prompt_lower)
        sub_problems = self._split(prompt_lower)

        # 2. Handle vague prompts
        if is_vague and len(sub_problems) == 1:
            return {
                "prompt": prompt,
                "sub_problems": [],
                "merged_c4": self.classifier.classify(prompt),
                "explanation": (
                    "Your query is broad. To give you the most useful result, "
                    "try being more specific. For example:\n"
                    "  • 'Why does X contradict Y?' → Einstein path (paradigm shift)\n"
                    "  • 'I observe that X varies with Y' → Darwin path (generalize)\n"
                    "  • 'Design X that achieves Y' → Tesla path (invention)\n"
                    "  • 'mRNA vaccine immune response problem' → Karikó path (perseverance)"
                ),
                "clarification_needed": True,
            }

        # 3. Route each sub-problem
        results = []
        for i, sub_text in enumerate(sub_problems):
            result = self.router.route(sub_text)
            c4 = self.classifier.classify(sub_text)
            results.append({
                "index": i + 1,
                "text": sub_text[:300],
                "c4_state": c4["c4_state"],
                "scientist": result["scientist_pattern"],
                "path_length": result["path_length"],
                "explanation": result["explanation"][:200],
            })

        # 4. Merge: overall C4 state for the combined prompt
        merged_c4 = self.classifier.classify(prompt)

        return {
            "prompt": prompt,
            "sub_problems": results,
            "merged_c4": merged_c4,
            "total_paths": len(results),
            "explanation": self._generate_explanation(results, is_vague, is_goal),
            "clarification_needed": False,
        }

    def _split(self, prompt: str) -> list[str]:
        """Split multi-problem prompt into sub-problems."""
        # Try explicit separators
        for sep in self.SEPARATORS:
            if sep in prompt:
                parts = [p.strip() for p in prompt.split(sep) if len(p.strip()) > 5]
                if len(parts) >= 2:
                    return parts

        # Try LLM decomposition (cheap model)
        if len(prompt) > 80:
            llm_split = self._llm_decompose(prompt)
            if llm_split:
                return llm_split

        return [prompt]

    def _llm_decompose(self, prompt: str) -> list[str] | None:
        """Use cheap LLM to decompose multi-problem prompt."""
        try:
            from src.plugins._llm_base import _llm_reason
            system = "You are a problem decomposer. Split multi-problem prompts into separate problems. Output one problem per line, no numbers."
            query = f"If this prompt contains multiple distinct problems, list each one on a separate line. If it's a single problem, output 'SINGLE'.\n\n{prompt[:800]}"
            result = _llm_reason(query, system=system, max_tokens=200, temperature=0.1)
            if result and result.strip() != "SINGLE":
                lines = [l.strip("-• ") for l in result.strip().split("\n") if l.strip()]
                if len(lines) >= 2:
                    return lines[:5]
        except (ImportError, ModuleNotFoundError, RuntimeError, OSError) as e:
            logger.warning("LLM decomposition unavailable: %s", e)
        return None

    def _is_vague(self, prompt: str) -> bool:
        words = prompt.split()
        if len(words) < 4:
            return True
        # Check: starts with vague indicator AND no specific problem keyword
        starts_vague = any(prompt.startswith(v) for v in self.VAGUE_INDICATORS)
        has_specific = any(kw in prompt for kw in
            ("contradict", "why", "how", "what if", "predict", "design", "build", "solve"))
        return starts_vague and not has_specific

    def _is_goal(self, prompt: str) -> bool:
        return any(prompt.startswith(g) for g in self.GOAL_INDICATORS)

    def _generate_explanation(self, results: list[dict[str, Any]], is_vague: bool, is_goal: bool) -> str:
        if is_vague:
            return "Broad query — narrowed to specific paths. Try adding more detail for precision."

        n = len(results)
        if n == 1:
            r = results[0]
            return f"Single problem routed to {r['scientist']} path ({r['path_length']} C4 steps). State: {r['c4_state']}."

        paths = ", ".join(f"{r['scientist']} ({r['c4_state']})" for r in results[:4])
        return f"Prompt decomposed into {n} sub-problems. Independent routes: {paths}."


__all__ = ["MultiPromptRouter"]
