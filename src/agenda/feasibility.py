"""
c4reqber: Feasibility Checker

Checks whether a research question can be addressed with available tools.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FeasibilityResult:
    has_tools: bool
    estimated_cost_usd: float
    estimated_time_minutes: float
    tractability_score: float  # 0-1

    def to_dict(self) -> dict[str, Any]:
        return {
            "has_tools": self.has_tools,
            "estimated_cost_usd": round(self.estimated_cost_usd, 4),
            "estimated_time_minutes": round(self.estimated_time_minutes, 1),
            "tractability_score": round(self.tractability_score, 3),
        }


class FeasibilityChecker:
    """Check feasibility of a research question."""

    TOOL_KEYWORDS = {
        "simulation": ["physics", "dynamics", "waves", "kinetics", "monte carlo"],
        "formal": ["theorem", "proof", "verify", "formalize"],
        "data": ["dataset", "empirical", "observational", "clinical"],
        "literature": ["review", "meta-analysis", "survey"],
    }

    def check(self, question: Any) -> FeasibilityResult:
        """Check feasibility of a research question."""
        text = question.text if hasattr(question, "text") else str(question)
        text_lower = text.lower()

        # Detect required tools
        required_tools = set()
        for tool, keywords in self.TOOL_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                required_tools.add(tool)

        has_tools = len(required_tools) > 0

        # Estimate cost based on complexity indicators
        complexity_markers = ["nonlinear", "multivariate", "longitudinal", "quantum", "molecular"]
        complexity = sum(1 for m in complexity_markers if m in text_lower)
        estimated_cost = 0.5 + complexity * 0.5  # USD
        estimated_time = 5 + complexity * 15  # minutes

        # Tractability: simpler = more tractable
        word_count = len(text.split())
        tractability = max(0.0, 1.0 - complexity * 0.15 - word_count * 0.005)

        return FeasibilityResult(
            has_tools=has_tools,
            estimated_cost_usd=estimated_cost,
            estimated_time_minutes=estimated_time,
            tractability_score=tractability,
        )
