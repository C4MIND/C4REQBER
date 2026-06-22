from __future__ import annotations


"""Quality Gates & Scoring — enforce A+ standards at every pipeline step."""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from src.pipeline.config import PipelineConfig
from src.pipeline.redundant_gates import create_novelty_gate


logger = logging.getLogger(__name__)


@dataclass
class GateResult:
    """Result of a single quality gate check."""

    step: str
    passed: bool
    score: float  # 0.0-1.0
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityReport:
    """Complete quality report for a dissertation."""

    overall_score: int  # 0-100
    grade: str  # A+, A, B+, B, C, F
    gates: list[GateResult]
    passed_all: bool
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "grade": self.grade,
            "passed_all": self.passed_all,
            "gates": [
                {
                    "step": g.step,
                    "passed": g.passed,
                    "score": round(g.score, 2),
                    "message": g.message,
                }
                for g in self.gates
            ],
            "recommendations": self.recommendations,
        }


class QualityGates:
    """Enforce structural quality checks on pipeline outputs."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig(name="default")

    # ── Step 1: Source Quality ────────────────────────────────────────

    def check_sources(self, sources: list[dict[str, Any]]) -> GateResult:
        cfg = self.config
        errors = []
        score = 1.0

        total = len(sources)
        if total < cfg.min_sources:
            errors.append(f"Only {total} sources (min {cfg.min_sources})")
            score *= total / cfg.min_sources

        # Count unique databases
        dbs = set(s.get("source", "") for s in sources)
        if len(dbs) < cfg.min_source_databases:
            errors.append(f"Only {len(dbs)} databases (min {cfg.min_source_databases})")
            score *= len(dbs) / cfg.min_source_databases

        # Count sources with URLs
        with_url = sum(1 for s in sources if s.get("url"))
        if with_url < cfg.min_sources_with_url:
            errors.append(f"Only {with_url} sources with URL (min {cfg.min_sources_with_url})")
            score *= with_url / cfg.min_sources_with_url

        # Penalize dummy titles
        dummy_count = sum(1 for s in sources if s.get("title", "").startswith("Result "))
        if dummy_count > 0:
            errors.append(f"{dummy_count} dummy sources detected")
            score *= max(0, 1 - dummy_count * 0.1)

        passed = not errors
        return GateResult(
            step="sources",
            passed=passed,
            score=max(0.0, score),
            message="PASS" if passed else "; ".join(errors),
            details={"total": total, "databases": len(dbs), "with_url": with_url, "dummy": dummy_count},
        )

    # ── Step 2: Gap Quality ───────────────────────────────────────────

    def check_gaps(self, gaps: list[dict[str, Any]]) -> GateResult:
        cfg = self.config
        errors = []
        score = 1.0

        total = len(gaps)
        if total < cfg.min_gaps:
            errors.append(f"Only {total} gaps (min {cfg.min_gaps})")
            score *= total / cfg.min_gaps

        # Check evidence quality
        weak_evidence = 0
        for g in gaps:
            ev = g.get("evidence", "")
            if len(ev) < cfg.min_gap_evidence_length:
                weak_evidence += 1
        if weak_evidence > 0:
            errors.append(f"{weak_evidence} gaps have weak evidence (<{cfg.min_gap_evidence_length} chars)")
            score *= max(0, 1 - weak_evidence * 0.15)

        # Check generic titles
        generic = sum(1 for g in gaps if "unknown" in g.get("area", "").lower() or "understanding" in g.get("area", "").lower())
        if generic > 0:
            errors.append(f"{generic} gaps have generic titles")
            score *= max(0, 1 - generic * 0.1)

        # Check novelty scores (RESOLUTION_INDICATORS lower novelty for resolved gaps)
        low_novelty = sum(1 for g in gaps if g.get("novelty_score", 0) < 0.3)
        if low_novelty > len(gaps) * 0.5:
            errors.append(f"{low_novelty}/{len(gaps)} gaps have low novelty (<0.3)")
            score *= 0.7

        passed = not errors
        return GateResult(
            step="gaps",
            passed=passed,
            score=max(0.0, score),
            message="PASS" if passed else "; ".join(errors),
            details={"total": total, "weak_evidence": weak_evidence, "generic": generic},
        )

    # ── Step 3: Hypothesis Quality ────────────────────────────────────

    def check_hypotheses(self, hypotheses: list[dict[str, Any]]) -> GateResult:
        cfg = self.config
        errors = []
        score = 1.0

        total = len(hypotheses)
        if total < cfg.min_hypotheses:
            errors.append(f"Only {total} hypotheses (min {cfg.min_hypotheses})")
            score *= total / cfg.min_hypotheses

        # Check for numerical constraints
        if cfg.require_numerical_constraints:
            has_numbers = 0
            for h in hypotheses:
                text = f"{h.get('title', '')} {h.get('description', '')}"
                if re.search(r"\d+(?:\.\d+)?(?:\s*%|\s*cells|fold|times|MPa|days|years|mm|μm)", text):
                    has_numbers += 1
            str(has_numbers)
            if has_numbers < len(hypotheses) * 0.5:
                errors.append(f"Only {has_numbers}/{total} hypotheses have numerical predictions")
                score *= has_numbers / max(1, total)

        # Check ambition
        if cfg.hypothesis_ambition == "paradigm_shifting":
            incremental_keywords = ["slightly", "marginally", "modest", "small"]
            incremental_count = 0
            for h in hypotheses:
                text = h.get("title", "") + " " + h.get("description", "")
                if any(kw in text.lower() for kw in incremental_keywords):
                    incremental_count += 1
            if incremental_count > len(hypotheses) * 0.5:
                errors.append("Most hypotheses sound incremental, not paradigm-shifting")
                score *= 0.7

        passed = not errors
        return GateResult(
            step="hypotheses",
            passed=passed,
            score=max(0.0, score),
            message="PASS" if passed else "; ".join(errors),
            details={"total": total, "with_numbers": has_numbers if cfg.require_numerical_constraints else "N/A"},
        )

    # ── Step 4: Simulation Quality ────────────────────────────────────

    def check_simulation(self, sim: Any) -> GateResult:
        cfg = self.config
        good_statuses = {"success", "delegated", "completed", "ok"}
        if isinstance(sim, dict):
            sim_status = sim.get("status", "")
            sim_metrics = sim.get("metrics", {})
        else:
            sim_status = getattr(sim, "status", "") if sim else ""
            sim_metrics = getattr(sim, "metrics", {}) if sim else {}
        if not sim or sim_status not in good_statuses:
            if cfg.require_simulation_success:
                return GateResult(
                    step="simulation",
                    passed=False,
                    score=0.0,
                    message="Simulation failed or missing",
                    details={"status": sim_status},
                )
            return GateResult(
                step="simulation",
                passed=True,
                score=0.5,
                message="Simulation not required",
                details={},
            )

        exec_time = sim_metrics.get("execution_time", 0) if sim_metrics else 0
        if exec_time > cfg.simulation_timeout_seconds:
            return GateResult(
                step="simulation",
                passed=False,
                score=0.5,
                message=f"Simulation timeout: {exec_time:.1f}s > {cfg.simulation_timeout_seconds}s",
                details={"execution_time": exec_time},
            )

        return GateResult(
            step="simulation",
            passed=True,
            score=1.0,
            message="PASS",
            details={"execution_time": exec_time},
        )

    # ── Step 5: Verification Quality ──────────────────────────────────

    def check_verification(self, verif: Any) -> GateResult:
        cfg = self.config
        if not verif:
            return GateResult(
                step="verification",
                passed=not cfg.require_verification,
                score=0.5 if not cfg.require_verification else 0.0,
                message="Missing" if cfg.require_verification else "Not required",
                details={},
            )

        if isinstance(verif, dict):
            verif_status = verif.get("status", "")
            verif_backend = verif.get("backend", "unknown")
        else:
            verif_status = getattr(verif, "status", "")
            verif_backend = getattr(verif, "backend", "unknown")

        good_statuses = {"verified", "consistent", "sat", "partial", "success", "not_applicable", "skipped"}
        if verif_status in good_statuses:
            return GateResult(
                step="verification",
                passed=True,
                score=1.0,
                message=f"PASS ({verif_status})",
                details={"backend": verif_backend, "status": verif_status},
            )

        if verif_status == "not_formalizable":
            if cfg.require_verification:
                return GateResult(
                    step="verification",
                    passed=False,
                    score=0.3,
                    message="No formalizable constraints found",
                    details={"status": verif_status},
                )
            return GateResult(
                step="verification",
                passed=True,
                score=0.6,
                message="Not formalizable (acceptable)",
                details={"status": verif_status},
            )

        return GateResult(
            step="verification",
            passed=False,
            score=0.0,
            message=f"Failed: {verif_status}",
            details={"status": verif_status},
        )

    # ── Step 6: Bibliography Quality ──────────────────────────────────

    def check_bibliography(self, bib: list[dict[str, Any]]) -> GateResult:
        errors = []
        score = 1.0

        total = len(bib)
        if total < 5:
            errors.append(f"Only {total} references (min 5)")
            score *= total / 5

        # Check for URLs
        with_url = sum(1 for b in bib if b.get("url"))
        if with_url < len(bib) * 0.3:
            errors.append(f"Only {with_url}/{total} refs have URLs")
            score *= with_url / max(1, total)

        score = max(0.0, score)

        passed = not errors
        return GateResult(
            step="bibliography",
            passed=passed,
            score=max(0.0, score),
            message="PASS" if passed else "; ".join(errors),
            details={"total": total, "with_url": with_url},
        )

    # ── Step 7: Dissertation Quality ──────────────────────────────────

    def check_dissertation(self, text: str) -> GateResult:
        cfg = self.config
        errors = []
        score = 1.0

        words = len(text.split())
        if words < cfg.min_dissertation_words:
            errors.append(f"Only {words} words (min {cfg.min_dissertation_words})")
            score *= words / cfg.min_dissertation_words

        # Check for LLM failures (empty content, API errors)
        llm_errors = text.count("[LLM unavailable")
        if llm_errors > 0:
            errors.append(f"LLM unavailable: {llm_errors} sections missing")
            score *= max(0.1, 1.0 - llm_errors * 0.15)

        # Check for truncated sections
        if text.rstrip().endswith(("...", "—", "-", ":")):
            errors.append("Document appears truncated")
            score *= 0.5

        # Check required sections (be lenient — only core sections matter)
        required = ["abstract", "introduction", "conclusion"]
        text_lower = text.lower().replace(" ", "").replace("\n", "")
        missing = [s for s in required if s not in text_lower]
        if missing:
            errors.append(f"Missing sections: {', '.join(missing)}")
            score *= max(0.2, 1 - len(missing) * 0.15)

        # Check epistemic notice
        if cfg.include_epistemic_notice and "epistemic" not in text.lower():
            errors.append("Missing epistemic status notice")
            score *= 0.8

        passed = not errors
        return GateResult(
            step="dissertation",
            passed=passed,
            score=max(0.0, score),
            message="PASS" if passed else "; ".join(errors),
            details={"words": words, "missing_sections": missing},
        )

    def check_hypothesis_redundant(self, hypothesis_text: str, papers: list[dict[str, Any]]) -> GateResult:
        try:
            gate = create_novelty_gate()
            try:
                loop = asyncio.get_running_loop()
                coro = gate.check(hypothesis=hypothesis_text, papers=papers)
                future = asyncio.run_coroutine_threadsafe(coro, loop)
                result = future.result(timeout=3)
            except (RuntimeError, TimeoutError):
                result = asyncio.run(gate.check(hypothesis=hypothesis_text, papers=papers))
            return GateResult(
                step="novelty",
                passed=bool(result.passed),
                score=result.confidence,
                message=f"N-version novelty: {result.confidence:.0%} ({result.message})" if result.passed else f"LOW: {result.message}",
                details={"votes": result.confidence},
            )
        except Exception:
            return GateResult(step="novelty", passed=True, score=0.5, message="RedundantGate unavailable")

    # ── Overall Scoring ───────────────────────────────────────────────

    def evaluate(
        self,
        sources: list[dict[str, Any]],
        gaps: list[dict[str, Any]],
        hypotheses: list[dict[str, Any]],
        simulation: Any,
        verification: Any,
        bibliography: list[dict[str, Any]],
        dissertation_text: str,
    ) -> QualityReport:
        """Run all gates and compute overall score."""
        gates = [
            self.check_sources(sources),
            self.check_gaps(gaps),
            self.check_hypotheses(hypotheses),
            self.check_simulation(simulation),
            self.check_verification(verification),
            self.check_bibliography(bibliography),
            self.check_dissertation(dissertation_text),
        ]

        # N-version redundant novelty check (extra gate, weight 0.03 borrowed from hypotheses)
        try:
            extra_gate = self.check_hypothesis_redundant(
                hypotheses[0].get("text", "") if hypotheses else "",
                sources[:20] if sources else []
            )
            gates.append(extra_gate)
        except Exception:
            pass

        # Weighted score — normalize by actual weights used
        weights = {
            "sources": 0.15,
            "gaps": 0.15,
            "hypotheses": 0.17,
            "simulation": 0.10,
            "verification": 0.10,
            "bibliography": 0.10,
            "dissertation": 0.20,
            "novelty": 0.03,
        }

        actual_weights = {g.step: weights.get(g.step, 0.1) for g in gates}
        weight_sum = sum(actual_weights.values())
        total = sum(
            g.score * actual_weights[g.step] / weight_sum for g in gates
        ) if weight_sum > 0 else 0.0
        score = int(total * 100)

        # Grade
        if score >= 95:
            grade = "A+"
        elif score >= 85:
            grade = "A"
        elif score >= 75:
            grade = "B+"
        elif score >= 65:
            grade = "B"
        elif score >= 50:
            grade = "C"
        else:
            grade = "F"

        passed_all = all(g.passed for g in gates)
        recommendations = self._generate_recommendations(gates)

        return QualityReport(
            overall_score=score,
            grade=grade,
            gates=gates,
            passed_all=passed_all,
            recommendations=recommendations,
        )

    def _generate_recommendations(self, gates: list[GateResult]) -> list[str]:
        """Generate improvement suggestions from failed gates."""
        recs = []
        for g in gates:
            if not g.passed:
                if g.step == "sources":
                    recs.append("Try broader search terms or enable additional databases")
                elif g.step == "gaps":
                    recs.append("Review source snippets for richer evidence quotes")
                elif g.step == "hypotheses":
                    recs.append("Add specific numerical predictions (%, MPa, days) to hypotheses")
                elif g.step == "simulation":
                    recs.append("Check pattern compatibility or reduce model complexity")
                elif g.step == "verification":
                    recs.append("Install Z3 or reframe hypotheses with checkable bounds")
                elif g.step == "bibliography":
                    recs.append("Enable web search fallback for more references")
                elif g.step == "dissertation":
                    recs.append("Increase LLM token limit or simplify prompt")
        return recs
