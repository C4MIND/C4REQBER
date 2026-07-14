from __future__ import annotations

import logging
from typing import Any


logger = logging.getLogger(__name__)


async def c4_prove(hypothesis: str, language: str = "lean4") -> dict[str, Any]:
    """Prove a hypothesis using LLM-based formal proof generation + iterative error correction.

    Uses an LLM (Claude/GPT/DeepSeek) to generate a formal proof in the
    target language, then compiles it with the native prover.
    On error, the LLM receives the error and fixes the proof.
    Repeats up to 3 iterations.

    Args:
        hypothesis: Natural-language hypothesis to prove
        language: Target language (lean4, coq, dafny, agda, z3, hoare, cvc5, tla, alloy)

    Returns:
        Dict with valid, proof, iterations, error
    """
    try:
        from src.verification.llm_prover import LLMProver

        prover = LLMProver()
        result = await prover.prove(hypothesis, language, max_iterations=3)
        return result.to_dict()
    except Exception as e:
        logger.exception("MCP tool failed")
        return {"valid": False, "error": str(e)}
