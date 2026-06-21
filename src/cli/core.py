#!/usr/bin/env python3
"""C4REQBER CLI — Core utilities and formatting."""
from __future__ import annotations

import os
import sys
from typing import Any

from src.config import get_key
from src.llm.client import LLMClient


# Add src to path (works both locally and inside Docker)
_SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _SRC_DIR)


def get_llm_client() -> Any:
    """Get LLM client based on environment."""
    api_key = get_key("openrouter") or os.getenv("OPENROUTER_API_KEY")  # ~/.c4reqber central
    if not api_key:
        raise RuntimeError(
            "No LLM provider available. Set OPENROUTER_API_KEY in .env\n"
            "Without a real LLM, the solve pipeline cannot generate hypotheses."
        )
    return LLMClient(api_key)


def print_banner() -> None:
    """Print welcome banner."""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  C4REQBER v5.4                                                   ║
║  Scientific Discovery Intelligence Platform                      ║
║  C4³ = 27 states | 6 operators | Discovery Agent | Auth          ║
╚══════════════════════════════════════════════════════════════════╝
""")


def format_solution(solution: Any, with_falsifiability: Any=False) -> str:
    """Format CDI solution for display."""
    output = []
    output.append(f"\n{'=' * 60}")
    output.append("HYPOTHESIS")
    output.append(f"{'=' * 60}")
    output.append(f"\n{solution.hypothesis}\n")

    output.append(f"{'-' * 60}")
    output.append("NAVIGATION PATH (C4 Cognitive Space)")
    output.append(f"{'-' * 60}")

    if solution.c4_path:
        for i, transition in enumerate(solution.c4_path, 1):
            output.append(
                f"  Step {i}: {transition.operator:12} "
                f"{transition.from_state} → {transition.to_state}"
            )
    else:
        output.append("  (No state transitions - identity solution)")

    output.append(f"\nTotal steps: {solution.steps_taken}/6 (Theorem 11 bound)")
    output.append(f"Confidence: {solution.confidence_score:.2f}")

    # Falsifiability criteria
    if with_falsifiability and hasattr(solution, "falsifiability_criteria"):
        output.append(f"\n{'-' * 60}")
        output.append("FALSIFIABILITY CRITERIA (Karl Popper style)")
        output.append(f"{'-' * 60}")
        for i, criterion in enumerate(solution.falsifiability_criteria[:3], 1):
            output.append(f"\n  {i}. {criterion.statement}")
            output.append(f"     Measurement: {criterion.measurement}")
            output.append(f"     Threshold: {criterion.threshold}")
            output.append(f"     Difficulty: {criterion.difficulty}")

    output.append(f"\n{'-' * 60}")
    output.append("PHYSICAL CONTRADICTION RESOLVED")
    output.append(f"{'-' * 60}")
    output.append(f"  {solution.contradiction}")

    output.append(f"\n{'=' * 60}\n")

    return "\n".join(output)
