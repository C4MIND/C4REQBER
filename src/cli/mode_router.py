from __future__ import annotations


"""Mode Router — auto-select best pipeline mode based on query characteristics."""

import logging
from typing import Literal


logger = logging.getLogger(__name__)

ModeType = Literal["solve", "turbo", "flash", "turbofactory"]


def auto_route(query: str) -> ModeType:
    """Auto-select best pipeline mode for a query."""
    q = query.lower().strip()

    scientific_keywords = [
        "hypothesis", "theory", "mechanism", "quantum", "study",
        "research", "experiment", "clinical", "dissertation", "phd",
        "paper", "publication", "journal", "review", "meta-analysis",
        "neuro", "epigenetic", "photosynthesis", "fusion", "mining",
        "concrete", "bacterial", "aging", "cellular", "molecular",
        "thermodynamic", "algorithm", "proof", "theorem", "verification",
        "astro", "geo", "climate", "particle", "plasma", "robotics",
        "surgery", "medical", "pharma", "drug", "disease", "treatment",
    ]
    sci_score = sum(1 for kw in scientific_keywords if kw in q)
    if sci_score >= 2:
        return "turbo"

    paradigm_keywords = [
        "paradigm", "revolution", "transform", "disrupt", "breakthrough",
        "factory", "scale", "domain", "industry", "field", "sector",
        "ultimate", "comprehensive", "survey", "state of the art",
        "literature review", "systematic review",
    ]
    paradigm_score = sum(1 for kw in paradigm_keywords if kw in q)
    if paradigm_score >= 2 or "turbofactory" in q:
        return "turbofactory"

    quick_indicators = ["what is", "how to", "explain", "define", "compare", "difference between"]
    is_question = q.endswith("?") or any(q.startswith(ind) for ind in quick_indicators)
    if is_question and len(q) <= 120:
        return "flash"

    return "solve"


def get_mode_description(mode: str) -> str:
    """Return human-readable description of a mode."""
    descriptions = {
        "solve": "12-stage pipeline with observer — produces strategic artifacts",
        "turbo": "Research pipeline — 28 knowledge sources, competing hypotheses, iterative paradigm detection",
        "flash": "Quick mode — instant answers with optional citations",
        "turbofactory": "Parallel paradigm factory — runs 10-100 pipelines",
    }
    return descriptions.get(mode, "Unknown mode")
