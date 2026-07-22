"""
C4REQBER: Pipeline Step 08 — Synthesis
"""

from __future__ import annotations

import logging
import time
from typing import Any


logger = logging.getLogger(__name__)


def _count_tokens(text: str) -> int:
    """Count tokens using tiktoken if available, otherwise approximate."""
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return len(text) // 4


from src.agents.pipeline.steps.base import (
    PipelineStage,
    PipelineStep,
    PipelineStepResult,
)
from src.c4.state import C4State
from src.discovery.pipeline_logic import _sanitize_for_prompt
from src.knowledge.citation_verifier import CitationVerifier
from src.knowledge.novelty_scorer import NoveltyScorer
from src.metamodels.mp.profiles import AgentPerspective


class SynthesisStep(PipelineStep):
    """Step 8: Synthesis — integrate perspectives into a cohesive solution."""

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.SYNTHESIS

    def get_required_context(self) -> list[str]:
        return ["problem", "c4_state", "plugin_results", "gap_results", "quality_gate_results"]

    def get_optional_context(self) -> list[str]:
        return [
            "perspectives",
            "qzrf_ops",
            "isomorphism_found",
            "mapping",
            "provider_router",
            "cost_tracker",
            "prior_art_confidence",
            "max_tokens",
            "sources",
        ]

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute."""
        problem: str = context["problem"]
        perspectives: list[AgentPerspective] = context.get("perspectives", [])
        qzrf_ops: list[str] = context.get("qzrf_ops", [])
        c4_state: C4State = context["c4_state"]
        isomorphism_found: bool = context.get("isomorphism_found", False)
        mapping: dict[str, str] = context.get("mapping", {})
        plugin_results: list[dict[str, Any]] | None = context.get("plugin_results")
        provider_router: Any = context.get("provider_router")
        cost_tracker: Any = context.get("cost_tracker")
        prior_art_confidence: float = context.get("prior_art_confidence", 0.0)
        gap_results: list[dict[str, Any]] | None = context.get("gap_results")
        quality_gate_results: dict[str, Any] | None = context.get("quality_gate_results")
        sources: list[dict[str, Any]] | None = context.get("sources")
        max_tokens: int = context.get("max_tokens", 1500)
        start = time.time()

        try:
            # RAG: retrieve semantically relevant abstracts for synthesis grounding
            rag_section = ""
            source_entries = []
            if sources:
                for i, s in enumerate(sources[:7], 1):
                    title = _sanitize_for_prompt(s.get("title", "")[:120])
                    abstract = _sanitize_for_prompt(s.get("abstract", "")[:300])
                    authors = ", ".join(s.get("authors", [])[:2])
                    year = s.get("year", "")
                    doi = s.get("doi", "")
                    src = s.get("source", "")
                    entry = f"[{i}] {title} ({authors}, {year}) [{src}]"
                    if abstract:
                        entry += f"\n    Abstract: {abstract}"
                    if doi:
                        entry += f"\n    DOI: {doi}"
                    source_entries.append(entry)
            if source_entries:
                rag_section = (
                    "\n\nRELEVANT RESEARCH (ground your claims in these sources):\n"
                    + "\n\n".join(source_entries)
                )
            else:
                rag_section = "\n\nRELEVANT RESEARCH: No external sources retrieved. Mark all factual claims as (proposed)."

            perspective_text = "\n\n".join(
                [
                    f"## {_sanitize_for_prompt(p.profile_name)} (confidence: {p.confidence:.0%})\n"
                    f"Insights: {_sanitize_for_prompt(', '.join((p.key_insights or [])[:3]))}\n"
                    f"Blind spots: {_sanitize_for_prompt(', '.join((p.blind_spots or [])[:2]))}"
                    for p in perspectives
                ]
            )

            qzrf_text = ", ".join(qzrf_ops) if qzrf_ops else "none selected"
            iso_text = (
                "Cross-domain isomorphism found with mapping."
                if isomorphism_found
                else "No direct isomorphism found."
            )

            plugin_section = ""
            if plugin_results:
                from src.agents.plugin_synthesis_integrator import (
                    format_plugin_results_for_synthesis,
                )

                formatted_plugins = format_plugin_results_for_synthesis(plugin_results)
                if formatted_plugins:
                    plugin_section = (
                        f"\n\nPLUGIN ANALYSIS:\n{formatted_plugins}\n\n"
                        f"Incorporate the above plugin analyses into your solution where relevant."
                    )

            gap_section = ""
            if gap_results:
                gap_text = "\n".join(
                    f"- {g.get('area', 'Unknown')} (novelty: {g.get('novelty_score', 0):.0%})"
                    for g in gap_results[:5]
                )
                gap_section = (
                    f"\n\nRESEARCH GAPS IDENTIFIED:\n{gap_text}\n\n"
                    f"Consider how the solution addresses or leverages these gaps."
                )

            quality_section = ""
            if quality_gate_results:
                src_passed = quality_gate_results.get("source_gate", {}).get("passed", False)
                gap_passed = quality_gate_results.get("gap_gate", {}).get("passed", False)
                quality_section = (
                    f"\n\nQUALITY GATES:\n"
                    f"- Source quality: {'PASS' if src_passed else 'WARNING'}\n"
                    f"- Gap quality: {'PASS' if gap_passed else 'WARNING'}\n"
                )

            observer_section = ""
            observer_insights: list[str] = context.get("observer_insights", [])
            if observer_insights:
                observer_section = (
                    "\n\nMETA-COGNITIVE OBSERVER INSIGHTS:\n"
                    + "\n".join(f"- {insight}" for insight in observer_insights)
                    + "\n\nConsider these observer insights when synthesizing — they reveal potential blind spots or biases in the perspectives above."
                )

            safe_problem = _sanitize_for_prompt(problem, max_len=500)
            prompt = (
                f"You are writing a COMPREHENSIVE RESEARCH DISSERTATION on the following problem. "
                f"Integrate multiple analytical perspectives into a rigorous, well-structured academic document.\n\n"
                f"PROBLEM: {safe_problem}\n\n"
                f"C4 STATE: {c4_state} (Time={c4_state.time_label}, Scale={c4_state.scale_label}, Agency={c4_state.agency_label})\n\n"
                f"QZRF OPERATORS: {qzrf_text}\n\n"
                f"CROSS-DOMAIN: {iso_text}\n\n"
                f"PERSPECTIVES:\n{perspective_text}\n\n"
                f"{rag_section}"
                f"{plugin_section}"
                f"{gap_section}"
                f"{quality_section}"
                f"{observer_section}"
                f"\n\nDISSERTATION STRUCTURE (required — each section must be substantive, 2-4 paragraphs minimum):\n"
                f"## 1. Abstract\n"
                f"   - 200-300 words summarizing the problem, methodology, key findings, and implications.\n"
                f"## 2. Introduction & Problem Framing\n"
                f"   - Context, significance, and why existing approaches are insufficient.\n"
                f"## 3. Literature Review & State of the Art\n"
                f"   - What is known (cite sources with [N]), what gaps exist.\n"
                f"## 4. Methodology & Analytical Framework\n"
                f"   - How the multi-perspective synthesis was constructed, C4 mapping, QZRF operators used.\n"
                f"## 5. Core Findings & Synthesis\n"
                f"   - Integrated solution: specific mechanisms, technologies, or frameworks proposed.\n"
                f"   - Ground claims with [N] citations; mark unsupported claims as '(proposed)'.\n"
                f"## 6. Discussion & Critical Analysis\n"
                f"   - Strengths, limitations, blind spots of each perspective, how they were mitigated.\n"
                f"## 7. Implementation Roadmap\n"
                f"   - Concrete phases, milestones, metrics, resource requirements.\n"
                f"## 8. Risk Assessment & Mitigation Strategies\n"
                f"   - Technical, economic, social, and epistemic risks with specific mitigations.\n"
                f"## 9. Future Research Directions\n"
                f"   - Open questions, follow-up studies, interdisciplinary connections.\n"
                f"## 10. Conclusion\n"
                f"   - Summary of contributions and broader implications.\n"
                f"## 11. References\n"
                f"   - List ALL sources cited in the dissertation using numbered bibliography format.\n"
                f"   - Format: [N] Authors. Title. Journal/venue. Year. DOI/URL (if available).\n\n"
                f"CRITICAL RULES:\n"
                f"1. Total length: MINIMUM 4000 words (≈8000+ characters). Be thorough and detailed.\n"
                f"2. Ground EVERY factual claim using [N] citations from the RELEVANT RESEARCH section above.\n"
                f"3. If a claim is NOT supported by the provided sources, explicitly mark it as '(proposed)'.\n"
                f"4. Each section must have SUBSTANCE — avoid fluff and generic statements.\n"
                f"5. Use specific examples, numbers, and named frameworks wherever possible.\n"
                f"6. Address the observer insights above — acknowledge and mitigate identified blind spots.\n"
                f"7. The References section MUST include real entries for every [N] citation used."
            )

            if not provider_router:
                raise RuntimeError("LLM provider required for synthesis")

            system = (
                "You are an expert research synthesizer. Write comprehensive academic "
                "dissertations that integrate multiple analytical perspectives. You MUST cite "
                "provided sources using [N] format and include a complete References section. "
                "Mark unsupported claims as (proposed)."
            )
            solution = ""
            usage: dict[str, Any] = {}
            response = None
            preferred_model = ""
            try:
                from src.llm.model_assignment import get_model_for_phase

                preferred_model = get_model_for_phase("F") or ""
            except Exception:
                preferred_model = ""
            try:
                response = await provider_router.generate("synthesis", prompt, system_prompt=system)
                solution = getattr(response, "content", str(response))
                usage = getattr(response, "usage", {}) or {}
            except Exception as exc:
                logger.warning("ProviderRouter synthesis failed (%s) — gateway sync fallback", exc)
                from src.llm import get_gateway

                try:
                    solution = get_gateway().generate_sync(
                        prompt,
                        system_prompt=system,
                        max_tokens=max(max_tokens, 4000),
                        temperature=0.7,
                        preferred_model=preferred_model or None,
                    )
                except RuntimeError as chain_exc:
                    logger.warning("Gateway sync chain failed: %s", chain_exc)
                    solution = ""

            if not solution or len(solution.split()) < 400:
                raise RuntimeError(
                    f"Synthesis produced insufficient content ({len(solution.split())} words)"
                )

            # Append References section if missing
            if sources and "## 11. References" not in solution and "## References" not in solution:
                ref_lines = ["\n\n## 11. References\n"]
                for i, s in enumerate(sources[:10], 1):
                    authors = ", ".join(s.get("authors", [])[:3])
                    if len(s.get("authors", [])) > 3:
                        authors += " et al."
                    title = s.get("title", "")
                    year = s.get("year", "")
                    venue = s.get("venue", "")
                    doi = s.get("doi", "")
                    url = s.get("url", "")
                    ref = f"[{i}] {authors}. {title}."
                    if venue:
                        ref += f" {venue}."
                    if year:
                        ref += f" {year}."
                    if doi:
                        ref += f" DOI:{doi}."
                    elif url:
                        ref += f" URL:{url}."
                    ref_lines.append(ref)
                solution += "\n".join(ref_lines)

            duration_ms = (time.time() - start) * 1000
            if cost_tracker is not None:
                model = getattr(response, "model", "unknown") if response else "unknown"
                provider = getattr(response, "provider", "unknown") if response else "unknown"
                input_tokens = usage.get("prompt_tokens", 0) or _count_tokens(prompt)
                output_tokens = usage.get("completion_tokens", 0) or _count_tokens(solution)
                cost_tracker.track_request(
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    duration_ms=duration_ms,
                )

            # ------------------------------------------------------------------
            # Citation Verification + Novelty Scoring
            # Honesty: unchecked novelty → null (never fake 0.5 under gates)
            # ------------------------------------------------------------------
            citation_verdicts: list[dict[str, Any]] = []
            novelty_score: float | None = None
            novelty_flag = "NOVELTY_UNCHECKED"
            try:
                verifier = CitationVerifier()
                citation_verdicts = [
                    v.__dict__ for v in await verifier.verify(solution, sources or [])
                ]
                await verifier.close()
            except Exception as exc:
                logger.debug("Citation verification skipped: %s", exc)

            try:
                scorer = NoveltyScorer()
                novelty_score = scorer.score(solution, sources or [])
                novelty_flag = scorer.flag(novelty_score)
                if novelty_score is None:
                    logger.debug("Novelty unchecked: empty or non-embeddable prior art")
            except Exception as exc:
                logger.debug("Novelty scoring skipped: %s", exc)
                novelty_score = None
                novelty_flag = "NOVELTY_UNCHECKED"

            # ------------------------------------------------------------------
            # Dynamic confidence calculation (v3 — real metrics, target >0.92)
            # ------------------------------------------------------------------
            import re

            # 1. Base confidence
            base_confidence = 0.38

            # 2. Perspective diversity: count unique C4 biases, not just count
            unique_c4_coords = set()
            for p in perspectives:
                if hasattr(p, "c4_state"):
                    unique_c4_coords.add(p.c4_state.to_tuple())
            diversity_ratio = len(unique_c4_coords) / max(len(perspectives), 1)
            perspective_boost = min(len(perspectives) * 0.05 * (1 + diversity_ratio), 0.22)

            # 3. Prior art boost: real sources vs demo data
            has_real_sources = sources and any(
                s.get("source", "") not in ("demo", "") for s in sources
            )
            prior_boost = (prior_art_confidence * 0.10) + (0.06 if has_real_sources else 0.0)

            # 4. Gap novelty boost
            gap_scores = [g.get("novelty_score", 0) for g in (gap_results or [])]
            gap_boost = (sum(gap_scores) / max(len(gap_scores), 1) * 0.10) if gap_scores else 0.0

            # 5. Quality gates
            quality_boost = (
                0.10 if quality_gate_results and quality_gate_results.get("all_passed") else 0.05
            )

            # 6. Solution quality metrics
            solution_len = len(solution)
            section_count = len(re.findall(r"#{1,3}\s+\w+", solution))
            citation_count = len(re.findall(r"\[\d+\]|\[Insight \d+\]", solution))
            has_risks = bool(re.search(r"(?i)risk|mitigation|blind.?spot", solution))
            has_concrete = bool(re.search(r"(?i)specifically|concrete|step \d|phase \d", solution))

            structure_score = min(section_count / 5, 1.0) * 0.06  # 5+ sections = full score
            depth_score = min(solution_len / 8000, 1.0) * 0.08  # 8000+ chars = full score
            citation_score = min(citation_count / 5, 1.0) * 0.05  # 5+ citations = full score
            completeness_score = (0.03 if has_risks else 0.0) + (0.03 if has_concrete else 0.0)
            solution_boost = structure_score + depth_score + citation_score + completeness_score

            # 7. Observer penalty / bonus
            observer_insights: list[str] = context.get("observer_insights", [])
            has_blind_spots = any("blind_spots_detected" in i.lower() for i in observer_insights)
            observer_penalty = (
                -0.03 if has_blind_spots else 0.02
            )  # penalty if blind spots, small bonus if clean

            # 8. Claim verification (downstream)
            claim_coverage = context.get("claim_verification", {}).get("overall_coverage", 0.0)
            claim_boost = claim_coverage * 0.08

            # 9. Novelty boost (v3) — only when scored; null ≠ mid-confidence
            novelty_boost = (novelty_score * 0.08) if novelty_score is not None else 0.0

            # 10. Citation verification penalty
            verified_count = sum(1 for v in citation_verdicts if v.get("verdict") == "VERIFIED")
            total_checked = len(citation_verdicts)
            verified_ratio = verified_count / max(total_checked, 1)
            citation_penalty = (1 - verified_ratio) * 0.10  # up to -0.10 for all hallucinated

            confidence = min(
                base_confidence
                + perspective_boost
                + prior_boost
                + gap_boost
                + quality_boost
                + solution_boost
                + observer_penalty
                + claim_boost
                + novelty_boost
                - citation_penalty,
                0.95,
            )
            confidence = max(confidence, 0.35)  # floor

            output_data = {
                "solution": solution,
                "confidence": round(confidence, 3),
                "confidence_breakdown": {
                    "base": round(base_confidence, 3),
                    "perspectives": round(perspective_boost, 3),
                    "prior_art": round(prior_boost, 3),
                    "gaps": round(gap_boost, 3),
                    "quality": round(quality_boost, 3),
                    "solution_quality": round(solution_boost, 3),
                    "observer": round(observer_penalty, 3),
                    "claims": round(claim_boost, 3),
                    "novelty": round(novelty_boost, 3),
                },
                "solution_metrics": {
                    "length_chars": solution_len,
                    "sections": section_count,
                    "citations": citation_count,
                    "has_risks": has_risks,
                    "has_concrete_steps": has_concrete,
                },
                "novelty": {
                    "score": round(novelty_score, 3) if novelty_score is not None else None,
                    "flag": novelty_flag,
                },
                "citation_verification": {
                    "verdicts": citation_verdicts,
                    "verified_count": sum(
                        1 for v in citation_verdicts if v.get("verdict") == "VERIFIED"
                    ),
                    "total_checked": len(citation_verdicts),
                },
                "prompt_tokens": _count_tokens(prompt),
            }
            status = "completed"
            error = None
        except Exception as e:
            status = "failed"
            error = str(e)
            output_data = {
                "solution": "",
                "confidence": 0.0,
                "error": str(e),
            }

        return PipelineStepResult(
            stage=self.stage,
            status=status,
            output_data=output_data,
            duration_ms=(time.time() - start) * 1000,
            error=error,
        )
