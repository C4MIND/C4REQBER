"""
C4REQBER: Physical Contradiction Extractor
Altshuller-style contradiction extraction from problem statements
"""
from __future__ import annotations

import re


try:
    from ..core.cdi_engine import ContradictionType, PhysicalContradiction
except ImportError:
    # For direct execution
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from core.cdi_engine import ContradictionType, PhysicalContradiction  # type: ignore[no-redef]


class ContradictionExtractor:
    """
    Extract physical contradictions from problem statements.

    Two-phase approach:
    1. Pattern matching (fast, deterministic)
    2. LLM analysis (deep, optional)
    """

    # Pattern templates for common contradictions
    PATTERNS: dict[str, re.Pattern] = {  # type: ignore[type-arg]
        "high_vs_low": re.compile(
            r"(?:must be|needs to be|should be)\s+(high|fast|large|strong|dense|heavy)"
            r".*?\s+(?:but|while|and)\s+(?:also|still|must remain)\s+(low|slow|small|weak|sparse|light)",
            re.IGNORECASE,
        ),
        "adjective_but_also_adjective": re.compile(
            r"(?:is|be)\s+(?:both\s+)?(\w+)\s+(?:and|but also)\s+(?:very\s+)?(\w+)",
            re.IGNORECASE,
        ),
        "trade_off": re.compile(
            r"(?:trade.off|balance|reconcile|resolve)\s+(?:between)?\s*(\w+)\s+and\s+(\w+)",
            re.IGNORECASE,
        ),
        "simultaneous": re.compile(
            r"(?:must|needs to)\s+(\w+)\s+(?:and|while|but)\s+(?:also|simultaneously)\s+(\w+)",
            re.IGNORECASE,
        ),
        "achieve_both": re.compile(
            r"(?:achieve|have|get)\s+(?:both\s+)?(\w+(?:\s+\w+)?)\s+and\s+(\w+(?:\s+\w+)?)",
            re.IGNORECASE,
        ),
    }

    # Domain-specific contradiction indicators
    DOMAIN_INDICATORS = {
        "battery": ["capacity", "charging speed", "cycle life", "safety"],
        "material": ["strength", "weight", "cost", "durability"],
        "software": ["security", "usability", "performance", "maintainability"],
        "medical": ["efficacy", "safety", "dosage", "side effects"],
    }

    def __init__(self, use_llm: bool = False) -> None:
        self.use_llm = use_llm

    def extract(self, problem_statement: str) -> PhysicalContradiction | None:
        """
        Extract physical contradiction from problem statement.

        Returns None if no clear contradiction found.
        """
        # Phase 1: Pattern matching
        contradiction = self._pattern_extract(problem_statement)
        if contradiction:
            return contradiction

        # Phase 2: Domain heuristic analysis
        contradiction = self._domain_heuristic_extract(problem_statement)
        if contradiction:
            return contradiction

        # Phase 3: LLM analysis (if enabled)
        if self.use_llm:
            return self._llm_extract(problem_statement)

        return None

    def _pattern_extract(self, problem: str) -> PhysicalContradiction | None:
        """Extract using regex patterns."""

        # Pattern: high X but low Y
        match = self.PATTERNS["high_vs_low"].search(problem)
        if match:
            high_val = match.group(1)
            low_val = match.group(2)

            return PhysicalContradiction(
                parameter="performance_metric",
                value_a=f"high/{high_val}",
                value_not_a=f"low/{low_val}",
                requirement_y="primary_objective",
                requirement_z="secondary_constraint",
                contradiction_type=ContradictionType.TRADE_OFF,
            )

        # Pattern: is/be [adj] and/but also [adj]
        match = self.PATTERNS["adjective_but_also_adjective"].search(problem)
        if match:
            return PhysicalContradiction(
                parameter="design_parameter",
                value_a=match.group(1),
                value_not_a=match.group(2),
                requirement_y=f"optimize_{match.group(1)}",
                requirement_z=f"optimize_{match.group(2)}",
                contradiction_type=ContradictionType.TRADE_OFF,
            )

        # Pattern: trade-off between X and Y
        match = self.PATTERNS["trade_off"].search(problem)
        if match:
            return PhysicalContradiction(
                parameter="design_parameter",
                value_a=match.group(1),
                value_not_a=match.group(2),
                requirement_y=f"optimize_{match.group(1)}",
                requirement_z=f"optimize_{match.group(2)}",
                contradiction_type=ContradictionType.TRADE_OFF,
            )

        # Pattern: must X and Y simultaneously
        match = self.PATTERNS["simultaneous"].search(problem)
        if match:
            return PhysicalContradiction(
                parameter="system_behavior",
                value_a=match.group(1),
                value_not_a=match.group(2),
                requirement_y="requirement_1",
                requirement_z="requirement_2",
                contradiction_type=ContradictionType.DUAL_REQUIREMENT,
            )

        # Pattern: achieve/have/get both X and Y
        match = self.PATTERNS["achieve_both"].search(problem)
        if match:
            # Detect domain from matched terms
            val_a = match.group(1).lower()
            val_b = match.group(2).lower()
            if "charging" in val_a or "charging" in val_b or "battery" in val_a or "battery" in val_b:
                parameter = "Charging characteristics"
            elif "energy" in val_a or "energy" in val_b:
                parameter = "Energy density"
            else:
                parameter = "system_behavior"
            return PhysicalContradiction(
                parameter=parameter,
                value_a=match.group(1),
                value_not_a=match.group(2),
                requirement_y=f"achieve_{match.group(1)}",
                requirement_z=f"achieve_{match.group(2)}",
                contradiction_type=ContradictionType.TRADE_OFF,
            )

        return None

    def _domain_heuristic_extract(
        self, problem: str
    ) -> PhysicalContradiction | None:
        """Extract using domain-specific heuristics."""
        problem_lower = problem.lower()

        # Check for battery domain
        if any(word in problem_lower for word in ["battery", "energy", "charging"]):
            if "fast" in problem_lower and "capacity" in problem_lower:
                return PhysicalContradiction(
                    parameter="Charging characteristics",
                    value_a="HIGH charging rate (fast)",
                    value_not_a="LOW charging rate (preserve capacity)",
                    requirement_y="Fast charging (user convenience)",
                    requirement_z="Long cycle life (capacity retention)",
                    contradiction_type=ContradictionType.TRADE_OFF,
                )
            if "fast" in problem_lower and "charging" in problem_lower and "life" in problem_lower:
                return PhysicalContradiction(
                    parameter="Charging characteristics",
                    value_a="FAST charging (high current)",
                    value_not_a="SLOW charging (preserve cycle life)",
                    requirement_y="Fast charging (user convenience)",
                    requirement_z="Long battery life (cycle retention)",
                    contradiction_type=ContradictionType.TRADE_OFF,
                )
            if "capacity" in problem_lower and ("light" in problem_lower or "weight" in problem_lower):
                return PhysicalContradiction(
                    parameter="Energy density",
                    value_a="HIGH capacity (energy storage)",
                    value_not_a="LOW weight (lightweight design)",
                    requirement_y="Long runtime / range",
                    requirement_z="Portability / weight minimization",
                    contradiction_type=ContradictionType.TRADE_OFF,
                )
            if "energy" in problem_lower and "density" in problem_lower and "charging" in problem_lower:
                return PhysicalContradiction(
                    parameter="Energy density",
                    value_a="HIGH energy density (range)",
                    value_not_a="FAST charging (power delivery)",
                    requirement_y="Long vehicle range",
                    requirement_z="Short charging time",
                    contradiction_type=ContradictionType.TRADE_OFF,
                )

        # Check for material domain
        if any(
            word in problem_lower for word in ["material", "structure", "component"]
        ):
            if "strong" in problem_lower and "light" in problem_lower:
                return PhysicalContradiction(
                    parameter="Material density",
                    value_a="HIGH density (strength)",
                    value_not_a="LOW density (lightweight)",
                    requirement_y="Structural integrity",
                    requirement_z="Weight minimization",
                    contradiction_type=ContradictionType.TRADE_OFF,
                )

        # Check for software domain
        if any(word in problem_lower for word in ["software", "system", "app"]):
            if "secure" in problem_lower and ("usable" in problem_lower or "easy" in problem_lower):
                return PhysicalContradiction(
                    parameter="Authentication strictness",
                    value_a="STRICT (multi-factor, complex)",
                    value_not_a="LENIENT (simple, fast)",
                    requirement_y="Security (prevent breaches)",
                    requirement_z="Usability (user adoption)",
                    contradiction_type=ContradictionType.TRADE_OFF,
                )

        return None

    def _llm_extract(self, problem: str) -> PhysicalContradiction | None:
        """
        Extract using LLM analysis.

        Uses OpenRouter API to analyze problem and extract contradiction.
        Falls back to pattern matching if LLM unavailable.
        """
        try:
            # Try to import and use LLM client
            from ..llm.client import LLMClient

            llm = LLMClient()
            if llm.api_key == "mock":
                # LLM not configured, skip
                return None

            prompt = f"""Analyze this problem and extract the physical contradiction in Altshuller TRIZ format.

Problem: {problem}

Identify:
1. PARAMETER - What property is in conflict?
2. VALUE_A - What value is needed for one requirement?
3. VALUE_NOT_A - What opposite value is needed for another requirement?
4. REQUIREMENT_Y - What requires VALUE_A?
5. REQUIREMENT_Z - What requires VALUE_NOT_A?

Respond in this exact format:
PARAMETER: <parameter name>
VALUE_A: <value A>
VALUE_NOT_A: <value not A>
REQUIREMENT_Y: <requirement Y>
REQUIREMENT_Z: <requirement Z>"""

            response = llm.generate(prompt, max_tokens=300, temperature=0.3)
            content = response.content

            # Parse response
            param_match = re.search(r"PARAMETER:\s*(.+)", content, re.IGNORECASE)
            value_a_match = re.search(r"VALUE_A:\s*(.+)", content, re.IGNORECASE)
            value_not_a_match = re.search(
                r"VALUE_NOT_A:\s*(.+)", content, re.IGNORECASE
            )
            req_y_match = re.search(r"REQUIREMENT_Y:\s*(.+)", content, re.IGNORECASE)
            req_z_match = re.search(r"REQUIREMENT_Z:\s*(.+)", content, re.IGNORECASE)

            if all(
                [
                    param_match,
                    value_a_match,
                    value_not_a_match,
                    req_y_match,
                    req_z_match,
                ]
            ):
                return PhysicalContradiction(
                    parameter=param_match.group(1).strip(),  # type: ignore[union-attr]
                    value_a=value_a_match.group(1).strip(),  # type: ignore[union-attr]
                    value_not_a=value_not_a_match.group(1).strip(),  # type: ignore[union-attr]
                    requirement_y=req_y_match.group(1).strip(),  # type: ignore[union-attr]
                    requirement_z=req_z_match.group(1).strip(),  # type: ignore[union-attr]
                    contradiction_type=ContradictionType.PHYSICAL,  # type: ignore[attr-defined]
                )

            return None

        except (ImportError, ConnectionError, TimeoutError, ValueError, RuntimeError):
            return None

    def extract_all(self, problem_statement: str) -> list[PhysicalContradiction]:
        """Extract all possible contradictions (may return multiple)."""
        contradictions = []

        # Primary extraction
        primary = self.extract(problem_statement)
        if primary:
            contradictions.append(primary)

        return contradictions


class ContradictionLibrary:
    """
    Library of common physical contradictions by domain.
    """

    CONTRADICTIONS: dict[str, list[PhysicalContradiction]] = {
        "battery": [
            PhysicalContradiction(
                parameter="Energy density",
                value_a="HIGH (>500 Wh/kg)",
                value_not_a="SAFE (stable chemistry)",
                requirement_y="Vehicle range",
                requirement_z="Safety certification",
                contradiction_type=ContradictionType.TRADE_OFF,
            ),
            PhysicalContradiction(
                parameter="Charging speed",
                value_a="FAST (<10 min)",
                value_not_a="SLOW (prevent dendrites)",
                requirement_y="User convenience",
                requirement_z="Cycle life >1000",
                contradiction_type=ContradictionType.TRADE_OFF,
            ),
        ],
        "aircraft": [
            PhysicalContradiction(
                parameter="Structural weight",
                value_a="HEAVY (strength)",
                value_not_a="LIGHT (fuel efficiency)",
                requirement_y="Structural integrity",
                requirement_z="Range/payload",
                contradiction_type=ContradictionType.TRADE_OFF,
            ),
        ],
        "software": [
            PhysicalContradiction(
                parameter="Code complexity",
                value_a="COMPLEX (features)",
                value_not_a="SIMPLE (maintainability)",
                requirement_y="Feature richness",
                requirement_z="Developer velocity",
                contradiction_type=ContradictionType.TRADE_OFF,
            ),
        ],
    }

    @classmethod
    def get_by_domain(cls, domain: str) -> list[PhysicalContradiction]:
        """Get common contradictions for a domain."""
        return cls.CONTRADICTIONS.get(domain, [])

    @classmethod
    def match_problem_to_contradictions(
        cls, problem: str, domain: str | None = None
    ) -> list[PhysicalContradiction]:
        """Match problem to known contradictions in library."""
        if domain and domain in cls.CONTRADICTIONS:
            return cls.CONTRADICTIONS[domain]

        # Search all domains for keyword matches
        matches = []
        problem_lower = problem.lower()

        for domain_name, contradictions in cls.CONTRADICTIONS.items():
            if domain_name in problem_lower:
                matches.extend(contradictions)

        return matches
