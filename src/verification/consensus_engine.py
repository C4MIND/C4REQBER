"""
c4reqber: Consensus Engine

Aggregates proof results across multiple formal backends (Lean4, Coq, Dafny).
Provides multi-language consensus with uncertainty quantification.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from src.verification.llm_prover import LLMProver

logger = logging.getLogger("c4reqber.verification.consensus")


@dataclass
class ConsensusResult:
    """Result of multi-language consensus verification."""

    status: str  # "verified", "partial", "failed", "insufficient"
    confidence: float  # 0.0 - 1.0
    languages: dict[str, dict[str, Any]] = field(default_factory=dict)
    human_review_recommended: bool = False
    theorem_statement: str = ""
    cost_estimate_usd: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "confidence": round(self.confidence, 3),
            "languages": self.languages,
            "human_review_recommended": self.human_review_recommended,
            "theorem_statement": self.theorem_statement,
            "cost_estimate_usd": round(self.cost_estimate_usd, 4),
        }


# Rough cost estimate per language (DeepSeek V4 Pro prices, USD per 1M tokens)
_COST_PER_LANGUAGE_USD = 0.012  # ~4K in + 2K out per iteration × 3 iterations


class ConsensusEngine:
    """Multi-language consensus verification for formal proofs."""

    def __init__(self) -> None:
        self._prover = LLMProver()

    async def verify_with_consensus(
        self,
        theorem_statement: str,
        languages: list[str] | None = None,
        min_agreement: int = 2,
    ) -> ConsensusResult:
        """Verify theorem across multiple languages and aggregate consensus.

        Args:
            theorem_statement: Formalizable theorem statement string.
            languages: List of languages to try (default: ["lean4", "coq", "dafny"]).
            min_agreement: Minimum number of languages that must agree for "verified".

        Returns:
            ConsensusResult with status, confidence, per-language details.
        """
        if languages is None:
            languages = ["lean4", "coq", "dafny"]

        if not theorem_statement or len(theorem_statement) < 10:
            return ConsensusResult(
                status="insufficient",
                confidence=0.0,
                theorem_statement=theorem_statement,
                human_review_recommended=True,
            )

        # Run all languages in parallel
        tasks = {
            lang: asyncio.create_task(self._try_prove(theorem_statement, lang))
            for lang in languages
        }

        results: dict[str, Any] = {}
        for lang, task in tasks.items():
            try:
                results[lang] = await task
            except Exception as e:
                logger.warning("ConsensusEngine: %s prover error: %s", lang, e)
                results[lang] = {"valid": False, "error": str(e)}

        # Count agreements
        valid_count = sum(1 for r in results.values() if r.get("valid", False))
        total = len(languages)

        if valid_count >= min_agreement:
            status = "verified"
            confidence = valid_count / total
            human_review = False
        elif valid_count == 1:
            status = "partial"
            confidence = valid_count / total
            human_review = True
        else:
            status = "failed"
            confidence = 0.0
            human_review = True

        # Build per-language details
        lang_details: dict[str, dict[str, Any]] = {}
        for lang, res in results.items():
            lang_details[lang] = {
                "valid": res.get("valid", False),
                "iterations": res.get("iterations", 0),
                "error": res.get("error", "")[:200] if not res.get("valid") else None,
                "total_time_ms": res.get("total_time_ms", 0),
            }

        return ConsensusResult(
            status=status,
            confidence=confidence,
            languages=lang_details,
            human_review_recommended=human_review,
            theorem_statement=theorem_statement,
            cost_estimate_usd=_COST_PER_LANGUAGE_USD * total,
        )

    async def _try_prove(self, theorem_statement: str, language: str) -> dict[str, Any]:
        """Attempt proof in a single language."""
        try:
            result = await self._prover.prove(theorem_statement, language)
            return {
                "valid": result.valid,
                "iterations": len(result.iterations),
                "error": result.error,
                "total_time_ms": result.total_time_ms,
                "proof": result.proof[:200] if result.proof else "",
            }
        except Exception as e:
            logger.warning("ConsensusEngine _try_prove error: %s", e)
            return {"valid": False, "error": str(e)}
