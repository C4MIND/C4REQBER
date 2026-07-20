from __future__ import annotations

import logging
from typing import Any

from src.mcp_server.tool_dependencies import (
    HAS_TOOLS,
    AgdaBridge,
    CoqClient,
    DafnyClient,
    Lean4Client,
    VerificationCalibrator,
    VerificationContext,
)


logger = logging.getLogger(__name__)


async def c4_verify(code: str, language: str | None = None) -> dict[str, Any]:
    """Verify formal proof in lean4, coq, dafny, agda, z3, hoare, cvc5, tla, or alloy."""
    try:
        if not HAS_TOOLS:
            return {"error": "Verification module not available"}

        if not language:
            calibrator = VerificationCalibrator()
            language = calibrator.select_backend(code, VerificationContext())

        if language == "lean4":
            client = Lean4Client()
            if not client.available:
                return {"valid": False, "error": "Lean4 not installed"}
            result = client.check_proof(code)
            return {
                "valid": result.get("success", False),
                "proof": code,
                "language": language,
                "details": result,
            }
        elif language == "coq":
            client = CoqClient()
            if not client.is_available():
                return {"valid": False, "error": "Coq not installed"}
            result = client.check_proof(code)
            return {
                "valid": result.get("valid", False),
                "proof": code,
                "language": language,
                "details": result,
            }
        elif language == "dafny":
            client = DafnyClient()
            if not client.is_available():
                return {"valid": False, "error": "Dafny not installed"}
            result = client.verify(code)
            return {
                "valid": result.get("valid", False),
                "proof": code,
                "language": language,
                "details": result,
            }
        elif language == "agda":
            client = AgdaBridge()
            if not client.available:
                return {"valid": False, "error": "Agda not installed"}
            result = client.type_check(code)
            return {
                "valid": result.get("success", False),
                "proof": code,
                "language": language,
                "details": result,
            }
        elif language == "z3":
            from src.mcp_server.z3_verify import verify_z3_mcp

            try:
                return verify_z3_mcp(code, language)
            except (ValueError, RuntimeError) as e:
                logger.warning("Z3 verification error: language=%s error=%s", language, e)
                return {"valid": False, "error": f"Z3 error: {e}", "language": language}
        elif language == "hoare":
            from src.verification.hoare_verifier import HoareVerifier

            hv = HoareVerifier()
            result = hv.verify(code)
            return {
                "valid": result.valid,
                "proof": code,
                "language": language,
                "details": result.to_dict(),
                "error": result.error or None,
            }
        elif language == "cvc5":
            from src.verification.cvc5_client import CVC5Client

            client = CVC5Client()
            if not client.is_available():
                return {"valid": False, "error": "CVC5 not installed"}
            result = client.verify(code)
            return {
                "valid": result.get("valid", False),
                "proof": code,
                "language": language,
                "details": result,
            }
        elif language in ("tla", "tla+"):
            from src.verification.tla_client import TLAClient

            client = TLAClient()
            if not client.is_available():
                return {"valid": False, "error": "TLA+ TLC not installed"}
            result = client.verify(code)
            return {
                "valid": result.get("valid", False),
                "proof": code,
                "language": "tla",
                "details": result,
            }
        elif language == "alloy":
            from src.verification.alloy_client import AlloyClient

            client = AlloyClient()
            if not client.is_available():
                return {"valid": False, "error": "Alloy not installed"}
            result = client.verify(code)
            return {
                "valid": result.get("valid", False),
                "proof": code,
                "language": language,
                "details": result,
            }
        elif language in ("haskell", "haskell-typecheck"):
            from src.verification.haskell_bridge import verify_haskell_typecheck

            result = verify_haskell_typecheck(code)
            valid = result.get("status") == "passed"
            return {
                "valid": valid,
                "proof": code,
                "language": "haskell-typecheck",
                "details": result,
                "error": None if valid else str(result.get("error", result.get("message", ""))),
            }
        elif language == "haskell-quickcheck":
            from src.verification.haskell_bridge import verify_haskell_quickcheck

            result = verify_haskell_quickcheck(code)
            valid = result.get("status") == "passed"
            return {
                "valid": valid,
                "proof": code,
                "language": "haskell-quickcheck",
                "details": result,
                "error": None if valid else str(result.get("error", result.get("message", ""))),
            }
        else:
            return {"valid": False, "error": f"Unsupported language: {language}"}
    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e)}
