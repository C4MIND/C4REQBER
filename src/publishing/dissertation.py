from __future__ import annotations


"""Dissertation Generator v2 — production-ready academic output."""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx


logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _sanitize_prompt_input(text: str, max_len: int = 500) -> str:
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(text)[:max_len])
    text = text.replace('"""', '"').replace("---", "-")
    text = text.replace("\nIgnore", " ").replace("\nignore", " ")
    return f"<user_input>{text}</user_input>"


def _sanitize_filename(name: str, max_len: int = 100) -> str:
    name = re.sub(r"[^\w\s.\-]", "_", str(name)[:max_len])
    name = name.strip().replace(" ", "_")
    if name.startswith(".") or ".." in name:
        name = re.sub(r"\.\.+", "__", name).lstrip(".")
    return name or "dissertation"

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


def _llm_generate(prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
    """Generate text via OpenRouter API — model configurable via DISSERTATION_MODEL env var."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        key = os.environ.get("DEEPSEEK_API_KEY", DEEPSEEK_KEY)
    if not key:
        return "[LLM generation disabled: no API key configured]"
    model = os.environ.get("DISSERTATION_MODEL", "anthropic/claude-3.5-sonnet")
    try:
        resp = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions" if "sk-or-" in key else DEEPSEEK_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "HTTP-Referer": "https://c4reqber.org", "X-Title": "C4Reqber"},
            json={
                "model": model if "sk-or-" in key else "deepseek-chat",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "system", "content": "You are a rigorous cross-domain research scientist. Write in academic English. Be bold and ambitious in hypotheses — aim for paradigm-shifting claims that challenge existing assumptions."},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=90,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[LLM unavailable: {type(e).__name__}]"


class DissertationGenerator:
    """Generate real academic dissertations from pipeline results using LLM."""

    def _format_reference(self, source: dict[str, Any], idx: int) -> str:
        """Format source as APA-style reference."""
        title = source.get("title", "Untitled").strip()
        authors = source.get("authors", "Unknown")
        if isinstance(authors, list):
            authors = ", ".join(authors[:3])
            if len(source.get("authors", [])) > 3:
                authors += " et al."
        year = source.get("year", "n.d.")
        venue = source.get("venue", source.get("source", ""))
        url = source.get("url", "")
        doi = source.get("doi", "")

        if not authors or authors == "Unknown" or authors == " ":
            authors = "[Authors unknown]"
        parts = [f"{idx}. {authors} ({year})."]
        parts.append(f"*{title}*.")
        if venue:
            parts.append(f"{venue}.")
        if doi:
            parts.append(f"https://doi.org/{doi}")
        elif url:
            parts.append(url)
        return " ".join(parts)

    def _build_source_list(self, sources: list[dict[str, Any]], max_refs: int = 15) -> str:
        """Build formatted reference list with deduplication."""
        seen_titles: set[str] = set()
        valid: list[dict[str, Any]] = []
        for s in sources:
            title = s.get("title", "").strip()
            if not title or title.startswith("Result "):
                continue
            # Dedup by normalized title
            norm = title.lower().replace(" ", "").replace("-", "")
            if norm in seen_titles:
                continue
            seen_titles.add(norm)
            valid.append(s)
        lines = []
        for i, s in enumerate(valid[:max_refs], 1):
            lines.append(self._format_reference(s, i))
        return "\n\n".join(lines)

    def _source_citations(self, sources: list[dict[str, Any]], max_cite: int = 8) -> str:
        """Build a compact citation list for LLM context."""
        valid = [s for s in sources if s.get("title") and not s.get("title", "").startswith("Result ")]
        lines = []
        for i, s in enumerate(valid[:max_cite], 1):
            authors = s.get("authors", "Unknown")
            if isinstance(authors, list):
                authors = authors[0].split()[-1] if authors else "Unknown"
            year = s.get("year", "n.d.")
            title = s.get("title", "")[:60]
            lines.append(f"[{i}] {authors} ({year}): {title}")
        return "\n".join(lines)

    def generate(
        self,
        topic: str,
        hypotheses: list[dict[str, Any]],
        sources: list[dict[str, Any]],
        c4_state: str | None = None,
        triz_principles: list[str] | None = None,
        simulation: dict[str, Any] | None = None,
        verification: dict[str, Any] | None = None,
        gaps: list[dict[str, Any]] | None = None,
        user_profile: Any | None = None,
        config: Any | None = None,
    ) -> str:
        """Generate a full dissertation with clear epistemic status markers."""
        now = datetime.now().strftime("%Y-%m-%d")

        # Build formatted references
        ref_list = self._build_source_list(sources, max_refs=15)
        citation_list = self._source_citations(sources, max_cite=8)

        # Build hypothesis summaries — ambitious, paradigm-shifting
        hypo_text = "\n".join([
            f"[HYPOTHESIS {i}] {_sanitize_prompt_input(h.get('title', ''), 200)}: {_sanitize_prompt_input(h.get('description', ''), 250)}"
            for i, h in enumerate(hypotheses[:5], 1)
        ])

        # Gap text
        gap_text = ""
        if gaps:
            gap_text = "\n".join([
                f"- Gap {i}: {_sanitize_prompt_input(g.get('area', ''), 200)}"
                for i, g in enumerate(gaps[:3], 1)
            ])

        # Simulation text
        sim_text = ""
        if simulation and simulation.get("status") == "success":
            sim_text = f"""
**Computational Simulation ({_sanitize_prompt_input(simulation.get('pattern_id', 'N/A'), 100)}):**
- Status: {_sanitize_prompt_input(str(simulation['status']), 50)}
- Metrics: {json.dumps(simulation.get('metrics', {}))}
- Interpretation: {_sanitize_prompt_input(simulation.get('interpretation', 'N/A'), 500)}

*⚠️ These are computational predictions, not empirical findings.*
"""
        else:
            sim_text = "*Computational simulation was not performed for this proposal. Future work should include numerical validation of the proposed hypotheses.*"

        # Verification text
        verif_text = ""
        if verification:
            verif_text = f"""
**Formal Verification ({_sanitize_prompt_input(str(verification.get('backend', 'N/A')), 50)}):**
- Status: {_sanitize_prompt_input(str(verification['status']), 50)}
- Note: {_sanitize_prompt_input(verification.get('proof_text', 'N/A'), 200)}

*⚠️ Mathematical consistency check, not empirical proof.*
"""
        else:
            verif_text = "*No formal verification attempted.*"

        safe_topic = _sanitize_prompt_input(topic, 300)

        # --- Chapter 1: Abstract + Introduction ---
        intro_prompt = f"""Write an academic ABSTRACT and INTRODUCTION for a RESEARCH PROPOSAL on:

"{safe_topic}"

This is a RESEARCH PROPOSAL proposing PARADIGM-SHIFTING hypotheses. Be bold and ambitious.

Key hypotheses (UNTESTED):
{hypo_text}

Available sources (cite ONLY these using [N] format):
{citation_list}

CRITICAL RULES:
1. ONLY cite sources from the list above using [N] format. NEVER invent citations.
2. If a claim has no supporting source, write "(proposed hypothesis)" instead of a citation.
3. Write 350-word Abstract + 800-word Introduction.
4. In Introduction, explicitly state: "This document proposes hypotheses for future empirical testing."
5. Be ambitious — frame the work as potentially transformative for the field.
6. Include specific, testable predictions in the Introduction.
7. Discuss 2-3 competing interpretations of the evidence.
8. Use concrete examples from the cited sources.

Format:
## Abstract
## 1. Introduction"""

        intro = _llm_generate(intro_prompt, max_tokens=2500, temperature=0.7)

        # --- Chapter 2: Literature Review ---
        lit_prompt = f"""Write a LITERATURE REVIEW for a research proposal on:

"{safe_topic}"

Available sources (cite ONLY these using [N] format):
{citation_list}

Identified gaps:
{gap_text}

CRITICAL RULES:
1. ONLY cite sources from the list above using [N] format. NEVER invent citations like (Author, Year).
2. If no source supports a claim, mark it as "proposed" or "hypothesized".
3. Identify 3-4 specific gaps that the proposed hypotheses address.
4. 1000 words. Academic tone.

Format:
## 2. Literature Review"""

        lit_review = _llm_generate(lit_prompt, max_tokens=2500, temperature=0.7)

        # --- Chapter 3: Methodology ---
        methodology_prompt = f"""Write a METHODOLOGY section for a research proposal on:

"{safe_topic}"

Hypotheses:
{hypo_text}

{sim_text}

{verif_text}

CRITICAL: Include a RISK ANALYSIS subsection:
- What could go wrong? (e.g., bacteria don't survive, null results)
- How will you mitigate? (alternative strains, sensitivity analyses)
- What are the epistemic limitations?

Also briefly mention c4reqber as hypothesis generation tool (1-2 sentences max).

Format:
## 3. Proposed Methodology
### 3.1 Experimental/Computational Methods
### 3.2 Validation Approach
### 3.3 Risk Analysis and Mitigation
### 3.4 Epistemic Limitations

800 words. Academic tone."""

        methodology = _llm_generate(methodology_prompt, max_tokens=2500, temperature=0.7)

        # --- Chapter 4: Proposed Research ---
        research_prompt = f"""Write a PROPOSED RESEARCH chapter for a research proposal on:

"{safe_topic}"

Hypotheses to be tested (AIM FOR PARADIGM-SHIFTING — challenge existing assumptions):
{hypo_text}

CRITICAL RULES:
1. Use language: "We predict that...", "If confirmed, this would suggest..."
2. NEVER use: "We demonstrate", "We show", "Our results prove".
3. Include: specific hypotheses, testable predictions with NUMERICAL BOUNDS, expected outcomes, potential implications.
4. Be BOLD — if hypotheses are confirmed, what paradigm would shift?
5. 800 words.

Format:
## 4. Proposed Research
### 4.1 Specific Hypotheses with Testable Predictions
### 4.2 Expected Outcomes
### 4.3 Potential Implications (if confirmed)

IMPORTANT: Section 4.3 MUST be complete. Do not truncate."""

        research = _llm_generate(research_prompt, max_tokens=2500, temperature=0.8)

        # --- Chapter 5: Conclusion ---
        conclusion_prompt = f"""Write a CONCLUSION for a research proposal on:

"{safe_topic}"

Key hypotheses:
{hypo_text}

CRITICAL RULES:
1. Be honest: this is a proposal, not completed work.
2. Include: summary, limitations, next steps, timeline, budget estimate.
3. Budget should be REALISTIC for the proposed work (equipment + personnel + time).
4. 500 words. Do NOT truncate.

Format:
## 5. Conclusion and Future Work

Write the COMPLETE text. Ensure the final sentence is complete."""

        conclusion = _llm_generate(conclusion_prompt, max_tokens=2000, temperature=0.7)

        # Build author block
        author_block = ""
        if user_profile:
            name = user_profile.formatted_name() if hasattr(user_profile, "formatted_name") else str(user_profile)
            affil = user_profile.full_affiliation() if hasattr(user_profile, "full_affiliation") else ""
            orcid = getattr(user_profile, "orcid", "")
            author_block = f"**Author:** {name}"
            if affil:
                author_block += f"  \n**Affiliation:** {affil}"
            if orcid:
                author_block += f"  \n**ORCID:** {orcid}"
            author_block += "\n"

        # Config-driven settings
        max_refs = getattr(config, "max_references", 15) if config else 15
        include_appendices = getattr(config, "include_appendices", True) if config else True
        include_epistemic = getattr(config, "include_epistemic_notice", True) if config else True

        # Assemble
        epistemic_block = """
---

> **⚠️ EPISTEMIC STATUS NOTICE**
>
> This document contains RESEARCH HYPOTHESES generated by an AI-assisted discovery system.
> - **Hypotheses**: Untested, require empirical validation
> - **Simulations**: Computational predictions only, not experimental data
> - **Verifications**: Mathematical consistency checks, not empirical proof
> - **Citations**: Based on automated search; fact-check before use
>
> This is NOT a completed dissertation. It is a starting point for human-led research.

---""" if include_epistemic else ""

        dissertation = f"""# {topic}

**Generated:** {now}
**Document Type:** Research Proposal (Hypotheses Untested)
**Discovery System:** c4reqber v5.0.0
**Methodology:** Cognitive hypothesis generation with computational pre-screening

{author_block}
{epistemic_block}

{intro}

{lit_review}

{methodology}

{research}

{conclusion}

---

## References

{ref_list}

---

*Document generated by c4reqber v5.0.0.
C4 cognitive state: {c4_state or 'N/A'}
Systematic innovation principles: {', '.join(triz_principles) if triz_principles else 'N/A'}
Human review: REQUIRED before any publication or experimental work*

---

*Sources: {len([s for s in sources if s.get('title')])} | Gaps: {len(gaps or [])} | Hypotheses: {len(hypotheses)} | Simulation: {simulation.get('status', 'N/A') if simulation else 'N/A'} | Verification: {verification.get('status', 'N/A') if verification else 'N/A'}*
"""

        if len(dissertation.split()) < 800:
            expansion_prompt = f"Expand the following research proposal to be more detailed and comprehensive. Add specific examples, elaborate on hypotheses, and discuss implications. Current proposal:\n\n{dissertation[:3000]}"
            expansion = _llm_generate(expansion_prompt, max_tokens=2000, temperature=0.8)
            dissertation = dissertation + "\n\n## Appendix: Expanded Discussion\n" + expansion

        # Coverage check: verify dissertation actually covers its bibliography
        try:
            from src.llm.embeddings import coverage_check
            coverage = coverage_check(dissertation, sources)
            if coverage.get("coverage", 1.0) < 0.5:
                uncovered = coverage.get("uncovered_indices", [])
                warning = (
                    f"\n\n> **⚠️ COVERAGE WARNING**: Only {coverage['covered']}/{coverage['total']} "
                    f"references are semantically covered in the text. "
                    f"Uncovered references: {len(uncovered)}."
                )
                dissertation = dissertation.replace("## References", warning + "\n\n## References")
        except Exception:
            pass

        return dissertation

    def generate_from_pipeline(self, result: dict[str, Any]) -> str:
        """Convenience wrapper from pipeline result dict."""
        topic = result.get("problem", result.get("topic", "Unknown Topic"))
        hypotheses = result.get("hypotheses", [])
        sources = result.get("sources", result.get("papers", []))
        c4_state = result.get("c4_state")
        triz = result.get("triz_principles")
        gaps = result.get("gaps", [])
        user = result.get("user_profile")
        cfg = result.get("config")
        return self.generate(topic, hypotheses, sources, c4_state, triz, gaps=gaps, user_profile=user, config=cfg)

    def save(self, dissertation: str, filename: str | None = None) -> str:
        """Save dissertation to file (path-traversal safe)."""
        diss_dir = _PROJECT_ROOT / "dissertations" / "live"
        diss_dir.mkdir(parents=True, exist_ok=True)
        if filename is None:
            filename = f"dissertation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        safe_name = _sanitize_filename(filename)
        path = diss_dir / safe_name
        if not str(path.resolve()).startswith(str(diss_dir.resolve())):
            raise ValueError(f"Path traversal blocked: {filename}")
        path.write_text(dissertation, encoding="utf-8")
        logger.info("Dissertation saved: %s", path)
        return str(path)
