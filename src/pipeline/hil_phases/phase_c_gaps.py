from __future__ import annotations


"""Phase C: Gap Analysis & Hypothesis Generation."""

import logging
import re
from typing import Any

from src.discovery.gap_analyzer import AutoGapAnalyzer
from src.pipeline.config import PipelineConfig


logger = logging.getLogger(__name__)


class PhaseC_GapAnalysis:
    """Analyze research gaps and generate hypotheses from them."""

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self.config = config or PipelineConfig(name="default")
        self.gap_analyzer = AutoGapAnalyzer()

    def run(self, topic: str, sources: list[dict[str, Any]], usp_context: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Run gap analysis and return (gaps, hypotheses)."""
        print("\n[Phase C] Gap Analysis & Hypothesis Generation...")
        print("\n[C1/7] Analyzing research gaps...")

        gaps = self.gap_analyzer.analyze(sources, topic)
        print(f"      Found {len(gaps)} research gaps")
        for g in gaps[:3]:
            print(f"        - {g.get('area', '')[:60]}...")

        # Generate hypotheses from gaps
        print("\n[D1/7] Generating hypotheses from gaps...")
        gap_hypotheses = self.gap_analyzer.generate_gap_hypotheses(gaps)

        # General hypotheses with config-driven ambition
        from src.publishing.dissertation import _llm_generate
        sources_text = "\n".join([
            f"- {s.get('title', '')[:80]}\n  {s.get('snippet', '')[:200]}"
            for s in sources[:5]
        ])
        ambition_text = {
            "incremental": "incremental improvements (10-20% better)",
            "transformative": "transformative claims (2-5x improvement, new mechanisms)",
            "paradigm_shifting": "PARADIGM-SHIFTING claims that challenge fundamental assumptions (10x improvement, overturn existing theory, enable new design principles)",
        }.get(self.config.hypothesis_ambition, "paradigm-shifting")

        c4_state = usp_context.get("c4_state", "unknown")
        mp_perspectives = usp_context.get("mp_perspectives", [])
        qzrf_operators = usp_context.get("qzrf_operators", [])
        iso_mappings = usp_context.get("iso_mappings", [])
        matrix_patterns = usp_context.get("matrix_patterns", [])
        impact_result = usp_context.get("impact", {})

        usp_context_text = f"""
C4 State: {c4_state}
MP Perspectives: {len(mp_perspectives)} perspectives generated
QZRF Operators: {', '.join(qzrf_operators[:5])}
Isomorphisms: {'found' if iso_mappings else 'none'}
MatrixDream Patterns: {len(matrix_patterns)} matches
IMPACT Entities: {len(impact_result.get('entities', []))}
"""

        hypo_prompt = f"""Based on these sources about \"{topic}\":
{sources_text}

{usp_context_text}

Generate {self.config.min_hypotheses} {ambition_text} scientific hypotheses. Each must include:
- A BOLD claim
- SPECIFIC NUMERICAL PREDICTIONS (percentages, timeframes, concentrations, factors)
- Clear falsifiability criteria

Format as numbered list (1., 2., 3.)."""
        hypo_raw = _llm_generate(hypo_prompt, max_tokens=600, temperature=self.config.llm_temperature)

        general_hypotheses: list[dict[str, Any]] = []
        for line in hypo_raw.split("\n"):
            m = re.match(r'^(?:\*\*)?\d+[\.\)]\s*(?:\*\*)?\s*(.+)', line.strip())
            if m and len(m.group(1)) > 10:
                general_hypotheses.append({"title": m.group(1), "description": m.group(1), "testability_score": 0.7})

        print(f"      General hypotheses: {len(general_hypotheses)}")
        hypotheses = gap_hypotheses + general_hypotheses
        if not hypotheses:
            hypotheses = [{"title": f"Novel mechanism in {topic}", "description": "TBD", "testability_score": 0.6}]

        print(f"      Generated {len(hypotheses)} hypotheses ({len(gap_hypotheses)} from gaps)")
        return gaps, hypotheses
