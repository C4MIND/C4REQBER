"""Pipeline step: formal verification via LLM-based proof generation."""

from __future__ import annotations

from typing import Any

from src.verification.llm_prover import LLMProver


class Step10Verify:
    """Pipeline step to verify discoveries via formal proof generation."""

    async def run(self, discovery: dict[str, Any]) -> dict[str, Any]:
        """Process a discovery, attempt formal verification.

        Args:
            discovery: Discovery dict to verify

        Returns:
            Updated discovery dict with verification status
        """
        prover = LLMProver()
        hypothesis = discovery.get("hypothesis", {}).get("text", str(discovery)[:500])
        result = await prover.prove(hypothesis, "lean4")

        discovery["formal_verification"] = result.to_dict()
        # Compilation success alone is not claim-aligned formal verification.
        if result.valid:
            discovery["verification_stamp"] = "COMPILED"
            discovery["verification_aligned"] = False
            discovery["verification_note"] = (
                "Proof artifact compiled; SemanticAlignmentChecker not run — "
                "not stamped FORMALLY VERIFIED"
            )
        else:
            discovery["verification_stamp"] = (
                f"VERIFICATION FAILED: {result.error or 'Unknown error'}"
            )
            discovery["verification_aligned"] = False
        return discovery
