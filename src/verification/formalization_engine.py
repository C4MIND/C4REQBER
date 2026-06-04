"""
c4reqber: Formalization Engine

Transforms natural-language hypothesis + evidence into a formalizable theorem statement.
Used as middleware between verify_discovery() and LLMProver.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from src.llm.router import ProviderRouter

logger = logging.getLogger("c4reqber.verification.formalization")


@dataclass
class FormalizationResult:
    """Result of formalizing a natural-language hypothesis."""

    theorem_statement: str = ""
    assumptions: list[str] | None = None
    domain: str = ""
    formalizability_score: float = 0.0
    not_formalizable_reason: str | None = None

    def __post_init__(self) -> None:
        if self.assumptions is None:
            self.assumptions = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "theorem_statement": self.theorem_statement,
            "assumptions": self.assumptions,
            "domain": self.domain,
            "formalizability_score": round(self.formalizability_score, 3),
            "not_formalizable_reason": self.not_formalizable_reason,
        }


def _sanitize_for_prompt(text: str, max_len: int = 2000) -> str:
    """Sanitize text before inserting into LLM prompts."""
    if not text:
        return text
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    text = re.sub(r'[\u202A-\u202E\u2066-\u2069]', '', text)
    text = text.replace("<system>", "[SYSTEM_TAG_REMOVED]").replace("</system>", "[/SYSTEM_TAG_REMOVED]")
    text = text.replace("</user_query>", "<\\/user_query>")
    text = text.replace("'''", "' ' '").replace('"""', '" " "')
    text = re.sub(r'(?i)^\s*(system|user|assistant)\s*[:>]', '[BLOCKED]', text)
    return text[:max_len]


FORMALIZATION_PROMPT = """You are a formal verification engineer. Given a scientific hypothesis and supporting evidence, extract a precise mathematical claim that can be formalized in a theorem prover (Lean4, Coq, or Dafny).

HYPOTHESIS:
{hypothesis}

EVIDENCE:
{evidence}

INSTRUCTIONS:
1. State the core mathematical claim explicitly.
2. List all assumptions needed for the claim to hold.
3. Identify the domain (mathematics, physics, biology, computer_science, or other).
4. Assess formalizability: how easily can this be turned into a formal proof? (0.0-1.0)
5. If the hypothesis is too vague, ambiguous, or not amenable to formalization, set formalizability_score below 0.3 and explain why.

Return ONLY a JSON object with this exact schema:
{{
  "theorem_statement": "string",
  "assumptions": ["string"],
  "domain": "string",
  "formalizability_score": float
}}

If not formalizable, use:
{{
  "theorem_statement": "",
  "assumptions": [],
  "domain": "",
  "formalizability_score": 0.0,
  "not_formalizable_reason": "string"
}}"""


class FormalizationEngine:
    """Transform natural-language hypothesis into formalizable theorem statement."""

    def __init__(self) -> None:
        self._router = ProviderRouter()

    async def formalize(
        self,
        hypothesis: dict[str, Any],
        evidence: list[str] | None = None,
    ) -> FormalizationResult:
        """Formalize a hypothesis into a theorem statement.

        Args:
            hypothesis: Dict with at least "text" key.
            evidence: Optional list of evidence strings (e.g. paper titles).

        Returns:
            FormalizationResult with theorem_statement, assumptions, domain, score.
        """
        hyp_text = hypothesis.get("text", "") if isinstance(hypothesis, dict) else str(hypothesis)
        hyp_text = _sanitize_for_prompt(hyp_text, 1500)

        evidence_text = ""
        if evidence:
            evidence_lines = []
            for i, ev in enumerate(evidence[:10], 1):
                ev_clean = _sanitize_for_prompt(str(ev), 300)
                if ev_clean:
                    evidence_lines.append(f"[{i}] {ev_clean}")
            evidence_text = "\n".join(evidence_lines)
        if not evidence_text:
            evidence_text = "No explicit evidence provided."

        prompt = FORMALIZATION_PROMPT.format(
            hypothesis=hyp_text,
            evidence=evidence_text,
        )

        try:
            response = await self._router.generate(
                stage_name="formalization",
                prompt=prompt,
                system_prompt="You are a precise formal verification engineer. Output valid JSON only.",
            )
            content = response.content if hasattr(response, "content") else str(response)
            return self._parse_response(content)
        except Exception as e:
            logger.warning("FormalizationEngine LLM error: %s", e)
            return FormalizationResult(
                not_formalizable_reason=f"LLM error: {e}",
            )

    def _parse_response(self, content: str) -> FormalizationResult:
        """Parse JSON response from LLM."""
        # Extract JSON from markdown code block if present
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)```', content, re.DOTALL)
        if json_match:
            content = json_match.group(1).strip()
        else:
            # Try to find outermost JSON object
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1 and end > start:
                content = content[start:end + 1]

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning("FormalizationEngine JSON parse error: %s. Content: %s", e, content[:200])
            return FormalizationResult(
                not_formalizable_reason=f"JSON parse error: {e}",
            )

        if not isinstance(data, dict):
            return FormalizationResult(
                not_formalizable_reason="Response is not a JSON object",
            )

        score = data.get("formalizability_score", 0.0)
        try:
            score = float(score)
        except (TypeError, ValueError):
            score = 0.0

        if score < 0.3 or data.get("not_formalizable_reason"):
            return FormalizationResult(
                formalizability_score=score,
                not_formalizable_reason=data.get("not_formalizable_reason", "Score below threshold"),
            )

        return FormalizationResult(
            theorem_statement=str(data.get("theorem_statement", "")),
            assumptions=[str(a) for a in data.get("assumptions", []) if a],
            domain=str(data.get("domain", "")),
            formalizability_score=score,
        )
