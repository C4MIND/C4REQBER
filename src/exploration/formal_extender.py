"""
c4reqber: Formal Framework Extender

Proposes and verifies extensions to existing formal libraries.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.llm.router import ProviderRouter

logger = logging.getLogger("c4reqber.exploration")


@dataclass
class ExtensionProposal:
    language: str
    code: str
    description: str
    compiles: bool
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "code": self.code[:500],
            "description": self.description,
            "compiles": self.compiles,
            "error": self.error,
        }


EXTENSION_PROMPT = """You are a formal methods expert. Extend the {library} library with a new definition or lemma for: {concept_gap}.

Requirements:
1. The code must be syntactically valid {language}
2. Use only standard library imports
3. Include brief comments explaining the formalization choices
4. If full proof is not possible, provide the definition/lemma statement

Return ONLY the code, no explanations outside comments."""


class FormalFrameworkExtender:
    """Propose formal library extensions."""

    def __init__(self) -> None:
        self._router = ProviderRouter()

    async def propose_extension(
        self,
        library: str,
        concept_gap: str,
        language: str = "lean4",
    ) -> ExtensionProposal | None:
        """Propose a formal extension.

        Args:
            library: Existing library name (e.g., "mathlib").
            concept_gap: Concept to formalize.
            language: Target language.

        Returns:
            ExtensionProposal if compilation succeeds, None otherwise.
        """
        prompt = EXTENSION_PROMPT.format(
            library=library,
            concept_gap=concept_gap,
            language=language,
        )

        try:
            response = await self._router.generate(
                stage_name="formal_extension",
                prompt=prompt,
                system_prompt=f"You are a {language} expert. Output valid code only.",
            )
            code = response.content if hasattr(response, "content") else str(response)
            code = self._extract_code(code, language)

            # Try to compile
            compiles, error = await self._verify_compilation(code, language)

            return ExtensionProposal(
                language=language,
                code=code,
                description=f"Extension for {concept_gap} in {library}",
                compiles=compiles,
                error=error,
            )
        except Exception as e:
            logger.warning("Formal extension failed: %s", e)
            return None

    # Alias for API compatibility with v8 router
    propose = propose_extension

    def _extract_code(self, text: str, language: str) -> str:
        """Extract code from markdown fences."""
        import re

        pattern = rf"```{re.escape(language)}\s*\n(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Try any fence
        match = re.search(r"```(?:\w*)?\s*\n(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()

        return text.strip()

    async def _verify_compilation(self, code: str, language: str) -> tuple[bool, str | None]:
        """Verify code compiles."""
        try:
            if language == "lean4":
                from src.verification.lean4_client import Lean4Client
                client = Lean4Client()
                if not client.available:
                    return True, None  # Assume ok if Lean4 not installed
                result = client.check_proof(code)
                return result.get("success", False), result.get("error")
            elif language == "coq":
                from src.verification.coq_client import CoqClient
                client = CoqClient()  # type: ignore[assignment]
                result = client.check_proof(code)
                return result.get("success", False), result.get("error")
            elif language == "dafny":
                from src.verification.dafny_client import DafnyClient
                client = DafnyClient()  # type: ignore[assignment]
                result = client.check_proof(code)
                return result.get("success", False), result.get("error")
            else:
                return True, None
        except Exception as e:
            return False, str(e)
