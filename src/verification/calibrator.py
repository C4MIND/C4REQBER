"""Smart verification backend calibrator for C44TCDI.

Automatically selects the optimal verification backend based on claim syntax,
pipeline context, and optional user domain hints.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal


BackendChoice = Literal["lean4", "coq", "dafny", "agda", "hoare", "cvc5", "tla", "alloy"]


@dataclass
class VerificationContext:
    """Context for backend selection decisions.

    Attributes:
        previous_tool: Name of the previous tool in the pipeline (e.g. ``c4_simulate``).
        domain_hint: Optional user override for the backend.
    """

    previous_tool: str | None = None
    domain_hint: str | None = None


class VerificationCalibrator:
    """Select the optimal verification backend for a given claim.

    Selection priority:
    1. User domain hint (if valid backend).
    2. Pipeline context (previous tool → backend mapping).
    3. Claim syntax pattern matching.
    4. Default fallback (Lean4).
    """

    # Keyword → backend mappings (lower priority than context/hint)
    _KEYWORD_PATTERNS: dict[BackendChoice, list[str]] = {
        "lean4": [
            r"\btheorem\b",
            r"\blemma\b",
            r"\bproof\b",
            r"\bexample\b",
            r"\binductive\b",
            r"\bstructure\b",
            r"\bnamespace\b",
            r"\bby\s+",
            r"\bsimp\b",
            r"\btactic\b",
            r"#eval",
        ],
        "coq": [
            r"\bTheorem\b",
            r"\bLemma\b",
            r"\bProof\b",
            r"\bQed\b",
            r"\bInductive\b",
            r"\bFixpoint\b",
            r"\bDefinition\b",
            r"\btauto\b",
            r"\bauto\b",
            r"\bintro[s]?\b",
        ],
        "agda": [
            r"\bdata\s+",
            r"\brecord\b",
            r"\bopen\b",
            r"\bmodule\b",
            r"\bpostulate\b",
            r"\bwhere\b",
            r"∀",
            r"∃",
            r"→",
            r"≡",
        ],
        "dafny": [
            r"\bmethod\b",
            r"\bfunction\b",
            r"\bpredicate\b",
            r"\brequires\b",
            r"\bensures\b",
            r"\bmodifies\b",
            r"\binvariant\b",
            r"\bdecreases\b",
            r"\bclass\b",
            r"\btrait\b",
            r"\bghost\b",
            r"\bcorrectness\b",
            r"\bquicksort\b",
            r"\bmergesort\b",
            r"\bsorted\b",
        ],
        "hoare": [
            r"\bprecondition\b",
            r"\bpostcondition\b",
            r"\bassertion\b",
            r"\binvariant\b",
            r"\bwhile\b.*\{.*\}",
            r"\bwp\b",
            r"\bweakest.precondition\b",
            r"\{[^}]*\}[^}]*?\{[^}]*\}",
            r"\bHoare\b",
            r"\bverification.condition\b",
        ],
        "cvc5": [
            r"\(declare-",
            r"\(assert",
            r"\(check-sat\)",
            r"set-logic",
            r"\(define-fun",
            r"\(forall",
            r"\(exists",
        ],
        "tla": [
            r"----\s*MODULE",
            r"\bEXTENDS\b",
            r"\bInit\s*==",
            r"\bNext\s*==",
            r"\[\]",
            r"<>",
            r"\bTLA\+",
        ],
        "alloy": [
            r"\bsig\b",
            r"\bfun\b",
            r"\bassert\b",
            r"\brun\b",
            r"\bcheck\b",
            r"\bfact\b",
            r"\bpred\b",
        ],
    }

    # Pipeline tool → backend mapping
    _PIPELINE_MAP: dict[str, BackendChoice] = {
        "c4_simulate": "hoare",
        "c4_codegen": "dafny",
        "c4_solve": "lean4",
        "c4_search": "agda",
    }

    # Valid backends for quick validation
    _VALID_BACKENDS: set[str] = {"lean4", "coq", "dafny", "agda", "hoare", "cvc5", "tla", "alloy"}

    def select_backend(
        self,
        claim: str,
        context: VerificationContext | None = None,
    ) -> BackendChoice:
        """Select the optimal verification backend.

        Args:
            claim: The theorem / code / specification to verify.
            context: Optional pipeline context and domain hint.

        Returns:
            Selected backend identifier.
        """
        if context is None:
            context = VerificationContext()

        # 1. User domain hint (highest priority)
        if context.domain_hint and context.domain_hint.lower() in self._VALID_BACKENDS:
            return context.domain_hint.lower()  # type: ignore[return-value]

        # 2. Pipeline context
        if context.previous_tool and context.previous_tool in self._PIPELINE_MAP:
            return self._PIPELINE_MAP[context.previous_tool]

        # 3. Syntax pattern matching
        scores = self._score_claim(claim)
        if scores:
            return max(scores, key=lambda k: scores[k])

        # 4. Default fallback
        return "lean4"

    def _score_claim(self, claim: str) -> dict[BackendChoice, int]:
        """Score each backend based on keyword matches in *claim*.

        Args:
            claim: The text to analyse.

        Returns:
            Mapping from backend to match count.
        """
        scores: dict[BackendChoice, int] = {}
        for backend, patterns in self._KEYWORD_PATTERNS.items():
            count = sum(1 for pat in patterns if re.search(pat, claim, re.IGNORECASE))
            if count:
                scores[backend] = count
        return scores

    @classmethod
    def available_backends(cls) -> list[str]:
        """Return a list of supported backend identifiers."""
        return list(cls._VALID_BACKENDS)

    def explain_choice(
        self,
        claim: str,
        context: VerificationContext | None = None,
    ) -> dict[str, str | int | None]:
        """Explain why a backend was selected (useful for debugging).

        Args:
            claim: The theorem / code / specification to verify.
            context: Optional pipeline context and domain hint.

        Returns:
            Dict with ``backend``, ``reason``, and ``scores``.
        """
        if context is None:
            context = VerificationContext()

        scores = self._score_claim(claim)

        if context.domain_hint and context.domain_hint.lower() in self._VALID_BACKENDS:
            reason = f"domain_hint: {context.domain_hint}"
            backend = context.domain_hint.lower()
        elif context.previous_tool and context.previous_tool in self._PIPELINE_MAP:
            reason = f"pipeline_tool: {context.previous_tool}"
            backend = self._PIPELINE_MAP[context.previous_tool]
        elif scores:
            backend = max(scores, key=scores.get)  # type: ignore[arg-type]
            reason = f"syntax_match (score={scores[backend]})"
        else:
            backend = "lean4"
            reason = "default_fallback"

        return {
            "backend": backend,
            "reason": reason,
            "scores": str(scores),
        }
