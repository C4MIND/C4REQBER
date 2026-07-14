# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
"""Mathematical Structure Detector — classify hypotheses by verifiability.

Distinguishes between:
Category A — Mathematically scaffolded claims (can be verified for consistency):
    "The Hamiltonian H = -J Σ σᵢσⱼ has a phase transition at T=2.27K"
    "The algorithm achieves O(n log n) through divide-and-conquer"
    "The information capacity of the channel is bounded by 1 - H(p)"

Category B — Empirical claims with mathematical bridge (partially verifiable):
    "Gene X upregulates pathway Y via mechanism Z where Z = k₁[X]/(k₂+[X])"
    "The neural network's generalization error follows ε ≤ C·√(d/n)"

Category C — Purely qualitative claims (not formally verifiable):
    "Sleep serves a metabolic clearance function"
    "Consciousness emerges from integrated information"
    "The culture of open science improves reproducibility"

For Category A → full formal verification (Lean4/Coq/Dafny/Z3)
For Category B → structural check + flag unvalidated assumptions
For Category C → skip formal verification, use literature consistency only
"""
from __future__ import annotations

import re
from typing import Any


MATH_INDICATORS = {
    "equation": re.compile(r"=.*[+\-*/^].*=|d/dt|∂|∇|∫|∑|∏|lim|sup|inf"),
    "inequality": re.compile(r"≤|<|≥|>|≪|≫"),
    "complexity": re.compile(r"O\(|Θ\(|Ω\(|o\("),
    "probability": re.compile(r"P\(|E\[|Var\[|Cov\[|Pr\("),
    "topology": re.compile(r"manifold|homeomorphic|homotopy|fibration|bundle"),
    "algebra": re.compile(r"group|ring|field|module|vector space|algebra"),
    "information_theory": re.compile(r"entropy|mutual information|channel capacity|KL divergence"),
    "numerical": re.compile(r"\d+\.?\d*\s*(?:kg|m|s|K|J|mol|Hz|Pa|N)"),
}


def detect_math_structure(hypothesis: str) -> dict[str, Any]:
    """Detect what kind of mathematical structure (if any) exists in a hypothesis."""
    matches: dict[str, list[str]] = {}
    for category, pattern in MATH_INDICATORS.items():
        found = pattern.findall(hypothesis)
        if found:
            matches[category] = found[:5]

    category = "C"  # Default: qualitative
    if len(matches) >= 3:
        category = "A"  # Rich mathematical scaffolding
    elif len(matches) >= 1:
        category = "B"  # Some mathematical bridge

    return {
        "category": category,
        "category_label": {
            "A": "MATHEMATICALLY SCAFFOLDED — formal verification applicable",
            "B": "EMPIRICAL WITH MATH BRIDGE — structural check with flagged assumptions",
            "C": "PURELY QUALITATIVE — formal verification not applicable",
        }[category],
        "matched_structures": list(matches.keys()),
        "matches": {k: v[:3] for k, v in matches.items()},
        "verifiability_score": {"A": 0.8, "B": 0.4, "C": 0.0}[category],
    }


def should_attempt_formal_verification(hypothesis: str) -> bool:
    """Decide whether formal verification is worth attempting."""
    assessment = detect_math_structure(hypothesis)
    return assessment["category"] in ("A", "B")
