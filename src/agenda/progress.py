"""
c4reqber: Progress Tracker

Tracks what has been done and what remains in research agenda.
"""
from __future__ import annotations

from typing import Any


class ProgressTracker:
    """Track research progress and open gaps."""

    def __init__(self) -> None:
        self._results: list[dict[str, Any]] = []
        self._covered_topics: set[str] = set()
        self._approved: list[str] = []
        self._rejected: list[str] = []

    def update(self, result: dict[str, Any]) -> None:
        """Record a completed discovery result."""
        self._results.append(result)
        hyp = result.get("hypothesis", {}).get("text", "")
        if hyp:
            # Simple topic extraction: first 3 words
            words = hyp.split()[:3]
            self._covered_topics.add(" ".join(words).lower())

    def get_open_gaps(self) -> list[str]:
        """Return list of open research gaps."""
        gaps = []
        for result in self._results:
            if "gaps" in result:
                gaps.extend(result["gaps"])
        return list(dict.fromkeys(gaps))  # dedup preserve order

    def get_covered_topics(self) -> set[str]:
        """Return set of covered topics."""
        return set(self._covered_topics)

    def add_approved(self, question: str) -> None:
        """Record an approved research question."""
        self._approved.append(question)

    def add_rejected(self, question: str) -> None:
        """Record a rejected research question."""
        self._rejected.append(question)

    def to_dict(self) -> dict[str, Any]:
        return {
            "results_count": len(self._results),
            "covered_topics": list(self._covered_topics),
            "open_gaps": self.get_open_gaps(),
            "approved_count": len(self._approved),
            "rejected_count": len(self._rejected),
            "latest_approved": self._approved[-5:] if self._approved else [],
        }
