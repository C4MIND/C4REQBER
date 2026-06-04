from __future__ import annotations

from abc import ABC, abstractmethod


class GapAnalyzer(ABC):
    """Abstract contract for gap analysis engines.

    All gap analyzers (AutoGapAnalyzer, GapMiner) must implement this interface.
    Phase 1.1 (Liskov audit): Previously AutoGapAnalyzer.analyze() and GapMiner.analyze_papers()
    had different signatures and no shared contract — LSP violation.
    """

    @abstractmethod
    def analyze(self, sources: list[dict], topic: str) -> list[dict]:
        """Analyze a corpus of source papers and return a list of research gaps.

        Each gap dict must contain:
            area: str — the topic area where the gap exists
            evidence: str — textual evidence from the paper
            novelty_score: float — 0.0 (well-covered) to 1.0 (completely novel)
            hypothesis_seed: str — a seed idea for generating a hypothesis
        """
        ...


# Default gap indicators — both gap-FINDING and gap-RESOLVING
GAP_INDICATORS: list[str] = [
    "remains unclear",
    "not well understood",
    "requires further",
    "limited understanding",
    "knowledge gap",
    "open question",
    "controversial",
    "debated",
    "unknown",
    "poorly characterized",
    "lacks systematic",
    "few studies",
    "no consensus",
    "insufficient data",
    "unexplored",
    "underinvestigated",
    "no study has",
    "has not been investigated",
    "remains unexplored",
    "limited research",
    "unknown whether",
    "not yet",
    "poorly understood",
    "understudied",
    "overlooked",
    "neglected",
    "surprisingly little",
    "scarcely investigated",
    "remains to be",
    "still unclear",
    "yet to be determined",
    "uncharacterized",
    "missing piece",
    "critical gap",
    "major gap",
]

RESOLUTION_INDICATORS: list[str] = [
    "well established",
    "thoroughly studied",
    "consensus exists",
    "resolved by",
    "conclusively shown",
    "widely accepted",
    "extensively documented",
    "multiple replications",
]
