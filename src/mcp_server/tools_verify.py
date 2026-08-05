from __future__ import annotations

import logging
import re
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

_SORRY_RE = re.compile(r"\b(sorry|admit)\b", re.I)


def _reject_placeholders(code: str, language: str) -> dict[str, Any] | None:
    """Fail-closed on sorry/admit for Lean/Coq (typecheck ≠ proof)."""
    lang = (language or "").lower()
    if lang not in {"lean4", "lean", "coq"}:
        return None
    if _SORRY_RE.search(code or ""):
        return {
            "valid": False,
            "status": "error",
            "stamp": "",
            "proof": code,
            "language": language,
            "error": "Empty/placeholder proof rejected: remove sorry/admit",
        }
    return None


def _verify_envelope(
    *,
    valid: bool,
    language: str,
    code: str,
    details: Any = None,
    error: str | None = None,
    compiled_only: bool = True,
) -> dict[str, Any]:
    """Honest outer status: compile success → partial/COMPILED, never success-as-verified."""
    if error and not valid:
        status = (
            "unavailable"
            if "not installed" in error.lower() or "unavailable" in error.lower()
            else "error"
        )
        stamp = ""
    elif valid and compiled_only:
        status = "partial"
        stamp = "COMPILED"
    elif valid:
        status = "success"
        stamp = "FORMALLY VERIFIED"
    else:
        status = "partial"
        stamp = ""
    out: dict[str, Any] = {
        "valid": valid,
        "status": status,
        "stamp": stamp,
        "verification_aligned": False,
        "proof": code,
        "language": language,
        "details": details,
        "error": error,
    }
    return out


async def c4_verify(code: str, language: str | None = None) -> dict[str, Any]:
    """Verify formal proof in lean4, coq, dafny, agda, z3, hoare, cvc5, tla, or alloy."""
    try:
        if not HAS_TOOLS:
            return {"error": "Verification module not available", "status": "unavailable"}

        if not language:
            calibrator = VerificationCalibrator()
            language = calibrator.select_backend(code, VerificationContext())

        blocked = _reject_placeholders(code, language or "")
        if blocked:
            return blocked

        if language == "lean4":
            client = Lean4Client()
            if not client.available:
                return _verify_envelope(
                    valid=False, language=language, code=code, error="Lean4 not installed"
                )
            result = client.check_proof(code)
            ok = bool(result.get("success", False))
            return _verify_envelope(
                valid=ok,
                language=language,
                code=code,
                details=result,
                error=None if ok else str(result.get("error") or "lean4 check failed"),
            )
        elif language == "coq":
            client = CoqClient()
            if not client.is_available():
                return _verify_envelope(
                    valid=False, language=language, code=code, error="Coq not installed"
                )
            result = client.check_proof(code)
            ok = bool(result.get("valid", False))
            return _verify_envelope(
                valid=ok,
                language=language,
                code=code,
                details=result,
                error=None if ok else str(result.get("error") or "coq check failed"),
            )
        elif language == "dafny":
            client = DafnyClient()
            if not client.is_available():
                return _verify_envelope(
                    valid=False, language=language, code=code, error="Dafny not installed"
                )
            result = client.verify(code)
            ok = bool(result.get("valid", False))
            return _verify_envelope(
                valid=ok,
                language=language,
                code=code,
                details=result,
                error=None if ok else str(result.get("error") or "dafny verify failed"),
            )
        elif language == "agda":
            client = AgdaBridge()
            if not client.available:
                return _verify_envelope(
                    valid=False, language=language, code=code, error="Agda not installed"
                )
            result = client.type_check(code)
            ok = bool(result.get("success", False))
            return _verify_envelope(
                valid=ok,
                language=language,
                code=code,
                details=result,
                error=None if ok else str(result.get("error") or "agda check failed"),
            )
        elif language == "z3":
            from src.mcp_server.z3_verify import verify_z3_mcp

            try:
                z3_out = verify_z3_mcp(code, language)
                # Z3 sat ≠ verified — preserve z3 helper honesty if present
                if "status" not in z3_out:
                    z3_out["status"] = "partial" if z3_out.get("valid") else "error"
                    z3_out.setdefault("verification_aligned", False)
                return z3_out
            except (ValueError, RuntimeError) as e:
                logger.warning("Z3 verification error: language=%s error=%s", language, e)
                return _verify_envelope(
                    valid=False, language=language, code=code, error=f"Z3 error: {e}"
                )
        elif language == "hoare":
            from src.verification.hoare_verifier import HoareVerifier

            hv = HoareVerifier()
            result = hv.verify(code)
            return _verify_envelope(
                valid=result.valid,
                language=language,
                code=code,
                details=result.to_dict(),
                error=result.error or None,
                compiled_only=True,
            )
        elif language == "cvc5":
            from src.verification.cvc5_client import CVC5Client

            client = CVC5Client()
            if not client.is_available():
                return _verify_envelope(
                    valid=False, language=language, code=code, error="CVC5 not installed"
                )
            result = client.verify(code)
            ok = bool(result.get("valid", False))
            return _verify_envelope(
                valid=ok,
                language=language,
                code=code,
                details=result,
                error=None if ok else str(result.get("error") or "cvc5 failed"),
            )
        elif language in ("tla", "tla+"):
            from src.verification.tla_client import TLAClient

            client = TLAClient()
            if not client.is_available():
                return _verify_envelope(
                    valid=False, language="tla", code=code, error="TLA+ TLC not installed"
                )
            result = client.verify(code)
            ok = bool(result.get("valid", False))
            return _verify_envelope(
                valid=ok,
                language="tla",
                code=code,
                details=result,
                error=None if ok else str(result.get("error") or "tla failed"),
            )
        elif language == "alloy":
            from src.verification.alloy_client import AlloyClient

            client = AlloyClient()
            if not client.is_available():
                return _verify_envelope(
                    valid=False, language=language, code=code, error="Alloy not installed"
                )
            result = client.verify(code)
            ok = bool(result.get("valid", False))
            return _verify_envelope(
                valid=ok,
                language=language,
                code=code,
                details=result,
                error=None if ok else str(result.get("error") or "alloy failed"),
            )
        elif language in ("haskell", "haskell-typecheck"):
            from src.verification.haskell_bridge import verify_haskell_typecheck

            result = verify_haskell_typecheck(code)
            valid = result.get("status") == "passed"
            return _verify_envelope(
                valid=valid,
                language="haskell-typecheck",
                code=code,
                details=result,
                error=None if valid else str(result.get("error", result.get("message", ""))),
            )
        elif language == "haskell-quickcheck":
            from src.verification.haskell_bridge import verify_haskell_quickcheck

            result = verify_haskell_quickcheck(code)
            valid = result.get("status") == "passed"
            return _verify_envelope(
                valid=valid,
                language="haskell-quickcheck",
                code=code,
                details=result,
                error=None if valid else str(result.get("error", result.get("message", ""))),
            )
        else:
            return _verify_envelope(
                valid=False,
                language=language or "unknown",
                code=code,
                error=f"Unsupported language: {language}",
            )
    except (AttributeError, ImportError) as e:
        logger.warning("MCP tool optional dep missing: %s", e)
        return {"error": str(e), "status": "unavailable"}
