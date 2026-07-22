"""
c4reqber: LLM-Based Formal Proof Generator

Takes a natural-language hypothesis and iteratively generates,
compiles, and fixes formal proofs across 9 verification backends:

  - Lean4, Coq, Dafny, Agda, Z3, Hoare, CVC5, TLA+, Alloy

Workflow per language:
  1. LLM generates a proof in the target language
  2. The native compiler/prover checks it
  3. On error → LLM gets the error + original hypothesis → fix
  4. Repeat up to ``max_iterations`` times
  5. Return final result with full trace

Uses ``src.llm.router.ProviderRouter`` for LLM access.
"""

from __future__ import annotations

import importlib
import inspect
import re
import time
from dataclasses import dataclass, field
from typing import Any

from src.llm.gateway import DefaultGateway


def _sanitize_for_prompt(text: str, max_len: int = 2000) -> str:
    """Sanitize text before inserting into LLM prompts."""
    if not text:
        return text
    # Strip control characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    # Strip Unicode bidi overrides
    text = re.sub(r"[\u202A-\u202E\u2066-\u2069]", "", text)
    # Neutralize role tags
    text = text.replace("<system>", "[SYSTEM_TAG_REMOVED]").replace(
        "</system>", "[/SYSTEM_TAG_REMOVED]"
    )
    text = text.replace("</user_query>", "<\\/user_query>")
    text = text.replace("'''", "' ' '").replace('"""', '" " "')
    # Block bare role prefixes
    text = re.sub(r"(?i)^\s*(system|user|assistant)\s*[:>]", "[BLOCKED]", text)
    return text[:max_len]


LANGUAGES = (
    "lean4",
    "coq",
    "dafny",
    "agda",
    "z3",
    "hoare",
    "cvc5",
    "tla",
    "alloy",
    "haskell-typecheck",
    "haskell-quickcheck",
)

PROOF_PROMPT_TEMPLATE = """You are a formal verification engineer. Translate the following scientific hypothesis into a {language} formal proof.

HYPOTHESIS:
{hypothesis}

CONSTRAINTS:
1. The proof must be syntactically valid {language}
2. Use only standard libraries — no custom imports
3. If the hypothesis cannot be fully formalized, prove the nearest formal approximation
4. Add comments explaining the formalization choices

{language_hints}

Return ONLY the proof code, no explanations outside comments."""

LANGUAGE_HINTS: dict[str, str] = {
    "lean4": "Use Lean 4 syntax. Start with 'theorem hypothesis : ...'",
    "coq": "Use Coq syntax. Start with 'Theorem hypothesis : Prop.'",
    "dafny": "Use Dafny syntax. Use 'method' or 'lemma' with ensures/requires.",
    "agda": "Use Agda syntax. Postulate what cannot be proved.",
    "z3": "Use SMT-LIB2 format. Submit as (assert ...) (check-sat).",
    "hoare": "Use format: {precondition} command {postcondition}",
    "cvc5": "Use SMT-LIB2 for CVC5. Include (set-logic ...) (declare-const ...) (assert ...) (check-sat).",
    "tla": "Use TLA+ MODULE syntax with Init, Next, optional Spec. Bounded state spaces preferred.",
    "alloy": "Use Alloy sig/fun/fact/run {} for N or check assertions.",
}

FIX_PROMPT_TEMPLATE = """The {language} proof you generated FAILED with this error:

ERROR:
{error}

ORIGINAL HYPOTHESIS:
{hypothesis}

YOUR PREVIOUS PROOF:
{previous_proof}

Fix the proof and return ONLY the corrected proof code."""

MAX_ITERATIONS = 3


@dataclass
class ProofAttempt:
    iteration: int = 0
    code: str = ""
    error: str = ""
    success: bool = False


@dataclass
class LLMProofResult:
    language: str
    hypothesis: str
    valid: bool
    proof: str = ""
    iterations: list[ProofAttempt] = field(default_factory=list)
    total_time_ms: float = 0.0
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        status = (
            "success"
            if self.valid
            else (
                "unavailable"
                if self.error
                and ("not installed" in self.error.lower() or "unavailable" in self.error.lower())
                else "partial"
            )
        )
        return {
            "language": self.language,
            "valid": self.valid,
            "status": status,
            "proof": self.proof[:500] + "..." if len(self.proof) > 500 else self.proof,
            "iterations": len(self.iterations),
            "total_time_ms": round(self.total_time_ms, 1),
            "error": self.error or None,
        }


from src.verification.rag_retriever import ProofExampleRetriever


_rag_retriever: ProofExampleRetriever | None = None


def _get_rag_retriever() -> ProofExampleRetriever:
    global _rag_retriever
    if _rag_retriever is None:
        _rag_retriever = ProofExampleRetriever()
    return _rag_retriever


def _retrieve_examples(hypothesis: str, language: str, k: int = 2) -> list[dict[str, str]]:
    """Retrieve top-k examples via RAG (TF-IDF + cosine similarity)."""
    retriever = _get_rag_retriever()
    return retriever.retrieve(hypothesis, language, k=k)


def _format_examples(examples: list[dict[str, str]], language: str) -> str:
    """Format examples for inclusion in prompt."""
    if not examples:
        return ""
    parts = ["\n## Examples:\n"]
    for i, ex in enumerate(examples, 1):
        parts.append(
            f"Example {i}:\nHypothesis: {ex['hypothesis']}\n{language} proof:\n{ex['proof']}\n"
        )
    return "\n".join(parts)


class LLMProver:
    """LLM-based formal proof generator with iterative error correction.

    Usage::

        prover = LLMProver()
        result = await prover.prove("sleep is active maintenance", "lean4")
        print(result.valid, result.proof[:200])
    """

    def __init__(self) -> None:
        self._router = DefaultGateway()
        self._client_cache: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def prove(
        self,
        hypothesis: str,
        language: str = "lean4",
        max_iterations: int = MAX_ITERATIONS,
    ) -> LLMProofResult:
        """Generate and iteratively fix a formal proof for ``hypothesis``."""
        start = time.perf_counter()
        language = language.lower()

        if language not in LANGUAGES:
            return LLMProofResult(
                language=language,
                hypothesis=hypothesis,
                valid=False,
                error=f"Unsupported language: {language}. Choose from: {LANGUAGES}",
            )

        if language == "agda":
            from src.verification.agda_bridge import AgdaBridge

            if not AgdaBridge().available:
                return LLMProofResult(
                    language=language,
                    hypothesis=hypothesis,
                    valid=False,
                    error="Agda unavailable (not installed). Install Agda or use another backend.",
                )

        iterations: list[ProofAttempt] = []
        proof_code = ""
        last_error = ""

        for i in range(max_iterations):
            if i == 0:
                code = await self._generate(hypothesis, language)
            else:
                code = await self._fix(hypothesis, language, proof_code, last_error)

            proof_code = code
            attempt = ProofAttempt(iteration=i + 1, code=code)
            iterations.append(attempt)

            if not code.strip():
                attempt.error = "Empty response from LLM"
                last_error = "Empty response from LLM"
                continue

            # Spoofing guard: reject proofs containing known cheat patterns (word-boundary aware)
            import re as _re

            code_lower = code.lower()
            cheat_patterns = {
                "lean4": [r"\bsorry\b"],
                "lean": [r"\bsorry\b"],
                "coq": [r"\badmitted\b", r"\babort\b"],
                "dafny": [r"\bassume\s+false\b", r"\{:verify\s+false\}", r"\{:axiom\}"],
                "agda": [r"\bpostulate\b"],
                "z3": [],
                "hoare": [],
            }
            cheats = cheat_patterns.get(language, [])
            if any(_re.search(c, code_lower) for c in cheats):
                attempt.error = f"Proof rejected: contains forbidden pattern ({', '.join(cheats)})"
                last_error = attempt.error
                continue

            # Verify with native prover
            verifier = self._get_verifier(language)
            try:
                result = await verifier(code)
            except Exception as e:
                attempt.error = f"Verifier error: {e}"
                last_error = attempt.error
                continue

            attempt.success = result.get("valid") or result.get("success", False)
            if not attempt.success and str(result.get("status", "")).lower() == "unavailable":
                err_list = result.get("errors") or []
                if err_list and isinstance(err_list[0], dict):
                    last_error = str(err_list[0].get("message", "Agda not installed"))
                else:
                    last_error = str(result.get("error") or "Verifier unavailable (not installed)")
                total_time = (time.perf_counter() - start) * 1000
                return LLMProofResult(
                    language=language,
                    hypothesis=hypothesis,
                    valid=False,
                    proof=proof_code,
                    iterations=iterations,
                    total_time_ms=total_time,
                    error=last_error,
                )

            if attempt.success:
                total_time = (time.perf_counter() - start) * 1000
                return LLMProofResult(
                    language=language,
                    hypothesis=hypothesis,
                    valid=True,
                    proof=code,
                    iterations=iterations,
                    total_time_ms=total_time,
                )

            # Extract error for next iteration
            if isinstance(result, dict):
                err = result.get("error") or result.get("output", "")
                if isinstance(err, dict):
                    err = str(err.get("error", ""))
                # Normalize structured error lists (Lean4/Coq/Agda/Dafny)
                if not err and "errors" in result:
                    errors_list = result["errors"]
                    if isinstance(errors_list, list) and errors_list:
                        err = "; ".join(
                            str(e.get("message", e)) if isinstance(e, dict) else str(e)
                            for e in errors_list[:3]
                        )
                if not err:
                    if "output" in result:
                        err = str(result["output"])
                    elif "details" in result:
                        err = str(result["details"])
                last_error = str(err)[:500] if err else "Verification failed (no error details)"
            else:
                last_error = f"Unrecognized result type: {type(result).__name__}"
            attempt.error = last_error

        total_time = (time.perf_counter() - start) * 1000
        return LLMProofResult(
            language=language,
            hypothesis=hypothesis,
            valid=False,
            proof=proof_code,
            iterations=iterations,
            total_time_ms=total_time,
            error=last_error or "Max iterations reached without valid proof",
        )

    # ------------------------------------------------------------------
    # LLM calls
    # ------------------------------------------------------------------

    async def _generate(self, hypothesis: str, language: str) -> str:
        """Generate an initial proof via LLM with few-shot examples."""
        examples = _retrieve_examples(hypothesis, language, k=2)
        examples_text = _format_examples(examples, language)
        prompt = PROOF_PROMPT_TEMPLATE.format(
            hypothesis=_sanitize_for_prompt(hypothesis, 1000),
            language=language,
            language_hints=LANGUAGE_HINTS.get(language, ""),
        )
        if examples_text:
            prompt = (
                prompt
                + "\n"
                + examples_text
                + "\nNow generate the proof for the hypothesis above.\n"
            )
        return await self._call_llm(prompt, language)

    async def _fix(self, hypothesis: str, language: str, previous: str, error: str) -> str:
        """Fix a proof given compilation error."""
        prompt = FIX_PROMPT_TEMPLATE.format(
            language=language,
            error=_sanitize_for_prompt(error, 1000),
            hypothesis=_sanitize_for_prompt(hypothesis, 500),
            previous_proof=_sanitize_for_prompt(previous, 2000),
        )
        return await self._call_llm(prompt, language)

    async def _call_llm(self, prompt: str, language: str) -> str:
        """Call the LLM via ProviderRouter.

        ``ProviderRouter.generate(stage_name, prompt)`` returns an
        ``LLMResponse`` with ``.content``, ``.model``, ``.usage``.
        """
        try:
            response = await self._router.generate_for_stage(
                stage_name="proof_generation",
                prompt=prompt,
            )
            # ProviderRouter returns LLMResponse with .content attribute
            if hasattr(response, "content"):
                text = response.content
            elif isinstance(response, dict):
                text = response.get("content") or response.get("text", "")
            else:
                text = str(response)
            return self._extract_code(text, language)
        except Exception:
            return ""

    @staticmethod
    def _extract_code(text: str, language: str) -> str:
        """Extract proof code from LLM response (handles markdown code blocks)."""
        import re

        lang_variants = [
            language,
            {
                "lean4": "lean",
                "coq": "coq",
                "dafny": "dafny",
                "agda": "agda",
                "z3": "z3",
                "hoare": "hoare",
                "cvc5": "smt2",
                "tla": "tla",
                "alloy": "alloy",
            }.get(language, language),
        ]
        for variant in lang_variants:
            # Find the outermost fenced block for this language
            pattern = rf"```{re.escape(variant)}\s*\n(.*?)```"
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                # Return the longest match to avoid truncation by inner fences
                return max(matches, key=len).strip()

        # Fallback: any ``` fence
        any_fence = re.findall(r"```(?:\w*)?\s*\n(.*?)```", text, re.DOTALL)
        if any_fence:
            return max(any_fence, key=len).strip()

        # No fence — return entire text (strip markdown)
        lines = text.split("\n")
        cleaned = [l for l in lines if not l.startswith("```")]
        return "\n".join(cleaned).strip()

    # ------------------------------------------------------------------
    # Verifier dispatch
    # ------------------------------------------------------------------

    def _get_verifier(self, language: str) -> Any:
        """Get an async verifier function for the given language."""
        if language in self._client_cache:
            return self._client_cache[language]

        dispatch: dict[str, tuple[str, str, str]] = {
            "lean4": ("src.verification.lean4_client", "Lean4Client", "check_proof"),
            "coq": ("src.verification.coq_client", "CoqClient", "check_proof"),
            "dafny": ("src.verification.dafny_client", "DafnyClient", "verify"),
            "agda": ("src.verification.agda_bridge", "AgdaBridge", "type_check"),
            "cvc5": ("src.verification.cvc5_client", "CVC5Client", "verify"),
            "tla": ("src.verification.tla_client", "TLAClient", "verify"),
            "alloy": ("src.verification.alloy_client", "AlloyClient", "verify"),
        }

        config = dispatch.get(language)
        if config:
            mod_path, cls_name, method = config
            try:
                mod = importlib.import_module(mod_path)
                cls = getattr(mod, cls_name)
                instance = cls()
                verifier = self._make_verifier(instance, method)
                self._client_cache[language] = verifier
                return verifier
            except Exception as e:
                e_msg = str(e)

                async def err_fn(code: str) -> dict[str, Any]:
                    return {
                        "valid": False,
                        "error": f"Cannot initialize {language} verifier: {e_msg}",
                    }

                self._client_cache[language] = err_fn
                return err_fn

        if language == "z3":
            self._client_cache[language] = self._verify_z3
            return self._verify_z3

        if language == "hoare":
            self._client_cache[language] = self._verify_hoare
            return self._verify_hoare

        async def unsupported(code: str) -> dict[str, Any]:
            return {"valid": False, "error": f"No verifier for {language}"}

        self._client_cache[language] = unsupported
        return unsupported

    @staticmethod
    def _make_verifier(instance: Any, method: str) -> Any:
        """Create an async verifier wrapper around a sync/async client."""
        fn = getattr(instance, method)
        import asyncio

        async def verify(code: str) -> dict[str, Any]:
            if inspect.iscoroutinefunction(fn):
                return await fn(code) or {}
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, fn, code) or {}

        return verify

    @staticmethod
    def _verify_z3(code: str) -> dict[str, Any]:
        """Verify Z3 code via SMT-LIB2.

        Z3 ``unsat`` means the assertion is valid (no counterexample exists).
        ``sat`` means a counterexample was found (assertion is NOT valid).
        """
        import z3

        try:
            code_stripped = code.strip()
            if not code_stripped:
                return {"valid": False, "error": "Empty Z3 code"}
            # Spoofing guard: must contain at least one assert
            if "assert" not in code_stripped.lower():
                return {
                    "valid": False,
                    "error": "Z3 proof rejected: no assertions found (vacuous proof)",
                }
            s = z3.Solver()
            s.set("timeout", 5000)
            s.from_string(code)
            result = s.check()
            # unsat = valid (negation is unsatisfiable = original is true)
            return {"valid": result == z3.unsat, "status": str(result)}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    @staticmethod
    def _verify_hoare(code: str) -> dict[str, Any]:
        """Verify Hoare triple."""
        from src.verification.hoare_verifier import HoareVerifier

        hv = HoareVerifier()
        result = hv.verify(code)
        return {"valid": result.valid, "error": result.error, "details": result.counterexample}
