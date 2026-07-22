"""Shared BLAST flash runner — CLI and MCP must share one path."""

from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)

_NOT_FOUND_PHRASES = (
    "unable to identify",
    "unable to find",
    "could not find",
    "cannot find a specific",
    "no peer-reviewed publication",
    "i am unable to",
    "i couldn't find",
    "i could not find",
)


def build_flash_prompt(
    question: str,
    *,
    context: str,
    usp_section: str,
    format_instructions: str,
    verified_count: int,
) -> str:
    """Grounded flash prompt. Forbids 'not found' when verified sources exist."""
    grounding = ""
    if verified_count > 0:
        grounding = (
            "CRITICAL: Verified sources are listed below. You MUST use them. "
            "Cite with [N]. Do NOT say you are unable to find a publication, "
            "do NOT claim the sources are missing, and do NOT refuse based on "
            "training-data cutoff when sources are provided.\n"
        )
    elif context.strip():
        grounding = (
            "Sources below may be incomplete (missing DOI/URL). Be honest about "
            "uncertainty; do not invent DOI or URLs.\n"
        )
    else:
        grounding = (
            "No verified sources were retrieved. Say so clearly. "
            "Do not invent citations, DOI, or URLs.\n"
        )

    return f"""{format_instructions}

{grounding}
Use the following context if present:
{context}
{usp_section}

Question: {question}

Answer:"""


def flash_honesty_status(
    *,
    answer: str,
    with_sources: bool,
    verified_count: int,
    found_count: int,
    deep: bool,
    usp_context: dict[str, Any],
) -> tuple[str, list[str]]:
    """Return (status, warnings) for flash results."""
    warnings: list[str] = []
    status = "success"
    if not (answer or "").strip():
        return "error", ["empty LLM answer"]
    if with_sources and verified_count == 0:
        status = "partial"
        if found_count:
            warnings.append(
                f"found {found_count} papers but 0 CitationVerifier-confirmed "
                f"(need CrossRef DOI and/or OpenAlex title match ≥ 0.82)"
            )
        else:
            warnings.append("with_sources requested but no sources returned")
    if deep and not usp_context:
        status = "partial" if status == "success" else status
        warnings.append("deep=True but USP context empty (components failed)")
    if verified_count > 0:
        lower = answer.lower()
        if any(p in lower for p in _NOT_FOUND_PHRASES):
            status = "partial"
            warnings.append("answer claims not-found despite verified sources (grounding failure)")
    return status, warnings


async def run_usp_context(question: str) -> dict[str, Any]:
    """Optional USP cognitive components for deep flash."""
    usp_context: dict[str, Any] = {}
    c4_state: Any = "unknown"

    try:
        from src.metamodels.impact import ImpactEngine

        impact = ImpactEngine()
        impact_result = impact.identify(question)  # type: ignore[attr-defined]
        impact_mapped = impact.map(impact_result)  # type: ignore[attr-defined]
        usp_context["impact"] = (
            f"{len(impact_mapped.get('entities', []))} entities, "
            f"{len(impact_mapped.get('stakeholders', []))} stakeholders"
        )
    except Exception as exc:
        logger.debug("IMPACT failed: %s", exc)

    try:
        from src.c4.engine import C4Space

        c4_space = C4Space()
        c4_state = c4_space.fingerprint(question)  # type: ignore[attr-defined]
        usp_context["c4_state"] = str(c4_state)
    except Exception as exc:
        logger.debug("C4 fingerprint failed: %s", exc)

    try:
        from src.metamodels.mp.library import MPLibrary
        from src.metamodels.mp.profiles import MPRotationEngine

        mp_lib = MPLibrary()
        mp_rotation = MPRotationEngine(mp_lib)
        perspectives = mp_rotation.rotate(question, state=str(c4_state))  # type: ignore[attr-defined]
        usp_context["perspectives"] = [p.get("name", "") for p in perspectives[:3]]
    except Exception as exc:
        logger.debug("MP rotation failed: %s", exc)

    try:
        from src.metamodels.qzrf.operators import QzrfLibrary

        qzrf = QzrfLibrary()
        operators = qzrf.select(str(c4_state))  # type: ignore[attr-defined]
        usp_context["qzrf"] = operators[:5]
    except Exception as exc:
        logger.debug("QZRF failed: %s", exc)

    try:
        from src.metamodels.matrix_dream import MatrixDreamLibrary

        matrix = MatrixDreamLibrary()
        patterns = matrix.match(question)
        usp_context["patterns"] = [p[0].id for p in patterns[:3]]
    except Exception as exc:
        logger.debug("MatrixDream failed: %s", exc)

    try:
        from src.core.cdi_engine import CDIEngine

        cdi = CDIEngine()
        cdi_result = cdi.analyze(question, context={"c4_state": str(c4_state)})  # type: ignore[attr-defined]
        usp_context["contradictions"] = len(cdi_result.get("contradictions", []))
    except Exception as exc:
        logger.debug("CDI failed: %s", exc)

    try:
        from src.metamodels.tote import ToteEngine

        tote = ToteEngine()
        tote_result = tote.validate(question)  # type: ignore[attr-defined]
        usp_context["tote_status"] = tote_result.get("status", "unknown")
    except Exception as exc:
        logger.debug("TOTE failed: %s", exc)

    return usp_context


def format_usp_section(usp_context: dict[str, Any]) -> str:
    if not usp_context:
        return ""
    perspectives = usp_context.get("perspectives") or []
    qzrf = usp_context.get("qzrf") or []
    patterns = usp_context.get("patterns") or []
    return f"""
Cognitive Analysis Context:
- C4 State: {usp_context.get("c4_state", "N/A")}
- IMPACT: {usp_context.get("impact", "N/A")}
- Perspectives: {", ".join(perspectives) if isinstance(perspectives, list) else perspectives}
- QZRF Operators: {", ".join(qzrf) if isinstance(qzrf, list) else qzrf}
- Patterns: {", ".join(patterns) if isinstance(patterns, list) else patterns}
- Contradictions: {usp_context.get("contradictions", "N/A")}
- TOTE: {usp_context.get("tote_status", "N/A")}
"""


async def run_flash(
    question: str,
    *,
    with_sources: bool = False,
    deep: bool = False,
    format: str = "concise",
) -> dict[str, Any]:
    """Single flash implementation for CLI and MCP."""
    from src.knowledge.flash_sources import format_source_card, gather_flash_sources
    from src.llm.gateway import get_gateway

    usp_context: dict[str, Any] = {}
    if deep:
        usp_context = await run_usp_context(question)

    papers: list[dict[str, Any]] = []
    context = ""
    search_meta: dict[str, Any] = {
        "domain": "",
        "sources_used": [],
        "errors": {},
        "tavily": "off",
        "found": 0,
        "verified": 0,
    }

    if deep or with_sources:
        try:
            papers, context, search_meta = await gather_flash_sources(
                question, deep=deep, include_web=True
            )
        except Exception as exc:
            logger.warning("flash gather failed: %s", exc)
            search_meta["errors"]["gather"] = str(exc)
            papers = []
            context = ""

    verified = [p for p in papers if p.get("verified")]
    verified_count = len(verified)
    # Never fall back to unverified under Sources — honesty contract
    display_papers = verified

    format_instructions = {
        "concise": "Answer in 2-4 sentences. Be direct and specific.",
        "detailed": "Provide a thorough explanation with examples where helpful.",
        "bullet": "Answer using bullet points. Each point should be atomic and clear.",
        "code": (
            "If the answer involves code, provide a clean working example. "
            "Explain briefly after the code block."
        ),
    }.get(format, "Answer concisely and accurately.")

    prompt = build_flash_prompt(
        question,
        context=context,
        usp_section=format_usp_section(usp_context),
        format_instructions=format_instructions,
        verified_count=verified_count,
    )

    llm = get_gateway()
    answer = ""
    rate_limited = False
    try:
        raw = await llm.chat(
            [{"role": "user", "content": prompt}],
            max_tokens=1200 if deep else 800,
            temperature=0.3,
        )
        answer = (raw or "").strip() if isinstance(raw, str) else str(raw or "").strip()
    except Exception as exc:
        from src.llm.errors import RateLimited

        if isinstance(exc, RateLimited):
            rate_limited = True
            logger.warning("flash LLM rate limited: %s", exc)
            answer = ""
        else:
            logger.warning("flash LLM chat failed, trying generate: %s", exc)
            try:
                resp = await llm.generate(prompt, max_tokens=800, temperature=0.3)
                answer = (getattr(resp, "content", None) or "").strip()
            except RateLimited as rl_exc:
                rate_limited = True
                logger.warning("flash LLM rate limited on generate: %s", rl_exc)
                answer = ""
            except Exception as exc2:
                logger.error("flash LLM failed: %s", exc2)
                answer = ""

    status, warnings = flash_honesty_status(
        answer=answer,
        with_sources=with_sources or deep,
        verified_count=verified_count,
        found_count=len(papers),
        deep=deep,
        usp_context=usp_context,
    )
    if rate_limited:
        status = "partial" if status == "success" else status
        if status == "error" and not answer.strip():
            status = "partial"
        warnings.append("rate_limited: all LLM providers exhausted (HTTP 429)")

    quality_score = 0
    if deep and verified:
        try:
            from src.pipeline.config import PipelineConfig
            from src.pipeline.quality import QualityGates

            qg = QualityGates(PipelineConfig(name="default"))
            gate = qg.check_sources(verified)
            if gate.passed and verified_count > 0:
                quality_score = int(gate.score * 100)
            else:
                quality_score = 0
                warnings.append("quality gate did not pass on verified sources")
                if status == "success":
                    status = "partial"
        except Exception as exc:
            logger.debug("flash quality gate failed: %s", exc)

    cards = [format_source_card(p) for p in display_papers[:5]]
    unverified_hits = [format_source_card(p) for p in papers if not p.get("verified")][:5]
    source_count = verified_count

    return {
        "status": status,
        "mode": "flash",
        "answer": answer,
        "sources": cards,
        "unverified_hits": unverified_hits,
        "source_count": source_count,
        "found_count": len(papers),
        "verified_count": verified_count,
        "usp_context": usp_context,
        "quality_score": quality_score,
        "search_meta": search_meta,
        "warnings": warnings,
        "context_length": len(context),
    }
