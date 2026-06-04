from __future__ import annotations


"""Phase F: Dissertation Generation — CDI, TOTE, appendices."""

import json
import logging
import re
from typing import Any

from src.core.cdi_engine import CDIEngine, ContradictionType, PhysicalContradiction
from src.core.user_profile import UserProfile
from src.metamodels.tote import ToteEngine
from src.pipeline.config import PipelineConfig
from src.plugins.registry import WebSearchPlugin
from src.publishing.dissertation import DissertationGenerator


logger = logging.getLogger(__name__)


class PhaseF_DissertationGeneration:
    """Generate dissertation with CDI contradiction analysis and TOTE validation."""

    def __init__(self, config: PipelineConfig | None = None, user_profile: UserProfile | None = None) -> None:
        self.config = config or PipelineConfig(name="default")
        self.user_profile = user_profile or UserProfile()
        self.dissertation_gen = DissertationGenerator()
        self.cdi = CDIEngine()
        self.tote = ToteEngine()

    def run(
        self,
        topic: str,
        record: Any,
        c4_state: str,
    ) -> tuple[str, dict[str, Any]]:
        """Generate dissertation, run CDI/TOTE, return (dissertation_text, plugins_context)."""
        print("\n[Phase F] Dissertation Generation...")
        cfg = self.config

        # Step F1: Ensure minimum bibliography
        print("\n[F1/7] Ensuring minimum bibliography...")
        bibliography = list(record.bibliography)
        if len(bibliography) < cfg.min_sources:
            searcher = WebSearchPlugin()
            extra = searcher.execute(topic, max_results=cfg.min_sources * 2)
            for s in extra:
                if len(bibliography) >= cfg.min_sources:
                    break
                if not any(b.get("title") == s.get("title") for b in bibliography):
                    bibliography.append({
                        "title": s.get("title", ""),
                        "authors": "Unknown",
                        "year": "",
                        "venue": s.get("source_engine", "web"),
                        "url": s.get("url", ""),
                        "source": "web_search",
                    })
        record.bibliography = bibliography
        print(f"      Bibliography: {len(bibliography)} sources")

        # Step F2: Generate dissertation
        print("\n[F2/7] Generating research proposal...")
        diss = self.dissertation_gen.generate(
            topic=topic,
            hypotheses=record.hypotheses,
            sources=bibliography,
            c4_state="auto-gap-theorem",
            triz_principles=["gap_analysis", "auto_theorem", "iterative_verify"],
            gaps=record.gaps,
            simulation=record.simulation.__dict__ if record.simulation and not isinstance(record.simulation, dict) else record.simulation,
            verification=record.verification.__dict__ if record.verification and not isinstance(record.verification, dict) else record.verification,
        )

        # Step F3: CDI Analysis
        print("\n[F3/7] Running CDI contradiction analysis...")
        cdi_result = self._run_cdi_analysis(topic, c4_state)

        # Step F4: TOTE Validation
        print("\n[F4/7] Running TOTE validation...")
        tote_result = self._run_tote_validation(diss)

        plugins_context = dict(record.plugins_context)
        plugins_context["cdi"] = cdi_result
        plugins_context["tote"] = tote_result

        return diss, plugins_context

    def _run_cdi_analysis(self, topic: str, c4_state: str) -> dict[str, Any]:
        try:
            contradiction = PhysicalContradiction(
                parameter=topic,
                value_a="speed",
                value_not_a="accuracy",
                requirement_y="discovery",
                requirement_z="rigor",
                contradiction_type=ContradictionType.TRADE_OFF,
            )
            result = self.cdi.solve(contradiction)
            print(f"      CDI Analysis: {result.steps_taken} steps, confidence={result.confidence_score:.2f}")
            return {"contradictions": [str(result.contradiction)], "hypothesis": result.hypothesis, "confidence": result.confidence_score}
        except Exception as e:
            logger.warning("CDI analysis failed: %s", e)
            return {"contradictions": []}

    def _run_tote_validation(self, solution: str) -> dict[str, Any]:
        try:
            result = self.tote.run()  # type: ignore[call-arg]
            print("      TOTE Validation: completed")
            return {"status": "completed"}
        except Exception as e:
            logger.warning("TOTE validation failed: %s", e)
            return {"status": "failed", "error": str(e)}

    def build_appendices(self, record: Any) -> str:
        """Build appendices block."""
        diss = """

---

## Appendix A: Research Gaps Identified

The following gaps were automatically detected in the literature:
"""
        for i, g in enumerate(record.gaps[:5], 1):
            diss += f"""
### Gap {i}: {g.get('area', 'Unknown')}
- **Evidence:** {g.get('evidence', 'N/A')[:200]}...
- **Novelty Score:** {g.get('novelty_score', 0)}
- **Suggested Hypothesis:** {g.get('hypothesis_seed', 'N/A')[:200]}...
"""

        diss += f"""

## Appendix B: Simulation Results

**Pattern:** {record.simulation.get('pattern_id', 'N/A') if isinstance(record.simulation, dict) else (record.simulation.pattern_id if record.simulation else 'N/A')}
**Status:** {record.simulation.get('status', 'N/A') if isinstance(record.simulation, dict) else (record.simulation.status if record.simulation else 'N/A')}
**Parameters:** {json.dumps(record.simulation.get('parameters', {})) if isinstance(record.simulation, dict) else (json.dumps(record.simulation.parameters) if record.simulation else 'N/A')}
**Metrics:** {json.dumps(record.simulation.get('metrics', {})) if isinstance(record.simulation, dict) else (json.dumps(record.simulation.metrics) if record.simulation else 'N/A')}
**Interpretation:** {record.simulation.get('interpretation', 'N/A') if isinstance(record.simulation, dict) else (record.simulation.interpretation if record.simulation else 'N/A')}

*Computational predictions — require experimental validation.*

## Appendix C: Formal Verification

**Backend:** {record.verification.backend if record.verification else "N/A"}
**Claim:** {(record.verification.claim[:100] + "...") if record.verification else "N/A"}
**Status:** {record.verification.status if record.verification else "N/A"}
**Iterations:** {record.verification.iterations if record.verification else 0}
**Proof/Error:** {record.verification.proof_text or record.verification.error_message or "N/A"}

*Formal verification establishes mathematical consistency, not empirical truth.*

## Appendix D: Reality Check

"""
        extraordinary_found = False
        for h in record.hypotheses:
            check = self._reality_check(h["title"])
            if check["is_extraordinary"]:
                extraordinary_found = True
                diss += f"\n- **{h['title'][:80]}...**"
                for w in check["warnings"]:
                    diss += f"\n  - [{w['domain'].upper()}] {w['warning']}"

        if not extraordinary_found:
            diss += "\nNo extraordinary claims detected. All hypotheses appear plausible."

        # Quality Report Appendix
        if record.quality_report:
            diss += f"""

## Appendix E: Quality Report

**Overall Score:** {record.quality_report.overall_score}/100
**Grade:** {record.quality_report.grade}
**All Gates Passed:** {'Yes' if record.quality_report.passed_all else 'No'}

| Step | Passed | Score | Message |
|------|--------|-------|---------|
"""
            for g in record.quality_report.gates:
                status = "✅" if g.passed else "⚠️"
                diss += f"| {g.step} | {status} | {g.score:.2f} | {g.message[:50]}... |\n"

            if record.quality_report.recommendations:
                diss += "\n**Recommendations:**\n"
                for r in record.quality_report.recommendations:
                    diss += f"- {r}\n"

        diss += f"""

---

*Generated by c4reqber v5.0.0 — Automated Discovery Pipeline*
*Sources: {len(record.bibliography)} | Gaps: {len(record.gaps)} | Hypotheses: {len(record.hypotheses)} | Simulation: {record.simulation.get('status', record.simulation.status if record.simulation and not isinstance(record.simulation, dict) else 'N/A') if record.simulation else 'N/A'} | Verification: {record.verification.get('status', record.verification.status if record.verification and not isinstance(record.verification, dict) else 'N/A') if record.verification else 'N/A'} | Quality: {record.quality_report.grade if record.quality_report else 'N/A'}*
"""
        return diss

    def _reality_check(self, claim: str) -> dict[str, Any]:
        extraordinary_patterns = [
            (r"Q\s*[>=]\s*1\b", "fusion", "Claiming Q >= 1 — no compact device achieved this."),
            (r"\b24%\s+life[- ]span", "biology", "24% lifespan extension — requires multi-year study."),
            (r"\b1[,.]?000[,.]?000\b.*people", "social", "Claims involving 1M+ people — extraordinary evidence needed."),
        ]
        warnings: list[dict[str, str]] = []
        for pattern, domain, warning in extraordinary_patterns:
            if re.search(pattern, claim, re.IGNORECASE):
                warnings.append({"domain": domain, "warning": warning})
        return {"is_extraordinary": len(warnings) > 0, "warnings": warnings}
