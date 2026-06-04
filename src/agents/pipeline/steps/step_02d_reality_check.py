"""
C44TCDI: Pipeline Step 02d — Reality Check

Flag extraordinary claims, numerical outliers, and known falsehoods
in problem/solution text using regex heuristics + falsifier integration.
"""
from __future__ import annotations

import re
import time
from typing import Any

from src.agents.pipeline.steps.base import PipelineStage, PipelineStep, PipelineStepResult


class RealityCheckStep(PipelineStep):
    """Step 2d: Reality Check — flag extraordinary claims requiring scrutiny."""

    # ── Known extraordinary claims (physical impossibilities / no evidence) ──
    EXTRAORDINARY_PATTERNS: list[tuple[str, str, str]] = [
        (r"Q\s*(?:>=|=)\s*1\b", "fusion", "Claiming Q >= 1 — no compact device achieved this."),
        (r"\b24%\s+life[- ]span", "biology", "24% lifespan extension — requires multi-year study."),
        (r"\b1[,.]?000[,.]?000\b.*people", "social", "Claims involving 1M+ people — extraordinary evidence needed."),
        (r"\bperpetual\s+motion", "physics", "Perpetual motion claims violate thermodynamic laws."),
        (r"\b100%\s+(?:cure|prevent|eliminate)", "medicine", "100% cure/prevention claims are extremely rare in medicine."),
        (r"\bcold\s+fusion\b|\bfleischmann[- ]pons\b", "physics", "Cold fusion claims lack reproducible evidence since 1989."),
        (r"\bhomeopath(?:y|ic)\b.*\bcure\b", "medicine", "Homeopathic cure claims contradict established pharmacology."),
        (r"\bantigravity\b|\banti-gravity\b", "physics", "Antigravity claims have no reproducible experimental support."),
        (r"\bem\s+drive\b|\bEMDrive\b", "physics", "EM Drive claims violate conservation of momentum; NASA Eagleworks results within error bars."),
        (r"\bwarp\s+drive\b|\balcubierre\b", "physics", "Warp drive requires exotic matter with negative energy density — not demonstrated."),
        (r"\btelepath(?:y|ic)\b|\btelekinesis\b", "parapsychology", "Telepathy/telekinesis lack reproducible evidence under controlled conditions."),
        (r"\bcreation\s+science\b.*\bpeer[- ]reviewed\b", "biology", "Creation science is not supported by peer-reviewed scientific evidence."),
    ]

    # ── Numerical outlier patterns (extraordinary magnitude claims) ──
    NUMERICAL_PATTERNS: list[tuple[str, str, str]] = [
        (r"\b\d{3,}%\s+(?:improvement|increase|enhancement|boost|gain)", "metrics", "Claim of >100% improvement — verify baseline and methodology."),
        (r"\b\d{2,}\s*-fold\s+(?:increase|improvement|enhancement)", "metrics", "Multi-fold claims (>10x) — check for unit errors or cherry-picked baselines."),
        (r"\borders?\s+of\s+magnitude\b.*\b(?:better|faster|stronger|more)\b", "metrics", "Orders-of-magnitude claims — require clear quantitative justification."),
        (r"\b\d+\s*(?:nm|μm|mm|cm)\b.*\bin\s+\d+\s*(?:ms|μs|ns|ps)\b", "engineering", "Extreme scale/time combination — verify with domain benchmarks."),
        (r"\b\d{2,}\s*orders\s+of\s+magnitude\b.*\b(?:cheaper|faster|smaller|larger)\b", "metrics", "Extreme orders-of-magnitude claims require independent replication."),
        (r"\b\d{4,}%\s+(?:efficiency|yield|conversion)\b", "engineering", ">1000% efficiency claims violate conservation laws."),
        (r"\bzero\s+(?:loss|waste|emission|defect)\b", "engineering", "Zero-loss claims are thermodynamically impossible; verify bounds."),
    ]

    # ── Domain-specific red flags ──
    DOMAIN_PATTERNS: list[tuple[str, str, str]] = [
        (r"\broom[- ]temperature\s+superconductor\b|\bRTSC\b", "materials", "Room-temperature superconductivity — LK-99 debunked; require peer replication."),
        (r"\bwater\s+powered\s+(?:car|engine)\b|\bHHO\s+(?:fuel|gas)\b", "energy", "Water-as-fuel claims violate thermodynamics (conservation of energy)."),
        (r"\bvaccine.*autism\b|\bMMR.*autism\b", "medicine", "Vaccine-autism link — thoroughly debunked by large-scale studies."),
        (r"\b5G.*(?:covid|coronavirus|virus)\b|\b5G.*radiation.*harm\b", "health", "5G health conspiracy — no credible mechanism or evidence."),
        (r"\bflat\s+earth\b|\bgeocentrism\b|\bearth\s+is\s+flat\b", "astronomy", "Flat Earth claims contradicted by all geodetic and spaceflight evidence."),
        (r"\bcreation\s+science\b|\bintelligent\s+design\b.*\bevidence\b", "biology", "Intelligent design is not supported by peer-reviewed scientific evidence."),
        (r"\btime\s+travel\b.*\bproven\b|\btime\s+machine\b.*\bdemonstrated\b", "physics", "Time travel to the past is not demonstrated and likely forbidden by causality."),
        (r"\bghost\b.*\bscientific\b.*\bevidence\b|\bhaunt\b.*\bpeer[- ]reviewed\b", "parapsychology", "Paranormal claims lack reproducible peer-reviewed evidence."),
        (r"\bfree\s+energy\b.*\bdevice\b|\bzero[- ]point\s+energy\b.*\bextract\b", "physics", "Free-energy devices violate conservation of energy."),
        (r"\bmoon\s+landing\s+hoax\b|\bapollo\s+fake\b", "astronomy", "Moon landing hoax claims are contradicted by independent tracking and lunar samples."),
    ]

    ALL_PATTERNS: list[tuple[str, str, str]] = EXTRAORDINARY_PATTERNS + NUMERICAL_PATTERNS + DOMAIN_PATTERNS

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.REALITY_CHECK

    def get_required_context(self) -> list[str]:
        return ["problem"]

    def _check_patterns(self, text: str) -> list[dict[str, str]]:
        """Check text against all pattern categories."""
        warnings: list[dict[str, str]] = []
        for pattern, domain, warning in self.ALL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                warnings.append({"domain": domain, "warning": warning, "type": "pattern"})
        return warnings

    def _check_falsifier(self, text: str, domain: str = "general") -> list[dict[str, str]]:
        """Cross-check against falsifier's known-false database."""
        warnings: list[dict[str, str]] = []
        try:
            from src.discovery.falsifier import Falsifier
            result = Falsifier().check(text, domain)
            if result.falsifiable and result.confidence > 0.5:
                for cx in result.counterexamples[:3]:
                    warnings.append({
                        "domain": "falsifier",
                        "warning": f"Counterexample: {cx.description}",
                        "type": "falsifier",
                    })
                for ct in result.contradictions[:3]:
                    warnings.append({
                        "domain": "falsifier",
                        "warning": f"Contradiction: {ct.claim} — {ct.opposing_evidence}",
                        "type": "falsifier",
                    })
                critique = result.critique
                if critique.get("physical_impossibilities"):
                    for imp in critique["physical_impossibilities"][:2]:
                        warnings.append({
                            "domain": "physics",
                            "warning": f"Physical impossibility: {imp}",
                            "type": "falsifier",
                        })
        except Exception as e:
            logger.warning("Falsifier check failed: %s", e)
            warnings.append({"domain": "falsifier", "warning": f"Falsifier unavailable: {e}", "type": "system"})
        return warnings

    def _reality_check(self, text: str, domain: str = "general") -> dict[str, Any]:
        """Run full reality check on text."""
        warnings = self._check_patterns(text)
        warnings.extend(self._check_falsifier(text, domain))
        return {"is_extraordinary": len(warnings) > 0, "warnings": warnings}

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute."""
        if "problem" not in context:
            return PipelineStepResult(
                step_id=self.step_id,
                status="failed",
                data={},
                errors=["Missing required context key: 'problem'"],
                metadata={"duration_seconds": 0.0},
            )
        problem = context["problem"]
        start = time.time()

        # Use explicit domain from context if present; fall back to inference
        domain = context.get("domain", "")
        if not domain:
            p_lower = problem.lower()
            domain_keywords = {
                "physics": ("physics", "quantum", "relativity", "thermodynamic", "particle", "field"),
                "biology": ("biology", "gene", "cell", "protein", "organism", "evolution"),
                "chemistry": ("chemistry", "molecule", "reaction", "catalyst", "synthesis"),
                "medicine": ("medicine", "clinical", "patient", "drug", "treatment", "disease"),
                "materials": ("material", "superconductor", "alloy", "polymer", "crystal"),
                "energy": ("energy", "battery", "solar", "fusion", "reactor"),
                "economics": ("economy", "market", "finance", "inflation", "gdp"),
                "astronomy": ("star", "galaxy", "black hole", "cosmology", "telescope"),
            }
            for d, keywords in domain_keywords.items():
                if any(kw in p_lower for kw in keywords):
                    domain = d
                    break
            if not domain:
                domain = "general"

        check = self._reality_check(problem, domain)

        # Also check any solution/hypothesis text if present
        for key in ("solution", "hypothesis"):
            text = context.get(key, "")
            if isinstance(text, dict):
                text = text.get("text", "")
            if text:
                extra = self._reality_check(text, domain)
                check["warnings"].extend(extra["warnings"])

        check["is_extraordinary"] = len(check["warnings"]) > 0
        status = "completed"
        error = None

        output_data: dict[str, Any] = {
            "is_extraordinary": check["is_extraordinary"],
            "warnings": check["warnings"],
            "warning_count": len(check["warnings"]),
            "extraordinary_count": len([w for w in check["warnings"] if w.get("type") == "pattern"]),
            "falsifier_count": len([w for w in check["warnings"] if w.get("type") == "falsifier"]),
        }

        context["reality_check"] = output_data

        return PipelineStepResult(
            stage=self.stage,
            status=status,
            input_data={"problem": problem},
            output_data=output_data,
            duration_ms=(time.time() - start) * 1000,
            error=error,
        )


# Function-based API
async def step_reality_check(problem: str, solution: str = "") -> PipelineStepResult:
    """Run reality check on problem and optional solution text."""
    step = RealityCheckStep()
    return await step.execute({"problem": problem, "solution": solution})
