# SPDX-License-Identifier: AGPL-3.0
# Copyright (c) 2026 c4reqber Contributors
from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


class ContradictionEngine:
    """Detect logical contradictions between two theoretical frameworks.

    Pipeline:
    1. Formalize each theory as {axioms, predictions, domain}
    2. Find overlapping domain (where both theories make predictions)
    3. Extract predictions for that domain
    4. Check for conflict: same domain, incompatible predictions
    5. Score contradiction strength
    6. Classify: DIRECT (same prediction, different values) vs
       INCOMPATIBLE (different functional forms) vs PARADOX (self-referential)
    """

    def __init__(self) -> None:
        self._contradiction_indicators = [
            "contradicts", "inconsistent with", "violates",
            "conflicts with", "incompatible", "fails to explain",
            "cannot account for", "breaks down when", "diverges from",
            "paradox", "anomaly", "tension between",
        ]

    def detect(
        self,
        theory_a: str,
        theory_b: str,
        domain: str = "",
        evidence: list[str] | None = None,
    ) -> dict[str, Any]:
        """Detect contradiction between two theories in a shared domain."""
        evidence = evidence or []

        # 1. Extract key claims from each theory
        claims_a = self._extract_claims(theory_a)
        claims_b = self._extract_claims(theory_b)

        # 2. Find overlapping domain
        overlap = self._find_overlap(claims_a, claims_b, domain)

        # 3. Check for direct contradictions
        contradictions = []
        for pred_a in claims_a.get("predictions", []):
            for pred_b in claims_b.get("predictions", []):
                conflict = self._check_conflict(pred_a, pred_b, overlap)
                if conflict:
                    contradictions.append(conflict)

        # 4. Score
        strength = self._score_contradiction(contradictions, evidence)

        # 5. Classify
        ctype = self._classify(contradictions, theory_a, theory_b)

        return {
            "contradictions": contradictions[:10],
            "count": len(contradictions),
            "strength": round(strength, 4),
            "type": ctype,
            "resolution_possible": strength < 0.7,
            "recommended_approach": self._recommend(ctype, strength),
            "domain_overlap": overlap,
            "theory_a_claims": len(claims_a.get("predictions", [])),
            "theory_b_claims": len(claims_b.get("predictions", [])),
        }

    def _extract_claims(self, text: str) -> dict[str, list[str]]:
        """Extract axioms and predictions from theory text."""
        text_lower = text.lower()
        axioms: list[str] = []
        predictions: list[str] = []

        sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if len(s.strip()) > 10]

        for s in sentences:
            s_l = s.lower()
            if any(kw in s_l for kw in ("assume", "postulate", "axiom", "suppose", "define")):
                axioms.append(s)
            elif any(kw in s_l for kw in ("predict", "implies", "therefore", "thus", "hence", "yields", "follows")):
                predictions.append(s)
            elif any(kw in s_l for kw in ("is", "are", "must", "cannot", "always", "never")):
                predictions.append(s)  # declarative statements are predictions

        return {"axioms": axioms[:20], "predictions": predictions[:30]}

    def _find_overlap(self, claims_a: dict[str, list[str]], claims_b: dict[str, list[str]], domain: str) -> dict[str, Any]:
        """Find shared domain concepts between theories."""
        tokens_a: set[str] = set()
        tokens_b: set[str] = set()

        for s in claims_a.get("predictions", []) + claims_a.get("axioms", []):
            tokens_a.update(w.strip(".,;:()[]") for w in s.lower().split() if len(w) > 3)
        for s in claims_b.get("predictions", []) + claims_b.get("axioms", []):
            tokens_b.update(w.strip(".,;:()[]") for w in s.lower().split() if len(w) > 3)

        shared = tokens_a & tokens_b

        # Filter non-content words
        content_filter = {"that", "this", "with", "from", "have", "been", "they", "their", "will", "when", "than", "more"}
        shared_terms = sorted(shared - content_filter)

        return {
            "shared_terms": shared_terms[:20],
            "count": len(shared_terms),
            "domain": domain or "theory",
            "coverage_a": len(shared_terms) / max(1, len(tokens_a - content_filter)),
            "coverage_b": len(shared_terms) / max(1, len(tokens_b - content_filter)),
        }

    def _check_conflict(self, pred_a: str, pred_b: str, overlap: dict[str, Any]) -> dict[str, Any] | None:
        """Check if two predictions conflict."""
        shared = set(overlap.get("shared_terms", []))
        tokens_a = set(pred_a.lower().split())
        tokens_b = set(pred_b.lower().split())

        # Must share some domain terms to be comparable
        if not (shared & tokens_a) or not (shared & tokens_b):
            return None

        # Check for direct negation
        negations_a = {"not", "never", "cannot", "no", "impossible"}
        negations_b = {"not", "never", "cannot", "no", "impossible"}

        has_neg_a = bool(negations_a & tokens_a)
        has_neg_b = bool(negations_b & tokens_b)

        # Direct contradiction: one says X, other says not-X
        if has_neg_a != has_neg_b:
            return {
                "type": "direct",
                "prediction_a": pred_a[:200],
                "prediction_b": pred_b[:200],
                "mechanism": "negation",
            }

        # Quantitative conflict: different values for same quantity
        numbers_a = self._extract_numbers(pred_a)
        numbers_b = self._extract_numbers(pred_b)
        if numbers_a and numbers_b:
            ratio = abs(numbers_a[0] - numbers_b[0]) / max(abs(numbers_a[0]), abs(numbers_b[0]), 0.001)
            if ratio > 0.1:  # >10% difference
                return {
                    "type": "quantitative",
                    "prediction_a": pred_a[:200],
                    "prediction_b": pred_b[:200],
                    "value_a": numbers_a[0],
                    "value_b": numbers_b[0],
                    "ratio": round(ratio, 4),
                    "mechanism": "different_values",
                }

        # Structural conflict: different functional forms
        forms_a = self._extract_forms(pred_a)
        forms_b = self._extract_forms(pred_b)
        if forms_a and forms_b and forms_a != forms_b:
            shared_vars = set(forms_a.keys()) & set(forms_b.keys())
            if shared_vars:
                return {
                    "type": "structural",
                    "prediction_a": pred_a[:200],
                    "prediction_b": pred_b[:200],
                    "form_a": forms_a,
                    "form_b": forms_b,
                    "shared_vars": list(shared_vars),
                    "mechanism": "different_functional_form",
                }

        return None

    def _extract_numbers(self, text: str) -> list[float]:
        import re
        nums = re.findall(r"[\d]+\.?[\d]*", text)
        return [float(n) for n in nums if float(n) > 0 and float(n) < 1e12][:3]

    def _extract_forms(self, text: str) -> dict[str, set[str]]:
        """Extract functional relationships: 'X depends on Y', 'Z ∝ W²' etc."""
        forms: dict[str, set[str]] = {}
        rel_indicators = ["depends on", "proportional to", "function of", "varies with", "∝", "f(", "g("]
        text_l = text.lower()
        for indicator in rel_indicators:
            if indicator in text_l:
                idx = text_l.find(indicator)
                before = text_l[max(0, idx - 30):idx].split()[-2:]
                after = text_l[idx + len(indicator):idx + len(indicator) + 30].split()[:2]
                for b in before:
                    if len(b) > 1:
                        forms[b] = set(after)
        return forms

    def _score_contradiction(self, contradictions: list[dict[str, Any]], evidence: list[str]) -> float:
        n = len(contradictions)
        if n == 0:
            return 0.0
        # Weighted by type
        weights = {"direct": 1.0, "quantitative": 0.8, "structural": 0.6}
        weighted = sum(weights.get(c.get("type", "structural"), 0.5) for c in contradictions)
        # Evidence confirmed contradictions score higher
        evidence_bonus = min(0.2, 0.05 * len(evidence))
        raw = min(1.0, weighted / (n * 0.8 + 0.2))
        return min(1.0, raw + evidence_bonus)

    def _classify(self, contradictions: list[dict[str, Any]], theory_a: str, theory_b: str) -> str:
        types = set(c.get("type") for c in contradictions)
        if "direct" in types:
            return "DIRECT_CONTRADICTION"
        if "quantitative" in types and "structural" in types:
            return "DEEP_INCOMPATIBILITY"
        if "structural" in types:
            return "STRUCTURAL_MISMATCH"
        if contradictions:
            return "TENSION"
        return "COMPATIBLE"

    def _recommend(self, ctype: str, strength: float) -> str:
        if ctype == "DIRECT_CONTRADICTION":
            return "Apply Abstraction Ladder → seek meta-level unifying principle (Z₃³ Scale:META)"
        if ctype == "DEEP_INCOMPATIBILITY":
            return "Constraint Solver → find invariant-preserving transformations between frameworks"
        if ctype == "STRUCTURAL_MISMATCH":
            return "Isomorphism Scanner → map structural invariants across domains"
        if ctype == "TENSION":
            return "Multi-Step Chain → refine hypothesis iteratively with self-validation"
        return "No contradiction detected — theories are compatible in this domain"


__all__ = ["ContradictionEngine"]
