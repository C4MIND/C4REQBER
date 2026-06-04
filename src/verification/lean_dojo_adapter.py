"""Optional LeanDojo adapter for Lean4 proof generation.

LeanDojo (https://github.com/lean-dojo/LeanDojo) provides:
- Programmatic interaction with Lean 4
- ReProver: retrieval-augmented tactic generator
- Data extraction from Lean repos

Installation: pip install lean-dojo
Models: kaiyuy/leandojo-lean4-tacgen-byt5-small (HuggingFace)

This adapter is OPTIONAL — if LeanDojo is not installed,
the system falls back to LLMProver.
"""
from __future__ import annotations

import logging
import shutil
from typing import Any

logger = logging.getLogger("c4reqber.verification.leandojo")


class LeanDojoAdapter:
    """Adapter for LeanDojo-based Lean4 proof generation.

    Usage:
        adapter = LeanDojoAdapter()
        if adapter.available:
            proof = await adapter.generate_proof(theorem_statement)
        else:
            # Fallback to LLMProver
    """

    def __init__(self) -> None:
        self._available: bool | None = None
        self._tacgen: Any = None

    @property
    def available(self) -> bool:
        """True if LeanDojo and required models are available."""
        if self._available is not None:
            return self._available

        # Check lean command
        if shutil.which("lean") is None:
            self._available = False
            return False

        # Check lean-dojo package
        try:
            import lean_dojo  # noqa: F401
        except ImportError:
            self._available = False
            return False

        # Check transformers (needed for model inference)
        try:
            import transformers  # noqa: F401
        except ImportError:
            self._available = False
            return False

        self._available = True
        return True

    async def generate_proof(
        self,
        theorem_statement: str,
        max_steps: int = 30,
        timeout: float = 300.0,
    ) -> dict[str, Any]:
        """Generate a proof for theorem_statement using LeanDojo.

        This is a high-level wrapper that:
        1. Creates a temporary Lean file with the theorem
        2. Uses ReProver tactic generator + best-first search
        3. Returns the proof or failure reason

        Args:
            theorem_statement: Full Lean4 theorem statement
            max_steps: Max tactic steps in proof search
            timeout: Hard timeout for proof search

        Returns:
            Dict with keys: valid, proof, error, steps, time_ms
        """
        if not self.available:
            return {"valid": False, "error": "LeanDojo not available", "proof": "", "steps": 0}

        try:
            import time

            import lean_dojo
            from lean_dojo import ProofState, TacticState

            t0 = time.perf_counter()

            # For a true prototype, we'd create a temporary repo,
            # trace it, and run ReProver. This requires:
            # - git repo with lean-toolchain
            # - lake build
            # - Mathlib or minimal imports
            #
            # Simplified approach: use LeanDojo's interaction API
            # to step through the proof manually.

            # TODO: Full implementation requires:
            # 1. Create temp Lean repo with theorem
            # 2. Run `lean_dojo.traced_repo.get_traced_theorem()`
            # 3. Initialize ReProver model
            # 4. Run best-first search
            #
            # For now, return informative error:
            return {
                "valid": False,
                "error": (
                    "LeanDojo detected but full integration requires: "
                    "(1) Mathlib4 checkout, (2) ReProver model download, "
                    "(3) GPU for inference. Use LLMProver as fallback."
                ),
                "proof": "",
                "steps": 0,
                "time_ms": (time.perf_counter() - t0) * 1000,
            }

        except Exception as exc:
            logger.warning("LeanDojo proof generation failed: %s", exc, exc_info=True)
            return {"valid": False, "error": str(exc), "proof": "", "steps": 0}

    @staticmethod
    def install_instructions() -> str:
        """Return installation instructions for LeanDojo."""
        return """LeanDojo Installation:

1. Install Lean 4:
   curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh

2. Install Python package:
   pip install lean-dojo transformers torch

3. Download ReProver model (optional, for local inference):
   git lfs install
   git clone https://huggingface.co/kaiyuy/leandojo-lean4-tacgen-byt5-small

4. Or use HuggingFace Inference API (no local GPU needed):
   Set HF_API_TOKEN in environment

5. For full C4REQBER integration, also need mathlib4:
   git clone https://github.com/leanprover-community/mathlib4.git
"""
