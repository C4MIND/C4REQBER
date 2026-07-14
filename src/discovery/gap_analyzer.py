from __future__ import annotations


"""Auto-Gap Analyzer — identifies research gaps from literature corpus."""

import logging
from typing import Any

from src.discovery.gap_analyzer_base import GAP_INDICATORS, RESOLUTION_INDICATORS, GapAnalyzer
from src.publishing.dissertation import _llm_generate


logger = logging.getLogger(__name__)


class AutoGapAnalyzer(GapAnalyzer):
    """Automatically identify research gaps from literature sources."""

    def analyze(self, sources: list[dict[str, Any]], topic: str) -> list[dict[str, Any]]:
        """Analyze sources and identify research gaps.

        Returns list of gap dicts with:
        - area: what is missing
        - evidence: supporting quotes from sources
        - novelty_score: how unexplored (0-1)
        - hypothesis_seed: suggested hypothesis direction
        """
        if not sources:
            return []

        # Extract text from sources
        texts = []
        for s in sources:
            title = s.get("title", "")
            snippet = s.get("snippet", s.get("abstract", s.get("description", "")))
            texts.append(f"{title}. {snippet}")

        "\n\n".join(texts)

        # Build rich corpus with real source attribution
        rich_corpus = ""
        for i, s in enumerate(sources[:10]):
            title = s.get("title", "")
            snippet = s.get("snippet", s.get("abstract", s.get("description", "")))
            url = s.get("url", "")
            rich_corpus += f"\n--- Source {i+1}: {title} ({url}) ---\n{snippet}\n"

        # Use LLM for sophisticated gap analysis WITH real evidence
        prompt = f"""Analyze this literature corpus on "{topic}" and identify the TOP 3 research gaps.

IMPORTANT: For evidence, you MUST quote specific phrases from the provided sources. Do NOT invent evidence.

Literature excerpts:
{rich_corpus[:5000]}

For each gap, provide:
1. **area**: What specific aspect is missing/underexplored?
2. **evidence**: Quote EXACT phrases from the sources above that indicate this gap, with source attribution (e.g., "Source 3: '...quote...'")
3. **novelty_score**: How unexplored is this? (0.0-1.0)
4. **hypothesis_seed**: What hypothesis could fill this gap?

Format as JSON list:
[
  {{
    "area": "...",
    "evidence": "Source X: '...exact quote from source...'",
    "novelty_score": 0.85,
    "hypothesis_seed": "..."
  }}
]

Focus on gaps that are:
- Specific enough to be testable
- Important for the field
- Feasible with current methods
- Supported by actual quotes from the provided sources
"""

        raw = _llm_generate(prompt, max_tokens=1200)

        # Parse JSON
        import json
        import re
        gaps = []
        try:
            match = re.search(r'\[.*?\]', raw, re.DOTALL)
            if match:
                gaps = json.loads(match.group())
        except (json.JSONDecodeError, re.error, ValueError):
            pass

        # Fallback: extract real quotes from sources
        if not gaps:
            gaps = self._extract_real_gaps(sources, topic)

        # Link each gap to best evidence sources via semantic similarity
        try:
            from src.llm.embeddings import find_best_evidence
            for gap in gaps:
                best = find_best_evidence(gap, sources, top_k=3)
                if best:
                    gap["evidence_sources"] = [
                        {"title": b.get("title", ""), "score": b.get("_evidence_score", 0.0)}
                        for b in best
                    ]
        except Exception:
            pass

        return gaps[:5]  # Max 5 gaps
    def _extract_real_gaps(self, sources: list[dict[str, Any]], topic: str) -> list[dict[str, Any]]:
        """Extract gaps with real quotes from source snippets."""
        gaps = []

        for s in sources:
            snippet = s.get("snippet", s.get("abstract", s.get("description", "")))
            title = s.get("title", "Untitled")

            if not snippet:
                continue

            # Find gap-indicating phrases in real snippets
            for indicator in GAP_INDICATORS:
                idx = snippet.lower().find(indicator)
                if idx != -1:
                    # Extract quote with context
                    start = max(0, idx - 120)
                    end = min(len(snippet), idx + len(indicator) + 120)
                    quote = snippet[start:end].strip()

                    # Compute resolution score — inverse of how well the gap is addressed
                    resolution_count = sum(1 for ri in set(RESOLUTION_INDICATORS) if ri in snippet.lower())
                    resolution_score = min(resolution_count * 0.15, 0.85)

                    # Build meaningful area from context + source title
                    ctx_start = max(0, idx - 20)
                    ctx = snippet[ctx_start:idx].strip()
                    ctx = ctx.lstrip("the ").lstrip("a ").lstrip("an ")
                    if len(ctx) < 5:
                        ctx = title[:50]

                    gaps.append({
                        "area": f"{ctx[:60]}: {indicator}",
                        "evidence": f"Source '{title[:50]}...': \"...{quote}...\"",
                        "novelty_score": max(0.15, 0.6 - resolution_score),
                        "resolution_score": resolution_score,
                        "hypothesis_seed": f"Investigate {topic} to resolve: {indicator}",
                    })

        # Deduplicate by area
        seen = set()
        unique = []
        for g in gaps:
            if g["area"] not in seen:
                seen.add(g["area"])
                unique.append(g)

        return unique[:3]

    def generate_gap_hypotheses(self, gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate hypotheses specifically targeting identified gaps."""
        hypotheses = []

        for gap in gaps:
            h = {
                "title": f"Addressing gap: {gap['area'][:80]}",
                "description": gap.get("hypothesis_seed", ""),
                "testability_score": gap.get("novelty_score", 0.5) * 0.9,
                "origin": "gap_analysis",
                "gap_evidence": gap.get("evidence", ""),
            }
            hypotheses.append(h)

        return hypotheses
