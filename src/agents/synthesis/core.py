"""
C4REQBER: Synthesis Core
Core data structures and result types for smart synthesis fallback.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SynthesisResult:
    """Structured result from smart synthesis fallback."""

    core_insight: str
    recommended_approach: str
    risks_mitigations: list[dict[str, str]]
    action_items: list[str]
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "core_insight": self.core_insight,
            "recommended_approach": self.recommended_approach,
            "risks_mitigations": self.risks_mitigations,
            "action_items": self.action_items,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }

    def to_markdown(self) -> str:
        """Render as markdown for pipeline output."""
        lines = [
            "## Core Insight",
            f"{self.core_insight}",
            "",
            "## Recommended Approach",
            f"{self.recommended_approach}",
            "",
            "## Risks & Mitigations",
        ]
        for rm in self.risks_mitigations:
            lines.append(f"- **Risk:** {rm['risk']}  ")
            lines.append(f"  **Mitigation:** {rm['mitigation']}")
        lines.extend(["", "## Action Items"])
        for i, item in enumerate(self.action_items, 1):
            lines.append(f"{i}. {item}")
        lines.extend([
            "",
            f"*Confidence: {self.confidence:.0%} (smart fallback)*",
        ])
        return "\n".join(lines)
