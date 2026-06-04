"""
c4reqber: Semantic Alignment Checker

Verifies that a compiled proof actually proves the stated theorem.
Catches cases where proof compiles but for a different theorem.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from src.llm.router import ProviderRouter


logger = logging.getLogger("c4reqber.verification.alignment")


@dataclass
class AlignmentResult:
    """Result of semantic alignment check."""

    aligned: bool
    explanation: str = ""
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "aligned": self.aligned,
            "explanation": self.explanation,
            "confidence": round(self.confidence, 3),
        }


ALIGNMENT_PROMPT = """You are a formal verification expert. Your task is to determine whether the given proof actually proves the stated theorem.

THEOREM STATEMENT:
{theorem_statement}

PROOF CODE ({language}):
{proof_code}

INSTRUCTIONS:
1. Read the theorem statement carefully.
2. Read the proof code carefully.
3. Determine if the proof proves THIS theorem, a DIFFERENT theorem, or nothing at all.
4. Consider: does the proof use `sorry`, `admitted`, `assume false`, or other placeholders?
5. Consider: does the proof prove a special case instead of the general claim?

Respond with ONLY a JSON object:
{{
  "aligned": true or false,
  "explanation": "brief explanation of why it aligns or doesn't align",
  "confidence": float between 0.0 and 1.0
}}

Be strict. If uncertain, set aligned to false and confidence below 0.5."""


class SemanticAlignmentChecker:
    """Check semantic alignment between theorem statement and proof code."""

    def __init__(self) -> None:
        self._router = ProviderRouter()

    async def check_alignment(
        self,
        theorem_statement: str,
        proof_code: str,
        language: str,
    ) -> AlignmentResult:
        """Check if proof_code actually proves theorem_statement.

        Args:
            theorem_statement: The claimed theorem.
            proof_code: The compiled proof.
            language: Target language (lean4, coq, dafny, etc.).

        Returns:
            AlignmentResult with aligned flag and explanation.
        """
        if not theorem_statement or not proof_code:
            return AlignmentResult(
                aligned=False,
                explanation="Empty theorem or proof",
                confidence=1.0,
            )

        # Quick heuristic: check if proof contains the theorem keywords
        # This is a fast pre-filter before LLM call
        theorem_keywords = set(
            w.lower()
            for w in re.findall(r'\b[A-Za-z][A-Za-z0-9_]*\b', theorem_statement)
            if len(w) > 3
        )
        proof_keywords = set(
            w.lower()
            for w in re.findall(r'\b[A-Za-z][A-Za-z0-9_]*\b', proof_code)
            if len(w) > 3
        )
        if theorem_keywords and not (theorem_keywords & proof_keywords):
            return AlignmentResult(
                aligned=False,
                explanation="Proof contains no overlapping keywords with theorem statement",
                confidence=0.8,
            )

        prompt = ALIGNMENT_PROMPT.format(
            theorem_statement=theorem_statement[:1000],
            proof_code=proof_code[:2000],
            language=language,
        )

        try:
            response = await self._router.generate(
                stage_name="semantic_alignment",
                prompt=prompt,
                system_prompt="You are a strict formal verification reviewer. Output valid JSON only.",
            )
            content = response.content if hasattr(response, "content") else str(response)
            return self._parse_response(content)
        except Exception as e:
            logger.warning("SemanticAlignmentChecker LLM error: %s", e)
            return AlignmentResult(
                aligned=False,
                explanation=f"LLM error during alignment check: {e}",
                confidence=0.0,
            )

    def _parse_response(self, content: str) -> AlignmentResult:
        """Parse JSON response from LLM."""
        import json

        json_match = re.search(r'```(?:json)?\s*\n?(.*?)```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1).strip()
        else:
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1 and end > start:
                content = content[start:end + 1]

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning("SemanticAlignmentChecker JSON parse error: %s", e)
            return AlignmentResult(
                aligned=False,
                explanation="Could not parse alignment response",
                confidence=0.0,
            )

        if not isinstance(data, dict):
            return AlignmentResult(
                aligned=False,
                explanation="Invalid alignment response format",
                confidence=0.0,
            )

        aligned = bool(data.get("aligned", False))
        confidence = 0.5
        try:
            confidence = float(data.get("confidence", 0.5))
        except (TypeError, ValueError):
            pass

        return AlignmentResult(
            aligned=aligned,
            explanation=str(data.get("explanation", "")),
            confidence=confidence,
        )
