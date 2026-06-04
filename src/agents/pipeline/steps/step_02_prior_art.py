"""
C4REQBER: Pipeline Step 02 — Prior Art Search

Uses MultiSourceSearcher for federated search across 10+ academic APIs.
"""
from __future__ import annotations

import time
from typing import Any

from src.agents.pipeline.steps.base import PipelineStage, PipelineStep, PipelineStepResult


class PriorArtStep(PipelineStep):
    """Step 2: Prior Art Search — search for existing solutions."""

    def __init__(self, prior_art: Any) -> None:
        self._prior_art = prior_art

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.PRIOR_ART

    def get_required_context(self) -> list[str]:
        return ["problem"]

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute federated prior-art search."""
        problem = context["problem"]
        start = time.time()

        try:
            result = await self._prior_art.search_all(
                problem,
                max_per_source=10,
                include_web=False,
            )
            papers = result.get("papers", [])

            # Compute max confidence from top result relevance score
            max_confidence = max(
                (p.get("relevance_score", 0.0) for p in papers),
                default=0.0,
            )

            # Generate recommendation based on confidence
            if max_confidence > 0.9:
                recommendation = (
                    f"High-confidence match found ({max_confidence:.0%}). "
                    "Consider using the top result as a starting point."
                )
            elif max_confidence > 0.7:
                recommendation = (
                    f"Related work found ({max_confidence:.0%} confidence). "
                    "Synthesize from these sources or proceed to novel solution."
                )
            else:
                recommendation = (
                    f"Limited prior art ({max_confidence:.0%} confidence). "
                    "Proceeding to full C4-based synthesis."
                )

            top_papers = papers[:10]
            output_data = {
                "total_results": len(papers),
                "max_confidence": round(max_confidence, 3),
                "recommendation": recommendation,
                "top_results": [self._paper_to_dict(p) for p in papers[:3]],
                "merged_sources": [self._paper_to_dict(p) for p in top_papers],
                "sources": [
                    {
                        "id": p.get("doi", p.get("id", "")),
                        "title": p.get("title", ""),
                        "authors": p.get("authors", []),
                        "year": p.get("year", 0),
                        "abstract": (p.get("abstract") or "")[:500],
                        "url": p.get("url", ""),
                        "source": p.get("source", ""),
                        "citation_count": p.get("citation_count", 0),
                    }
                    for p in top_papers
                ],
                "source_names": result.get("source_names", []),
                "total_time": result.get("total_time", 0.0),
            }
            prior_art_confidence = max_confidence
            status = "completed"
            error = None
        except Exception as e:
            status = "error"
            error = str(e)
            prior_art_confidence = 0.0
            output_data = {
                "max_confidence": 0.0,
                "recommendation": "Search failed",
            }

        # Store confidence in context for early-exit logic
        context["prior_art_confidence"] = prior_art_confidence

        return PipelineStepResult(
            stage=self.stage,
            status=status,
            input_data={"problem": problem},
            output_data=output_data,
            duration_ms=(time.time() - start) * 1000,
            error=error,
        )

    @staticmethod
    def _paper_to_dict(paper: dict[str, Any]) -> dict[str, Any]:
        """Normalize paper dict for downstream consumption."""
        return {
            "id": paper.get("doi", paper.get("id", "")),
            "title": paper.get("title", ""),
            "authors": paper.get("authors", []),
            "year": paper.get("year", 0),
            "abstract": (paper.get("abstract") or "")[:300]
            + ("..." if (paper.get("abstract") or "") else ""),
            "url": paper.get("url", ""),
            "source": paper.get("source", ""),
            "relevance_score": round(paper.get("relevance_score", 0.0), 3),
            "citation_count": paper.get("citation_count", 0),
            "cross_validated": paper.get("cross_validated", False),
        }


# Backward compatibility: function-based API
async def step_prior_art(
    problem: str, prior_art: Any, multi_searcher: Any = None
) -> tuple[PipelineStepResult, float]:
    """Legacy function-based API."""
    step = PriorArtStep(prior_art)
    result = await step.execute({"problem": problem})
    confidence = result.output_data.get("max_confidence", 0.0)
    return result, confidence
