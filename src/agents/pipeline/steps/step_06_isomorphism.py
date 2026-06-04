"""
C4REQBER: Pipeline Step 06 — Isomorphism Search
"""
from __future__ import annotations

import re
import time
from typing import Any

from src.agents.pipeline.steps.base import (
    PipelineStage,
    PipelineStep,
    PipelineStepResult,
)
from src.c4.state import C4State
from src.c4.transformer import DomainTransformer
from src.memory.bank import MemoryQuery, StructuralMemoryBank


_STOP_WORDS = frozenset(
    [
        "about",
        "above",
        "across",
        "after",
        "against",
        "along",
        "among",
        "around",
        "because",
        "before",
        "behind",
        "below",
        "beneath",
        "beside",
        "between",
        "beyond",
        "during",
        "except",
        "inside",
        "instead",
        "into",
        "near",
        "off",
        "onto",
        "outside",
        "over",
        "since",
        "through",
        "throughout",
        "till",
        "toward",
        "under",
        "until",
        "upon",
        "within",
        "without",
        "should",
        "would",
        "could",
        "might",
        "must",
        "shall",
        "will",
        "this",
        "that",
        "these",
        "those",
        "they",
        "them",
        "their",
        "there",
        "then",
        "than",
        "when",
        "where",
        "what",
        "which",
        "while",
        "with",
        "from",
        "have",
        "been",
        "being",
        "were",
        "are",
        "was",
        "is",
        "has",
        "had",
        "does",
        "did",
        "doing",
        "done",
        "each",
        "every",
        "some",
        "many",
        "much",
        "more",
        "most",
        "other",
        "another",
        "such",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "can",
        "may",
        "also",
        "how",
        "all",
        "any",
        "both",
        "either",
        "neither",
        "one",
        "two",
        "first",
        "last",
        "next",
        "now",
    ]
)


def _extract_entities(text: str) -> list[str]:
    cleaned = re.sub(r"[^\w\s-]", " ", text)
    words = cleaned.split()
    entities = []
    for word in words:
        w = word.strip("-").lower()
        if not w or w in _STOP_WORDS or w.isdigit():
            continue
        if word[0].isupper() or len(w) >= 5 or "-" in word:
            entities.append(w)
    seen = set()
    result = []
    for e in entities:
        if e not in seen:
            seen.add(e)
            result.append(e)
    return result[:15]


class IsomorphismSearchStep(PipelineStep):
    """Step 6: Isomorphism Search — find structural mappings across domains."""

    @property
    def stage(self) -> PipelineStage:
        return PipelineStage.ISOMORPHISM_SEARCH

    def get_required_context(self) -> list[str]:
        return ["problem", "domain_hint", "c4_state", "transformer"]

    def get_optional_context(self) -> list[str]:
        return ["memory"]

    async def execute(self, context: dict[str, Any]) -> PipelineStepResult:
        """Execute."""
        problem: str = context["problem"]
        domain_hint: str | None = context.get("domain_hint")
        c4_state: C4State = context["c4_state"]
        transformer: DomainTransformer = context["transformer"]
        memory: StructuralMemoryBank | None = context.get("memory")
        start = time.time()

        try:
            entities = _extract_entities(problem)
            transformer.fingerprint(
                domain=domain_hint or "general",
                entities=entities[:10],
                relations=[],
                constraints=[],
                c4_state=c4_state,
            )

            memory_results = []
            if memory is not None:
                query = MemoryQuery(
                    query_text=problem,
                    domain=domain_hint or "general",
                    min_confidence=0.5,
                    limit=5,
                )
                memory_results = await memory.search(query)
            found = len(memory_results) > 0

            output_data = {
                "found": found,
                "memory_hits": len(memory_results),
                "mapping": memory_results[0].get("mapping", {})
                if memory_results
                else {},
            }
            status = "completed"
            error = None
        except Exception as e:
            status = "error"
            error = str(e)
            output_data = {"found": False, "memory_hits": 0}

        return PipelineStepResult(
            stage=self.stage,
            status=status,
            output_data=output_data,
            duration_ms=(time.time() - start) * 1000,
            error=error,
        )


async def step_isomorphism_search(
    problem: str,
    domain_hint: str | None,
    c4_state: C4State,
    transformer: DomainTransformer,
    memory: StructuralMemoryBank,
) -> PipelineStepResult:
    """Legacy function-based API."""
    step = IsomorphismSearchStep()
    return await step.execute(
        {
            "problem": problem,
            "domain_hint": domain_hint,
            "c4_state": c4_state,
            "transformer": transformer,
            "memory": memory,
        }
    )
