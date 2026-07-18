# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class FormalCitation:
    """FormalCitation."""

    id: str
    label: str
    tool: str
    result: str
    detail: str = ""
    timestamp: float = field(default_factory=time.time)

    @property
    def short(self) -> str:
        """Short."""
        symbols = {
            "verified": "✓",
            "falsified": "✗",
            "satisfiable": "◇",  # SAT ≠ verified
            "passed": "✓",
            "found": "✓",
            "confirmed": "✓",
            "unknown": "?",
            "heuristic": "~",
        }
        sym = symbols.get(self.result, "?")
        return f"[{self.id}{sym}]"

    @property
    def expanded(self) -> str:
        return f"{self.tool}: {self.label} — {self.result}"


class CitationFormatter:
    """CitationFormatter."""

    @staticmethod
    def format_inline(citations: list[FormalCitation]) -> str:
        return " ".join(c.short for c in citations)

    @staticmethod
    def format_footnotes(citations: list[FormalCitation]) -> str:
        return "\n".join(f"  [{c.id}] {c.expanded}" for c in citations)

    @staticmethod
    def to_terminal(citations: list[FormalCitation]) -> str:
        """To terminal."""
        inline = CitationFormatter.format_inline(citations)
        footnotes = CitationFormatter.format_footnotes(citations)
        status = (
            "✓"
            if all(c.result in ("verified", "passed", "confirmed") for c in citations)
            else "◇"
            if all(
                c.result in ("verified", "passed", "confirmed", "satisfiable") for c in citations
            )
            else "✗"
        )
        count_ok = sum(1 for c in citations if c.result in ("verified", "passed", "confirmed"))
        return f"Results: {inline}  [{count_ok}/{len(citations)} {status}]\n{footnotes}"


CITATION_TEMPLATES: dict[str, FormalCitation] = {
    "discovery_found": FormalCitation(
        id="F1", label="Prior art found", tool="search", result="found"
    ),
    "formalized": FormalCitation(
        id="F2", label="Hypothesis formalized", tool="logic", result="confirmed"
    ),
    "lean4_verified": FormalCitation(
        id="F3", label="Theorem verified", tool="Lean4", result="verified"
    ),
    "coq_verified": FormalCitation(
        id="F4", label="Theorem verified", tool="Coq", result="verified"
    ),
    "z3_verified": FormalCitation(
        id="F5", label="SMT check passed", tool="Z3", result="satisfiable"
    ),
    "counterexample": FormalCitation(
        id="CE", label="Counterexample found", tool="falsifier", result="falsified"
    ),
    "novelty_confirmed": FormalCitation(
        id="N1", label="Novelty confirmed", tool="novelty_validator", result="confirmed"
    ),
    "paradigm_detected": FormalCitation(
        id="P1", label="Paradigm shift detected", tool="paradigm_detector", result="found"
    ),
}


def create_discovery_citation(**kwargs: object) -> FormalCitation:
    return CITATION_TEMPLATES["discovery_found"]


def create_formalized_citation(**kwargs: object) -> FormalCitation:
    return CITATION_TEMPLATES["formalized"]


def create_verification_citation(
    tool: str = "lean4", result: str = "verified", **kwargs: object
) -> FormalCitation:
    """Create verification citation."""
    key = f"{tool}_verified" if f"{tool}_verified" in CITATION_TEMPLATES else "lean4_verified"
    c = CITATION_TEMPLATES[key]
    c.tool = tool
    c.result = result
    return c


create_verified_citation = create_verification_citation


def create_model_check_citation(result: str = "passed", **kwargs: object) -> FormalCitation:
    return FormalCitation(id="MC", label="Model check", tool="model-checker", result=result)


def create_smt_citation(result: str = "satisfiable", **kwargs: object) -> FormalCitation:
    return FormalCitation(id="F5", label="SMT check", tool="Z3", result=result)


def create_novelty_citation(
    confirmed: bool = False,
    score: float | None = None,
    **kwargs: object,
) -> FormalCitation:
    """Only stamp novelty when an explicit check passed."""
    if not confirmed:
        return FormalCitation(
            id="N1",
            label="Novelty unchecked",
            tool="novelty_validator",
            result="unknown",
            detail=f"score={score}" if score is not None else "",
        )
    return FormalCitation(
        id="N1",
        label="Novelty confirmed",
        tool="novelty_validator",
        result="confirmed",
        detail=f"score={score}" if score is not None else "",
    )


def create_paradigm_citation(**kwargs: object) -> FormalCitation:
    return CITATION_TEMPLATES["paradigm_detected"]


def create_counterexample_citation(**kwargs: object) -> FormalCitation:
    return CITATION_TEMPLATES["counterexample"]
