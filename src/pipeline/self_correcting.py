"""Self-Correcting Dissertation — fix sections based on quality gate feedback.

When specific gates fail (e.g. sources, gaps, hypotheses), instead of
regenerating the entire dissertation, only rewrite affected sections.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from src.pipeline.quality import QualityReport


logger = logging.getLogger(__name__)


class SelfCorrectingDissertation:
    """Surgical dissertation corrections based on gate feedback."""

    SECTION_MAP = {
        "sources": ["Literature Review", "References", "Bibliography"],
        "gaps": ["Literature Review", "Research Gaps", "Introduction"],
        "hypotheses": ["Hypotheses", "Methodology", "Expected Results"],
        "simulation": ["Results", "Simulation", "Computational Experiments"],
        "verification": ["Verification", "Proof", "Formal Analysis"],
        "bibliography": ["References", "Bibliography"],
        "dissertation": ["Abstract", "Introduction", "Conclusion"],  # structural issues
    }

    def __init__(self, dissertation_gen: Any | None = None) -> None:
        self.dissertation_gen = dissertation_gen

    def identify_sections_to_fix(self, report: QualityReport) -> dict[str, list[str]]:
        """Map failed gates to dissertation sections that need rewriting."""
        sections_to_fix: dict[str, list[str]] = {}
        for gate in report.gates:
            if not gate.passed and gate.step in self.SECTION_MAP:
                sections_to_fix[gate.step] = self.SECTION_MAP[gate.step]
        return sections_to_fix

    def extract_section(self, dissertation: str, section_name: str) -> str | None:
        """Extract a section from markdown dissertation by heading."""
        pattern = rf'##\s+{re.escape(section_name)}\s*\n(.*?)(?=\n##\s|\Z)'
        match = re.search(pattern, dissertation, re.DOTALL | re.IGNORECASE)
        return match.group(0) if match else None

    def replace_section(self, dissertation: str, section_name: str, new_content: str) -> str:
        """Replace a section in the dissertation."""
        pattern = rf'(##\s+{re.escape(section_name)}\s*\n).*?(?=\n##\s|\Z)'
        replacement = rf'\1{new_content}\n\n'
        new_diss, count = re.subn(pattern, replacement, dissertation, count=1,
                                   flags=re.DOTALL | re.IGNORECASE)
        if count == 0:
            # Section not found — append it
            new_diss += f"\n\n## {section_name}\n\n{new_content}\n"
        return new_diss

    async def fix_dissertation(
        self,
        dissertation: str,
        report: QualityReport,
        record: Any,
        topic: str,
    ) -> str:
        """Apply surgical fixes to dissertation based on failed gates.

        Returns corrected dissertation.
        """
        sections_to_fix = self.identify_sections_to_fix(report)
        if not sections_to_fix:
            return dissertation

        corrected = dissertation
        from src.publishing.dissertation import _llm_generate

        for gate_name, section_names in sections_to_fix.items():
            logger.info("Self-correcting gate '%s' → sections: %s", gate_name, section_names)

            for section_name in section_names:
                # Generate improved content for this section
                context = self._build_section_context(gate_name, record, topic)
                prompt = f"""Rewrite the '{section_name}' section of a research proposal on "{topic}".

Previous quality issue: {gate_name} gate failed.
Context:
{context}

Requirements:
- Address the specific quality issue
- Maintain academic tone and rigor
- Include specific citations where relevant
- Minimum 300 words

Write ONLY the section content (no heading):
"""
                new_content = _llm_generate(prompt, max_tokens=1500, temperature=0.6)
                corrected = self.replace_section(corrected, section_name, new_content)
                logger.info("Rewrote section '%s' (%d chars)", section_name, len(new_content))

        return corrected

    def _build_section_context(self, gate_name: str, record: Any, topic: str) -> str:
        """Build context string for section regeneration."""
        ctx_parts = [f"Topic: {topic}"]

        if gate_name == "sources" and record.sources:
            ctx_parts.append(f"Sources available: {len(record.sources)}")
            ctx_parts.append("Key sources:")
            for s in record.sources[:5]:
                ctx_parts.append(f"  - {s.get('title', '')} ({s.get('venue', '')})")

        elif gate_name == "gaps" and record.gaps:
            ctx_parts.append(f"Gaps identified: {len(record.gaps)}")
            for g in record.gaps[:3]:
                ctx_parts.append(f"  - {g.get('area', '')}: {g.get('evidence', '')[:100]}")

        elif gate_name == "hypotheses" and record.hypotheses:
            ctx_parts.append(f"Hypotheses: {len(record.hypotheses)}")
            for h in record.hypotheses[:3]:
                ctx_parts.append(f"  - {h.get('title', '')}")

        elif gate_name == "simulation" and record.simulation:
            sim = record.simulation
            ctx_parts.append(f"Simulation: {sim.pattern_id} ({sim.status})")
            ctx_parts.append(f"Metrics: {sim.metrics}")

        elif gate_name == "verification" and record.verification:
            ver = record.verification
            ctx_parts.append(f"Verification: {ver.backend} ({ver.status})")

        elif gate_name == "bibliography" and record.bibliography:
            ctx_parts.append(f"Bibliography: {len(record.bibliography)} sources")

        return "\n".join(ctx_parts)
