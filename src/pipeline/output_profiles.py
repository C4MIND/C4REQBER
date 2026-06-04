# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class OutputFormat(Enum):
    """OutputFormat."""
    DISSERTATION = "dissertation"
    ARTICLE = "article"
    WHITEPAPER = "whitepaper"
    BLUEPRINT = "blueprint"
    CODE = "code"
    VERIFICATION_REPORT = "verification_report"


@dataclass
class OutputProfile:
    """OutputProfile."""
    format: OutputFormat
    label: str
    description: str

    # Size limits per pipeline mode: turbo / solve / turbofactory
    word_min: dict[str, int] = field(default_factory=dict)   # {"turbo": 2000, "solve": 800, ...}
    word_max: dict[str, int] = field(default_factory=dict)
    word_optimal: dict[str, int] = field(default_factory=dict)
    page_estimate: dict[str, str] = field(default_factory=dict)  # "5-15" etc

    # Generation config
    prompt_role: str = "You are an academic researcher writing a paper."
    prompt_structure: str = ""  # Additional structure instructions
    require_abstract: bool = True
    require_sections: bool = True
    require_references: bool = True
    require_epistemic_notice: bool = True

    # Verification auto-selection
    verification_backends: list[str] = field(default_factory=lambda: ["lean4", "coq", "dafny", "agda", "z3", "hoare"])
    require_formal_proof: bool = False
    require_empirical_validation: bool = False

    # Export
    file_extension: str = ".md"
    export_formats: list[str] = field(default_factory=lambda: ["markdown", "json"])

    # Detection keywords (used by Phase A auto-classifier)
    detection_keywords: list[str] = field(default_factory=list)


OUTPUT_PROFILES: dict[OutputFormat, OutputProfile] = {
    OutputFormat.DISSERTATION: OutputProfile(
        format=OutputFormat.DISSERTATION,
        label="Academic Dissertation",
        description="Full academic dissertation with abstract, introduction, methods, results, discussion, references",
        word_min={"turbo": 2000, "solve": 1200, "turbofactory": 3000},
        word_max={"turbo": 8000, "solve": 4000, "turbofactory": 15000},
        word_optimal={"turbo": 4000, "solve": 2000, "turbofactory": 6000},
        page_estimate={"turbo": "5-15", "solve": "3-8", "turbofactory": "10-50"},
        prompt_role="You are a distinguished professor writing a paradigm-shifting academic dissertation.",
        prompt_structure="Include: Abstract, Introduction, Literature Review, Methodology, Results, Discussion, Conclusion, References.",
        verification_backends=["lean4", "coq", "dafny", "agda", "z3", "hoare"],
        require_formal_proof=True,
        file_extension=".md",
        export_formats=["markdown", "json", "bibtex", "latex"],
        detection_keywords=["dissertation", "thesis", "paradigm", "shift", "prove", "theorem", "hypothesis"],
    ),

    OutputFormat.ARTICLE: OutputProfile(
        format=OutputFormat.ARTICLE,
        label="Scientific Article",
        description="Journal-style scientific paper (4-12 pages)",
        word_min={"turbo": 1500, "solve": 800, "turbofactory": 3000},
        word_max={"turbo": 5000, "solve": 2500, "turbofactory": 8000},
        word_optimal={"turbo": 2500, "solve": 1500, "turbofactory": 4000},
        page_estimate={"turbo": "4-12", "solve": "2-6", "turbofactory": "8-20"},
        prompt_role="You are a senior researcher writing a scientific paper for journal submission.",
        prompt_structure="Include: Abstract, Introduction, Methods, Results, Discussion, References. Target: journal-ready formatting.",
        verification_backends=["z3", "dafny", "hoare"],
        require_formal_proof=False,
        require_empirical_validation=True,
        file_extension=".md",
        export_formats=["markdown", "json", "bibtex", "latex"],
        detection_keywords=["paper", "article", "journal", "study", "experiment", "empirical", "survey", "review"],
    ),

    OutputFormat.WHITEPAPER: OutputProfile(
        format=OutputFormat.WHITEPAPER,
        label="Technical Whitepaper",
        description="Architecture document with diagrams, tradeoffs, recommendations",
        word_min={"turbo": 2000, "solve": 1000, "turbofactory": 3000},
        word_max={"turbo": 6000, "solve": 3000, "turbofactory": 10000},
        word_optimal={"turbo": 3000, "solve": 1500, "turbofactory": 5000},
        page_estimate={"turbo": "5-15", "solve": "3-7", "turbofactory": "8-25"},
        prompt_role="You are a senior software architect writing a technical whitepaper.",
        prompt_structure="Include: Executive Summary, Problem Statement, Architecture Overview, Design Decisions, Trade-offs, Implementation Plan, Recommendations.",
        verification_backends=["z3", "cvc5", "alloy", "hoare"],  # SMT + Alloy for architecture verification
        require_formal_proof=False,
        require_epistemic_notice=False,
        file_extension=".md",
        export_formats=["markdown", "json", "html"],
        detection_keywords=["architecture", "design", "system", "framework", "whitepaper", "technical report", "platform"],
    ),

    OutputFormat.BLUEPRINT: OutputProfile(
        format=OutputFormat.BLUEPRINT,
        label="Engineering Blueprint",
        description="Structured specification with requirements, design, implementation",
        word_min={"turbo": 1500, "solve": 800, "turbofactory": 2500},
        word_max={"turbo": 5000, "solve": 2500, "turbofactory": 8000},
        word_optimal={"turbo": 2500, "solve": 1500, "turbofactory": 4000},
        page_estimate={"turbo": "3-12", "solve": "2-6", "turbofactory": "6-20"},
        prompt_role="You are a lead engineer writing a technical specification.",
        prompt_structure="Include: Requirements (functional + non-functional), System Design, Component Architecture, API Contracts, Data Flow, Security Model, Deployment Architecture.",
        verification_backends=["dafny", "z3", "hoare", "haskell-typecheck", "haskell-quickcheck"],
        require_formal_proof=True,
        require_epistemic_notice=False,
        file_extension=".md",
        export_formats=["markdown", "json", "code"],
        detection_keywords=["blueprint", "specification", "requirements", "api", "implementation plan", "system design", "component"],
    ),

    OutputFormat.CODE: OutputProfile(
        format=OutputFormat.CODE,
        label="Generated Code",
        description="Source code with inline verification and documentation",
        word_min={"turbo": 0, "solve": 0, "turbofactory": 0},  # Lines of code, not words
        word_max={"turbo": 0, "solve": 0, "turbofactory": 0},
        word_optimal={"turbo": 0, "solve": 0, "turbofactory": 0},
        page_estimate={"turbo": "100-500 LOC", "solve": "50-200 LOC", "turbofactory": "500-2000 LOC"},
        prompt_role="You are an expert programmer generating production-quality code.",
        prompt_structure="Include: File header, Imports, Class/Function definitions with docstrings, Inline comments, Type hints, Unit tests.",
        verification_backends=["dafny", "z3", "hoare", "haskell-typecheck", "haskell-quickcheck"],
        require_formal_proof=True,
        require_epistemic_notice=False,
        require_abstract=False,
        require_sections=False,
        require_references=False,
        file_extension=".py",
        export_formats=["code", "json"],
        detection_keywords=["code", "implement", "library", "function", "class", "algorithm", "api client", "script", "program"],
    ),

    OutputFormat.VERIFICATION_REPORT: OutputProfile(
        format=OutputFormat.VERIFICATION_REPORT,
        label="Verification Report",
        description="Formal verification output with proof artifacts and counterexample documentation",
        word_min={"turbo": 500, "solve": 300, "turbofactory": 1000},
        word_max={"turbo": 3000, "solve": 1500, "turbofactory": 5000},
        word_optimal={"turbo": 1000, "solve": 500, "turbofactory": 2000},
        page_estimate={"turbo": "1-5", "solve": "1-3", "turbofactory": "2-8"},
        prompt_role="You are a formal methods expert writing a verification report.",
        prompt_structure="Include: Theorem Statement, Proof Strategy, Verification Backend, Proof Status, Counterexample (if any), Coverage Report.",
        verification_backends=["lean4", "coq", "dafny", "agda", "z3", "cvc5", "hoare", "alloy", "tla"],
        require_formal_proof=True,
        require_epistemic_notice=False,
        require_abstract=False,
        file_extension=".md",
        export_formats=["markdown", "json", "latex"],
        detection_keywords=["verify", "prove", "proof", "theorem", "lemma", "coq", "lean", "dafny", "formal verification"],
    ),
}


def detect_format(problem: str, mode: str = "solve") -> OutputFormat:
    """Auto-detect output format from problem text via keyword scoring."""
    scores: dict[OutputFormat, int] = {}
    problem_lower = problem.lower()

    for fmt, profile in OUTPUT_PROFILES.items():
        score = sum(2 if kw in problem_lower else 1 if any(w in problem_lower for w in kw.split()) else 0 for kw in profile.detection_keywords)
        scores[fmt] = score

    # Boost dissertation for turbo mode
    if mode == "turbo":
        scores[OutputFormat.DISSERTATION] += 3

    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return OutputFormat.DISSERTATION if mode == "turbo" else OutputFormat.ARTICLE
    return best


def get_profile(fmt: OutputFormat) -> OutputProfile:
    return OUTPUT_PROFILES.get(fmt, OUTPUT_PROFILES[OutputFormat.DISSERTATION])
