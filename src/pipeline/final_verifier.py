from __future__ import annotations

import logging
from typing import Any


class FinalVerifier:
    """Post-pipeline output verifier.

    Phase 1.8 (von Neumann audit): After the pipeline produces output, verify that
    the result is genuinely novel and all gates were properly re-evaluated.
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger("c44tcdi.pipeline.final_verifier")

    async def verify(self, result: dict[str, Any], papers: list[dict[str, Any]]) -> VerificationReport:
        """Verify."""
        issues: list[str] = []
        warnings: list[str] = []

        hypothesis_text = self._extract_hypothesis(result)
        if not hypothesis_text:
            issues.append("No hypothesis text found in result")

        similarity_check = self._check_max_similarity(hypothesis_text, papers)
        if similarity_check["max_similarity"] > 0.85:
            issues.append(
                f"FLAGGED: hypothesis too similar to existing paper '{similarity_check['closest_title']}' "
                f"(similarity={similarity_check['max_similarity']:.2f})"
            )
        elif similarity_check["max_similarity"] > 0.70:
            warnings.append(
                f"Borderline similarity ({similarity_check['max_similarity']:.2f}) to '{similarity_check['closest_title']}'"
            )

        gate_issues = self._check_gates_reevaluated(result)
        issues.extend(gate_issues)

        report = VerificationReport(
            passed=len(issues) == 0,
            issue_count=len(issues),
            warning_count=len(warnings),
            issues=issues,
            warnings=warnings,
            max_similarity=similarity_check["max_similarity"],
            closest_paper=similarity_check["closest_title"],
        )
        return report

    def _extract_hypothesis(self, result: dict[str, Any]) -> str:
        hyp = result.get("hypothesis", {})
        if isinstance(hyp, dict):
            return str(hyp.get("text") or hyp.get("final_solution") or "")
        return str(hyp) if hyp else ""

    def _check_max_similarity(self, hypothesis: str, papers: list[dict[str, Any]]) -> dict[str, Any]:
        if not hypothesis or not papers:
            return {"max_similarity": 0.0, "closest_title": ""}
        max_sim = 0.0
        closest_title = ""
        hyp_lower = hypothesis.lower()
        for p in papers:
            title = p.get("title", "")
            abstract = p.get("abstract", p.get("snippet", ""))
            text = f"{title} {abstract}".lower()
            if not text.strip():
                continue
            sim = self._jaccard_similarity(hyp_lower, text)
            if sim > max_sim:
                max_sim = sim
                closest_title = title
        return {"max_similarity": round(max_sim, 4), "closest_title": closest_title}

    @staticmethod
    def _jaccard_similarity(a: str, b: str) -> float:
        words_a = set(a.split())
        words_b = set(b.split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union) if union else 0.0

    def _check_gates_reevaluated(self, result: dict[str, Any]) -> list[str]:
        issues: list[str] = []
        abort_reasons_original = result.get("abort_reasons_original", [])
        refinement_history = result.get("refinement_history", [])
        if abort_reasons_original and not refinement_history:
            issues.append("Gates triggered but no refinement history — were they re-evaluated?")
        for entry in refinement_history:
            if not entry.get("paradigm_shift_rechecked"):
                issues.append(f"Iteration {entry.get('iteration', '?')}: paradigm_shift not rechecked")
        return issues


class VerificationReport:
    """VerificationReport."""
    def __init__(self, passed: bool, issue_count: int, warning_count: int, issues: list[str], warnings: list[str], max_similarity: float, closest_paper: str) -> None:
        self.passed = passed
        self.issue_count = issue_count
        self.warning_count = warning_count
        self.issues = issues
        self.warnings = warnings
        self.max_similarity = max_similarity
        self.closest_paper = closest_paper
